from rcon_bridge_1_0_0.rcon_reciever import Rcon_reciever
from dataclasses import dataclass
from typing import Dict, Callable, List, Optional, Tuple, Any

@dataclass
class Entity:
    type: str
    x: int
    y: int

@dataclass
class AssemblingMachine(Entity):
    status: Optional[int] = None
    is_crafting: Optional[bool] = None
    recipe_name: Optional[str] = None
    energy: Optional[bool] = None
    products_finished: Optional[int] = None

@dataclass
class TransportBelt(Entity):
    rotation: Optional[int] = None

@dataclass
class StoneFurnace(Entity):
    status: Optional[int] = None
    is_crafting: Optional[bool] = None

@dataclass
class BurnerMiningDrill(Entity):
    status: Optional[int] = None
    mining_target: Optional[str] = None

# --- Parser registry ---
Parser = Callable[[str, Dict[str, str]], Entity]
parsers: Dict[str, Parser] = {}

def register_many(type_names: List[str]):
    def deco(fn: Parser):
        for t in type_names:
            parsers[t] = fn
        return fn
    return deco

def default_parser(t: str, kv: Dict[str, str]) -> Entity:
    e = Entity(
        type=t,
        x=int(float(kv["x"])),
        y=int(float(kv["y"])),
    )
    # Attach common optional fields if present
    if "status" in kv:
        setattr(e, "status", int(kv["status"]))
    if "is_crafting" in kv:
        setattr(e, "is_crafting", to_bool(kv["is_crafting"]))
    if "recipe_name" in kv:
        setattr(e, "recipe_name", kv["recipe_name"])
    if "energy" in kv:
        setattr(e, "energy", to_bool(kv["energy"]))
    if "products_finished" in kv:
        setattr(e, "products_finished", int(kv["products_finished"]))
    if "rotation" in kv:
        setattr(e, "rotation", int(kv["rotation"]))
    if "mining_target" in kv:
        setattr(e, "mining_target", kv["mining_target"])
    return e

def parse_entity(type_name: str, kv: Dict[str, str]) -> Entity:
    # Use a specific parser if registered, else the generic fallback
    return parsers.get(type_name, default_parser)(type_name, kv)

def register(type_name: str):
    def deco(fn: Parser):
        parsers[type_name] = fn
        return fn
    return deco

def to_bool(v: str) -> bool:
    return v.lower() in ("true", "1")


STATUS_MAP: Dict[int, int] = {
    1: 1,   # working
    2: 2,   # normal
    5: 3,   # no_power
    7: 4,   # no_fuel
    23: 5,  # no_ingredients
    24: 6,  # no_input_fluid
    26: 7,  # no_minable_resources
    30: 8,  # full_output
    35: 9,  # missing_science_packs
}
# Unknown -> default to 2 (normal)

MACHINE_NAME_MAP: Dict[str, int] = {
    "assembling-machine-1": 1,
    "assembling-machine-2": 2,
    "burner-mining-drill": 3,
    "burner-inserter": 4,
    "transport-belt": 5,
    "small-electric-pole": 6,
    "medium-electric-pole": 7,
    "stone-furnace": 8,
    "steel-furnace": 9,
    "electric-furnace": 10,
    "boiler": 11,
    "offshore-pump": 12,
    "steam-engine": 13,
    "inserter": 14,
    "fast-inserter": 15,
    "bulk-inserter": 16,
    "long-handed-inserter": 17,
    "fast-transport-belt": 18,
    "express-transport-belt": 19,
    "pumpjack": 20,
    "oil-refinery": 21,
    "chemical-plant": 23,
    "underground-belt": 24,
    "fast-underground-belt": 25,
    "express-underground-belt": 26,
    "splitter": 27,
    "fast-splitter": 28,
    "express-splitter": 29,
    "pipe": 30,
    "pipe-to-ground": 31,
    "electric-mining-drill": 32,
    "assembling-machine-3": 33,
}

MINING_TARGET_MAP: Dict[str, int] = {
    "stone": 1,
    "iron-ore": 2,
    "copper-ore": 3,
    "coal": 4,
}

