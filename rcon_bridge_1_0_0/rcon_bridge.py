import json
import math
from typing import List, Dict, Any, Optional
from mcrcon import MCRcon
from typing import TypedDict, Any, List

HOST = "localhost"
PORT = 27015
PASSWORD = "eenie7Uphohpaim"

class Position(TypedDict):
    x: float
    y: float

class InventoryItem(TypedDict):
    name: str
    count: int

class CharInfo(TypedDict):
    pos: Position
    inventory: List[InventoryItem]

class Coordinates(TypedDict):
    x: float
    y: float

# 2. Define the structure of the bounding box itself
class BoundingBox(TypedDict):
    left_top: Coordinates
    right_bottom: Coordinates

# 3. Define the main Entity structure
class EntityData(TypedDict):
    machine_name: str
    x: float
    y: float
    # Note: Your Lua script uses "selection_box", but your JSON example
    # uses "bounding_box". Ensure these match.
    bounding_box: BoundingBox

class Rcon_reciever:
    def __init__(self, host: str = HOST, password: str = PASSWORD , port: int = PORT):
        self.host = host
        self.password = password
        self.port = port
        self._rcon: Optional[MCRcon] = None

    def connect(self) -> None:
        if self._rcon is None:
            self._rcon = MCRcon(self.host, self.password, port=self.port)
            self._rcon.connect()

    def disconnect(self) -> None:
        if self._rcon:
            try:
                self._rcon.disconnect()
            finally:
                self._rcon = None

    def scan_entities(self) -> List[Dict[str, Any]]:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        response = self._rcon.command("/scan_entities")
        if not response or not response.strip():
            return []
        entities = json.loads(response)
        return entities

    def scan_entities_boundingboxes(self) -> List[EntityData]:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")

        # Note: Ensure the Lua command string matches the function name in Lua
        response = self._rcon.command("/scan_entities_boundingboxes")

        if not response or not response.strip():
            return []

        entities_with_bounding_boxes: List[EntityData] = json.loads(response)
        return entities_with_bounding_boxes

    def move_to(self, x: int, y: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        command = self._rcon.command(f"/moveto {x} {y}")
        return None

    def char_info(self) -> CharInfo:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")

        response = self._rcon.command("/char_info")
        if not response or not response.strip():
            return {"pos": {"x": 0, "y": 0}, "inventory": []}

        return json.loads(response)

    def give(self, itemIndex: int, amount: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        self._rcon.command(f"/give {itemIndex} {amount}")

    def craft(self, itemIndex: int, amount: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        self._rcon.command(f"/craft {itemIndex} {amount}")

    def mine(self, x: float, y: float) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        if self.distanceCheck(x, y):
            self._rcon.command(f"/mine {x} {y} ")

    def insert(self,x: float, y: float, itemIndex: int, amount: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        if self.distanceCheck(x, y):
            self._rcon.command(f"/insert_into {x} {y} {itemIndex} {amount}")

    def take(self,x: float, y: float) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        if self.distanceCheck(x, y):
            self._rcon.command(f"/take {x} {y} ")

    def change_recipe(self,x: float, y: float, itemIndex: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        if self.distanceCheck(x, y):
            self._rcon.command(f"/c_recipe {x} {y} {itemIndex} ")

    def build(self, x: float, y: float, buildingIndex: int, rotation: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        if self.distanceCheck(x, y):
            self._rcon.command(f"/build {x} {y} {buildingIndex} {rotation} ")

    def distanceCheck(self, x2: float, y2: float) -> bool:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        char_info = self.char_info()
        x1 = char_info['pos']['x']
        y1 = char_info['pos']['y']
        dist = math.dist((x1, y1), (x2, y2))

        if dist <= 20.0:
            return True
        else:
            return False

if __name__ == "__main__":
    receiver =  Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        entities = receiver.scan_entities()
        print(entities)
    finally:
        receiver.disconnect()