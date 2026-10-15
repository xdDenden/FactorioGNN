import streamlit as st
import pandas as pd
import json
import time
import os
import datetime
import glob

# Configuration
UPDATE_INTERVAL_SEC = 5
CSV_FILE = "training_log.csv"
STATE_FILE = "dashboard_state.json"

st.set_page_config(page_title="Factorio AI Dashboard", layout="wide")


def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


placeholder = st.empty()

while True:
    with placeholder.container():
        st.title("Factorio AI Dashboard")

        # 1. Load Global Learner State
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            except json.JSONDecodeError:
                pass

        # Determine number of actors dynamically (fallback to counting files if learner hasn't posted yet)
        num_actors = state.get("num_actors", 0)
        if num_actors == 0:
            actor_files = glob.glob("actor_*_state.json")
            num_actors = len(actor_files)

        # Shared values used by both the overview and the per-actor tabs
        hparams = state.get("hyperparameters", {}) if state else {}
        max_timesteps = hparams.get("MAX_TIMESTEPS", 1000)
        episodes_per_actor = hparams.get("NUM_EPISODES", 50)

        # Overall episode progress across all actors (partial credit for the episode in flight)
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
            # 2. Create Dynamic Tabs
            tab_names = ["Overall Progress"] + [f"actor {i}" for i in range(num_actors)]
            tabs = st.tabs(tab_names)


            # TAB 0: OVERALL PROGRESS (Learner)

            with tabs[0]:
                # TOTAL COMPLETION BAR + ETA
                if total_episodes > 0:
                    st.header("Total Completion")
                    elapsed_total = state.get("elapsed_total", 0) if state else 0

                    st.progress(min(overall_fraction, 1.0),
                                text=f"{episodes_done} / {total_episodes} episodes completed "
                                     f"({overall_fraction * 100:.1f}%) across {num_actors} actors")

                    e1, e2, e3 = st.columns(3)
                    if overall_fraction >= 1.0:
                        e1.metric("ETA", "Complete")
                    elif overall_fraction > 0.01 and elapsed_total > 0:
                        # Linear extrapolation of the average pace so far
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
                    c2.metric("Network Updates Done", f"{state.get('updates_done', 0):,}",
                              help="The total number of times the Learner has performed a training update on the GPU.")
                    c3.metric("Replay Buffer", f"{state.get('buffer_size', 0):,}",
                              help="The amount of steps inside the replay buffer ready for training.")

                    # Only use the safe string-formatting
                    raw_qsize = state.get('queue_size', 0)
                    display_qsize = f"{raw_qsize:,}" if isinstance(raw_qsize, (int, float)) else str(raw_qsize)
                    c4.metric("MP Queue Size", display_qsize,
                              help="The amount of chunks not in the replay buffer. Value * chunk size = Steps")

                    c5.metric("Current Loss", state.get("current_loss", 0.0))

                    st.subheader("Performance")
                    t1, t2, t3 = st.columns(3)
                    t1.metric("Iterations / Sec (Learner GPU)", state.get("updates_per_sec", 0))
                    t2.metric("Elapsed (Total)", format_time(state.get("elapsed_total", 0)))

                    queue_health = "Healthy" if state.get('updates_per_sec', 0) > 0 else "Stalled"
                    t3.metric("Training Status", queue_health)

                    st.divider()

                    # BOTTLENECK ANALYSIS
                    st.subheader("Bottleneck Analysis (System Flow)")

                    b1, b2, b3 = st.columns(3)

                    ingest_rate = state.get("ingestion_rate", 0)
                    train_rate = state.get("training_rate", 0)
                    utd = state.get("utd_ratio", 0)

                    b1.metric("Actor Ingestion Rate", f"{ingest_rate} steps/sec",
                              help="Global speed of all Actors combined.")
                    b2.metric("GPU Training Rate", f"{train_rate} samples/sec",
                              help="Speed the GPU is pulling from the Replay Buffer. Updates/Sec * Batch Size.")

                    # Safely check queue size for Bottleneck
                    safe_qsize_for_math = raw_qsize if isinstance(raw_qsize, (int, float)) else 0

                    # Determine Bottleneck Status dynamically
                    # these emojis are NOT AI we specifically used them cus its actually useful and looks good here
                    if utd > 8:
                        bottleneck = "🔴 Actor Limited (GPU Starving)"
                    elif safe_qsize_for_math > 100:
                        bottleneck = "🔴 Learner Limited (CPU Waiting)"
                    else:
                        bottleneck = "🟢 Balanced Pipeline"

                    b3.metric("Update To Data (UTD) Ratio", f"{utd}x",
                              help="Represents how many times the GPU trains on the same Data", delta=bottleneck,
                              delta_color="off")

                    st.divider()

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Architecture")
                        st.info(
                            "Actors stream chunks of 32 steps to Host RAM queue.\n\nLearner unrolls chunks, batches, trains on GPU, and pushes weights back to CPU.")

                    with col2:
                        st.subheader("Hyperparameters")
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
                            if 'step_count' in df.columns:
                                st.line_chart(df, x="step_count", y="reward")
                            else:
                                st.line_chart(df, y="reward")
                        with chart_col2:
                            if 'step_count' in df.columns:
                                st.line_chart(df, x="step_count", y="avg_loss")
                            else:
                                st.line_chart(df, y="avg_loss")
                    except Exception as e:
                        st.error(f"Error reading CSV: {e}")
                else:
                    st.info("No training CSV found yet. Actors might still be playing their first maps.")

            # TABS 1..N: INDIVIDUAL ACTORS
            max_timesteps = state.get("hyperparameters", {}).get("MAX_TIMESTEPS", 1000) if state else 1000

            for i in range(num_actors):
                with tabs[i + 1]:
                    actor_file = f"actor_{i}_state.json"
                    if os.path.exists(actor_file):
                        try:
                            with open(actor_file, 'r') as f:
                                actor_state = json.load(f)

                            st.header(f"Live Feed: actor {i}")

                            # Expanded to 4 columns to fit the new metric
                            ac1, ac2, ac3, ac4 = st.columns(4)
                            ac1.metric("Current Map", actor_state.get("current_map", "Unknown"))
                            ac2.metric("Epsilon (Exploration)", f"{actor_state.get('epsilon', 0.0):.4f}")
                            ac3.metric("Total Actor Steps", f"{actor_state.get('total_actor_steps', 0):,}")
                            ac4.metric("Iterations / Sec", actor_state.get("steps_per_sec", 0.0))

                            current_step = actor_state.get("step", 0)
                            ep1, ep2 = st.columns(2)
                            ep1.metric("Episode",
                                       f"{min(actor_state.get('episode', 1), episodes_per_actor)} / {episodes_per_actor}",
                                       help="Episode this actor is currently playing.")
                            ep2.metric("Current Episode Reward", round(actor_state.get("episode_reward", 0.0), 3))

                            # Safe progress bar
                            progress_val = max(0.0, min(current_step / max_timesteps, 1.0))
                            st.progress(progress_val, text=f"Episode Progress (Step {current_step} / {max_timesteps})")

                            # --- REWARD BREAKDOWN ---
                            reward_breakdown = actor_state.get("reward_breakdown")
                            if reward_breakdown:
                                st.divider()
                                st.subheader("Reward Breakdown (Current Episode)")

                                # Convert the nested dictionary into a pandas DataFrame for Streamlit
                                breakdown_df = pd.DataFrame(reward_breakdown).T

                                # Clean up index names (e.g., 'invalid_action' -> 'Invalid Action')
                                breakdown_df.index = breakdown_df.index.str.replace("_", " ").str.title()
                                breakdown_df.columns = ["Total Reward", "Trigger Count"]

                                rb_col1, rb_col2 = st.columns(2)

                                with rb_col1:
                                    st.dataframe(breakdown_df, width='content')

                                with rb_col2:
                                    st.bar_chart(breakdown_df["Total Reward"])

                        except json.JSONDecodeError:
                            st.warning(f"Syncing data for actor {i}...")
                    else:
                        st.info(f"Waiting for actor {i} to start exploring and report in...")

        else:
            st.warning("Waiting for live data. Make sure train_dqn.py is running...")

    time.sleep(UPDATE_INTERVAL_SEC)
    st.rerun()

    #TODO: Add Ngrok functionality fully
    # One click should start/check for ngrok, streamlit, docker. Start all depending on user wishes