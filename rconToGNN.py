import traceback
import torch
import rcon_bridge_1_0_0.rcon_bridge
import Edging

from parsers import parse_entity, Entity
from features import transform_entities, map_items, compute_bounds,unnormalize_coord
from FactorioHGNN import (
    FactorioHGNN,
    preprocess_features_for_gnn,
    create_grid_hypergraph
)
from GNNtoFactorio import translateGNNtoFactorio

if __name__ == "__main__":
    receiver = rcon_bridge_1_0_0.rcon_bridge.Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        # raw_entities is a List[Dct[str, str]]
        raw_entities = receiver.scan_entities()
        raw_playerInfo = receiver.char_info()

        # receiver.move_to(-18,-2)
        # receiver.give(38,100)
        # receiver.craft(44,10)
        # receiver.mine(-19.203,-1.988)
        # receiver.insert(-43.5,-25.5,38,10)
        # receiver.take(-43.5,-25.5)
        # receiver.change_recipe(-43.5,-25.5, 1)
        # receiver.char_info()


        """
        Imaginary point 1 tile in the opposite direction the inserter is facing
        if the point is inside the collision bounding box of an entity, then the inserter is facing that entity therefore we can make edges between them.
        Same thing for belt. 
        Every building must edge
        edge, edge... interlinked... edge edge...interlinked...
        (electric poles might edge between each other too(and maybe edge with power generating buildings?))

        """



        # 1. Parse raw dicts into Entity objects
        # We need this original list for coordinates
        entities = [parse_entity(e['machine_name'], e) for e in raw_entities]
        #Edging.translateEntitesToEdges(receiver)

        # Calculate bounds once, covering both entities and player position
        bounds = compute_bounds(entities, char_info=raw_playerInfo)

        playerInfo = map_items(raw_playerInfo, bounds)

        # 2. Transform entities into feature dictionaries using the shared bounds
        features = transform_entities(entities, bounds=bounds)

        # 3. Preprocess features into the final node feature tensor
        # We now pass the playerInfo to be encoded as the last node
        node_features = preprocess_features_for_gnn(features, player_info=playerInfo)

        # 4. Create a hypergraph (using our grid-based method)
        # We need to include the player in the hypergraph as well.
        # Create a dummy Entity for the player using raw coordinates.
        player_x = int(raw_playerInfo.get('pos', {}).get('x', 0))
        player_y = int(raw_playerInfo.get('pos', {}).get('y', 0))
        player_entity = Entity('player', player_x, player_y)

        # Combine entities with player for the graph structure
        all_entities = entities + [player_entity]
        H = create_grid_hypergraph(all_entities, grid_size=10)

        # 5. Instantiate and run the model
        model = FactorioHGNN()
        model.eval()  # Set to evaluation mode

        # 5. Instantiate and run the model
        model = FactorioHGNN()
        model.eval()  # Set to evaluation mode

        # The model returns logits (raw scores) for each output head.
        action_logits, item_logits, rotation_logits, heatmap, _ = model(node_features, H)

        # Get the predicted index by finding the max logit value.
        # .item() extracts the scalar value from the tensor.
        action_idx = torch.argmax(action_logits).item()
        item_idx = torch.argmax(item_logits).item()
        rotation_idx = torch.argmax(rotation_logits).item()

        flat_max_idx = torch.argmax(heatmap)

        y_grid_idx = (flat_max_idx // 17).item()
        x_grid_idx = (flat_max_idx % 17).item()

        # 3. Convert grid indices to normalized floats [-1.0, 1.0]
        # We divide by 16.0 because in a 17-step grid, there are 16 intervals.
        # Index 0 -> -1.0, Index 16 -> 1.0
        x_norm = -1.0 + (x_grid_idx / 16.0) * 2.0
        y_norm = -1.0 + (y_grid_idx / 16.0) * 2.0

        # 4. Unnormalize to get actual world coordinates using the bounds
        # bounds structure is: [min_x, max_x, min_y, max_y]
        final_x = unnormalize_coord(x_norm, bounds[0], bounds[1])
        final_y = unnormalize_coord(y_norm, bounds[2], bounds[3])


        print("\n--- Model Ran Successfully ---")
        print(f"Predicted heatmap index: [{x_grid_idx}, {y_grid_idx}]")
        print(f"Predicted World position: x={final_x}, y={final_y}")

        translateGNNtoFactorio(final_x, final_y, action_idx, item_idx, rotation_idx, receiver)


        # print(f"Action logits shape: {action.shape}")
        # print(f"Item logits shape: {item.shape}")
        # print(f"Heatmap logits shape: {heatmap.shape}")

        # print(features)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    finally:
        receiver.disconnect()