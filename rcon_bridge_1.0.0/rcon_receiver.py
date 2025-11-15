import json
import time
from mcrcon import MCRcon

HOST = "localhost"
PORT = 27015
PASSWORD = "eenie7Uphohpaim"
POLL_INTERVAL = 5  # Alle 5 Sekunden abfragen

try:
    rcon = MCRcon(HOST, PASSWORD, port=PORT)
    rcon.connect()
    print(f"✓ Connected to Factorio RCON at {HOST}:{PORT}\n")
except Exception as e:
    print(f"✗ Failed to connect: {e}")
    exit(1)

try:
    while True:
        # Assembler Scan aufrufen
        response = rcon.command("/scan_assemblers")
        
        if response and response.strip():
            try:
                entities = json.loads(response)
                
                print("=" * 80)
                print("Vectorlist:\n")
                
                for entity in entities:
                    # Dynamisch alle Keys ausgeben
                    values = [f"{key}={value}" for key, value in entity.items()]
                    print(", ".join(values))
                
                print(f"\nTotal Entities: {len(entities)}")
                print("=" * 80)
                print()
                
            except json.JSONDecodeError as e:
                print(f"⚠ JSON parse error: {e}")
                print(f"Raw response: {response}\n")
        
        time.sleep(POLL_INTERVAL)
        
except KeyboardInterrupt:
    print("\n✓ Closing RCON connection...")
    rcon.disconnect()