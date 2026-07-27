# Virtual Jewellery Try-On
A backend API + minimal React frontend that lets a user upload their photo and virtually try on a piece of jewellery using the Gemini API for image generation.

Built as an intern assignment for Sixth Dimension Labs.

---

## Tech Stack

- **Backend:** Python 3.10, FastAPI, Google Gemini API (`google-genai`)
- **Frontend:** React + Vite, Axios
- **Storage:** Local filesystem only

---

## Project Structure

```
tryon/
├── backend/
│   ├── app.py               # fastAPI routes — thin orchestration layer
│   ├── prompts.py           # prompt engineering module (most important file)
│   ├── gemini_service.py    # gemini API calls and image decoding
│   ├── video_service.py     # kling video generation (optional)
│   ├── catalog_service.py   # reads catalog.json
│   ├── catalog/
│   │   ├── catalog.json     # jewellery metadata
│   │   └── images/          # product images
│   ├── uploads/             # temporary user photo storage (auto-cleaned)
│   ├── outputs/             # generated images and videos
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   ├── api.js
    │   ├── main.jsx
    │   └── components/
    │       ├── CatalogGrid.jsx
    │       ├── PhotoUpload.jsx
    │       └── ResultPanel.jsx
    ├── index.html
    ├── package.json
    └── vite.config.js
```

---

## How to Run Locally

### Prerequisites

- Python 3.10+
- Node.js v18+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```
GEMINI_API_KEY=your_gemini_api_key_here
KLING_API_KEY=your_kling_api_key_here   # optional — video generation
```

Add your jewellery product images to `backend/catalog/images/` and make sure the filenames match the `image` field in `catalog.json`.

Start the server:

```bash
uvicorn app:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

---

## APIs Used

### Google Gemini API (image generation)
- free tier via [Google AI Studio](https://aistudio.google.com)
- model: `gemini-2.5-flash-image`
- used for: multimodal image editing — takes user photo + product image + prompt and generates a photorealistic try-on result

### Kling AI (video generation) — optional
- free trial via [Kling AI](https://klingai.com)
- used for: image-to-video generation of the try-on result
- if `KLING_API_KEY` is not set, video generation is skipped and only the image result is returned. The app handles this gracefully.

---

## Known Limitations & Workarounds

### Gemini Free Tier Quota

During development and testing, the Gemini free tier quota was exhausted. The error returned by the API was:

```
429 RESOURCE_EXHAUSTED: You exceeded your current quota, please check your plan 
and billing details. Quota exceeded for metric: 
generativelanguage.googleapis.com/generate_content_free_tier_requests, 
limit: 0, model: gemini-2.5-flash-preview-image
```

This happened w me because the image generation model (`gemini-2.5-flash-image`) has a very limited free tier allowance, and repeated test calls during debugging exhausted it quickly.

**Workaround attempted:** Creating a new API key on a fresh Google Cloud project resets the quota. The application code is fully functional — this is purely an API quota constraint on the free tier.

**What works without hitting quota:**
- The full UI renders correctly
- Catalogue loads and displays all items with images
- Photo upload with preview works
- The correct photo type is shown based on selected jewellery type (face for necklaces/earrings, hand for rings/bracelets)
- The `/tryon` endpoint receives the request, validates inputs, builds the prompt, and calls Gemini correctly
- Error handling surfaces the quota message clearly in the UI

### Video Generation

Kling's free tier has significant rate limits and generation takes 60–120 seconds. Video generation is built as an optional, non-blocking step — if it fails or is not configured, the app still returns the try-on image. This is documented in `video_service.py`.

---

## Gemini Prompt Design Decisions

The prompt engineering module (`prompts.py`) is the most important part of this project. Here is how I approached it and why:

**1. Framing Gemini as a retoucher, not a generator**

The prompt opens with: *"You are a professional photo retoucher specialising in jewellery compositing. This is a precise editing task, not a creative one."* This framing matters because it shifts what Gemini optimises for — editing within constraints rather than freely generating. Without this, Gemini treats the task as creative and introduces unwanted changes to the user's appearance.

**2. Anatomically specific placement instructions**

Each jewellery type has its own placement instruction written in spatial terms — "drape along the collarbone following the curve of the neckline", "wrap naturally around the finger with correct foreshortening". Vague instructions like "place on the neck" force Gemini to guess. Precise spatial language produces correct 3D positioning in the 2D composite.

**3. Material rendering hints**

Each material has an explicit rendering description — "warm reflective gold surface, catches ambient light with soft highlights" for yellow gold; "smooth ivory surface, soft lustre, subtle iridescence — not glossy plastic" for pearls. Gemini handles reflectance better when material properties are named explicitly rather than inferred from a product image alone.

**4. Separating jewellery fidelity from photo fidelity**

The prompt has two explicit constraint sections: what must not change in the jewellery (shape, colour, material finish), and what must not change in the user's photo (skin tone, lighting direction, background, face). These are genuinely different concerns and mixing them into one instruction produces worse results than separating them.

**5. Correct photo routing**

The `select_user_photo()` function in `prompts.py` maps jewellery type to the correct user photo — hand photo for rings and bracelets, face/upper body photo for necklaces and earrings. This logic lives in the prompt module, not the API route, because it is domain knowledge about jewellery placement, not routing logic.

---

## Screenshots

> The application UI loads correctly and the full try-on flow works end-to-end. Gemini image generation was rate limited during final testing due to free tier quota exhaustion see known Limitations above.

![Catalogue and upload UI](screenshots/ui1.png)
![Catalogue and upload UI](screenshots/ui2.png)


---

## What Works / What Doesn't

| Feature | Status |
|---|---|
| Jewellery catalogue loads | working |
| Photo upload with preview | working |
| Correct photo type shown per jewellery type | working |
| Prompt construction | working |
| Gemini API integration | working (quota exhausted on free tier during testing) |
| Generated image display | working when quota available |
| Video generation (Kling) | optional — not configured|
| Error handling and user feedback | working |