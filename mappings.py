from typing import Dict, List, Set, Union, Any

STATUS_MAP: Dict[int, int] = {
    1: 1,   # working
    2: 2,   # normal
    54: 3,   # no_power
    53: 4,   # no_fuel
    18: 5,  # no_ingredients
    24: 6,  # no_input_fluid
    20: 7,  # no research in progress
    21: 8,  # no_minable_resources
    27: 9,  # full_output
    31: 10,  # missing_science_packs
    26: 11,  # item_ingredient_shortage
    25: 12,  # fluid_ingredient_shortage
    23: 13,  # low_input_fluid
    19: 14,  #no_recipe
    14: 15,  #low_power
    5: 16    #not_plugged_in_electric_network
# Unknown -> default to 2 (normal)
}

MACHINE_NAME_MAP: Dict[str, int] = {
    "none": 0,
    "storage-tank": 1,
    "transport-belt": 2,
    "fast-transport-belt": 3,
    "underground-belt": 4,
    "fast-underground-belt": 5,
    "splitter": 6,
    "fast-splitter": 7,
    "burner-inserter": 8,
    "inserter": 9,
    "long-handed-inserter": 10,
    "fast-inserter": 11,
    "bulk-inserter": 12,
    "small-electric-pole": 13,
    "medium-electric-pole": 14,
    "big-electric-pole": 15,
    "pipe": 16,
    "pipe-to-ground": 17,
    "boiler": 18,
    "steam-engine": 19,
    "burner-mining-drill": 20,
    "electric-mining-drill": 21,
    "offshore-pump": 22,
    "pumpjack": 23,
    "stone-furnace": 24,
    "steel-furnace": 25,
    "assembling-machine-1": 26,
    "assembling-machine-2": 27,
    "oil-refinery": 28,
    "chemical-plant": 29,
    "lab": 30,
    "pump": 31
}

MINING_TARGET_MAP: Dict[str, int] = {
    "stone": 1,
    "iron-ore": 2,
    "copper-ore": 3,
    "coal": 4,
    "crude-oil": 5
}

RECIPE_MAP: Dict[str, int] = {
    "none": 0,
    "storage-tank": 1,
    "transport-belt": 2,
    "fast-transport-belt": 3,
    "underground-belt": 4,
    "fast-underground-belt": 5,
    "splitter": 6,
    "fast-splitter": 7,
    "burner-inserter": 8,
    "inserter": 9,
    "long-handed-inserter": 10,
    "fast-inserter": 11,
    "bulk-inserter": 12,
    "small-electric-pole": 13,
    "medium-electric-pole": 14,
    "big-electric-pole": 15,
    "pipe": 16,
    "pipe-to-ground": 17,
    "boiler": 18,
    "steam-engine": 19,
    "burner-mining-drill": 20,
    "electric-mining-drill": 21,
    "offshore-pump": 22,
    "pumpjack": 23,
    "stone-furnace": 24,
    "steel-furnace": 25,
    "assembling-machine-1": 26,
    "assembling-machine-2": 27,
    "oil-refinery": 28,
    "chemical-plant": 29,
    "lab": 30,
    "iron-plate": 37,
    "copper-plate": 38,
    "steel-plate": 39,
    "basic-oil-processing": 40,
    "plastic-bar": 41,
    "sulfur": 42,
    "iron-gear-wheel": 43,
    "iron-stick": 44,
    "copper-cable": 45,
    "electronic-circuit": 46,
    "advanced-circuit": 47,
    "engine-unit": 48,
    "automation-science-pack": 49,
    "logistic-science-pack": 50,
    "chemical-science-pack": 51
}
ITEM_MAP: Dict[str, int] = {
    "none": 0,
    "storage-tank": 1,
    "transport-belt": 2,
    "fast-transport-belt": 3,
    "underground-belt": 4,
    "fast-underground-belt": 5,
    "splitter": 6,
    "fast-splitter": 7,
    "burner-inserter": 8,
    "inserter": 9,
    "long-handed-inserter": 10,
    "fast-inserter": 11,
    "bulk-inserter": 12,
    "small-electric-pole": 13,
    "medium-electric-pole": 14,
    "big-electric-pole": 15,
    "pipe": 16,
    "pipe-to-ground": 17,
    "boiler": 18,
    "steam-engine": 19,
    "burner-mining-drill": 20,
    "electric-mining-drill": 21,
    "offshore-pump": 22,
    "pumpjack": 23,
    "stone-furnace": 24,
    "steel-furnace": 25,
    "assembling-machine-1": 26,
    "assembling-machine-2": 27,
    "oil-refinery": 28,
    "chemical-plant": 29,
    "lab": 30,
    "iron-plate": 31,
    "copper-plate": 32,
    "steel-plate": 33,
    "plastic-bar": 34,
    "sulfur": 35,
    "iron-gear-wheel": 36,
    "iron-stick": 37,
    "copper-cable": 38,
    "electronic-circuit": 39,
    "advanced-circuit": 40,
    "engine-unit": 41,
    "automation-science-pack": 42,
    "logistic-science-pack": 43,
    "chemical-science-pack": 44,
    "wood": 45,
    "coal": 46,
    "stone": 47,
    "iron-ore": 48,
    "copper-ore": 49,
    "stone-brick": 50,
    "pump": 51
}

