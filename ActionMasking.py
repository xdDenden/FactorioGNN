import json
import numpy as np
import math
from typing import List, Dict, Tuple, Any, Optional
from shapely.geometry import Polygon
from OrePatchDetector import OrePatchDetector

# Import your existing mappings
from mappings import ID_TO_ACTION, ID_TO_ITEM, ITEM_MAP, ACTION_MAP, MACHINE_NAME_MAP, INSERT_MAP

# ==========================================
#          Directly Usable Recipes
# ==========================================

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
    "assembling-machine-2": {"iron-gear-wheel": 5, "electronic-circuit": 3, "steel-plate": 2,"assembling-machine-1": 1},
    "oil-refinery": {"electronic-circuit": 10, "iron-gear-wheel": 10, "steel-plate": 15, "pipe": 10, "stone-brick": 10},
    "chemical-plant": {"electronic-circuit": 5, "iron-gear-wheel": 5, "steel-plate": 5, "pipe": 5},
    "lab": {"electronic-circuit": 10, "iron-gear-wheel": 10, "transport-belt": 4},

    # Smelting Recipes (These are crafted IN furnaces, not crafted as items)
    #"iron-plate": {"iron-ore": 1},
    #"copper-plate": {"copper-ore": 1},
    #"steel-plate": {"iron-plate": 5},

    # Oil Processing also not directly crafted
    #"basic-oil-processing": {"crude-oil": 100},  # Produces: petroleum-gas: 45
    #"plastic-bar": {"coal": 1, "petroleum-gas": 20},
    #"sulfur": {"water": 30, "petroleum-gas": 30},

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
}


# ==========================================
#           HELPER FUNCTIONS
# ==========================================

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


def check_reach(p_x, p_y, t_x, t_y, max_dist=75.0):
    """Checks if target (t_x, t_y) is within reach of player (p_x, p_y)."""
    return math.sqrt((p_x - t_x) ** 2 + (p_y - t_y) ** 2) <= max_dist


# ==========================================
#           CORE MASKING LOGIC
# ==========================================

def get_action_masks(
        entities: List[Dict],
        player_info: Dict,
        inventory: Dict[str, int],
        science_level: int,
        bounds: Tuple[int, int, int, int],
        grid_steps: int = 17,
        patches: Optional[List[Dict]] = None,
        move_state: Optional[Dict] = None
):
    """
    Generates bitmasks to filter illegal actions.

    Args:
        entities: List of entity dicts (from environment.py/parsers.py)
        player_info: Dict containing 'pos' {'x', 'y'}
        inventory: Dict of {item_name: count}
        science_level: (int) Placeholder for tech availability
        bounds: (min_x, max_x, min_y, max_y) current observation window

    Returns:
        action_mask: np.array [num_actions] (1=Legal, 0=Illegal)
        item_mask:   np.array [num_actions, num_items]
                     (Rows correspond to actions. E.g., item_mask[CRAFT] shows valid recipes)
        spatial_mask: np.array [num_actions, grid_steps * grid_steps]
                     (Rows correspond to actions. E.g., spatial_mask[MINE] shows tiles with ore)
    """

    num_actions = len(ACTION_MAP)
    num_items = len(ITEM_MAP)
    grid_size = grid_steps * grid_steps

    # Initialize masks (Default to 0/False)
    action_mask = np.zeros(num_actions, dtype=np.float32)
    item_mask = np.zeros((num_actions, num_items), dtype=np.float32)
    spatial_mask = np.zeros((num_actions, grid_size), dtype=np.float32)

    # Player position
    px = player_info.get('pos', {}).get('x', 0)
    py = player_info.get('pos', {}).get('y', 0)

    # --- Pre-calculate Spatial State ---
    # 1. Occupied Grid (For Build)
    entity_grid = np.zeros((grid_steps, grid_steps), dtype=bool)

    # 2. Insertable Grid (For Insert/Take)
    insertable_grid = np.zeros((grid_steps, grid_steps), dtype=bool)

    # Map entities to grid
    for e in entities:
        gx, gy = world_to_grid(e['x'], e['y'], bounds, grid_steps)
        entity_grid[gy, gx] = True  # Mark occupied

