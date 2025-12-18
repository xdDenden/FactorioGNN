from rcon_bridge_1_0_0.rcon_bridge import CharInfo
from typing import Dict, List, Optional, Tuple, Any
from parsers import Entity  # Import the base Entity class
from mappings import (
    STATUS_MAP,
    MACHINE_NAME_MAP,
    MINING_TARGET_MAP,
    RECIPE_MAP,
    ITEM_MAP
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


def map_items(char_info: CharInfo, bounds: Tuple[int, int, int, int]) -> Dict[str, Any]:
    """
    Maps player inventory to item IDs and normalizes player position
    using the provided entity bounds.
    """
    min_x, max_x, min_y, max_y = bounds

    # Normalize Player Position
    # Handle cases where pos might be missing or None
    pos = char_info.get("pos", {"x": 0, "y": 0})
    raw_x: float = pos.get("x", 0)
    raw_y: float = pos.get("y", 0)

    norm_x = normalize_coord(raw_x, min_x, max_x)
    norm_y = normalize_coord(raw_y, min_y, max_y)

    # Map Inventory
    # Structure: { item_id_int: count_int, ... }
    inventory_map = {}
    raw_inventory = char_info.get("inventory", [])

    for item in raw_inventory:
        name = item.get("name", "")
        count = item.get("count", 0)

        # Match against ITEM_MAP keys (lowercase, stripped)
        clean_name = name.strip().lower()
        item_id = ITEM_MAP.get(clean_name, 0)

        if item_id != 0:
            inventory_map[item_id] = count

    return {
        "x": norm_x,
        "y": norm_y,
        "inventory": inventory_map
    }


# --- Feature Transformation ---

def compute_bounds(entities: List[Entity], char_info: Optional[CharInfo] = None, radius: int = 64) -> Tuple[
    int, int, int, int]:
    # 1. Determine Center Point (Player Position)
    # Default to 0,0 if char_info is missing
    pos = char_info.get("pos", {"x": 0, "y": 0}) if char_info else {"x": 0, "y": 0}

    center_x = int(pos.get("x", 0))
    center_y = int(pos.get("y", 0))

    # REMOVED: The block that calculated the average of entities and caused the crash.

    # 2. Calculate Bounds
    min_x = center_x - radius
    max_x = center_x + radius
    min_y = center_y - radius
    max_y = center_y + radius

    return (min_x, max_x, min_y, max_y)


def normalize_coord(v: int, min_v: int, max_v: int) -> float:
    # int -> normalize to [-1, 1]
    v_i = int(v)
    return -1.0 + 2.0 * ((v_i - min_v) / (max_v - min_v))


def unnormalize_coord(v_norm: float, min_v: int, max_v: int) -> int:
    v_original = min_v + ((v_norm + 1.0) / 2.0) * (max_v - min_v)

    # Round to nearest integer to restore original int type
    return int(round(v_original))


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
    if hasattr(e, "ore_name"):
        base["mining_target"] = map_mining_target(getattr(e, "ore_name"))
    return base


def transform_entities(entities: List[Entity], bounds: Optional[Tuple[int, int, int, int]] = None) -> List[
    Dict[str, Any]]:
    # If bounds aren't passed, compute them from entities alone (fallback)
    if bounds is None:
        bounds = compute_bounds(entities)
    return [to_feature_row(e, bounds) for e in entities]