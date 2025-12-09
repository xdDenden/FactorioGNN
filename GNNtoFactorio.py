from sympy import false

import rcon_bridge_1_0_0.rcon_bridge as rcon_bridge
from mappings import ID_TO_ACTION, ID_TO_ITEM

def generate_jimbo_thought(action_idx, item_idx, rotation_idx):
    """
    Pure string generation. Fast CPU operation.
    Does not touch RCON or the GPU.
    """
    act_name = ID_TO_ACTION.get(action_idx, f"UNKNOWN_ACTION_{action_idx}")
    # Use ITEM map for items, fallback to ID if missing
    item_name = ID_TO_ITEM.get(item_idx, f"ITEM_{item_idx}")

    return f"Jimbo wants to {act_name} with {item_name} at rotation {rotation_idx}!"


def translateGNNtoFactorio(x, y, action, item, rotation, receiver, verbose) -> str:
    """
    Executes the command and returns the Jimbo log string.
    """
    # 1. Generate the Personality String
    jimbo_msg = generate_jimbo_thought(action, item, rotation)

    # 2. Append specific coordinates for the final log
    full_log = f"{jimbo_msg} (Target: {x:.1f}, {y:.1f})"

    # 3. Execute RCON Command
    try:
        match action:
            case 0:  # move_to
                receiver.move_to(x, y)
            case 1:  # mine
                receiver.mine(x, y)
            case 2:  # craft
                if item is not None or not "none":
                    receiver.craft(item, 1)
            case 3:  # build
                if item is not None and rotation is not None:
                    receiver.build(x, y, item, rotation)
            case 4:  # insert
                if item is not None or not "None":
                    receiver.insert(x, y, item, 1)
            case 5:  # take
                receiver.take(x, y)
            case 6:  # change_recipe
                if item is not None or not "None":
                    receiver.change_recipe(x, y, item)
            case _:
                pass  # No-op for 'none' or unknown

    except Exception as e:
        full_log += f" [FAILED: {e}]"

    # 4. Optional Printing (Controlled by Main Loop)
    if verbose:
        print(full_log)

    return full_log