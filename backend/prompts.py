PHOTO_TYPE_MAP = {
    "ring": "hand",
    "bracelet": "hand",
    "necklace": "face",
    "earring": "face",
}

#how each jewellery type will physically sits on the body
PLACEMENT_INSTRUCTIONS = {
    "ring": (
        "place the ring on the ring finger of the hand in the photo. "
        "the band should wrap naturally around the finger with correct foreshortening. "
        "the stone or top face of the ring should face upward toward the camera."
    ),
    "bracelet": (
        "drape the bracelet naturally around the wrist in the photo. "
        "it should follow the curve of the wrist, with slight looseness — "
        "not rigid or perfectly horizontal. show natural contact with skin."
    ),
    "necklace": (
        "place the necklace so it drapes naturally along the collarbone and upper chest. "
        "the chain should follow the curve of the neckline. "
        "if layered, each chain should fall at a slightly different depth. "
        "the pendant, if present, should hang at the natural lowest point of the chain."
    ),
    "earring": (
        "attach the earrings to the earlobes. "
        "they should hang or sit exactly as the product image shows — "
        "match the orientation, drop length, and angle. "
        "both ears should show the earring if both are visible in the photo."
    ),}
MATERIAL_HINTS = {
    "yellow gold": "warm reflective gold surface, catches ambient light with soft highlights",
    "rose gold": "pinkish-gold tone, subtle warm sheen, not overly shiny",
    "white gold": "cool silver-toned metal, mirror-like finish, sharp specular highlights",
    "sterling silver": "cool grey-white metal, slightly matte with gentle reflections",
    "freshwater pearl": "smooth ivory surface, soft lustre, subtle iridescence — not glossy plastic",
    "pearl": "smooth ivory surface, soft lustre, subtle iridescence — not glossy plastic",
}
def select_user_photo(jewellery_type: str) -> str:
    """returns which photo type ('face' or 'hand') is needed for this jewellery."""
    photo_type = PHOTO_TYPE_MAP.get(jewellery_type)
    if not photo_type:
        raise ValueError(f"Unknown jewellery type: '{jewellery_type}'. Expected one of {list(PHOTO_TYPE_MAP.keys())}")
    return photo_type
def build_tryon_prompt(item: dict, photo_type: str) -> str:
    """
    builds the full Gemini prompt for a try-on request.

    structured in four sections:
    1. role framing — tells Gemini how to approach the task
    2. placement instructions — anatomically specific positioning
    3. jewellery fidelity constraints — what must not change in the product
    4. photo fidelity constraints — what must not change in the user's photo
    """
    jewellery_type = item["type"]
    material = item["material"]
    name = item["name"]
    description = item["description"]
    placement_label = item.get("placement", "appropriate position")

    placement_instruction = PLACEMENT_INSTRUCTIONS.get(jewellery_type, "")
    material_hint = MATERIAL_HINTS.get(material, f"{material} surface with natural reflectance")

    # these two variables are set based on photo type, then used in the prompt below
    if photo_type == "face":
        user_photo_description = "the person's face and upper body photo"
        preserve_section = (
            "- do not alter the person's face, skin tone, hair, or expression\n"
            "- do not change the lighting direction or colour temperature of the photo\n"
            "- do not modify the background\n"
            "- do not change the person's clothing or neckline"
        )
    else:
        user_photo_description = "the hand photo"
        preserve_section = (
            "- do not alter the hand's skin tone, shape, or proportions\n"
            "- do not change the lighting direction or colour temperature of the photo\n"
            "- do not modify the background\n"
            "- do not add nail polish or change the fingernails unless already present"
        )

    # prompt is built here, after both branches have set their variables
    prompt = f"""You are a professional photo retoucher specialising in jewellery compositing.
Your task is to edit {user_photo_description} so that the person appears to be wearing the jewellery shown in the product image.
This is a precise editing task, not a creative one. Follow these instructions exactly.

---

JEWELLERY ITEM:
Name: {name}
Type: {jewellery_type}
Material: {material}
Description: {description}
Placement: {placement_label}

---

PLACEMENT:
{placement_instruction}

---

JEWELLERY FIDELITY — the following must be preserved exactly from the product image:
- the shape and silhouette of the jewellery must not change
- the colour and material finish must match the product image exactly: {material_hint}
- do not simplify, stylise, or reinterpret the design
- the jewellery must cast a natural shadow on the skin consistent with the photo's lighting
- the jewellery must not appear to float — it should make contact with the skin or body as it naturally would

---

PHOTO FIDELITY — the following must not change in the user's photo:
{preserve_section}

---

OUTPUT:
Produce a single photorealistic image that looks like a real photograph, not a digital render or illustration.
The jewellery should look like it was always part of the original photo.
Do not add any text, watermarks, or borders to the output image."""

    return prompt.strip()