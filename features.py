from typing import Dict, List, Optional, Tuple, Any
from parsers import Entity  # Import the base Entity class
from mappings import (
    STATUS_MAP,
    MACHINE_NAME_MAP,
    MINING_TARGET_MAP,
    RECIPE_MAP
)

# --- Mappers ---

def map_rotation(rot: Optional[int]) -> Optional[int]:
    if rot is None:
        return None
    v = int(rot) % 16
    return v // 4  # 0..3

def map_status(status: Optional[int]) -> Optional[int]:
    if status is None:
        return None
    return STATUS_MAP.get(int(status), 2)  # default to "normal"=2

def bool_to_int(b: Optional[bool]) -> Optional[int]:
    if b is None:
        return None
    return 1 if b else 0

def map_machine(type_name: str) -> int:
    key = type_name.strip().lower()
    return MACHINE_NAME_MAP.get(key, 0)

def map_mining_target(name: Optional[str]) -> Optional[int]:
    if not name:
        return None
    return MINING_TARGET_MAP.get(name.strip().lower(), 0)

def map_recipe(name: Optional[str]) -> Optional[int]:
    if not name:
        return None
    return RECIPE_MAP.get(name.strip().lower(), 0)

# --- Feature Transformation ---

def compute_bounds(entities: List[Entity]) -> Tuple[int, int, int, int]:
    if not entities:
        return (0, 1, 0, 1)
    xs = [int(e.x) for e in entities]
    ys = [int(e.y) for e in entities]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # Avoid zero-range
    if min_x == max_x:
        max_x = min_x + 1
    if min_y == max_y:
        max_y = min_y + 1
    return (min_x, max_x, min_y, max_y)

def normalize_coord(v: int, min_v: int, max_v: int) -> float:
    # int -> normalize to [-1, 1]
    v_i = int(v)
    return -1.0 + 2.0 * ((v_i - min_v) / (max_v - min_v))

def to_feature_row(e: Entity, bounds: Tuple[int, int, int, int]) -> Dict[str, Any]:
    min_x, max_x, min_y, max_y = bounds
    base = {
        "machine": map_machine(e.type),
        "x": normalize_coord(e.x, min_x, max_x),
        "y": normalize_coord(e.y, min_y, max_y),
        "status": None,
        "energy": None,
        "is_crafting": None,
        "recipe": None,
        "mining_target": None,
        "rotation": None,
        "products_finished": None,
    }

    # Optional fields per entity type
    if hasattr(e, "status"):
        base["status"] = map_status(getattr(e, "status"))
    if hasattr(e, "energy"):
        base["energy"] = bool_to_int(getattr(e, "energy"))
    if hasattr(e, "is_crafting"):
        base["is_crafting"] = bool_to_int(getattr(e, "is_crafting"))
    if hasattr(e, "recipe_name"):
        base["recipe"] = map_recipe(getattr(e, "recipe_name"))
    if hasattr(e, "mining_target"):
        base["mining_target"] = map_mining_target(getattr(e, "mining_target"))
    if hasattr(e, "rotation"):
        base["rotation"] = map_rotation(getattr(e, "rotation"))
    if hasattr(e, "products_finished"):
        pf = getattr(e, "products_finished")
        base["products_finished"] = int(pf) if pf is not None else None

    return base

def transform_entities(entities: List[Entity]) -> List[Dict[str, Any]]:
    bounds = compute_bounds(entities)
    return [to_feature_row(e, bounds) for e in entities]