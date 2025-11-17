import traceback
from rcon_bridge_1_0_0.rcon_reciever import Rcon_reciever
from parsers import parse_entity
from features import transform_entities

if __name__ == "__main__":
    receiver = Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        # raw_entities is a List[Dict[str, str]]
        raw_entities = receiver.scan_entities()

        entities = [parse_entity(e['machine_name'], e) for e in raw_entities]
        features = transform_entities(entities)

        #print(features)

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
    finally:
        receiver.disconnect()