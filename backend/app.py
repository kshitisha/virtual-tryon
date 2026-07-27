from dotenv import load_dotenv
load_dotenv()
import os
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from catalog_service import load_catalog, get_item_by_id
from prompts import build_tryon_prompt, select_user_photo
from gemini_service import generate_tryon_image
from video_service import generate_video
app = FastAPI(title="Virtual Try-On API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_methods=["*"],
    allow_headers=["*"],)
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
app.mount("/catalog", StaticFiles(directory="catalog"), name="catalog")
@app.get("/catalog")
def get_catalog():
    """Returns the full jewellery catalogue. Frontend calls this on mount."""
    return load_catalog()
@app.post("/tryon")
async def tryon(
    item_id: str = Form(...),
    face_photo: UploadFile = File(None),
    hand_photo: UploadFile = File(None),
):
    """core endpoint. Accepts user photos + a catalogue item ID,
    runs gemini image generation, then video generation.
    returns URLs the frontend can display directly."""
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found in catalogue")
#yeh figure out karke whhich photo the jewellery type will need
    photo_type_needed = select_user_photo(item["type"])

    if photo_type_needed == "face" and not face_photo:
        raise HTTPException(status_code=400, detail="This jewellery type requires a face/upper-body photo")
    if photo_type_needed == "hand" and not hand_photo:
        raise HTTPException(status_code=400, detail="This jewellery type requires a hand photo")

    #this onw will save uploaded photos temporarily
    session_id = uuid.uuid4().hex[:8]
    saved_photos = {}

    for label, upload in [("face", face_photo), ("hand", hand_photo)]:
        if upload:
            ext = Path(upload.filename).suffix or ".jpg"
            save_path = UPLOAD_DIR / f"{session_id}_{label}{ext}"
            with open(save_path, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            saved_photos[label] = save_path
#this will pick the right photo based on jewellery type
    user_photo_path = saved_photos.get(photo_type_needed)
    #product image path comes from the catalogue
    product_image_path = Path(item["image"])
    if not product_image_path.exists():
        raise HTTPException(status_code=500, detail=f"Product image not found: {item['image']}")
#actual catch yeh hai
    prompt = build_tryon_prompt(item, photo_type_needed)
#this one will return raw image bytes
    try:
        image_bytes = await generate_tryon_image(
            prompt=prompt,
            user_photo_path=user_photo_path,
            product_image_path=product_image_path,)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini image generation failed: {str(e)}")
#this one will save the generated image
    output_image_name = f"{session_id}_result.png"
    output_image_path = OUTPUT_DIR / output_image_name
    with open(output_image_path, "wb") as f:
        f.write(image_bytes)
#video generatione liye this doesn't break the response if it fails
    output_video_url = None
    try:
        video_bytes = await generate_video(image_path=output_image_path, item=item)
        if video_bytes:
            output_video_name = f"{session_id}_result.mp4"
            output_video_path = OUTPUT_DIR / output_video_name
            with open(output_video_path, "wb") as f:
                f.write(video_bytes)
            output_video_url = f"/outputs/{output_video_name}"
    except Exception as e:
        #just incase video generation fails puura response nhi kill hoga
        print(f"[video] generation skipped: {e}")
#cleaning uploads
    for path in saved_photos.values():
        try:
            path.unlink()
        except Exception:
            pass
        return JSONResponse({
        "image_url": f"/outputs/{output_image_name}",
        "video_url": output_video_url,  #null agar video generation fail hua toh
        "item": item,
        "session_id": session_id,
    })