INSERT_MAP: Dict[str, int] = {
    "burner-inserter": 0,
    "boiler": 1,
    "burner-mining-drill": 2,
    "stone-furnace": 3,
    "steel-furnace": 4,
    "assembling-machine-1": 5,
    "assembling-machine-2": 6,
    "oil-refinery": 7,
    "chemical-plant": 8,
    "lab": 9
}
ACTION_MAP = {
    #"none": 0,
    "moveto": 0,
    "mine": 1,
    "craft": 2,
    "build": 3,
    "insert_into": 4,
    "take": 5,
    "change_recipe": 6
}

# Map technology internal names to a unique integer ID
RESEARCH_MAP: Dict[str, int] = {
    "base": 0,  # Base game items available from start (including "steam-power", "electronics", "automation-science-pack")
    "automation": 1,
    "logistics": 2,
    "gun-turret": 3,
    "optics": 4,
    "stone-wall": 5,
    "military": 6,
    "steel-processing": 7,
    "logistic-science-pack": 8,
    "heavy-armor": 9,
    "fast-inserter": 10,
    "automation-2": 11,
    "electric-energy-distribution-1": 12,
    "advanced-material-processing": 13,
    "solar-energy": 14,
    "logistics-2": 15,
    "engine": 16,
    "fluid-handling": 17,
    "oil-processing": 18,
    "sulfur-processing": 19,
    "plastics": 20,
    "advanced-electronics": 21,
    "automobilism": 22,
    "explosives": 23,
    "battery": 24,
    "gate": 25,
    "landfill": 26,
    "circuit-network": 27,
    "toolbelt": 28,
    "steel-axe": 29
}

