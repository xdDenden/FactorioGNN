import json
import math
from typing import List, Dict, Any, Optional
import factorio_rcon
from typing import TypedDict, Any, List

HOST = "localhost"
PORT = 27015
PASSWORD = "eenie7Uphohpaim"
TIMEOUT = 5.0

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
    def __init__(self, host: str = HOST, password: str = PASSWORD , port: int = PORT,timeout: float = 5.0 ,):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = timeout
        self._rcon: Optional[factorio_rcon.RCONClient] = None

    def connect(self) -> None:
        # If we are reconnecting, ensure we close the old broken connection first
        if self._rcon:
            try:
                self._rcon.close()
            except Exception:
                pass
            self._rcon = None

        self._rcon = factorio_rcon.RCONClient(self.host, self.port, self.password, self.timeout)
        self._rcon.connect()

    def disconnect(self) -> None:
        if self._rcon:
            try:
                self._rcon.close()
            finally:
                self._rcon = None

    def _send_command_with_retry(self, command: str) -> str:
        """
        Sends a command to the RCON server.
        If the connection is lost, it attempts to reconnect and resend the command once.
        """
        if not self._rcon:
            self.connect()

        try:
            return self._rcon.send_command(command)
        except Exception as e:
            # Check for RCONNotConnected or other connection errors.
            # We check the exception name to be robust against import differences.
            error_name = type(e).__name__
            if "RCONNotConnected" in error_name or "ConnectionError" in error_name:
                print(f"RCON Connection lost ({e}). Attempting to reconnect...")
                try:
                    self.connect()
                    return self._rcon.send_command(command)
                except Exception as retry_e:
                    print(f"Reconnection failed: {retry_e}")
                    raise retry_e
            else:
                # If it's a different error (e.g. JSON decode), raise it.
                raise e

    def scan_entities(self) -> List[Dict[str, Any]]:
        # 'mcrcon' uses .command(), 'rcon' uses .run()
        # Use the retry wrapper
        response = self._send_command_with_retry("/scan_entities")
        if not response or not response.strip():
            return []
        try:
            entities = json.loads(response)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Partial response received: {response[:100]}...")
            return []
        return entities

    def scan_entities_boundingboxes(self) -> List[EntityData]:
        # Note: Ensure the Lua command string matches the function name in Lua
        response = self._send_command_with_retry("/scan_entities_boundingboxes")

        if not response or not response.strip():
            return []

        try:
            entities_with_bounding_boxes: List[EntityData] = json.loads(response)
            return entities_with_bounding_boxes
        except json.JSONDecodeError:
            return []

    def move_to(self, x: int, y: int) -> None:
        self._send_command_with_retry(f"/moveto {x} {y}")
        return None

    def char_info(self) -> CharInfo:
        response = self._send_command_with_retry("/char_info")
        if not response or not response.strip():
            return {"pos": {"x": 0, "y": 0}, "inventory": []}

        return json.loads(response)

    def give(self, itemIndex: int, amount: int) -> None:
        self._send_command_with_retry(f"/give {itemIndex} {amount}")

    def craft(self, itemIndex: int, amount: int) -> None:
        self._send_command_with_retry(f"/craft {itemIndex} {amount}")

    def mine(self, x: float, y: float) -> None:
        if self.distanceCheck(x, y):
            self._send_command_with_retry(f"/mine {x} {y} ")

    def insert(self,x: float, y: float, itemIndex: int, amount: int) -> None:
        if self.distanceCheck(x, y):
            self._send_command_with_retry(f"/insert_into {x} {y} {itemIndex} {amount}")

    def take(self,x: float, y: float) -> None:
        if self.distanceCheck(x, y):
            self._send_command_with_retry(f"/take {x} {y} ")

    def change_recipe(self,x: float, y: float, itemIndex: int) -> None:
        if self.distanceCheck(x, y):
            self._send_command_with_retry(f"/c_recipe {x} {y} {itemIndex} ")

    def build(self, x: float, y: float, buildingIndex: int, rotation: int) -> None:
        if self.distanceCheck(x, y):
            self._send_command_with_retry(f"/build {x} {y} {buildingIndex} {rotation} ")

    def distanceCheck(self, x2: float, y2: float) -> bool:
        # We generally expect self._rcon to be set, but if it's broken,
        # char_info() will handle the reconnect inside its call.
        if not self._rcon:
             # If completely uninitialized, force connect (though _send_command_with_retry does this too)
             self.connect()

        char_info = self.char_info()
        x1 = char_info['pos']['x']
        y1 = char_info['pos']['y']
        dist = math.dist((x1, y1), (x2, y2))

        if dist <= 20.0:
            return True
        else:
            return False

    def rotate(self, x: float, y: float, direction: int) -> None:
        self._send_command_with_retry(f"/rotate {x} {y} {direction} ")


if __name__ == "__main__":
    receiver =  Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        entities = receiver.scan_entities()
        bbentities = receiver.scan_entities_boundingboxes()
        print(entities)
        print(bbentities)
    finally:
        receiver.disconnect()