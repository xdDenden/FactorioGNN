import json
import numpy as np
import math
from typing import List, Dict, Tuple, Any, Optional, Set
from shapely.geometry import Polygon
from OrePatchDetector import OrePatchDetector

# Import mappings
from mappings import ITEM_MAP, ACTION_MAP, MACHINE_NAME_MAP, INSERT_MAP

# Directly Usable Recipes

RECIPES = {
    # Buildings & Storage
    "wooden-chest": {"wood": 2},
    "storage-tank": {"iron-plate": 20, "steel-plate": 5},

    # Transport Belts
    "transport-belt": {"iron-plate": 1, "iron-gear-wheel": 1},
    "fast-transport-belt": {"iron-gear-wheel": 5, "transport-belt": 1},
    "underground-belt": {"iron-plate": 10, "transport-belt": 5},
    "fast-underground-belt": {"iron-gear-wheel": 40, "underground-belt": 2},
    "splitter": {"electronic-circuit": 5, "iron-plate": 5, "transport-belt": 4},
    "fast-splitter": {"electronic-circuit": 10, "iron-gear-wheel": 10, "splitter": 1},

    # Inserters
    "burner-inserter": {"iron-plate": 1, "iron-gear-wheel": 1},
    "inserter": {"electronic-circuit": 1, "iron-gear-wheel": 1, "iron-plate": 1},
    "long-handed-inserter": {"iron-gear-wheel": 1, "iron-plate": 1, "inserter": 1},
    "fast-inserter": {"electronic-circuit": 2, "iron-plate": 2, "inserter": 1},
    "bulk-inserter": {"electronic-circuit": 15, "iron-gear-wheel": 15, "advanced-circuit": 1, "fast-inserter": 1},

    # Power Poles
    "small-electric-pole": {"wood": 1, "copper-cable": 2},
    "medium-electric-pole": {"iron-stick": 4, "steel-plate": 2, "copper-cable": 2},
    "big-electric-pole": {"iron-stick": 8, "steel-plate": 5, "copper-cable": 4},

    # Pipes & Fluids
    "pipe": {"iron-plate": 1},
    "pipe-to-ground": {"iron-plate": 5, "pipe": 10},
    "boiler": {"stone-furnace": 1, "pipe": 4},
    "steam-engine": {"iron-gear-wheel": 8, "iron-plate": 10, "pipe": 5},

    # Mining & Extraction
    "burner-mining-drill": {"iron-gear-wheel": 3, "stone-furnace": 1, "iron-plate": 3},
    "electric-mining-drill": {"electronic-circuit": 3, "iron-gear-wheel": 5, "iron-plate": 10},
    "offshore-pump": {"iron-gear-wheel": 2, "pipe": 3},
    "pumpjack": {"electronic-circuit": 5, "iron-gear-wheel": 10, "steel-plate": 5, "pipe": 10},

    # Furnaces
    "stone-furnace": {"stone": 5},
    "steel-furnace": {"steel-plate": 6, "stone-brick": 10},

    # Production Buildings
    "assembling-machine-1": {"electronic-circuit": 3, "iron-gear-wheel": 5, "iron-plate": 9},
    "assembling-machine-2": {"iron-gear-wheel": 5, "electronic-circuit": 3, "steel-plate": 2,
                             "assembling-machine-1": 1},
    "oil-refinery": {"electronic-circuit": 10, "iron-gear-wheel": 10, "steel-plate": 15, "pipe": 10, "stone-brick": 10},
    "chemical-plant": {"electronic-circuit": 5, "iron-gear-wheel": 5, "steel-plate": 5, "pipe": 5},
    "lab": {"electronic-circuit": 10, "iron-gear-wheel": 10, "transport-belt": 4},

    # Smelting Recipes (These are crafted IN furnaces, not crafted as items)
    # "iron-plate": {"iron-ore": 1},
    # "copper-plate": {"copper-ore": 1},
    # "steel-plate": {"iron-plate": 5},

    # Oil Processing also not directly crafted
    # "basic-oil-processing": {"crude-oil": 100},  # Produces: petroleum-gas: 45
    # "plastic-bar": {"coal": 1, "petroleum-gas": 20},
    # "sulfur": {"water": 30, "petroleum-gas": 30},

    # Intermediate Products
    "iron-gear-wheel": {"iron-plate": 2},
    "iron-stick": {"iron-plate": 1},
    "copper-cable": {"copper-plate": 1},
    "electronic-circuit": {"iron-plate": 1, "copper-cable": 3},
    "advanced-circuit": {"electronic-circuit": 2, "plastic-bar": 2, "copper-cable": 4},
    "engine-unit": {"steel-plate": 1, "iron-gear-wheel": 1, "pipe": 2},

    # Science Packs
    "automation-science-pack": {"copper-plate": 1, "iron-gear-wheel": 1},
    "logistic-science-pack": {"transport-belt": 1, "inserter": 1},
    "chemical-science-pack": {"advanced-circuit": 3, "engine-unit": 2, "sulfur": 1},

    # RECIPES THAT CANNOT BE HAND CRAFTED BUT CAN BE SET IN MACHINES
    # These are needed for ACTION 6 (Change Recipe), but strictly should not be in ACTION 2 (Craft)
    # The logic below handles this by checking if ingredients are in inventory
    # Since you can't hold fluid in inventory, 'sulfur' or 'plastic' naturally fail the hand-craft check
    "sulfur": {"water": 30, "petroleum-gas": 30},
    "plastic-bar": {"coal": 1, "petroleum-gas": 20},
    "empty-barrel": {"steel-plate": 1},
    "solid-fuel": {"light-oil": 10}, # Simplified
}

