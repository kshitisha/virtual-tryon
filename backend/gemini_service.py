from __future__ import annotations
import os
import asyncio
from pathlib import Path
from functools import partial
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
MOCK_IMAGE_PATH = Path(__file__).parent / "mock_assets" / "sample_result.png"
from google import genai
from google.genai import types
if not MOCK_MODE:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")
    client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash-image"
MIME_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",}
def _read_image_part(image_path: Path) -> types.Part:
    """reads an image from disk and returns it as a genai Part."""
    ext = image_path.suffix.lower()
    mime_type = MIME_TYPE_MAP.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
def _extract_image_bytes(response) -> bytes:
    """pulls image bytes out of the Gemini response.
iterates parts looking for inline image data.
raises with Gemini's explanation if no image came back."""
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return part.inline_data.data
    text_parts = [
        part.text for part in response.candidates[0].content.parts
        if part.text]
    reason = " | ".join(text_parts) if text_parts else "no explanation returned"
    raise ValueError(f"Gemini returned no image. Response: {reason}")
def _call_gemini(prompt: str, user_photo_path: Path, product_image_path: Path) -> bytes:
    """synchronous Gemini call — runs in a thread executor.
input order: prompt text -> user photo -> product image.
this mirrors how you'd brief a retoucher: explain the task,
show the canvas, then show the reference."""
    user_image_part = _read_image_part(user_photo_path)
    product_image_part = _read_image_part(product_image_path)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, user_image_part, product_image_part],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],),)
    return _extract_image_bytes(response)
async def generate_tryon_image(
    prompt: str,
    user_photo_path: Path,
    product_image_path: Path,
) -> bytes:
    """async wrapper — runs the blocking Gemini SDK call in a thread
    so FastAPI's event loop stays free during the API wait.

    if MOCK_MODE is on, skips Gemini entirely and returns the
    placeholder image instead — used when the API quota is exhausted
    but the rest of the pipeline (upload, prompt build, response
    handling) still needs to be demoed end-to-end."""
    if MOCK_MODE:
        with open(MOCK_IMAGE_PATH, "rb") as f:
            return f.read()
    loop = asyncio.get_event_loop()
    call = partial(_call_gemini, prompt, user_photo_path, product_image_path)
    return await loop.run_in_executor(None, call)