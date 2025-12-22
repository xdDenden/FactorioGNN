import numpy as np
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN
from shapely.geometry import Point, Polygon
from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever


class OrePatchDetector:
    def __init__(self, ore_data, eps=5.0, min_samples=3):
        """
        Initialize the ore patch detector.

        Args:
            ore_data: List of dicts with 'name', 'x', 'y' keys
            eps: Maximum distance between points in same cluster (DBSCAN parameter)
            min_samples: Minimum points to form a cluster
        """
        self.ore_data = ore_data
        self.eps = eps
        self.min_samples = min_samples
        self.patches = []

    def process_patches(self, tree_gap=10.0):
        """
        Group positions into patches and compute convex hulls.
        tree_gap: The max distance (tiles) allowed between trees to be part of the same forest.
        """
        groups = {}

        # 1. Group Data: Merge all tree names into one 'tree' category
        for entity in self.ore_data:
            # Check if entity is a tree (using 'type' from Lua or name fallback)
            is_tree = entity.get('type') == 'tree' or 'tree' in entity['name']

            # If it's a tree, use a generic key. If it's ore, use the specific name.
            group_key = 'tree' if is_tree else entity['name']

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append([entity['x'], entity['y']])

        # 2. Process each group (Ores and Trees)
        for group_key, positions in groups.items():
            positions = np.array(positions)

            # SELECT EPSILON: Use tree_gap for trees, default self.eps for ores
            if group_key == 'tree':
                current_eps = tree_gap
                current_min_samples = 5  # Optional: Trees might need a different density threshold
            else:
                current_eps = self.eps
                current_min_samples = self.min_samples

            # Cluster using the selected epsilon
            clustering = DBSCAN(eps=current_eps, min_samples=current_min_samples).fit(positions)
            labels = clustering.labels_

            # Create convex hull for each cluster
            for label in set(labels):
                if label == -1:  # Skip noise
                    continue

                cluster_points = positions[labels == label]

                if len(cluster_points) < 3:
                    continue

                try:
                    hull = ConvexHull(cluster_points)
                    hull_points = cluster_points[hull.vertices]
                    polygon = Polygon(hull_points)

                    self.patches.append({
                        'ore_type': group_key,  # Will be 'tree' or 'iron-ore', etc.
                        'boundary': hull_points.tolist(),
                        'polygon': polygon,
                        'center': cluster_points.mean(axis=0).tolist(),
                        'size': len(cluster_points)
                    })
                except Exception as e:
                    continue

        return self.patches

    def is_position_in_patch(self, x, y, patches=None, ore_type=None):
        """
        Check if a position is within any ore patch boundary.

        Args:
            x, y: Position to check
            patches: List of patches to check (defaults to self.patches if None)
            ore_type: Optional filter for specific ore type

        Returns:
            List of matching patches or empty list
        """
        if patches is None:
            patches = self.patches

        point = Point(x, y)
        matches = []

        for patch in patches:
            if ore_type and patch['ore_type'] != ore_type:
                continue

            if patch['polygon'].contains(point):
                matches.append(patch)

        return matches


# Example usage:
if __name__ == "__main__":

    receiver = Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        ores=receiver.scan_ore()
    except Exception as e:
        print(f"Failed to connect to RCON or fetch ores: {e}")
        ores = []

    # Create detector and process patches
    detector = OrePatchDetector(ores, eps=5.0, min_samples=3)
    patches = detector.process_patches()

    print(f"Found {len(patches)} ore patches\n")

    for i, patch in enumerate(patches):
        print(f"Patch {i + 1}:")
        print(f"  Type: {patch['ore_type']}")
        print(f"  Size: {patch['size']} ore tiles")
        print(f"  Center: {patch['center']}")
        print(f"  Boundary points: {len(patch['boundary'])}")
        print()

    # Test if position is in patch
    test_x, test_y = 15.0, -54.0
    matches = detector.is_position_in_patch(test_x, test_y)
    print(f"Position ({test_x}, {test_y}) is in {len(matches)} patch(es)")