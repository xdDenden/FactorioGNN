import json
import os
import shutil

import docker

from OrePatchDetector import OrePatchDetector
from environment import FactorioEnv
from RunConfig import Config
from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever


class ActorWorker:
    def __init__(self, agent_id, base_rcon_port=27015):
        self.agent_id = agent_id
        self.rcon_port = base_rcon_port + agent_id
        self.container_name = f"factorio_agent_{self.agent_id}"
        self.save_dir = os.path.abspath(f"./factorio_data/agent_{self.agent_id}/saves")

        # We will initialize these later
        self.container = None
        self.env = None

    def spin_up_container(self):
        """Spins up the Docker container for this specific agent."""
        client = docker.from_env()
        os.makedirs(self.save_dir, exist_ok=True)

        print(f"[Agent {self.agent_id}] Spinning up container on port {self.rcon_port}...")
        self.container = client.containers.run(
            "factoriotools/factorio",  # Make sure this matches your image
            name=self.container_name,
            ports={'27015/tcp': self.rcon_port},
            volumes={self.save_dir: {'bind': '/opt/factorio/saves', 'mode': 'rw'}},
            detach=True,
            remove=True
        )

    def init_environment(self):
        """Initializes the FactorioEnv specifically for this agent's port."""
        cfg = Config()
        # Pass the dynamic port to the environment
        self.env = FactorioEnv(cfg, rcon_port=self.rcon_port)

    def stop(self):
        """Gracefully stops the container."""
        if self.container:
            print(f"[Agent {self.agent_id}] Stopping container...")
            self.container.stop()

    def prepare_map_and_ores(self, map_source_path):
        """Handles independent map loading and ore scanning for this specific agent."""
        # 1. Clean and setup unique save directory
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)
        os.makedirs(self.save_dir, exist_ok=True)

        # Copy map to this agent's specific folder
        map_filename = os.path.basename(map_source_path)
        shutil.copy2(map_source_path, os.path.join(self.save_dir, map_filename))

        # 2. Spin up container and init env (assuming these are updated to use self.save_dir)
        self.spin_up_container()
        self.init_environment()

        # 3. Ore Patch Process (Kept in memory, or saved with agent_id to avoid collisions)
        # Using your existing Rcon_receiver logic tied to this agent's port:
        receiver_ore = Rcon_reciever("localhost", "eenie7Uphohpaim", self.rcon_port)
        receiver_ore.connect()
        raw_ores = receiver_ore.scan_ore()
        receiver_ore.disconnect()

        detector = OrePatchDetector(raw_ores)
        patches = detector.process_patches()

        # Save with unique ID if ActionMasking requires reading from disk
        self.patches_file = f"patches_agent_{self.agent_id}.json"
        with open(self.patches_file, "w") as f:
            patches_serializable = [{k: v for k, v in p.items() if k != 'polygon'} for p in patches]
            json.dump(patches_serializable, f)

        return patches