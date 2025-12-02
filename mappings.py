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
}

RECIPE_MAP: Dict[str, int] = {
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
    "basic-oil-processing": 35,
    "plastic-bar": 36,
    "sulfur": 37,
    "iron-gear-wheel": 38,
    "iron-stick": 39,
    "copper-cable": 40,
    "electronic-circuit": 41,
    "advanced-circuit": 42,
    "engine-unit": 43,
    "automation-science-pack": 44,
    "logistic-science-pack": 45,
    "chemical-science-pack": 46,
    "wood": 47,
    "coal": 48,
    "stone": 49,
    "iron-ore": 50,
    "copper-ore": 51,
    "stone-brick": 52,

}
ACTION_MAP = {
    "moveto": 1,      # Index 0
    "mine": 2,         # Index 1
    "craft": 3,        # Index 2
    "build": 4,      # Index 3
    "insert_into": 5,  # Index 4
    "take": 6,          # Index 5
    "change_recipe":7  # Index 6
}