import streamlit as st
import pandas as pd
import json
import time
import os
import sys
import datetime
import glob
import subprocess
import signal
import urllib.request
import docker
from pathlib import Path
from RunConfig import Config

st.set_page_config(page_title="Factorio AI Dashboard", layout="wide")

CSV_FILE = "training_log.csv"
TRAIN_PID_FILE = ".train.pid"
PLAY_PID_FILE = ".play.pid"
STOP_TRAIN_FILE = ".stop_train"
STOP_PLAY_FILE = ".stop_play"

# --- SESSION STATE INITIALIZATION ---
if "ngrok_proc" not in st.session_state:
    st.session_state.ngrok_proc = None
if "ngrok_url" not in st.session_state:
    st.session_state.ngrok_url = None


# --- HELPER FUNCTIONS ---
def is_docker_running() -> bool:
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False

def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def is_pid_running(pid_file: str):
    """Checks if a PID stored in pid_file is currently alive across OSs."""
    if not os.path.exists(pid_file):
        return False, None
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        if sys.platform.startswith("win"):
            out = subprocess.check_output(
                ["tasklist", "/FI", f"PID eq {pid}"],
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode(errors="ignore")
            if str(pid) in out:
                return True, pid
        else:
            os.kill(pid, 0)  # Doesn't kill; just checks if process exists
            return True, pid
    except Exception:
        pass

    # Process is dead; clean up stale PID file
    try:
        os.remove(pid_file)
    except OSError:
        pass
    return False, None


def start_background_process(cmd, pid_file: str, stop_file: str):
    """Starts process in its own process group so we can signal the whole tree if needed."""
    if os.path.exists(stop_file):
        try:
            os.remove(stop_file)
        except OSError:
            pass

    kwargs = {}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True  # Creates a new process group (pgid == pid)

    proc = subprocess.Popen(cmd, **kwargs)
    with open(pid_file, "w") as f:
        f.write(str(proc.pid))
    return proc.pid


def stop_background_process(pid_file: str, stop_file: str, cleanup_containers_prefix: str = None):
    """
    1. Writes cooperative stop file (.stop_train / .stop_play) so Python loops exit cleanly.
    2. Waits up to 10s for graceful shutdown.
    3. Force-kills the entire OS process tree if stuck (e.g. mid-Docker boot).
    4. Sweeps any leftover Docker containers matching prefix.
    """
    # 1. Trigger cooperative stop file
    with open(stop_file, "w") as f:
        f.write("stop")

    running, pid = is_pid_running(pid_file)
    if running and pid:
        # Wait up to 10 seconds for graceful loop exit
        for _ in range(20):
            time.sleep(0.5)
            still_alive, _ = is_pid_running(pid_file)
            if not still_alive:
                break

        # 2. If still alive (e.g. stuck inside spin_up_container sleep), kill the whole process tree
        still_alive, _ = is_pid_running(pid_file)
        if still_alive:
            try:
                if sys.platform.startswith("win"):
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    time.sleep(1.0)
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
            except Exception:
                pass

    # Clean up files
    for fpath in (pid_file, stop_file):
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except OSError:
                pass

    # 3. Guarantee Docker container cleanup even if an actor was hard-killed mid-boot
    if cleanup_containers_prefix:
        try:
            client = docker.from_env()
            for container in client.containers.list(all=True):
                if container.name.startswith(cleanup_containers_prefix):
                    try:
                        container.stop(timeout=2)
                        container.remove(force=True)
                    except Exception:
                        pass
        except Exception:
            pass


def get_launch_cmd(mode: str, extra_args=None):
    """
    Constructs the proper command whether running from source (python)
    or as a compiled PyInstaller executable (sys.frozen).
    """
    extra_args = extra_args or []
    if getattr(sys, "frozen", False):
        # Running inside PyInstaller bundle -> call our own executable with --mode flag
        return [sys.executable, "--mode", mode] + extra_args
    else:
        # Running from normal Python environment
        if os.path.exists("launcher.py"):
            return [sys.executable, "launcher.py", "--mode", mode] + extra_args
        elif mode == "train":
            return [sys.executable, "train_dqn.py"] + extra_args
        elif mode == "play":
            return [sys.executable, "PlayFactorioWithWeights.py"] + extra_args


def fetch_ngrok_public_url():
    """Queries the local ngrok agent API (port 4040) for the active public URL."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as response:
            data = json.loads(response.read().decode())
            tunnels = data.get("tunnels", [])
            if tunnels:
                return tunnels[0].get("public_url")
    except Exception:
        return None
    return None


# Load current config
cfg = Config()
docker_ok = is_docker_running()

if not docker_ok:
    st.error(
        "**Docker is not running or cannot be reached!** "
        "Please start Docker Desktop (Windows/macOS) or the `docker` service (Linux) "
        "before launching training or inference.",
    )
# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("Control Center")

    # --- 1. TRAINING CONTROL ---
    st.subheader("1. DQN Training (`train_dqn`)")
    train_running, train_pid = is_pid_running(TRAIN_PID_FILE)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("▶️ Start Train", disabled=(train_running or not docker_ok), width="stretch", type="primary"):
            cmd = get_launch_cmd("train")
            pid = start_background_process(cmd, TRAIN_PID_FILE, STOP_TRAIN_FILE)
            st.toast(f"Started train_dqn (PID {pid})!", icon="🚀")
            st.rerun()
    with col_t2:
        if st.button("⏹️ Stop Train", disabled=(not train_running), width="stretch"):
            with st.spinner("Stopping actors and cleaning up Factorio containers..."):
                stop_background_process(TRAIN_PID_FILE, STOP_TRAIN_FILE, cleanup_containers_prefix="factorio_actor_")
            st.toast("Stopped train_dqn and cleaned up containers.", icon="🛑")
            st.rerun()

    if train_running:
        st.success(f"🟢 Training Active (PID: {train_pid})")
    else:
        st.caption("⚪ Training Idle")

    st.divider()

    # --- 2. PLAY WITH WEIGHTS CONTROL ---
    st.subheader("2. Inference (`PlayFactorio`)")
    play_running, play_pid = is_pid_running(PLAY_PID_FILE)

    # Allow browsing via file dialog OR selecting an existing .pth file in the directory
    uploaded_weights = st.file_uploader("Upload / Select Weights (.pth)", type=["pth"], disabled=play_running)
    local_pth_files = sorted(glob.glob("*.pth"))
    selected_local_pth = st.selectbox(
        "Or choose existing local `.pth`:",
        options=["(Use Uploaded File)"] + local_pth_files,
        index=1 if cfg.WEIGHTS_PATH in local_pth_files else 0,
        disabled=play_running
    )

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Play Factorio", disabled=play_running, width="stretch", type="primary"):
            target_weights_path = None

            if uploaded_weights is not None:
                # Save the file chosen via File Dialog into a local runtime path
                os.makedirs("uploaded_weights", exist_ok=True)
                target_weights_path = os.path.abspath(os.path.join("uploaded_weights", uploaded_weights.name))
                with open(target_weights_path, "wb") as f:
                    f.write(uploaded_weights.getbuffer())
            elif selected_local_pth != "(Use Uploaded File)":
                target_weights_path = os.path.abspath(selected_local_pth)

            if not target_weights_path or not os.path.exists(target_weights_path):
                st.error("Please select or upload a valid `.pth` weights file first!")
            else:
                cmd = get_launch_cmd("play", ["--weights", target_weights_path])
                pid = start_background_process(cmd, PLAY_PID_FILE, STOP_PLAY_FILE)
                st.toast(f"Launched Factorio (PID {pid})!", icon="🎮")
                st.rerun()

    with col_p2:
        if st.button("⏹️ Stop Play", disabled=not play_running, width="stretch"):
            with st.spinner("Stopping Actor 99 container..."):
                stop_background_process(PLAY_PID_FILE, STOP_PLAY_FILE, cleanup_containers_prefix="factorio_actor_99")
            st.toast("Stopped Play session.", icon="🛑")
            st.rerun()

    if play_running:
        st.success(f"🟢 Inference Active (PID: {play_pid})")
    else:
        st.caption("⚪ Inference Idle")

    st.divider()

    # --- 3. NGROK REMOTE TUNNEL ---
    st.subheader("3. Remote Observation (`ngrok`)")
    ngrok_proc = st.session_state.ngrok_proc
    ngrok_running = ngrok_proc is not None and ngrok_proc.poll() is None
    existing_tunnel = fetch_ngrok_public_url()

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        if st.button("Launch Ngrok", disabled=(ngrok_running or existing_tunnel is not None), width="stretch"):
            try:
                st.session_state.ngrok_proc = subprocess.Popen(
                    ["ngrok", "http", "8501"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(2.0)  # Give ngrok a moment to establish the tunnel
                st.session_state.ngrok_url = fetch_ngrok_public_url()
                st.rerun()
            except FileNotFoundError:
                st.error("`ngrok` executable not found in PATH! Please install ngrok.")
    with col_n2:
        if st.button("Stop Ngrok", disabled=not (ngrok_running or existing_tunnel is not None), width="stretch"):
            if st.session_state.ngrok_proc:
                st.session_state.ngrok_proc.terminate()
                st.session_state.ngrok_proc = None
            st.session_state.ngrok_url = None
            st.rerun()

    active_url = existing_tunnel or st.session_state.ngrok_url
    if active_url:
        st.success("🟢 Tunnel Online:")
        st.code(active_url, language=None)
    elif ngrok_running:
        st.info("⏳ Starting Ngrok tunnel... (Refresh in a moment)")
    else:
        st.caption("⚪ Ngrok Offline (Port 8501)")

    st.divider()
    auto_refresh = st.toggle("🔄 Auto-Refresh Telemetry", value=True)


# ==========================================
# MAIN PAGE: CONFIGURATION & LIVE TELEMETRY
# ==========================================
st.title("Factorio AI Dashboard & Launcher")

main_tabs = st.tabs(["Live Telemetry", "Startup Parameters (`RunConfig`)"])

# ------------------------------------------
# TAB 1: RUNCONFIG PARAMETER EDITOR
# ------------------------------------------
with main_tabs[1]:
    st.header("Startup Parameters (`RunConfig`)")
    st.caption("Modify parameters below and click **Save Parameters**. Saved settings persist across restarts in `user_config.json`.")

    with st.form("runconfig_form"):
        c_rcon, c_rl1, c_rl2 = st.columns(3)

        with c_rcon:
            st.subheader("RCON & Distributed")
            rcon_host = st.text_input("RCON_HOST", value=cfg.RCON_HOST)
            rcon_port = st.number_input("RCON_PORT (Base)", value=int(cfg.RCON_PORT), step=1)
            rcon_pw = st.text_input("RCON_PASSWORD", value=cfg.RCON_PASSWORD, type="password")
            num_actors = st.number_input("NUM_ACTORS", min_value=1, max_value=64, value=int(cfg.NUM_ACTORS), step=1)
            chunk_size = st.number_input("CHUNK_SIZE", min_value=1, value=int(cfg.CHUNK_SIZE), step=1)
            sync_interval = st.number_input("SYNC_INTERVAL", min_value=1, value=int(cfg.SYNC_INTERVAL), step=1)

        with c_rl1:
            st.subheader("RL Hyperparameters")
            max_timesteps = st.number_input("MAX_TIMESTEPS", min_value=10, value=int(cfg.MAX_TIMESTEPS), step=100)
            num_episodes = st.number_input("NUM_EPISODES (Per Actor)", min_value=1, value=int(cfg.NUM_EPISODES), step=1)
            gamma = st.number_input("GAMMA", min_value=0.0, max_value=1.0, value=float(cfg.GAMMA), format="%.4f")
            lr = st.number_input("LR (Learning Rate)", min_value=1e-7, max_value=1.0, value=float(cfg.LR), format="%.6f")
            batch_size = st.number_input("BATCH_SIZE", min_value=1, value=int(cfg.BATCH_SIZE), step=8)
            buffer_size = st.number_input("BUFFER_SIZE", min_value=100, value=int(cfg.BUFFER_SIZE), step=1000)
            random_seed = st.number_input("Random_Seed", value=int(cfg.Random_Seed), step=1)

        with c_rl2:
            st.subheader("Exploration & Checkpoints")
            eps_start = st.number_input("EPSILON_START", min_value=0.0, max_value=1.0, value=float(cfg.EPSILON_START), format="%.3f")
            eps_end = st.number_input("EPSILON_END", min_value=0.0, max_value=1.0, value=float(cfg.EPSILON_END), format="%.3f")
            eps_decay = st.number_input("EPSILON_DECAY", min_value=1, value=int(cfg.EPSILON_DECAY), step=1000)
            target_update = st.number_input("TARGET_UPDATE", min_value=1, value=int(cfg.TARGET_UPDATE), step=10)
            num_autosaves = st.number_input("NUM_AUTOSAVES", min_value=1, value=int(cfg.NUM_AUTOSAVES), step=1)
            num_weightautosave = st.number_input("NUM_WEIGHTAUTOSAVE", min_value=1, value=int(cfg.NUM_WEIGHTAUTOSAVE), step=1)

        st.divider()
        c_model, c_paths, c_debug = st.columns(3)

        with c_model:
            st.subheader("Model Architecture")
            hidden_dim = st.number_input("HIDDEN_DIM", min_value=16, value=int(cfg.HIDDEN_DIM), step=16)
            lstm_hidden_dim = st.number_input("LSTM_HIDDEN_DIM", min_value=16, value=int(cfg.LSTM_HIDDEN_DIM), step=16)

        with c_paths:
            st.subheader("Docker & Paths")
            container_name = st.text_input("CONTAINER_NAME", value=cfg.CONTAINER_NAME)
            save_folder = st.text_input("SAVE_FOLDER", value=cfg.SAVE_FOLDER)
            saves_pool = st.text_input("SAVES_POOL", value=cfg.SAVES_POOL)
            autosave_path = st.text_input("AUTOSAVE_PATH", value=cfg.AUTOSAVE_PATH)
            weights_path = st.text_input("WEIGHTS_PATH", value=getattr(cfg, "WEIGHTS_PATH", "jimbo_dqn_weights.pth"))
            state_file = st.text_input("STATE_FILE", value=cfg.STATE_FILE)

        with c_debug:
            st.subheader("UI & Debugging")
            update_interval = st.number_input("UPDATE_INTERVAL_SEC", min_value=1.0, value=float(cfg.UPDATE_INTERVAL_SEC), step=0.5)
            verbose = st.checkbox("VERBOSE (Keep crashed containers & print steps)", value=bool(cfg.VERBOSE))
            save_graphs = st.checkbox("SAVE_GRAPHS (Export GraphML every step)", value=bool(cfg.SAVE_GRAPHS))

        submitted = st.form_submit_button("Save Parameters for Current & Next Startup", width="stretch", type="primary")
        if submitted:
            cfg.RCON_HOST = rcon_host
            cfg.RCON_PORT = int(rcon_port)
            cfg.RCON_PASSWORD = rcon_pw
            cfg.NUM_ACTORS = int(num_actors)
            cfg.CHUNK_SIZE = int(chunk_size)
            cfg.SYNC_INTERVAL = int(sync_interval)
            cfg.MAX_TIMESTEPS = int(max_timesteps)
            cfg.NUM_EPISODES = int(num_episodes)
            cfg.GAMMA = float(gamma)
            cfg.LR = float(lr)
            cfg.BATCH_SIZE = int(batch_size)
            cfg.BUFFER_SIZE = int(buffer_size)
            cfg.Random_Seed = int(random_seed)
            cfg.EPSILON_START = float(eps_start)
            cfg.EPSILON_END = float(eps_end)
            cfg.EPSILON_DECAY = int(eps_decay)
            cfg.TARGET_UPDATE = int(target_update)
            cfg.NUM_AUTOSAVES = int(num_autosaves)
            cfg.NUM_WEIGHTAUTOSAVE = int(num_weightautosave)
            cfg.HIDDEN_DIM = int(hidden_dim)
            cfg.LSTM_HIDDEN_DIM = int(lstm_hidden_dim)
            cfg.CONTAINER_NAME = container_name
            cfg.SAVE_FOLDER = save_folder
            cfg.SAVES_POOL = saves_pool
            cfg.AUTOSAVE_PATH = autosave_path
            cfg.WEIGHTS_PATH = weights_path
            cfg.STATE_FILE = state_file
            cfg.UPDATE_INTERVAL_SEC = float(update_interval)
            cfg.VERBOSE = bool(verbose)
            cfg.SAVE_GRAPHS = bool(save_graphs)

            cfg.save()
            st.success("✅ Parameters saved to `user_config.json`! Any newly started training or play session will use these settings.")


# ------------------------------------------
# TAB 0: LIVE TELEMETRY (Non-blocking Fragment)
# ------------------------------------------
refresh_interval = cfg.UPDATE_INTERVAL_SEC if auto_refresh else None

@st.fragment(run_every=refresh_interval)
def render_live_telemetry():
    state = load_json(cfg.STATE_FILE) or {}

    num_actors = state.get("num_actors", 0)
    if num_actors == 0:
        actor_files = glob.glob("actor_*_state.json")
        num_actors = len(actor_files)

    hparams = state.get("hyperparameters", {}) if state else {}
    max_timesteps = hparams.get("MAX_TIMESTEPS", cfg.MAX_TIMESTEPS)
    episodes_per_actor = hparams.get("NUM_EPISODES", cfg.NUM_EPISODES)

    total_episodes = episodes_per_actor * num_actors
    episodes_done = 0
    progress_units = 0.0
    for i in range(num_actors):
        a = load_json(f"actor_{i}_state.json") or {}
        completed = min(a.get("episodes_completed", 0), episodes_per_actor)
        episodes_done += completed
        progress_units += completed
        if completed < episodes_per_actor:
            progress_units += max(0.0, min(a.get("step", 0) / max_timesteps, 1.0))
    overall_fraction = progress_units / total_episodes if total_episodes > 0 else 0.0

    if state or num_actors > 0:
        tab_names = ["Overall Progress"] + [f"actor {i}" for i in range(num_actors)]
        tabs = st.tabs(tab_names)

        with tabs[0]:
            if total_episodes > 0:
                st.header("Total Completion")
                elapsed_total = state.get("elapsed_total", 0) if state else 0

                st.progress(
                    min(overall_fraction, 1.0),
                    text=f"{episodes_done} / {total_episodes} episodes completed "
                         f"({overall_fraction * 100:.1f}%) across {num_actors} actors"
                )

                e1, e2, e3 = st.columns(3)
                if overall_fraction >= 1.0:
                    e1.metric("ETA", "Complete")
                elif overall_fraction > 0.01 and elapsed_total > 0:
                    remaining = elapsed_total * (1 - overall_fraction) / overall_fraction
                    finish_at = datetime.datetime.now() + datetime.timedelta(seconds=remaining)
                    e1.metric("ETA (Time Remaining)", format_time(remaining))
                    e2.metric("Estimated Finish", finish_at.strftime("%a %H:%M"))
                else:
                    e1.metric("ETA (Time Remaining)", "Calculating...",
                              help="Needs ~1% of total progress before an estimate is meaningful.")
                e3.metric("Episodes Per Actor", f"{episodes_per_actor}")
                st.divider()

            if state:
                st.header("Learner Status")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Total Steps Ingested", f"{state.get('steps_ingested', 0):,}")
                c2.metric("Network Updates Done", f"{state.get('updates_done', 0):,}")
                c3.metric("Replay Buffer", f"{state.get('buffer_size', 0):,}")

                raw_qsize = state.get('queue_size', 0)
                display_qsize = f"{raw_qsize:,}" if isinstance(raw_qsize, (int, float)) else str(raw_qsize)
                c4.metric("MP Queue Size", display_qsize)
                c5.metric("Current Loss", state.get("current_loss", 0.0))

                st.subheader("Performance")
                t1, t2, t3 = st.columns(3)
                t1.metric("Iterations / Sec (Learner GPU)", state.get("updates_per_sec", 0))
                t2.metric("Elapsed (Total)", format_time(state.get("elapsed_total", 0)))
                queue_health = "Healthy" if state.get('updates_per_sec', 0) > 0 else "Stalled"
                t3.metric("Training Status", queue_health)

                st.divider()
                st.subheader("Bottleneck Analysis (System Flow)")
                b1, b2, b3 = st.columns(3)
                ingest_rate = state.get("ingestion_rate", 0)
                train_rate = state.get("training_rate", 0)
                utd = state.get("utd_ratio", 0)

                b1.metric("Actor Ingestion Rate", f"{ingest_rate} steps/sec")
                b2.metric("GPU Training Rate", f"{train_rate} samples/sec")

                safe_qsize_for_math = raw_qsize if isinstance(raw_qsize, (int, float)) else 0
                if utd > 8:
                    bottleneck = "🔴 Actor Limited (GPU Starving)"
                elif safe_qsize_for_math > 100:
                    bottleneck = "🔴 Learner Limited (CPU Waiting)"
                else:
                    bottleneck = "🟢 Balanced Pipeline"

                b3.metric("Update To Data (UTD) Ratio", f"{utd}x", delta=bottleneck, delta_color="off")
                st.divider()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Architecture")
                    st.info("Actors stream chunks of steps to Host RAM queue.\n\nLearner unrolls chunks, batches, trains on GPU, and pushes weights back to CPU.")
                with col2:
                    st.subheader("Active Hyperparameters")
                    with st.expander("View Config Variables"):
                        st.json(state.get("hyperparameters", {}))
            else:
                st.warning("Waiting for live data from the Learner...")

            st.divider()
            st.header("Historical Training Log")
            if os.path.exists(CSV_FILE):
                try:
                    df = pd.read_csv(CSV_FILE)
                    st.dataframe(df.tail(10), width="stretch")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        st.line_chart(df, x="step_count" if 'step_count' in df.columns else None, y="reward")
                    with chart_col2:
                        st.line_chart(df, x="step_count" if 'step_count' in df.columns else None, y="avg_loss")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
            else:
                st.info("No training CSV found yet.")

        for i in range(num_actors):
            with tabs[i + 1]:
                actor_state = load_json(f"actor_{i}_state.json")
                if actor_state:
                    st.header(f"Live Feed: actor {i}")
                    ac1, ac2, ac3, ac4 = st.columns(4)
                    ac1.metric("Current Map", actor_state.get("current_map", "Unknown"))
                    ac2.metric("Epsilon (Exploration)", f"{actor_state.get('epsilon', 0.0):.4f}")
                    ac3.metric("Total Actor Steps", f"{actor_state.get('total_actor_steps', 0):,}")
                    ac4.metric("Iterations / Sec", actor_state.get("steps_per_sec", 0.0))

                    current_step = actor_state.get("step", 0)
                    ep1, ep2 = st.columns(2)
                    ep1.metric("Episode", f"{min(actor_state.get('episode', 1), episodes_per_actor)} / {episodes_per_actor}")
                    ep2.metric("Current Episode Reward", round(actor_state.get("episode_reward", 0.0), 3))

                    progress_val = max(0.0, min(current_step / max_timesteps, 1.0))
                    st.progress(progress_val, text=f"Episode Progress (Step {current_step} / {max_timesteps})")

                    reward_breakdown = actor_state.get("reward_breakdown")
                    if reward_breakdown:
                        st.divider()
                        st.subheader("Reward Breakdown (Current Episode)")
                        breakdown_df = pd.DataFrame(reward_breakdown).T
                        breakdown_df.index = breakdown_df.index.str.replace("_", " ").str.title()
                        breakdown_df.columns = ["Total Reward", "Trigger Count"]
                        rb_col1, rb_col2 = st.columns(2)
                        with rb_col1:
                            st.dataframe(breakdown_df, width='content')
                        with rb_col2:
                            st.bar_chart(breakdown_df["Total Reward"])
                else:
                    st.info(f"Waiting for actor {i} to start exploring and report in...")
    else:
        st.info("No active telemetry files found yet. Configure your parameters in the **Startup Parameters** tab or click **▶️ Start Train** in the sidebar.")

with main_tabs[0]:
    render_live_telemetry()