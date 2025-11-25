import traceback
import torch
import rcon_bridge_1_0_0.rcon_bridge

from parsers import parse_entity
from features import transform_entities
from FactorioHGNN import (
    FactorioHGNN,
    preprocess_features_for_gnn,
    create_grid_hypergraph
)

if __name__ == "__main__":
    receiver = rcon_bridge_1_0_0.rcon_bridge.Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        # raw_entities is a List[Dct[str, str]]
        #raw_entities = receiver.scan_entities()
        #receiver.move_to(10,10)
        receiver.give(38,100)
        receiver.char_info()

        # 1. Parse raw dicts into Entity objects
        # We need this original list for coordinates
        #entities = [parse_entity(e['machine_name'], e) for e in raw_entities]

        # 2. Transform entities into feature dictionaries
        #features = transform_entities(entities)

        """
        # 3. Preprocess features into the final node feature tensor
        node_features = preprocess_features_for_gnn(features)

        # 4. Create a hypergraph (using our grid-based method)
        # We pass the *original* entities to use their raw coordinates
        H = create_grid_hypergraph(entities, grid_size=10)
        # 5. Instantiate and run the model
        model = FactorioHGNN()
        model.eval()  # Set to evaluation mode

        with torch.no_grad():
            action, item, heatmap = model(node_features, H)

        print("\n--- Model Ran Successfully ---")
        print(f"Action logits shape: {action.shape}")
        print(f"Item logits shape: {item.shape}")
        print(f"Heatmap logits shape: {heatmap.shape}")
        """
        #print(features)
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    finally:
        receiver.disconnect()