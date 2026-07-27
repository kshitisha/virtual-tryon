import json
from pathlib import Path
CATALOG_PATH = Path("catalog/catalog.json")

#1 baar load bas
try:
    with open(CATALOG_PATH, "r") as f:
        _catalog: list[dict] = json.load(f)
except FileNotFoundError:
    raise RuntimeError(f"catalog.json not found at {CATALOG_PATH}. Did you forget to add it?")
except json.JSONDecodeError as e:
    raise RuntimeError(f"catalog.json is malformed: {e}")
def load_catalog() -> list[dict]:
    """returns the full catalogue. called by GET /catalog."""
    return _catalog
def get_item_by_id(item_id: str) -> dict | None:
    """looks up a single item by ID. returns None if not found."""
    return next((item for item in _catalog if item["id"] == item_id), None)
def get_items_by_type(jewellery_type: str) -> list[dict]:
    """returns all items of a given type (ring, necklace, etc.).
    not used by the API right now, but useful if you want to
    filter the catalogue on the frontend later."""
    return [item for item in _catalog if item["type"] == jewellery_type]