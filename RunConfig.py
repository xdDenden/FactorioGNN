import os
import json
from dataclasses import dataclass, asdict, fields

CONFIG_FILE = "user_config.json"

@dataclass
class Config:
    # RCON Settings
    # Port is now a base setting since each agent does base port +1
    RCON_HOST: str = "localhost"
    RCON_PORT: int = 27015
    RCON_PASSWORD: str = "eenie7Uphohpaim"

    # RL / Training Settings
    MAX_TIMESTEPS: int = 2000
    Random_Seed: int = 67
    GAMMA: float = 0.99  # Discount factor for future rewards
    LR: float = 1e-4  # Learning rate for the optimizer
    BATCH_SIZE: int = 128  # Number of samples per training batch
    BUFFER_SIZE: int = 5000  # Maximum size of the replay buffer
    EPSILON_START: float = 1.0  # Initial value of epsilon for epsilon-greedy policy
    EPSILON_END: float = 0.05  # Minimum value of epsilon for epsilon-greedy policy
    EPSILON_DECAY: int = 255555  # Decay rate for epsilon over time
    TARGET_UPDATE: int = 200  # Frequency of target network updates (in gradient steps)
    NUM_EPISODES: int = 100  # Total number of episodes to train the model
    NUM_AUTOSAVES: int = 5 # Rolling cache of autosaves
    NUM_WEIGHTAUTOSAVE: int = 5 #Rolling cache of the weights autosaves

    # Distributed / Multiprocessing Settings
    NUM_ACTORS: int = 6
    CHUNK_SIZE: int = 32
    SYNC_INTERVAL: int = 128

    @property
    def MIN_BUFFER_SIZE(self) -> int:
        return self.BATCH_SIZE * 5

    # Model Settings
    HIDDEN_DIM: int = 256
    LSTM_HIDDEN_DIM: int = 256

    # Docker & File Paths
    CONTAINER_NAME: str = "factorio"  # Name of the Factorio Docker container
    SAVE_FOLDER: str = os.path.join(".", "factorio_data", "saves")  # Path to the saves folder on host
    SAVES_POOL: str = "./SAVES_POOL"  # Path to the saves we use to test the AI
    AUTOSAVE_PATH: str = "autosave.pth"
    WEIGHTS_PATH: str = "jimbo_dqn_weights.pth"
    STATE_FILE: str = "dashboard_state.json"

    # Dashboard / UI Settings
    UPDATE_INTERVAL_SEC: float = 5.0  # Update the dashboard JSON every 5 seconds

    # Debugging
    VERBOSE: bool = False  # Set to False to silence per-step prints
    SAVE_GRAPHS: bool = False  # If True, saves GraphML every step (very slow)

    def __post_init__(self):
        """Automatically load saved user parameters on initialization."""
        self.load()

    def load(self, filepath: str = CONFIG_FILE):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                # Build a map of {field_name: field_type} from the dataclass definition
                field_types = {f.name: f.type for f in fields(self)}

                for key, value in data.items():
                    if key in field_types:
                        target_type = field_types[key]
                        if target_type is bool or target_type == "bool":
                            setattr(self, key, bool(value))
                        elif target_type in (int, float, str):
                            setattr(self, key, target_type(value))
                        else:
                            setattr(self, key, value)
            except Exception as e:
                print(f"[RunConfig] Warning: Could not load {filepath}: {e}")

    def save(self, filepath: str = CONFIG_FILE):
        """Save current configuration to JSON for next startup."""
        try:
            with open(filepath, "w") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            print(f"[RunConfig] Error saving config to {filepath}: {e}")