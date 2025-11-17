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
    "lab": 34,
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
    "electric-mining- drill": 31,
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