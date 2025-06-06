import json
from pathlib import Path
from typing import Dict
from .schemas import Product, Additive, Effect, Transformation

DATA_PATH = Path(__file__).parent.parent / "data"
PRODUCTS_FILE = DATA_PATH / "products.json"

def load_json_dict(path: Path) -> Dict[str, dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_products() -> Dict[str, Product]:
    raw = load_json_dict(DATA_PATH / "products.json")
    return {k: Product(**v) for k, v in raw.items()}

def load_additives() -> Dict[str, Additive]:
    raw = load_json_dict(DATA_PATH / "additives.json")
    return {k: Additive(**v) for k, v in raw.items()}

def load_effects() -> Dict[str, Effect]:
    raw = load_json_dict(DATA_PATH / "effects.json")
    return {k: Effect(**v) for k, v in raw.items()}

def load_transformations() -> Dict[str, Transformation]:
    raw = load_json_dict(DATA_PATH / "transformations.json")
    return {k: Transformation(**v) for k, v in raw.items()}

def load_ranks() -> list[str]:
    raw = load_json_dict(DATA_PATH / "ranks.json")
    return list(raw)

def load_effect_rules_nested() -> Dict[str, Dict[str, str]]:
    raw = load_json_dict(DATA_PATH / "EffectRulesNested.json")
    return raw  # raw is already Dict[str, Dict[str, str]]

def save_products(products: Dict[str, Product]) -> None:
    """
    Overwrites products.json with the given Pydantic‐schema Product objects.
    """
    # If each product is a Pydantic model, use `.dict()`. Otherwise, fall back to to_dict()
    output_dict = {}
    for name, prod in products.items():
        if hasattr(prod, "dict"):        # Pydantic
            output_dict[name] = prod.dict()
        else:                             # fallback (if someone passed a dataclass)
            output_dict[name] = prod.to_dict()

    PRODUCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, indent=4)