# Define which items are mining drills
MINING_DRILLS = {"burner-mining-drill", "electric-mining-drill"}
OIL_EXTRACTORS = {"pumpjack"}


# HELPER FUNCTIONS

def world_to_grid(x: float, y: float, bounds: Tuple[int, int, int, int], grid_steps: int = 17) -> Tuple[int, int]:
    """
    Converts world coordinates to the 17x17 grid index used in rconToGNN.py.
    """
    min_x, max_x, min_y, max_y = bounds

    # Avoid division by zero
    if max_x == min_x:
        width = 1
    else:
        width = max_x - min_x

    if max_y == min_y:
        height = 1
    else:
        height = max_y - min_y

    # Normalize to [0, 1]
    norm_x = (x - min_x) / width
    norm_y = (y - min_y) / height

    # Scale to grid (0..16)
    grid_x = int(norm_x * (grid_steps - 1))
    grid_y = int(norm_y * (grid_steps - 1))

    # Clamp
    grid_x = max(0, min(grid_steps - 1, grid_x))
    grid_y = max(0, min(grid_steps - 1, grid_y))

    return grid_x, grid_y


def check_reach(p_x, p_y, t_x, t_y, max_dist=30.0):
    """Checks if target (t_x, t_y) is within reach of player (p_x, p_y)."""
    return math.sqrt((p_x - t_x) ** 2 + (p_y - t_y) ** 2) <= max_dist


def is_player_near_ore_patch_center(px, py, patches, distance_threshold=7.0):
    """
    Check if player is within distance_threshold tiles of any ore patch center.

    Args:
        px, py: Player position
        patches: List of ore patches with 'center' key
        distance_threshold: Maximum distance to patch center (default 6-7 tiles)

    Returns:
        bool: True if player is near any ore patch center
    """
    for patch in patches:
        center_x, center_y = patch['center']
        distance = math.sqrt((px - center_x) ** 2 + (py - center_y) ** 2)
        if distance <= distance_threshold:
            return True
    return False



# CORE MASKING LOGIC