# Map the integer ID to the list of items/buildings it unlocks
RESEARCH_UNLOCKS: Dict[int, List[str]] = {
    # Base items (Assumes "steam-power", "electronics", "automation-science-pack" are unlocked)
    0: [
        "iron-plate", "copper-plate", "wood", "stone", "coal", "stone-brick",
        "iron-gear-wheel", "copper-cable", "electronic-circuit", "iron-chest",
        "burner-inserter", "inserter",
        "small-electric-pole", "pipe", "pipe-to-ground",
        "boiler", "steam-engine", "offshore-pump",
        "burner-mining-drill", "electric-mining-drill",
        "stone-furnace",
        "lab", "automation-science-pack",
        "pistol", "firearm-magazine", "light-armor",
        "repair-pack", "radar"
    ],
    # Automation
    1: ["assembling-machine-1", "long-handed-inserter"],
    # Logistics
    2: ["transport-belt", "underground-belt", "splitter"],
    # Gun Turret
    3: ["gun-turret"],
    # Optics
    4: ["lamp"],
    # Stone Wall
    5: ["stone-wall"],
    # Military
    6: ["submachine-gun", "shotgun", "shotgun-shell"],
    # Steel Processing
    7: ["steel-plate"],
    # Logistic Science Pack
    8: ["logistic-science-pack"],
    # Heavy Armor
    9: ["heavy-armor"],
    # Fast Inserter
    10: ["fast-inserter"],
    # Automation 2
    11: ["assembling-machine-2"],
    # Electric Energy Distribution 1
    12: ["medium-electric-pole", "big-electric-pole"],
    # Advanced Material Processing
    13: ["steel-furnace"],
    # Solar Energy
    14: ["solar-panel"],
    # Logistics 2
    15: ["fast-transport-belt", "fast-underground-belt", "fast-splitter"],
    # Engine
    16: ["engine-unit"],
    # Fluid Handling
    17: ["storage-tank", "empty-barrel"], # Also barrels logic
    # Oil Processing
    18: ["oil-refinery", "chemical-plant", "solid-fuel"], # Unlocks Basic Oil Processing recipe
    # Sulfur Processing
    19: ["sulfur", "sulfuric-acid"],
    # Plastics
    20: ["plastic-bar"],
    # Advanced Electronics
    21: ["advanced-circuit"],
    # Automobilism
    22: ["car"],
    # Explosives
    23: ["explosives"],
    # Battery
    24: ["battery"],
    # Gate
    25: ["gate"],
    # Landfill
    26: ["landfill"],
    # Circuit Network
    27: ["red-wire", "green-wire", "arithmetic-combinator", "decider-combinator", "constant-combinator", "power-switch", "programmable-speaker"],
    # Toolbelt (Bonus only)
    28: [],
    # Steel Axe (Bonus only)
    29: []
}


def get_available_items(unlocked_research: Union[Dict[str, bool], List[Dict[str, Any]]]) -> List[str]:
    """
    Translates the output of scan_research into a list of items that are technologically possible to craft/build.

    Args:
        unlocked_research: Can be:
            1. A dictionary {tech_name: bool} (e.g. {"automation": True})
            2. A list of dicts (e.g. [{"name": "automation", "researched": True}, ...])

    Returns:
        A list of item names (strings) that the AI allows based on unlocked tech.
    """
    # 1. Start with the Base set (ID 0) which is always unlocked.
    available_items: Set[str] = set(RESEARCH_UNLOCKS[0])

    # 2. Normalize input to a Dictionary {name: is_unlocked}
    research_dict: Dict[str, bool] = {}

    if isinstance(unlocked_research, list):
        for item in unlocked_research:
            if isinstance(item, dict):
                # Expects keys like 'name' and 'researched' (standard Factorio API dump)
                name = item.get("name")
                # Default to False if 'researched' key is missing, unless implied otherwise
                researched = item.get("researched", False)
                if name:
                    research_dict[name] = researched
    elif isinstance(unlocked_research, dict):
        research_dict = unlocked_research
    else:
        # Fallback for unexpected types (return basic items only)
        print(f"Warning: Unexpected research format: {type(unlocked_research)}")
        return list(available_items)

    # 3. Process the normalized dictionary
    for tech_name, is_unlocked in research_dict.items():
        if is_unlocked:
            tech_id = RESEARCH_MAP.get(tech_name)
            if tech_id is not None:
                items = RESEARCH_UNLOCKS.get(tech_id, [])
                available_items.update(items)

    return list(available_items)





# --- REVERSE MAPPINGS (For Jimbo/Logging) ---
# These allow O(1) lookup from ID -> Name without searching
ID_TO_ACTION = {v: k for k, v in ACTION_MAP.items()}
ID_TO_ITEM = {v: k for k, v in ITEM_MAP.items()}
ID_TO_RECIPE = {v: k for k, v in RECIPE_MAP.items()}
