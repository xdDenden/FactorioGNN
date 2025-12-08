import math
from typing import Any

import rcon_bridge_1_0_0.rcon_bridge

# ==========================================
#              HELPER FUNCTIONS
# ==========================================

def get_search_coords(x, y, rotation, distance=1):
    """Return the coordinates at a certain distance in the direction of rotation."""
    if rotation == 0:
        return x, y - distance
    elif rotation == 4:
        return x + distance, y
    elif rotation == 8:
        return x, y + distance
    elif rotation == 12:
        return x - distance, y
    return x, y


def is_point_in_selection_box(px, py, selection_box):
    """Check if a point (px, py) is inside the selection box."""
    left_top = selection_box['left_top']
    right_bottom = selection_box['right_bottom']
    return (left_top['x'] <= px <= right_bottom['x'] and
            left_top['y'] <= py <= right_bottom['y'])


# ==========================================
#           LOGIC FINDER FUNCTIONS
# ==========================================

def find_edges(machine_list, check_from, check_to, max_distance=1, strict_rotation=False, check_selection_box=False,
               is_underground_belt=False, is_inserter=False, is_pipe_to_ground=False, is_burner_miner=False):
    """Generic edge detection for Belts, Inserters, and simple connections."""
    edges = []

    # ==========================================
    # 1. INSERTER LOGIC (Optimized)
    # ==========================================
    if is_inserter:
        # PRE-FILTER: Create a list of only things an inserter can actually touch.
        # This removes trees, walls, poles, and landmines from the inner loop calculations.
        interactable_targets = []
        for m in machine_list:
            name = m['machine_name']
            # Fast string checks to categorize valid targets
            if (name.startswith('assembling') or
                    'belt' in name or
                    'chest' in name or
                    'lab' in name or
                    'furnace' in name or
                    'chemical' in name or
                    name in ['roboport', 'beacon', 'boiler', 'steam-engine', 'rocket-silo']):
                interactable_targets.append(m)

        for machine in machine_list:
            if machine['machine_name'] not in check_from: continue


            raw_rot = machine.get('rotation')
            if raw_rot is None or raw_rot == "None":
                rotation = 0  # Default to 0 if missing rotation
            else:
                try:
                    rotation = int(raw_rot)
                except ValueError:
                    rotation = 0

            x, y = machine['x'], machine['y']
            is_long = machine['machine_name'] == 'long-handed-inserter'
            pickup_dist = 2 if is_long else 1
            drop_dist = 2 if is_long else 1

            # Pickup (Front)
            front_x, front_y = get_search_coords(x, y, rotation, distance=pickup_dist)
            # Drop (Behind - opposite rotation)
            behind_rotation = (rotation + 8) % 16
            behind_x, behind_y = get_search_coords(x, y, behind_rotation, distance=drop_dist)

            front_entity, behind_entity = None, None

            # Iterate only over valid targets, not the whole map
            for other in interactable_targets:
                if other == machine: continue

                # Optimization: Bounding box pre-check (AABB)
                # If the target is too far away in X or Y, don't run the detailed selection box math.
                # Max reach + machine size ~ 3 tiles.
                if abs(other['x'] - x) > 3 or abs(other['y'] - y) > 3:
                    continue

                if is_point_in_selection_box(front_x, front_y, other['selection_box']):
                    front_entity = other
                if is_point_in_selection_box(behind_x, behind_y, other['selection_box']):
                    behind_entity = other

            if front_entity:
                edges.append({"from_name": front_entity['machine_name'], "from_x": front_entity['x'],
                              "from_y": front_entity['y'],
                              "to_name": machine['machine_name'], "to_x": x, "to_y": y})
            if behind_entity:
                edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                              "to_name": behind_entity['machine_name'], "to_x": behind_entity['x'],
                              "to_y": behind_entity['y']})
        return edges

    # ==========================================
    # 2. PIPE TO GROUND LOGIC (Coordinate Lookup - Already Optimal)
    # ==========================================
    if is_pipe_to_ground:
        coord_lookup = {(m['x'], m['y']): m for m in machine_list}
        for machine in machine_list:
            if machine['machine_name'] not in check_from: continue
            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            if rotation is None:
                rotation = 0  # Default to 0 if missing rotation
            opposite_rotation = (rotation + 8) % 16

            # Check for pipe-to-ground 1 tile away in the direction we're facing
            # with opposite rotation (entrance-to-entrance connection)
            # Only add edge if we're the "lower" coordinate to avoid duplicates
            check_x, check_y = get_search_coords(x, y, rotation, distance=1)
            adjacent = coord_lookup.get((check_x, check_y))
            if adjacent and adjacent['machine_name'] in check_to:
                if adjacent['rotation'] == opposite_rotation:
                    # Only create edge from the pipe with smaller coordinates
                    if (x, y) < (check_x, check_y):
                        edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                      "to_name": adjacent['machine_name'], "to_x": check_x, "to_y": check_y})

            # Original logic: Check for underground connection (2-10 tiles away)
            for distance in range(2, max_distance + 1):
                sx, sy = get_search_coords(x, y, opposite_rotation, distance)
                other = coord_lookup.get((sx, sy))
                if other and other['machine_name'] in check_to:
                    if other['rotation'] == rotation: break
                    if other['rotation'] == opposite_rotation:
                        edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                      "to_name": other['machine_name'], "to_x": sx, "to_y": sy})
                        break
        return edges

    # ==========================================
    # 3. UNDERGROUND BELT LOGIC (Coordinate Lookup - Already Optimal)
    # ==========================================
    if is_underground_belt:
        coord_lookup = {(m['x'], m['y']): m for m in machine_list}
        for machine in machine_list:
            if machine['machine_name'] not in check_from: continue
            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            for distance in range(1, max_distance + 1):
                sx, sy = get_search_coords(x, y, rotation, distance)
                other = coord_lookup.get((sx, sy))
                if other and other['machine_name'] in check_to:
                    if other['rotation'] == rotation:
                        edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                      "to_name": other['machine_name'], "to_x": sx, "to_y": sy})
                        break
        return edges

    # ==========================================
    # 4. BURNER MINER LOGIC (Optimized)
    # ==========================================
    if is_burner_miner:
        # PRE-FILTER: Only look at valid output targets (Furnaces, Belts)
        valid_targets = [m for m in machine_list if m['machine_name'] in check_to]

        for machine in machine_list:
            if machine['machine_name'] not in check_from: continue
            x, y, rotation = machine['x'], machine['y'], machine['rotation']

            # Use Distance 2 to ensure we land IN the tile, not on the edge
            sx, sy = get_search_coords(x, y, rotation, distance=2)

            for other in valid_targets:
                if other == machine: continue

                # Simple distance check optimization before complex box math
                if abs(other['x'] - sx) > 1.5 or abs(other['y'] - sy) > 1.5:
                    continue

                if is_point_in_selection_box(sx, sy, other['selection_box']):
                    edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                  "to_name": other['machine_name'], "to_x": other['x'], "to_y": other['y']})
                    break
        return edges

    # ==========================================
    # 5. STANDARD LOGIC (Coordinate Lookup - Already Optimal)
    # ==========================================
    coord_lookup = {(m['x'], m['y']): m for m in machine_list}

    for machine in machine_list:
        if machine['machine_name'] not in check_from: continue
        x, y, rotation = machine['x'], machine['y'], machine['rotation']

        if rotation is None:
            rotation = 0  # Default to 0 if missing rotation
        valid_rotations = [rotation] if strict_rotation else [rotation, (rotation + 4) % 16, (rotation - 4) % 16]

        for distance in range(1, max_distance + 1):
            sx, sy = get_search_coords(x, y, rotation, distance)
            other = coord_lookup.get((sx, sy))

            if other and other['machine_name'] in check_to:
                if check_selection_box and not is_point_in_selection_box(sx, sy, other['selection_box']):
                    continue

                if other['rotation'] in valid_rotations:
                    edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                  "to_name": other['machine_name'], "to_x": sx, "to_y": sy})
    return edges


