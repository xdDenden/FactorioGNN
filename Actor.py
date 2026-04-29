import RunConfig
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
    def __init__(self, actor_id, base_rcon_port=27015, base_game_port=34197):
        self.actor_id = actor_id
        self.rcon_port = base_rcon_port + actor_id
        self.container_name = f"factorio_actor_{self.actor_id}"
        self.save_dir = os.path.abspath(f"./factorio_data/actor_{self.actor_id}/saves")
        self.game_port = base_game_port + actor_id

        # 1. Expand the directory structure
        self.base_dir = os.path.abspath(f"./factorio_data/actor_{self.actor_id}")
        self.save_dir = os.path.join(self.base_dir, "saves")
        self.config_dir = os.path.join(self.base_dir, "config")

        self.container = None
        self.env = None

    def spin_up_container(self):
        """Spins up the Docker container for this specific actor."""
        client = docker.from_env()

        # 2. Verzeichnisse sicherstellen
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        # MOD INJEKTION
        actor_mods_dir = os.path.join(self.base_dir, "mods")
        os.makedirs(actor_mods_dir, exist_ok=True)

        # Liste der Mods, die kopiert werden sollen
        # (Ordnername im Hauptverzeichnis : Name im Actor-Mod-Ordner)
        mods_to_inject = {
            "rcon_bridge": "rcon_bridge",
            "replay_mod_1.0.0": "replay_mod_1.0.0"
        }

        for source_name, target_name in mods_to_inject.items():
            source_path = os.path.abspath(f"./{source_name}")
            target_path = os.path.join(actor_mods_dir, target_name)

            if os.path.exists(source_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
                print(f"[actor {self.actor_id}] Mod injiziert: {target_name}")
            else:
                print(f"[actor {self.actor_id}] WARNUNG: Mod-Quelle nicht gefunden: {source_path}")

        # 3. Inject the RCON password BEFORE the container boots
        rconpw_path = os.path.join(self.config_dir, "rconpw")
        with open(rconpw_path, "w") as f:
            f.write("eenie7Uphohpaim")

            # Aggressive Cleanup
            try:
                old_container = client.containers.get(self.container_name)
                print(f"[actor {self.actor_id}] Found stuck container. Stopping it...")
                old_container.stop()
                old_container.remove(force=True)
            except docker.errors.NotFound:
                pass
            except docker.errors.APIError as e:
                # If Docker is already removing it automatically, just let it happen quietly
                if e.response.status_code == 409 and "already in progress" in str(e):
                    pass
                else:
                    print(f"[actor {self.actor_id}] Cleanup warning: {e}")

            # Give the port and name 3 seconds to fully release
            time.sleep(3)

        # 4. START NEW CONTAINER
        print(f"[actor {self.actor_id}] Spinning up container on port {self.rcon_port}...")

        cfg = Config()
        # makes sure we can inspect the docker logs if we want to by not instantly deleting
        # the containers if a crash or exit does occur
        # by default it should remove all of them
        if cfg.VERBOSE == True:
            self.container = client.containers.run(
                "factoriotools/factorio:2.0.72",
                name=self.container_name,
                ports={
                    '27015/tcp': self.rcon_port,
                    '34197/udp': self.game_port  # <--- Add this line!
                },
                volumes={self.base_dir: {'bind': '/factorio', 'mode': 'rw'}},
                detach=True,
                remove=False
            )
        else:
            self.container = client.containers.run(
                "factoriotools/factorio:2.0.72",
                name=self.container_name,
                ports={
                    '27015/tcp': self.rcon_port,
                    '34197/udp': self.game_port  # <--- Add this line!
                },
                volumes={self.base_dir: {'bind': '/factorio', 'mode': 'rw'}},
                detach=True,
                remove=True
            )

        print(f"[actor {self.actor_id}] Waiting for Factorio server to boot...")
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
                print(f"[actor {self.actor_id}] Server is ONLINE and responding.")
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
            print(f"\n--- CONTAINER CRASH LOGS FOR actor {self.actor_id} ---")
            try:
                print(self.container.logs().decode('utf-8'))
            except Exception as log_e:
                print(f"Could not fetch logs: {log_e}")
            print("------------------------------------------\n")

            raise Exception(f"Container {self.container_name} failed to boot. Last error: {last_error}")

    def init_environment(self):
        """Initializes the FactorioEnv specifically for this actor's port."""
        cfg = Config()
        # Pass the dynamic port to the environment
        self.env = FactorioEnv(cfg, rcon_port=self.rcon_port)
        self.env.actor_id = self.actor_id

    def stop(self):
        """Gracefully stops and explicitly removes the container."""
        # Safely get the ID in case it was missing or renamed
        a_id = getattr(self, 'agent_id', 'Unknown')

        # Safely check if the container attribute actually exists and holds a container
        if hasattr(self, 'container') and self.container is not None:
            print(f"[Agent {a_id}] Halting and deleting container...")
            try:
                self.container.stop()
                self.container.remove(force=True)
                print(f"[Agent {a_id}] Container successfully deleted.")
            except Exception as e:
                print(f"[Agent {a_id}] Error during container deletion: {e}")
        else:
            print(f"[Agent {a_id}] No container found to delete. Shutting down.")
    def prepare_map_and_ores(self, map_source_path):
        """Handles independent map loading and actor environment setup."""
        # 1. Clean and setup unique save directory
        if os.path.exists(self.save_dir):
            shutil.rmtree(self.save_dir)
        os.makedirs(self.save_dir, exist_ok=True)

        # Copy map to this actor's specific folder
        map_filename = os.path.basename(map_source_path)
        shutil.copy2(map_source_path, os.path.join(self.save_dir, map_filename))

        # 2. Spin up container and init env
        self.spin_up_container()
        self.init_environment()

        # We return an empty list because train_dqn.py overwrites this
        # variable immediately with actor.env.current_patches anyway!
        return []