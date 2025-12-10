# config.py
from dataclasses import dataclass


@dataclass
class Config:
    # RCON Settings
    RCON_HOST: str = "localhost"
    RCON_PORT: int = 27015
    RCON_PASSWORD: str = "eenie7Uphohpaim"

    # --- BATCH & BURST SETTINGS ---
    COLLECTION_STEPS: int = 128  # Play this many steps (~2 seconds at 60fps)
    TRAIN_EPOCHS: int = 32  # Then train this many times back-to-back
    
    # RL / Training Settings
    MAX_TIMESTEPS: int = 10000
    Random_Seed: int = 42

    # Model Settings
    HIDDEN_DIM: int = 256
    LSTM_HIDDEN_DIM: int = 256

    # Debugging
    VERBOSE: bool = False  # Set to False to silence per-step prints
    SAVE_GRAPHS: bool = False  # If True, saves GraphML every step (slow)