RECIPE_MAP: Dict[str, int] = {
    "battery": 1,
    "iron-plate": 2,
    "advanced-circuit": 3,
    "electronic-circuit": 4,
    "steel-chest": 5,
    "copper-cable": 6,
    "plastic-bar": 7,
    "processing-unit": 8,
    "iron-gear-wheel": 9,
    "steel-plate": 10,
    "engine-unit": 11,
    "pipe": 12,
    "assembling-machine-1": 13,
    "assembling-machine-2": 14,
    "atomic-bomb": 15,
    "copper-plate": 16,
    "sulfuric-acid": 17,
    "big-electric-pole": 18,
    "boiler": 19,
    "stone-furnace": 20,
    "burner-inserter": 21,
    "burner-mining-drill": 22,
    "chemical-plant": 23,
    "iron-ore": 24,
    "stone-brick": 25,
    "flying-robot-frame": 26,
    "copper-ore": 27,
    "electric-engine-unit": 28,
    "lubricant": 29,
    "electric-furnace": 30,
    "electric-mining-drill": 31,
    "sulfur": 32,
    "express-splitter": 33,
    "fast-splitter": 34,
    "express-transport-belt": 35,
    "fast-transport-belt": 36,
    "express-underground-belt": 37,
    "fast-underground-belt": 38,
    "fast-inserter": 39,
    "inserter": 40,
    "splitter": 41,
    "transport-belt": 42,
    "underground-belt": 43,
    "storage-tank": 44,
    "iron-stick": 45,
    "iron-chest": 46,
    "lab": 47,
    "landfill": 48,
    "long-handed-inserter": 49,
    "low-density-structure": 50,
    "medium-electric-pole": 51,
    "offshore-pump": 52,
    "oil-refinery": 53,
    "pipe-to-ground": 54,
    "power-switch": 55,
    "pump": 56,
    "pumpjack": 57,
    "solid-fuel": 58,
    "small-electric-pole": 59,
    "stack-inserter": 60,
    "steam-engine": 61,
    "steel-furnace": 62,
    "wooden-chest": 63,
    "automation-science-pack": 64,
    "logistic-science-pack": 65,
    "chemical-science-pack": 66,
    "assembling-machine-3": 67,
}

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

@register("assembling-machine-1")
def parse_assembling_machine(t: str, kv: Dict[str, str]) -> Entity:
    return AssemblingMachine(
        type=t,
        x=int(float(kv["x"])),
        y=int(float(kv["y"])),
        status=int(kv.get("status", 0)) if "status" in kv else None,
        is_crafting=to_bool(kv["is_crafting"]) if "is_crafting" in kv else None,
        recipe_name=kv.get("recipe_name"),
        energy=to_bool(kv["energy"]) if "energy" in kv else None,
        products_finished=int(kv["products_finished"]) if "products_finished" in kv else None,
    )

@register("transport-belt")
def parse_transport_belt(t: str, kv: Dict[str, str]) -> Entity:
    return TransportBelt(
        type=t,
        x=int(float(kv["x"])),
        y=int(float(kv["y"])),
        rotation=int(kv.get("rotation", 0)) if "rotation" in kv else None,
    )

@register("stone-furnace")
def parse_stone_furnace(t: str, kv: Dict[str, str]) -> Entity:
    return StoneFurnace(
        type=t,
        x=int(float(kv["x"])),
        y=int(float(kv["y"])),
        status=int(kv.get("status", 0)) if "status" in kv else None,
        is_crafting=to_bool(kv["is_crafting"]) if "is_crafting" in kv else None,
    )

@register("burner-mining-drill")
def parse_burner_drill(t: str, kv: Dict[str, str]) -> Entity:
    return BurnerMiningDrill(
        type=t,
        x=int(float(kv["x"])),
        y=int(float(kv["y"])),
        status=int(kv.get("status", 0)) if "status" in kv else None,
        mining_target=kv.get("mining_target"),
    )

register_many(["fast-transport-belt", "express-transport-belt"])(parse_transport_belt)
register_many(["steel-furnace", "electric-furnace"])(parse_stone_furnace)

if __name__ == "__main__":
    receiver = Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        raw_entities = receiver.scan_entities()
        entities = [parse_entity(e, e) for e in raw_entities]
        features = transform_entities(raw_entities)
        print(features)
    finally:
        receiver.disconnect()