# Check if entity is in INSERT_MAP (using machine_name or name)
        name = e.get('machine_name', e.get('name', ''))
        if name in INSERT_MAP:
            insertable_grid[gy, gx] = True

    # Flatten grid for the mask (Row-major order to match rconToGNN decoding)
    # Note: rconToGNN uses: y_grid_idx = flat // 17, x = flat % 17
    flat_entity_mask = entity_grid.flatten()
    flat_empty_mask = ~flat_entity_mask

    # --- Pre-calculate Grid-to-World steps ---
    min_x, max_x, min_y, max_y = bounds
    step_x = (max_x - min_x) / grid_steps
    step_y = (max_y - min_y) / grid_steps
    flat_insertable_mask = insertable_grid.flatten()

    # --- Load Patches (if not provided) ---
    loaded_patches = []
    if patches is not None:
        loaded_patches = patches
    else:
        try:
            with open('patches.json', 'r') as f:
                data = json.load(f)
                # FIX: Reconstruct Polygon objects from boundary points
                for p in data:
                    if 'boundary' in p:
                        p['polygon'] = Polygon(p['boundary'])
                        loaded_patches.append(p)
        except FileNotFoundError:
            # print("Warning: patches.json not found.")
            pass
        except Exception as e:
            print(f"Error loading patches: {e}")

    # Detector instance
    detector = OrePatchDetector(ore_data=[])


    # --- Pre-calculate Reach Mask ---
    # Which grid cells are reachable?
    reach_grid = np.zeros((grid_steps, grid_steps), dtype=bool)
    min_x, max_x, min_y, max_y = bounds
    step_x = (max_x - min_x) / grid_steps
    step_y = (max_y - min_y) / grid_steps

    for gy in range(grid_steps):
        for gx in range(grid_steps):
            # Approx world pos of this grid cell
            wx = min_x + (gx * step_x)
            wy = min_y + (gy * step_y)
            if check_reach(px, py, wx, wy, max_dist=75):
                reach_grid[gy, gx] = True

    flat_reach_mask = reach_grid.flatten()

    # ==========================================
    # 0. ACTION: NONE (0)
    # ==========================================
    #action_mask[0] = 1.0  # Always legal to do nothing
    #item_mask[0, :] = 1.0  # Args irrelevant
    #spatial_mask[0, :] = 1.0

    # ==========================================
    # 0. ACTION: MOVE_TO (0)
    # ==========================================
    # Always legal to try moving (pathfinding handles the rest)
    if move_state and move_state['active']:
        action_mask[0] = 0.0
    else:
        action_mask[0] = 1.0

    item_mask[0, :] = 0.0
    item_mask[0, 0] = 1.0
    spatial_mask[0, :] = 1.0

    # ==========================================
    # 1. ACTION: MINE (1)
    # ==========================================
    can_mine_any = False

    for gy in range(grid_steps):
        for gx in range(grid_steps):
            flat_idx = gy * grid_steps + gx

            # 1. Approximate World Position (center of the grid tile)
            wx = min_x + (gx * step_x) + (step_x / 2)
            wy = min_y + (gy * step_y) + (step_y / 2)

            # 2. Check Reach
            if not check_reach(px, py, wx, wy, max_dist=75):
                continue

            # 3. Check for valid Ore Patch (excluding crude-oil)
            # This relies on the internal structure of patches.json being compatible
            # with OrePatchDetector and Shapely geometry objects being loaded correctly.

            is_mineable = False
            if loaded_patches:
                valid_patches = detector.is_position_in_patch(wx, wy, patches=loaded_patches)

                for patch in valid_patches:
                    if patch['ore_type'] != 'crude-oil':
                        is_mineable = True
                        break

            if is_mineable:
                spatial_mask[1, flat_idx] = 1.0
                can_mine_any = True

    if can_mine_any:
        action_mask[1] = 1.0

    item_mask[1, :] = 1.0  # Item arg irrelevant for mining

    # ==========================================
    # 2. ACTION: CRAFT (2)
    # ==========================================
    # Legal IF: Player has ingredients for at least one recipe
    # TODO: Consider which buildings can be placed on which surface (mining drills need ore etc)
    can_craft_any = False

    for item_name, recipe_data in RECIPES.items():
        # Check ingredients
        craftable = True
        for ingredient, required_qty in recipe_data.items():
            if inventory.get(ingredient, 0) < required_qty:
                craftable = False
                break

        if craftable:
            item_id = ITEM_MAP.get(item_name, 0)
            if item_id > 0:
                item_mask[2, item_id] = 1.0
                can_craft_any = True

    if can_craft_any:
        action_mask[2] = 1.0
        spatial_mask[2, :] = 1.0  # Location irrelevant for crafting

    # ==========================================
    # 3. ACTION: BUILD (3)
    # ==========================================
    # Legal IF: Player has the item AND target is empty AND within reach
    can_build_any = False

    # 1. Check Inventory for buildable items
    for item_name, count in inventory.items():
        if count > 0:
            item_id = MACHINE_NAME_MAP.get(item_name, 0)
            # Simple check: is it in our ID map? (Assumes map implies buildable)
            if item_id > 0:
                item_mask[3, item_id] = 1.0
                can_build_any = True


    # 2. Check Spatial (Empty + Reach)
    valid_build_locs = flat_empty_mask & flat_reach_mask

    # DEBUG: Check why it fails
    #if can_build_any and not np.any(valid_build_locs):
        #print(f"[Masking Debug] Build blocked by spatial mask!")
        #print(f"  Player Pos: {px}, {py}")
        #print(f"  Bounds: {min_x}, {max_x}, {min_y}, {max_y}")
        #print(f"  Reach Grid True Count: {np.sum(reach_grid)}")
        #print(f"  Empty Grid True Count: {np.sum(flat_empty_mask)}")

    if can_build_any and np.any(valid_build_locs):
        action_mask[3] = 1.0
        spatial_mask[3, :] = valid_build_locs.astype(np.float32)
        #print(f"[Masking Debug] Build blocked by spatial mask!")
        #print(f"  Player Pos: {px}, {py}")
        #print(f"  Bounds: {min_x}, {max_x}, {min_y}, {max_y}")
        #print(f"  Reach Grid True Count: {np.sum(reach_grid)}")
        #print(f"  Empty Grid True Count: {np.sum(flat_empty_mask)}")

    # ==========================================
    # 4. ACTION: INSERT_INTO (4)
    # ==========================================
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
                item_mask[4, iid] = 1.0

    # ==========================================
    # 5. ACTION: TAKE (5)
    # ==========================================
    # Legal IF: Entity at target (to take from)
    if np.any(valid_insert_targets):
        action_mask[5] = 1.0
        spatial_mask[5, :] = valid_insert_targets.astype(np.float32)
        item_mask[5, :] = 1.0  # Item arg irrelevant

    # ==========================================
    # 6. ACTION: CHANGE_RECIPE (6)
    # ==========================================
    # Legal IF: Entity at target
    if np.any(valid_insert_targets):
        action_mask[6] = 1.0
        spatial_mask[6, :] = valid_insert_targets.astype(np.float32)
        # Enable all valid recipes
        # For simplicity, we enable all items that act as recipe outputs
        for name, _ in RECIPES.items():
            iid = ITEM_MAP.get(name, 0)
            if iid > 0:
                item_mask[6, iid] = 1.0

    return action_mask, item_mask, spatial_mask