def find_pipe_edges(machine_list):
    """Find pipe-to-pipe connections (+ shape)."""
    edges = []
    coord_lookup = {(m['x'], m['y']): m for m in machine_list if m['machine_name'] == 'pipe'}
    seen = set()

    for machine in machine_list:
        if machine['machine_name'] != 'pipe': continue
        x, y = machine['x'], machine['y']

        # Check North, East, South, West
        directions = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]

        for cx, cy in directions:
            other = coord_lookup.get((cx, cy))
            if other:
                # Deduplication key
                coord1, coord2 = (x, y), (cx, cy)
                edge_key = tuple(sorted([coord1, coord2]))

                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({"from_name": machine['machine_name'], "from_x": x, "from_y": y,
                                  "to_name": other['machine_name'], "to_x": cx, "to_y": cy})
    return edges


def find_belt_to_splitter_edges(machine_list):
    """Find connections entering or leaving splitters."""
    edges = []
    # Optimization: Filter lists once
    splitters = [m for m in machine_list if 'splitter' in m['machine_name']]
    belts = [m for m in machine_list if 'transport-belt' in m['machine_name']]  # includes fast/express

    for splitter in splitters:
        x, y, rotation = splitter['x'], splitter['y'], splitter['rotation']
        if rotation is None:
            rotation = 0
        opposite_rotation = (rotation + 8) % 16

        # Coords
        left_rot = (rotation + 8) % 16
        lx, ly = get_search_coords(x, y, left_rot, 1)  # Behind (Input)
        rx, ry = get_search_coords(x, y, rotation, 1)  # Front (Output)

        for belt in belts:
            # Input Side
            if is_point_in_selection_box(lx, ly, belt['selection_box']):
                if belt['rotation'] == rotation:
                    edges.append({"from_name": belt['machine_name'], "from_x": belt['x'], "from_y": belt['y'],
                                  "to_name": splitter['machine_name'], "to_x": x, "to_y": y})

            # Output Side
            if is_point_in_selection_box(rx, ry, belt['selection_box']):
                if belt['rotation'] != opposite_rotation:
                    edges.append({"from_name": splitter['machine_name'], "from_x": x, "from_y": y,
                                  "to_name": belt['machine_name'], "to_x": belt['x'], "to_y": belt['y']})
    return edges


