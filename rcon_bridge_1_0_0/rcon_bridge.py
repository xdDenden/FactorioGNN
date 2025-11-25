import json
from typing import List, Dict, Any, Optional
from mcrcon import MCRcon

HOST = "localhost"
PORT = 27015
PASSWORD = "eenie7Uphohpaim"

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
    def move_to(self, x: int, y: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        command = self._rcon.command("/moveto x={} y={}".format(x, y))
        return None
    def char_info(self) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        command = self._rcon.command("/char_info")
    def give(self, itemIndex: int, amount: int) -> None:
        if not self._rcon:
            raise RuntimeError("Not connected. Call connect() first.")
        command = self._rcon.command("/give itemIndex={} amount={}".format(itemIndex, amount))
        return None



if __name__ == "__main__":
    receiver =  Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
    try:
        receiver.connect()
        entities = receiver.scan_entities()
        print(entities)
    finally:
        receiver.disconnect()