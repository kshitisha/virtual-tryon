from __future__ import annotations
import io
import os
import asyncio
from pathlib import Path
from functools import partial
from huggingface_hub import InferenceClient

#mock mode letting the rest of the app run/demo without hitting any real API
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
MOCK_IMAGE_PATH = Path(__file__).parent / "mock_assets" / "sample_result.png"

if not MOCK_MODE:
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN environment variable is not set")
    client = InferenceClient(provider="fal-ai", api_key=HF_TOKEN)


#note: unlike Gemini, this model edits ONE input image based on a text(ONLY REASON I CHOSE THIS)
#prompt — it has no way to "see" a second reference image. so the
#jewellery's look comes entirely from the text description in `prompt`
#(built in prompts.py from the catalogue item's material/type/description),
#not from the product photo itself. fidelity to the exact catalogue piece
#will be looser than Gemini's — this is the real tradeoff of the free route.
MODEL_NAME = "black-forest-labs/FLUX.1-Kontext-dev"


def _call_flux(prompt: str, user_photo_path: Path) -> bytes:
    """synchronous HF Inference call — runs in a thread executor."""
    with open(user_photo_path, "rb") as f:
        input_image = f.read()

    #returns a PIL.Image object
    result_image = client.image_to_image(
        input_image,
        prompt=prompt,
        model=MODEL_NAME,
    )

    buf = io.BytesIO()
    result_image.save(buf, format="PNG")
    return buf.getvalue()


async def generate_tryon_image(
    prompt: str,
    user_photo_path: Path,
    product_image_path: Path,
) -> bytes:
    """async wrapper — runs the blocking HF call in a thread so FastAPI's
    event loop stays free during the API wait.

    if MOCK_MODE is on, skips the real call entirely and returns the
    placeholder image instead.

    product_image_path is accepted for compatibility with app.py's call
    site but isn't used here — FLUX Kontext can't take a second reference
    image the way Gemini could, so it's kept only so app.py needs no changes."""
    if MOCK_MODE:
        with open(MOCK_IMAGE_PATH, "rb") as f:
            return f.read()
    loop = asyncio.get_event_loop()
    call = partial(_call_flux, prompt, user_photo_path)
    return await loop.run_in_executor(None, call)