def find_power_edges(machine_list):
    """Finds electric pole connections."""
    edges = []
    pole_stats = {
        'small-electric-pole': {'reach': 7.5, 'area_size': 5},
        'medium-electric-pole': {'reach': 9.0, 'area_size': 7},
        'big-electric-pole': {'reach': 32.0, 'area_size': 4},
        'substation': {'reach': 18.0, 'area_size': 18}
    }

    no_power = {"wooden-chest", "storage-tank", "transport-belt", "fast-transport-belt",
                "underground-belt", "fast-underground-belt", "splitter", "fast-splitter",
                "burner-inserter", "pipe", "pipe-to-ground", "boiler", "burner-mining-drill",
                "stone-furnace", "steel-furnace", "offshore-pump"}

    poles = [m for m in machine_list if m['machine_name'] in pole_stats]
    consumers = [m for m in machine_list if m['machine_name'] not in no_power and m['machine_name'] not in pole_stats]

    # 1. Pole to Pole (Wire)
    for i, p1 in enumerate(poles):
        for j in range(i + 1, len(poles)):
            p2 = poles[j]
            dist = math.sqrt((p1['x'] - p2['x']) ** 2 + (p1['y'] - p2['y']) ** 2)
            max_reach = min(pole_stats[p1['machine_name']]['reach'], pole_stats[p2['machine_name']]['reach'])

            if dist <= max_reach:
                edges.append({"from_name": p1['machine_name'], "from_x": p1['x'], "from_y": p1['y'],
                              "to_name": p2['machine_name'], "to_x": p2['x'], "to_y": p2['y'],
                              "relation_type": "power_wire"})

    # 2. Pole to Machine (Supply Area)
    def boxes_overlap(box1, box2):
        l1, r1 = box1['left_top'], box1['right_bottom']
        l2, r2 = box2['left_top'], box2['right_bottom']
        return not (l1['x'] >= r2['x'] or l2['x'] >= r1['x'] or l1['y'] >= r2['y'] or l2['y'] >= r1['y'])

    for p in poles:
        size = pole_stats[p['machine_name']]['area_size']
        half = size / 2.0
        supply_box = {'left_top': {'x': p['x'] - half, 'y': p['y'] - half},
                      'right_bottom': {'x': p['x'] + half, 'y': p['y'] + half}}

        for m in consumers:
            if 'selection_box' in m and boxes_overlap(supply_box, m['selection_box']):
                edges.append({"from_name": p['machine_name'], "from_x": p['x'], "from_y": p['y'],
                              "to_name": m['machine_name'], "to_x": m['x'], "to_y": m['y'],
                              "relation_type": "power_supply"})
    return edges


