import os
from dataclasses import dataclass


@dataclass
class Config:
    # RCON Settings
    # Port is now a base setting since each agent does base port +1
    RCON_HOST: str = "localhost"
    RCON_PORT: int = 27015
    RCON_PASSWORD: str = "eenie7Uphohpaim"

    # RL / Training Settings
    MAX_TIMESTEPS: int = 20000
    Random_Seed: int = 67
    GAMMA: float = 0.99  # Discount factor for future rewards
    LR: float = 1e-4  # Learning rate for the optimizer
    BATCH_SIZE: int = 128  # Number of samples per training batch
    BUFFER_SIZE: int = 5000  # Maximum size of the replay buffer
    EPSILON_START: float = 1.0  # Initial value of epsilon for epsilon-greedy policy
    EPSILON_END: float = 0.05  # Minimum value of epsilon for epsilon-greedy policy
    EPSILON_DECAY: int = 563698  # Decay rate for epsilon over time
    TARGET_UPDATE: int = 200  # Frequency of target network updates (in gradient steps)
    NUM_EPISODES: int = 50  # Total number of episodes to train the model

    # Distributed / Multiprocessing Settings
    NUM_ACTORS: int = 5
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
    STATE_FILE: str = "dashboard_state.json"

    # Dashboard / UI Settings
    UPDATE_INTERVAL_SEC: float = 5.0  # Update the dashboard JSON every 5 seconds

    # Debugging
    VERBOSE: bool = False  # Set to False to silence per-step prints
    SAVE_GRAPHS: bool = False  # If True, saves GraphML every step (very slow)