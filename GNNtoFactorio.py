import rcon_bridge_1_0_0.rcon_bridge as rcon_bridge

def translateGNNtoFactorio( x,  y, action,  item,  receiver) -> None:
    """
    Translates GNN model outputs into Factorio commands via RCON.
    :param x: World X coordinate to target
    :param y: World Y coordinate to target
    :param action: Action logits from the model
    :param item: Item logits from the model
    :param receiver: An instance of RconBridge to send commands through
    """
    match action:

        case 0:
            receiver.move_to(x, y)
            print(f"Moving to position x={x}, y={y}")
        case 1:
            receiver.mine(x, y)
            print(f"Mining at position x={x}, y={y}")
        case 2:
            receiver.craft(item, 1)
            print(f"Crafting item index {item}, amount 1")
        case 3:
            receiver.build(x,y,item,0)
            print(f"Building item index {item} at position x={x}, y={y}")
        case 4:
            receiver.insert(x,y,item,1)
            print(f"Inserting item index {item}, amount 1 at position x={x}")
        case 5:
            receiver.take(x,y)
            print(f"Taking items at position x={x}, y={y}")
        case 6:
            receiver.change_recipe(x,y,item)
            print(f"Changing recipe to item index {item} at position x={x}, y={y}")