# --- FLUID HELPERS (Specific Machines) ---
# Keeping these separate to preserve the specific offset logic provided in the prompt

def _find_machine_fluid_edges(machine_list, target_name, config_map):
    """Generic helper for specific fluid machines to reduce duplication."""
    edges = []
    coord_lookup = {(m['x'], m['y']): m for m in machine_list if m['machine_name'] in ('pipe', 'pipe-to-ground')}

    for machine in machine_list:
        if machine['machine_name'] != target_name: continue
        x, y, rotation = machine['x'], machine['y'], machine['rotation']

        # Get connections for this rotation
        connections = config_map.get(rotation, [])

        for conn in connections:
            ox, oy = conn['offset']
            check_x, check_y = x + ox, y + oy
            pipe = coord_lookup.get((check_x, check_y))

            if pipe:
                is_valid = False
                if pipe['machine_name'] == 'pipe':
                    is_valid = True
                elif pipe['machine_name'] == 'pipe-to-ground' and pipe['rotation'] == conn['req_rot']:
                    is_valid = True

                if is_valid:
                    edges.append({"from_name": pipe['machine_name'], "from_x": check_x, "from_y": check_y,
                                  "to_name": machine['machine_name'], "to_x": x, "to_y": y})
    return edges


def find_chemical_plant_pipe_edges(machine_list):
    config = {
        0: [{'offset': (-1, -2), 'req_rot': 8}, {'offset': (1, -2), 'req_rot': 8},
            {'offset': (-1, 2), 'req_rot': 0}, {'offset': (1, 2), 'req_rot': 0}],
        4: [{'offset': (2, -1), 'req_rot': 12}, {'offset': (2, 1), 'req_rot': 12},
            {'offset': (-2, -1), 'req_rot': 4}, {'offset': (-2, 1), 'req_rot': 4}],
        8: [{'offset': (1, 2), 'req_rot': 0}, {'offset': (-1, 2), 'req_rot': 0},
            {'offset': (1, -2), 'req_rot': 8}, {'offset': (-1, -2), 'req_rot': 8}],
        12: [{'offset': (-2, 1), 'req_rot': 4}, {'offset': (-2, -1), 'req_rot': 4},
             {'offset': (2, 1), 'req_rot': 12}, {'offset': (2, -1), 'req_rot': 12}]
    }
    return _find_machine_fluid_edges(machine_list, 'chemical-plant', config)


def find_oil_ref_pipe_edges(machine_list):
    config = {
        0: [{'offset': (2, -3), 'req_rot': 8}, {'offset': (1, 3), 'req_rot': 0}],
        4: [{'offset': (3, 2), 'req_rot': 12}, {'offset': (-3, 1), 'req_rot': 4}],
        8: [{'offset': (-1, 3), 'req_rot': 0}, {'offset': (-2, -3), 'req_rot': 8}],
        12: [{'offset': (-3, -1), 'req_rot': 4}, {'offset': (3, -2), 'req_rot': 12}]
    }
    return _find_machine_fluid_edges(machine_list, 'oil-refinery', config)


def find_steam_engine_pipe_edges(machine_list):
    config = {
        0: [{'offset': (0, -3), 'req_rot': 8}, {'offset': (0, 3), 'req_rot': 0}],
        4: [{'offset': (3, 0), 'req_rot': 12}, {'offset': (-3, 0), 'req_rot': 4}],
        8: [], 12: []
    }
    return _find_machine_fluid_edges(machine_list, 'steam-engine', config)


def find_boiler_pipe_edges(machine_list):
    config = {
        0: [{'offset': (0, -1.5), 'req_rot': 8}, {'offset': (2, 0.5), 'req_rot': 12},
            {'offset': (-2, 0.5), 'req_rot': 4}],
        4: [{'offset': (1.5, 0), 'req_rot': 12}, {'offset': (-0.5, 2), 'req_rot': 0},
            {'offset': (-0.5, -2), 'req_rot': 8}],
        8: [{'offset': (0, 1.5), 'req_rot': 0}, {'offset': (-2, -0.5), 'req_rot': 4},
            {'offset': (2, -0.5), 'req_rot': 12}],
        12: [{'offset': (-1.5, 0), 'req_rot': 4}, {'offset': (0.5, -2), 'req_rot': 8},
             {'offset': (0.5, 2), 'req_rot': 0}]
    }
    return _find_machine_fluid_edges(machine_list, 'boiler', config)


