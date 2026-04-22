import streamlit as st
import pandas as pd
import json
import time
import os
import datetime

# Configuration
UPDATE_INTERVAL_SEC = 5  # Matches the AI script interval
CSV_FILE = "training_log.csv"
STATE_FILE = "dashboard_state.json"

st.set_page_config(page_title="Factorio AI Dashboard", layout="wide")


def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))


# Create an empty placeholder so we can redraw the UI without a full page flicker
placeholder = st.empty()

while True:
    with placeholder.container():
        st.title("Factorio AI Dashboard")

        # 1. Read Live State
        state = None
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            except json.JSONDecodeError:
                pass  # JSON is currently being written by the other script

        if state:
            st.header("Current Run Info")

            # Top row metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Current Map", state.get("current_map", "N/A"))
            c2.metric("Episode", state.get("episode", 0))
            step = state.get("step", 0)
            max_steps = state.get("max_steps", 1)
            c3.metric("Step / Max", f"{step} / {max_steps}")
            c4.metric("Total Reward", state.get("total_reward", 0))

            # Timing Metrics
            st.subheader("Timing & Performance")
            t1, t2, t3, t4, t5 = st.columns(5)
            t1.metric("Iterations / Sec", state.get("it_per_sec", 0))
            t2.metric("Elapsed (Episode)", format_time(state.get("elapsed_episode", 0)))
            t3.metric("Elapsed (Total)", format_time(state.get("elapsed_total", 0)))
            t4.metric("ETA (Episode)", format_time(state.get("eta_episode", 0)))
            t5.metric("ETA (All Episodes)", format_time(state.get("eta_total", 0)))

            st.progress(step / max_steps)

            # Lower half: Reports and Hyperparameters
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Timing Report (Cumulative)")
                timing = state.get("timing_report", {})
                st.dataframe(pd.DataFrame(list(timing.items()), columns=["Task", "Seconds Spend"]),
                             use_container_width=True)

            with col2:
                st.subheader("Hyperparameters")
                with st.expander("View Config Variables"):
                    st.json(state.get("hyperparameters", {}))
        else:
            st.warning("Waiting for live data from the Agent...")

        st.divider()

        # 2. Historical Training Data
        st.header("Training CSV Log")
        if os.path.exists(CSV_FILE):
            try:
                df = pd.read_csv(CSV_FILE)
                st.dataframe(df.tail(10), use_container_width=True)  # Show last 10 entries to save UI space

                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    st.line_chart(df, x="episode", y="reward")
                with chart_col2:
                    st.line_chart(df, x="episode", y="avg_loss")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        else:
            st.info("No training CSV found yet.")

    # Auto-refresh logic
    time.sleep(UPDATE_INTERVAL_SEC)
    st.rerun()