import json
import os
import shutil
import time
import docker
from OrePatchDetector import OrePatchDetector
from environment import FactorioEnv
from RunConfig import Config
from rcon_bridge.rcon_bridge import Rcon_reciever


class ActorWorker:
    def __init__(self, agent_id, base_rcon_port=27015):
        self.agent_id = agent_id
        self.rcon_port = base_rcon_port + agent_id
        self.container_name = f"factorio_agent_{self.agent_id}"
        self.save_dir = os.path.abspath(f"./factorio_data/agent_{self.agent_id}/saves")

        # 1. Expand the directory structure
        self.base_dir = os.path.abspath(f"./factorio_data/agent_{self.agent_id}")
        self.save_dir = os.path.join(self.base_dir, "saves")
        self.config_dir = os.path.join(self.base_dir, "config")

        self.container = None
        self.env = None

    def spin_up_container(self):
        """Spins up the Docker container for this specific agent."""
        client = docker.from_env()

        # 2. Ensure directories exist
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # INJECT THE MOD INTO THE AGENT'S FOLDER
        agent_mods_dir = os.path.join(self.base_dir, "mods")
        os.makedirs(agent_mods_dir, exist_ok=True)

        source_mod_dir = os.path.abspath("./rcon_bridge")
        target_mod_dir = os.path.join(agent_mods_dir, "rcon_bridge")

        # Copy the mod into this specific agent's isolated mods folder
        if os.path.exists(target_mod_dir):
            shutil.rmtree(target_mod_dir)  # Refresh it in case you made script changes
        shutil.copytree(source_mod_dir, target_mod_dir)

        # 3. Inject the RCON password BEFORE the container boots
        rconpw_path = os.path.join(self.config_dir, "rconpw")
        with open(rconpw_path, "w") as f:
            f.write("eenie7Uphohpaim")

        # Aggressive Cleanup
        try:
            old_container = client.containers.get(self.container_name)
            print(f"[Agent {self.agent_id}] Found stuck container. Removing it...")
            old_container.stop()
            old_container.remove()
        except docker.errors.NotFound:
            pass
        except Exception as e:
            print(f"[Agent {self.agent_id}] Cleanup warning: {e}")

        # 4. START NEW CONTAINER
        print(f"[Agent {self.agent_id}] Spinning up container on port {self.rcon_port}...")
        self.container = client.containers.run(
            "factoriotools/factorio",
            name=self.container_name,
            ports={'27015/tcp': self.rcon_port},
            volumes={self.base_dir: {'bind': '/factorio', 'mode': 'rw'}},
            detach=True,
            remove=False
            #TODO:should be set to true once working
        )

        print(f"[Agent {self.agent_id}] Waiting for Factorio server to boot...")
        time.sleep(10)

        # 5. SMART POLLING LOOP
        import rcon_bridge.rcon_bridge as bridge

        max_retries = 60
        server_ready = False
        last_error = ""

        for attempt in range(max_retries):
            # Check if container actually died before even trying RCON
            self.container.reload()
            if self.container.status == 'exited':
                last_error = "Container crashed/exited prematurely."
                break  # Break out of the polling loop completely

            time.sleep(2)
            test_receiver = None

            try:
                test_receiver = bridge.Rcon_reciever("localhost", "eenie7Uphohpaim", self.rcon_port)
                test_receiver.connect()

                # Bypass the JSON parser temporarily to see what Factorio is ACTUALLY saying
                test_receiver.reset()
                time.sleep(5)
                raw_response = test_receiver._send_command_with_retry("/char_info")

                # CASE 1: Mod not ready yet (NOT a crash)
                if not raw_response or raw_response.strip() == "":
                    last_error = "RCON alive but game still initializing"
                    continue

                # CASE 2: Mod not loaded yet (also NOT a crash)
                if "Unknown command" in raw_response:
                    last_error = "Mod not ready yet"
                    continue

                # CASE 3: Try JSON validation only if it actually looks valid
                try:
                    json.loads(raw_response)
                except json.JSONDecodeError:
                    last_error = f"Non-JSON response (still booting): {raw_response[:100]}"
                    continue

                # SUCCESS
                server_ready = True
                print(f"[Agent {self.agent_id}] Server is ONLINE and responding.")
                test_receiver.reset()
                break

            except Exception as e:
                # Catching general exceptions here (like connection refused) as normal booting behavior
                last_error = f"RCON connection failed (still booting): {str(e)}"
            finally:
                # Safely disconnect only if test_receiver was instantiated
                if test_receiver:
                    try:
                        test_receiver.disconnect()
                    except Exception:
                        pass

        # FINALLY evaluate if the server failed AFTER the loop concludes
        if not server_ready:
            print(f"\n--- CONTAINER CRASH LOGS FOR AGENT {self.agent_id} ---")
            try:
                print(self.container.logs().decode('utf-8'))
            except Exception as log_e:
                print(f"Could not fetch logs: {log_e}")
            print("------------------------------------------\n")

            raise Exception(f"Container {self.container_name} failed to boot. Last error: {last_error}")

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

        receiver_ore.reset()
        time.sleep(10)
        receiver_ore.disconnect()

        detector = OrePatchDetector(raw_ores)
        patches = detector.process_patches()

        # Save with unique ID if ActionMasking requires reading from disk
        self.patches_file = f"patches_agent_{self.agent_id}.json"
        with open(self.patches_file, "w") as f:
            patches_serializable = [{k: v for k, v in p.items() if k != 'polygon'} for p in patches]
            json.dump(patches_serializable, f)

        return patches