def find_offshore_pipe_edges(machine_list):
    config = {
        0: [{'offset': (0, 1), 'req_rot': 0}],
        4: [{'offset': (-1, 0), 'req_rot': 4}],
        8: [{'offset': (0, -1), 'req_rot': 8}],
        12: [{'offset': (1, 0), 'req_rot': 12}]
    }
    return _find_machine_fluid_edges(machine_list, 'offshore-pump', config)


def find_pumpjack_pipe_edges(machine_list):
    config = {
        0: [{'offset': (1, -2), 'req_rot': 8}],
        4: [{'offset': (2, -1), 'req_rot': 12}],
        8: [{'offset': (-1, 2), 'req_rot': 0}],
        12: [{'offset': (-2, 1), 'req_rot': 4}]
    }
    return _find_machine_fluid_edges(machine_list, 'pumpjack', config)


def find_ground_pipe_pipe_edges(machine_list):
    config = {
        0: [{'offset': (0, -1), 'req_rot': 0}],
        4: [{'offset': (1, 0), 'req_rot': 4}],
        8: [{'offset': (0, 1), 'req_rot': 8}],
        12: [{'offset': (-1, 0), 'req_rot': 12}]
    }
    return _find_machine_fluid_edges(machine_list, 'pipe-to-ground', config)


# ==========================================
#              MAIN FUNCTION
# ==========================================

def translateEntitesToEdges(reciever) -> list[Any] | None:
    # 1. Fetch Data
    machines = reciever.scan_entities_boundingboxes()
    if not machines:
        #print("No entities found.")
        return []

    # 2. Consolidate Edge Finding
    all_edges = []

    # --- Transport & Belts ---
    #print("\nProcessing Belts...")
    all_edges.extend(
        find_edges(machines, check_from=('transport-belt', 'fast-transport-belt', 'express-transport-belt'),
                   check_to=('transport-belt', 'fast-transport-belt', 'express-transport-belt')))

    all_edges.extend(find_edges(machines, check_from=('electric-mining-drill',),
                                check_to=('transport-belt', 'fast-transport-belt', 'express-transport-belt'),
                                max_distance=2, check_selection_box=True))

    all_edges.extend(find_edges(machines, check_from=('transport-belt',),
                                check_to=('underground-belt',), strict_rotation=True))

    all_edges.extend(find_edges(machines, check_from=('underground-belt',),
                                check_to=('underground-belt',), max_distance=5, is_underground_belt=True))
    all_edges.extend(find_edges(machines, check_from=('burner-mining-drill',),
                                check_to=('stone-furnace', 'transport-belt','fast-transport-belt', 'express-transport-belt'),max_distance=1,is_burner_miner=True))

    all_edges.extend(find_belt_to_splitter_edges(machines))

    # --- Inserters ---
    #print("\nProcessing Inserters...")
    all_edges.extend(find_edges(machines,
                                check_from=('inserter', 'fast-inserter', 'long-handed-inserter', 'stack-inserter',
                                            'burner-inserter', 'bulk-inserter'),
                                check_to=None,  # Ignored inside is_inserter logic
                                is_inserter=True))

    # --- Fluids (Pipes & Machines) ---
    #print("\nProcessing Fluids...")
    all_edges.extend(find_edges(machines, check_from=('pipe-to-ground',),
                                check_to=('pipe-to-ground',), max_distance=10, is_pipe_to_ground=True))

    all_edges.extend(find_pipe_edges(machines))
    all_edges.extend(find_ground_pipe_pipe_edges(machines))
    all_edges.extend(find_chemical_plant_pipe_edges(machines))
    all_edges.extend(find_oil_ref_pipe_edges(machines))
    all_edges.extend(find_steam_engine_pipe_edges(machines))
    all_edges.extend(find_boiler_pipe_edges(machines))
    all_edges.extend(find_offshore_pipe_edges(machines))
    all_edges.extend(find_pumpjack_pipe_edges(machines))

    # --- Power ---
    #print("\nProcessing Power...")
    all_edges.extend(find_power_edges(machines))

    # 3. Final Output
    #print(f"\n=== FINAL CONSOLIDATION ===")
    #print(f"Total edges generated: {len(all_edges)}")

    # Optional: #print edges or process further
    # for e in all_edges:
    #     #print(e)

    return all_edges