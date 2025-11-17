from dataclasses import dataclass
from typing import Dict, Callable, List, Optional, Any

# --- Dataclasses ---

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

def register(type_name: str):
    def deco(fn: Parser):
        parsers[type_name] = fn
        return fn
    return deco

def to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).lower() in ("true", "1")

# --- Parsers ---

def default_parser(t: str, kv: Dict[str, str]) -> Entity:
    """
    Generic parser for entities that don't have a specific one.
    It will attach any common optional fields it finds.
    """
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
    """
    Top-level parser function.
    Uses a specific parser if registered, else the generic fallback.
    """
    return parsers.get(type_name, default_parser)(type_name, kv)

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

# Register aliases
register_many(["fast-transport-belt", "express-transport-belt"])(parse_transport_belt)
register_many(["steel-furnace", "electric-furnace"])(parse_stone_furnace)