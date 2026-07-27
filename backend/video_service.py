import os
import time
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
KLING_API_KEY = os.getenv("KLING_API_KEY")
KLING_BASE_URL = "https://api.klingai.com"
#free tier is slow — 90s is generous but not infinite
POLL_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 5
def _is_video_enabled() -> bool:
    """video generation only runs if the API key is actually configured."""
    return bool(KLING_API_KEY)
def _build_headers() -> dict:
    return {
        "Authorization": f"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json",}
async def _submit_video_task(client: httpx.AsyncClient, image_path: Path, item: dict) -> str:
    """submits the image-to-video task to Kling.
    returns the task_id for polling.
we send a short, specific prompt so Kling knows what kind of
motion to generate — gentle rotation works well for jewellery.
    """#this will read the generated try on image as base64
    import base64
    with open(image_path, "rb") as f:
        image_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
#keep the motion prompt minimal and jewellery-specific
    motion_prompt = (
        f"Slow, gentle camera rotation around the {item['type']}. "
        "Soft studio lighting. No sudden movement. Product showcase style.")
    payload = {
        "model": "kling-v1",
        "image": image_b64,
        "prompt": motion_prompt,
        "duration": 5,      #free tier supports up to 5s
        "cfg_scale": 0.5, }  #how closely to follow the prompt; 0.5 is a safe middle groun
    response = await client.post(
        f"{KLING_BASE_URL}/v1/images/image2video",
        headers=_build_headers(),
        json=payload,
        timeout=30.0,)
    response.raise_for_status()
    data = response.json()
    task_id = data.get("data", {}).get("task_id")
    if not task_id:
        raise ValueError(f"Kling did not return a task_id. Response: {data}")
    return task_id
async def _poll_until_done(client: httpx.AsyncClient, task_id: str) -> str:
    """polls the Kling task endpoint until status is 'succeed' or we time out.
    returns the video URL on success, raises on failure or timeout."""
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > POLL_TIMEOUT_SECONDS:
            raise TimeoutError(f"Kling video generation timed out after {POLL_TIMEOUT_SECONDS}s")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        response = await client.get(
            f"{KLING_BASE_URL}/v1/video/query/{task_id}",
            headers=_build_headers(),
            timeout=15.0,)
        response.raise_for_status()
        data = response.json()
        task_status = data.get("data", {}).get("task_status")
        if task_status == "succeed":
            #dig into the nested response for the actual video URL
            videos = data.get("data", {}).get("task_result", {}).get("videos", [])
            if not videos:
                raise ValueError("Kling returned succeed but no video URLs in response")
            return videos[0]["url"]
        elif task_status == "failed":
            reason = data.get("data", {}).get("task_status_msg", "unknown reason")
            raise RuntimeError(f"Kling video generation failed: {reason}")
#extra wait
        print(f"[video] task {task_id} still processing... ({elapsed:.0f}s elapsed)")
async def _download_video(client: httpx.AsyncClient, video_url: str) -> bytes:
    """Downloads the completed video from Kling's CDN."""
    response = await client.get(video_url, timeout=60.0)
    response.raise_for_status()
    return response.content
async def generate_video(image_path: Path, item: dict) -> bytes | None:
    """full video generation flow: submit → poll → download → return bytes.
    returns None if video generation is disabled (no API key).
    raises on actual API failures so app.py can log and continue.
 Args:
image_path: path to the generated try-on image (our Gemini output)
item: catalogue item dict, used to build the motion prompt"""
    if not _is_video_enabled():
        print("[video] KLING_API_KEY not set — skipping video generation")
        return None
    async with httpx.AsyncClient() as client:
        task_id = await _submit_video_task(client, image_path, item)
        print(f"[video] submitted task {task_id}, polling...")
        video_url = await _poll_until_done(client, task_id)
        print(f"[video] task {task_id} done, downloading...")
        video_bytes = await _download_video(client, video_url)
        print(f"[video] downloaded {len(video_bytes) / 1024:.1f}KB")
        return video_bytes