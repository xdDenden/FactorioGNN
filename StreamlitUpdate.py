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


placeholder = st.empty()

while True:
    with placeholder.container():
        st.title("Factorio AI Distributed Dashboard")

        # 1. Load Global Learner State
        state = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            except json.JSONDecodeError:
                pass

        # Determine number of agents dynamically (fallback to counting files if learner hasn't posted yet)
        num_actors = state.get("num_actors", 0)
        if num_actors == 0:
            agent_files = glob.glob("agent_*_state.json")
            num_actors = len(agent_files)

        if state or num_actors > 0:
            # 2. Create Dynamic Tabs
            tab_names = ["Overall Progress"] + [f"Agent {i}" for i in range(num_actors)]
            tabs = st.tabs(tab_names)

            # ==========================================
            # TAB 0: OVERALL PROGRESS (Learner)
            # ==========================================
            with tabs[0]:
                if state:
                    st.header("Learner Status")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Steps Ingested", f"{state.get('steps_ingested', 0):,}")
                    c2.metric("Network Updates Done", f"{state.get('updates_done', 0):,}")
                    c3.metric("Buffer Size", f"{state.get('buffer_size', 0):,}")
                    c4.metric("Current Loss", state.get("current_loss", 0.0))

                    st.subheader("Performance")
                    t1, t2, t3 = st.columns(3)
                    # Labelled explicitly as Iterations / Sec
                    t1.metric("Iterations / Sec (Learner GPU)", state.get("updates_per_sec", 0))
                    t2.metric("Elapsed (Total)", format_time(state.get("elapsed_total", 0)))

                    queue_health = "Healthy" if state.get('updates_per_sec', 0) > 0 else "Stalled"
                    t3.metric("Training Status", queue_health)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Architecture")
                        st.info(
                            "Actors stream chunks of 32 steps to Host RAM queue.\n\nLearner unrolls chunks, batches, trains on GPU, and pushes weights to CPU.")

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

            # ==========================================
            # TABS 1..N: INDIVIDUAL AGENTS
            # ==========================================
            max_timesteps = state.get("hyperparameters", {}).get("MAX_TIMESTEPS", 1000) if state else 1000

            for i in range(num_actors):
                with tabs[i + 1]:
                    agent_file = f"agent_{i}_state.json"
                    if os.path.exists(agent_file):
                        try:
                            with open(agent_file, 'r') as f:
                                agent_state = json.load(f)

                            st.header(f"Live Feed: Agent {i}")

                            # Expanded to 4 columns to fit the new metric
                            ac1, ac2, ac3, ac4 = st.columns(4)
                            ac1.metric("Current Map", agent_state.get("current_map", "Unknown"))
                            ac2.metric("Epsilon (Exploration)", f"{agent_state.get('epsilon', 0.0):.4f}")
                            ac3.metric("Total Actor Steps", f"{agent_state.get('total_actor_steps', 0):,}")
                            ac4.metric("Iterations / Sec", agent_state.get("steps_per_sec", 0.0))

                            current_step = agent_state.get("step", 0)
                            st.metric("Current Episode Reward", round(agent_state.get("episode_reward", 0.0), 3))

                            # Safe progress bar
                            progress_val = max(0.0, min(current_step / max_timesteps, 1.0))
                            st.progress(progress_val, text=f"Episode Progress (Step {current_step} / {max_timesteps})")

                        except json.JSONDecodeError:
                            st.warning(f"Syncing data for Agent {i}...")
                    else:
                        st.info(f"Waiting for Agent {i} to start exploring and report in...")

        else:
            st.warning("Waiting for live data. Make sure train_dqn.py is running...")

    time.sleep(UPDATE_INTERVAL_SEC)
    st.rerun()