_SHARED_DETECTOR = OrePatchDetector(ore_data=[])
#TODO: Add comments
def get_action_masks(
        entities: List[Dict],
        player_info: Dict,
        inventory: Dict[str, int],
        available_items: List[str],
        bounds: Tuple[int, int, int, int],
        grid_steps: int = 17,
        patches: Optional[List[Dict]] = None,
        move_state: Optional[Dict] = None
):
    num_actions = len(ACTION_MAP)
    num_items = max(ITEM_MAP.values()) + 1
    grid_size = grid_steps * grid_steps

    # Initialize masks (Default to 0/False)
    action_mask = np.zeros(num_actions, dtype=np.float32)
    item_mask = np.zeros((num_actions, num_items), dtype=np.float32)
    spatial_mask = np.zeros((num_actions, grid_size), dtype=np.float32)

    # Player position
    px = player_info.get('pos', {}).get('x', 0)
    py = player_info.get('pos', {}).get('y', 0)

    # Convert available items to set for O(1) lookup
    unlocked_set = set(available_items) if available_items else set()

    # Pre-calculate Spatial State
    # 1. Occupied Grid (For Build)
    entity_grid = np.zeros((grid_steps, grid_steps), dtype=bool)

    # 2. Insertable Grid (For Insert/Take)
    insertable_grid = np.zeros((grid_steps, grid_steps), dtype=bool)

    # Map entities to grid
    for e in entities:
        gx, gy = world_to_grid(e['x'], e['y'], bounds, grid_steps)
        entity_grid[gy, gx] = True
        name = e.get('machine_name', e.get('name', ''))
        if name in INSERT_MAP:
            insertable_grid[gy, gx] = True

    flat_entity_mask = entity_grid.flatten()
    flat_empty_mask = ~flat_entity_mask
    flat_insertable_mask = insertable_grid.flatten()

    # Pre-calculate Grid-to-World steps
    min_x, max_x, min_y, max_y = bounds
    step_x = (max_x - min_x) / grid_steps if max_x != min_x else 1.0
    step_y = (max_y - min_y) / grid_steps if max_y != min_y else 1.0

    loaded_patches = patches if patches is not None else []

    reach_grid = np.zeros((grid_steps, grid_steps), dtype=bool)
    for gy in range(grid_steps):
        for gx in range(grid_steps):
            wx = min_x + (gx * step_x)
            wy = min_y + (gy * step_y)
            if check_reach(px, py, wx, wy, max_dist=30):
                reach_grid[gy, gx] = True

    flat_reach_mask = reach_grid.flatten()

    # 0. ACTION: MOVE_TO (0)
    action_mask[0] = 0.0 if (move_state and move_state.get('active')) else 1.0
    item_mask[0, 0] = 1.0
    spatial_mask[0, :] = 1.0

    # 1. ACTION: MINE (1)
    can_mine_any = False
    if loaded_patches:
        for gy in range(grid_steps):
            for gx in range(grid_steps):
                flat_idx = gy * grid_steps + gx
                wx = min_x + (gx * step_x) + (step_x / 2)
                wy = min_y + (gy * step_y) + (step_y / 2)
                if not check_reach(px, py, wx, wy, max_dist=30):
                    continue
                p_list = _SHARED_DETECTOR.is_position_in_patch(wx, wy, patches=loaded_patches)
                if any(p['ore_type'] != 'crude-oil' for p in p_list):
                    spatial_mask[1, flat_idx] = 1.0
                    can_mine_any = True

    if can_mine_any:
        action_mask[1] = 1.0
    item_mask[1, :] = 1.0

    # 2. ACTION: CRAFT (2)
    can_craft_any = False
    for item_name, recipe_data in RECIPES.items():
        if item_name not in unlocked_set:
            continue
        if all(inventory.get(ing, 0) >= qty for ing, qty in recipe_data.items()):
            item_id = ITEM_MAP.get(item_name, 0)
            if item_id > 0:
                item_mask[2, item_id] = 1.0
                can_craft_any = True

    if can_craft_any:
        action_mask[2] = 1.0
        spatial_mask[2, :] = 1.0

    # 3. ACTION: BUILD (3)
    valid_build_locs = flat_empty_mask & flat_reach_mask
    miner_spatial_mask = np.zeros(grid_size, dtype=bool)
    pumpjack_spatial_mask = np.zeros(grid_size, dtype=bool)
    regular_spatial_mask = valid_build_locs.copy()

    player_near_ore_center = is_player_near_ore_patch_center(px, py, loaded_patches, distance_threshold=7.0)
    player_near_oil = any(
        p['ore_type'] == 'crude-oil' and math.sqrt((px - p['center'][0]) ** 2 + (py - p['center'][1]) ** 2) < 7.0
        for p in loaded_patches
    )

    has_miner = any(inventory.get(n,0)>0 for n in MINING_DRILLS)
    has_pumpjack = any(inventory.get(n,0)>0 for n in OIL_EXTRACTORS)

    if (has_miner and player_near_ore_center) or (has_pumpjack and player_near_oil):
        for gy in range(grid_steps):
            for gx in range(grid_steps):
                flat_idx = gy * grid_steps + gx
                if not valid_build_locs[flat_idx]:
                    continue
                wx = min_x + (gx * step_x) + (step_x / 2)
                wy = min_y + (gy * step_y) + (step_y / 2)
                p_list = _SHARED_DETECTOR.is_position_in_patch(wx, wy, patches=loaded_patches)
                for p in p_list:
                    if p['ore_type'] == 'crude-oil' and has_pumpjack:
                        pumpjack_spatial_mask[flat_idx] = True
                    elif p['ore_type'] != 'crude-oil' and has_miner:
                        miner_spatial_mask[flat_idx] = True

    build_spatial_by_item: Dict[int, np.ndarray] = {}
    combined_spatial = np.zeros(grid_size, dtype=bool)

    for item_name, count in inventory.items():
        if count <= 0 or item_name not in MACHINE_NAME_MAP:
            continue
        # Index using ITEM_MAP so it aligns with the network's item_head and ID_TO_ITEM!
        item_id = ITEM_MAP.get(item_name, 0)
        if item_id <= 0:
            continue

        if item_name in MINING_DRILLS:
            if player_near_ore_center and np.any(miner_spatial_mask):
                item_mask[3, item_id] = 1.0
                build_spatial_by_item[item_id] = miner_spatial_mask.astype(np.float32)
                combined_spatial |= miner_spatial_mask
        elif item_name in OIL_EXTRACTORS:
            if player_near_oil and np.any(pumpjack_spatial_mask):
                item_mask[3, item_id] = 1.0
                build_spatial_by_item[item_id] = pumpjack_spatial_mask.astype(np.float32)
                combined_spatial |= pumpjack_spatial_mask
        else:
            if np.any(regular_spatial_mask):
                item_mask[3, item_id] = 1.0
                build_spatial_by_item[item_id] = regular_spatial_mask.astype(np.float32)
                combined_spatial |= regular_spatial_mask

    if np.any(item_mask[3]) and np.any(combined_spatial):
        action_mask[3] = 1.0
        spatial_mask[3, :] = combined_spatial.astype(np.float32)

    # 4. ACTION: INSERT_INTO (4)
    # Legal IF: Entity is in INSERT_MAP + Reachable
    has_items = sum(inventory.values()) > 0
    valid_insert_targets = flat_insertable_mask & flat_reach_mask

    if has_items and np.any(valid_insert_targets):
        action_mask[4] = 1.0
        spatial_mask[4, :] = valid_insert_targets.astype(np.float32)
        # Enable all items in inventory
        for item_name, count in inventory.items():
            if count > 0:
                iid = ITEM_MAP.get(item_name, 0)
                if iid > 0:
                    item_mask[4, iid] = 1.0

    # 5. ACTION: TAKE (5)
    # Legal IF: Entity at target (to take from)
    if np.any(valid_insert_targets):
        action_mask[5] = 1.0
        spatial_mask[5, :] = valid_insert_targets.astype(np.float32)
        item_mask[5, :] = 1.0

    # 6. ACTION: CHANGE_RECIPE (6)
    # Legal IF: Entity at target
    if np.any(valid_insert_targets):
        action_mask[6] = 1.0
        spatial_mask[6, :] = valid_insert_targets.astype(np.float32)
        for name in RECIPES:
            if name in unlocked_set:
                iid = ITEM_MAP.get(name, 0)
            if iid > 0:
                item_mask[6, iid] = 1.0

    return action_mask, item_mask, spatial_mask, build_spatial_by_item