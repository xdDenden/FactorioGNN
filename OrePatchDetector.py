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

    def process_patches(self):
        """Group ore positions into patches and compute convex hulls."""
        # Group by ore type
        ore_types = {}
        for ore in self.ore_data:
            ore_type = ore['name']
            if ore_type not in ore_types:
                ore_types[ore_type] = []
            ore_types[ore_type].append([ore['x'], ore['y']])

        # Process each ore type
        for ore_type, positions in ore_types.items():
            positions = np.array(positions)

            # Cluster nearby positions using DBSCAN
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(positions)
            labels = clustering.labels_

            # Create convex hull for each cluster
            for label in set(labels):
                if label == -1:  # Skip noise points
                    continue

                cluster_points = positions[labels == label]

                # Need at least 3 points for convex hull
                if len(cluster_points) < 3:
                    continue

                try:
                    hull = ConvexHull(cluster_points)
                    hull_points = cluster_points[hull.vertices]

                    # Create polygon for fast point-in-polygon tests
                    polygon = Polygon(hull_points)

                    self.patches.append({
                        'ore_type': ore_type,
                        'boundary': hull_points.tolist(),
                        'polygon': polygon,
                        'center': cluster_points.mean(axis=0).tolist(),
                        'size': len(cluster_points)
                    })
                except:
                    # Skip degenerate cases
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