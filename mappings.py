from typing import Dict

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
    "wooden-chest": 1,
    "storage-tank": 2,
    "transport-belt": 3,
    "fast-transport-belt": 4,
    "underground-belt": 5,
    "fast-underground-belt": 6,
    "splitter": 7,
    "fast-splitter": 8,
    "burner-inserter": 9,
    "inserter": 10,
    "long-handed-inserter": 11,
    "fast-inserter": 12,
    "bulk-inserter": 13,
    "small-electric-pole": 14,
    "medium-electric-pole": 15,
    "big-electric-pole": 16,
    "pipe": 17,
    "pipe-to-ground": 18,
    "boiler": 19,
    "steam-engine": 20,
    "burner-mining-drill": 21,
    "electric-mining-drill": 22,
    "offshore-pump": 23,
    "pumpjack": 24,
    "stone-furnace": 25,
    "steel-furnace": 26,
    "assembling-machine-1": 27,
    "assembling-machine-2": 28,
    "oil-refinery": 29,
    "chemical-plant": 30,
    "lab": 31
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
    "wooden-chest": 1,
    "storage-tank": 2,
    "transport-belt": 3,
    "fast-transport-belt": 4,
    "underground-belt": 5,
    "fast-underground-belt": 6,
    "splitter": 7,
    "fast-splitter": 8,
    "burner-inserter": 9,
    "inserter": 10,
    "long-handed-inserter": 11,
    "fast-inserter": 12,
    "bulk-inserter": 13,
    "small-electric-pole": 14,
    "medium-electric-pole": 15,
    "big-electric-pole": 16,
    "pipe": 17,
    "pipe-to-ground": 18,
    "boiler": 19,
    "steam-engine": 20,
    "burner-mining-drill": 21,
    "electric-mining-drill": 22,
    "offshore-pump": 23,
    "pumpjack": 24,
    "stone-furnace": 25,
    "steel-furnace": 26,
    "assembling-machine-1": 27,
    "assembling-machine-2": 28,
    "oil-refinery": 29,
    "chemical-plant": 30,
    "lab": 31,
    "iron-plate": 38,
    "copper-plate": 39,
    "steel-plate": 40,
    "basic-oil-processing": 41,
    "plastic-bar": 42,
    "sulfur": 43,
    "iron-gear-wheel": 44,
    "iron-stick": 45,
    "copper-cable": 46,
    "electronic-circuit": 47,
    "advanced-circuit": 48,
    "engine-unit": 49,
    "automation-science-pack": 50,
    "logistic-science-pack": 51,
    "chemical-science-pack": 52
}
ITEM_MAP: Dict[str, int] = {
    "none": 0,
    "wooden-chest": 1,
    "storage-tank": 2,
    "transport-belt": 3,
    "fast-transport-belt": 4,
    "underground-belt": 5,
    "fast-underground-belt": 6,
    "splitter": 7,
    "fast-splitter": 8,
    "burner-inserter": 9,
    "inserter": 10,
    "long-handed-inserter": 11,
    "fast-inserter": 12,
    "bulk-inserter": 13,
    "small-electric-pole": 14,
    "medium-electric-pole": 15,
    "big-electric-pole": 16,
    "pipe": 17,
    "pipe-to-ground": 18,
    "boiler": 19,
    "steam-engine": 20,
    "burner-mining-drill": 21,
    "electric-mining-drill": 22,
    "offshore-pump": 23,
    "pumpjack": 24,
    "stone-furnace": 25,
    "steel-furnace": 26,
    "assembling-machine-1": 27,
    "assembling-machine-2": 28,
    "oil-refinery": 29,
    "chemical-plant": 30,
    "lab": 31,
    "iron-plate": 32,
    "copper-plate": 33,
    "steel-plate": 34,
    "plastic-bar": 35,
    "sulfur": 36,
    "iron-gear-wheel": 37,
    "iron-stick": 38,
    "copper-cable": 39,
    "electronic-circuit": 40,
    "advanced-circuit": 41,
    "engine-unit": 42,
    "automation-science-pack": 43,
    "logistic-science-pack": 44,
    "chemical-science-pack": 45,
    "wood": 46,
    "coal": 47,
    "stone": 48,
    "iron-ore": 49,
    "copper-ore": 50,
    "stone-brick": 51,

}
ACTION_MAP = {
    "none": 0,
    "moveto": 1,
    "mine": 2,
    "craft": 3,
    "build": 4,
    "insert_into": 5,
    "take": 6,
    "change_recipe":7
}

# --- REVERSE MAPPINGS (For Jimbo/Logging) ---
# These allow O(1) lookup from ID -> Name without searching
ID_TO_ACTION = {v: k for k, v in ACTION_MAP.items()}
ID_TO_ITEM = {v: k for k, v in ITEM_MAP.items()}
ID_TO_RECIPE = {v: k for k, v in RECIPE_MAP.items()}
ID_TO_RECIPE = {v: k for k, v in RECIPE_MAP.items()}