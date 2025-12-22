# import unittest
# import numpy as np
# from shapely.geometry import Polygon
# from ActionMasking import get_action_masks
# from mappings import ACTION_MAP, ITEM_MAP, MACHINE_NAME_MAP
#
#  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
##  DEPRECATED
#
#
#
#
#
# class TestActionMasking(unittest.TestCase):
#
#     def setUp(self):
#         # Common setup for all tests
#         self.bounds = (-10, 10, -10, 10)  # 20x20 world size
#         self.grid_steps = 17  # Standard grid size from your config
#         self.player_pos = {'x': 0, 'y': 0}
#         self.player_info = {'pos': self.player_pos, 'inventory': []}
#
#         # Helper to create an empty list of entities
#         self.entities = []
#
#         # Action IDs for readability
#         self.MINE = ACTION_MAP.get('mine', 2)
#         self.CRAFT = ACTION_MAP.get('craft', 3)
#         self.BUILD = ACTION_MAP.get('build', 4)
#
#     def test_mining_ore_patch(self):
#         """Test if mining mask correctly identifies ore patches within reach."""
#         print("\n--- Testing Mining Mask ---")
#
#         # 1. Create a dummy patch close to the player (0,0)
#         # A square from x=1 to x=3, y=1 to y=3
#         patch_polygon = Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])
#         patches = [{
#             'ore_type': 'iron-ore',
#             'polygon': patch_polygon,
#             'name': 'iron-ore'
#         }]
#
#         # 2. Get Masks
#         act_mask, item_mask, spatial_mask = get_action_masks(
#             entities=[],
#             player_info=self.player_info,
#             inventory={},
#             science_level=1,
#             bounds=self.bounds,
#             grid_steps=self.grid_steps,
#             patches=patches
#         )
#
#         # 3. Assertions
#         # Mining action should be allowed (1.0)
#         self.assertEqual(act_mask[self.MINE], 1.0, "Mine action should be enabled when near ore.")
#
#         # Check Spatial Mask
#         # We expect some bits to be 1.0 corresponding to the patch location
#         valid_tiles = np.sum(spatial_mask[self.MINE])
#         print(f"Valid mining tiles found: {valid_tiles}")
#         self.assertGreater(valid_tiles, 0, "Should have valid tiles to mine in the spatial mask.")
#
#     def test_mining_reach_limit(self):
#         """Test that we cannot mine a patch that is too far away."""
#         print("\n--- Testing Mining Reach ---")
#
#         # Patch at x=50, y=50 (Way outside reach of 10)
#         patch_polygon = Polygon([(50, 50), (52, 50), (52, 52), (50, 52)])
#         patches = [{
#             'ore_type': 'copper-ore',
#             'polygon': patch_polygon,
#             'name': 'copper-ore'
#         }]
#
#         act_mask, _, spatial_mask = get_action_masks(
#             entities=[],
#             player_info=self.player_info,
#             inventory={},
#             science_level=1,
#             bounds=self.bounds,
#             patches=patches
#         )
#
#         # Mining should be disabled (0.0) if nothing is in reach
#         # Note: If there are no entities AND no reachable patches, mask is 0
#         self.assertEqual(act_mask[self.MINE], 0.0, "Mine action should be disabled when patch is out of reach.")
#         self.assertEqual(np.sum(spatial_mask[self.MINE]), 0, "No spatial tiles should be valid.")
#
#     def test_crafting_logic(self):
#         """Test if crafting mask enables specific items based on inventory."""
#         print("\n--- Testing Crafting Logic ---")
#
#         # 1. Case: Have ingredients for 'transport-belt' (1 iron-plate, 1 gear)
#         inventory = {'iron-plate': 10, 'iron-gear-wheel': 10}
#
#         act_mask, item_mask, _ = get_action_masks(
#             entities=[],
#             player_info=self.player_info,
#             inventory=inventory,
#             science_level=1,
#             bounds=self.bounds,
#             patches=[]
#         )
#
#         belt_id = ITEM_MAP.get('transport-belt')
#
#         self.assertEqual(act_mask[self.CRAFT], 1.0, "Craft action should be active.")
#         self.assertEqual(item_mask[self.CRAFT, belt_id], 1.0, "Should be able to craft transport-belt.")
#
#         # 2. Case: Missing ingredients (No iron)
#         inventory_poor = {'wood': 10}  # Can only make chest/poles
#
#         act_mask, item_mask, _ = get_action_masks(
#             entities=[],
#             player_info=self.player_info,
#             inventory=inventory_poor,
#             science_level=1,
#             bounds=self.bounds,
#             patches=[]
#         )
#
#         self.assertEqual(item_mask[self.CRAFT, belt_id], 0.0, "Should NOT be able to craft belt without iron.")
#
#     def test_building_collision(self):
#         """Test that we cannot build on top of existing entities."""
#         print("\n--- Testing Building Collision ---")
#
#         # Place an entity at (2, 2)
#         entities = [{'name': 'stone-furnace', 'x': 2, 'y': 2}]
#         inventory = {'transport-belt': 5}  # We have item to build
#
#         act_mask, _, spatial_mask = get_action_masks(
#             entities=entities,
#             player_info=self.player_info,
#             inventory=inventory,
#             science_level=1,
#             bounds=self.bounds,
#             grid_steps=self.grid_steps,
#             patches=[]
#         )
#
#         # 1. Convert (2,2) to grid coordinates to check the mask
#         # Simplified conversion logic mirroring ActionMasking.py
#         min_x, max_x, min_y, max_y = self.bounds
#         step_x = (max_x - min_x) / self.grid_steps
#         step_y = (max_y - min_y) / self.grid_steps
#
#         grid_x = int((2 - min_x) / (max_x - min_x) * (self.grid_steps - 1))
#         grid_y = int((2 - min_y) / (max_y - min_y) * (self.grid_steps - 1))
#
#         flat_idx = grid_y * self.grid_steps + grid_x
#
#         # 2. Assertions
#         self.assertEqual(act_mask[self.BUILD], 1.0, "Build action should be available.")
#
#         # The specific tile at (2,2) should be masked OUT (0.0) because an entity is there
#         self.assertEqual(spatial_mask[self.BUILD, flat_idx], 0.0,
#                          "Should not be able to build on top of existing entity.")
#
#
# if __name__ == '__main__':
#     unittest.main()