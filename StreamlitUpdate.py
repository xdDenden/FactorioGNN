import streamlit as st
import pandas as pd
import json
import time
import os
import datetime

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

        state = None
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
            except json.JSONDecodeError:
                pass

        if state:
            st.header("Learner Status")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Steps Ingested", f"{state.get('steps_ingested', 0):,}")
            c2.metric("Network Updates Done", f"{state.get('updates_done', 0):,}")
            c3.metric("Buffer Size", f"{state.get('buffer_size', 0):,}")
            c4.metric("Current Loss", state.get("current_loss", 0.0))

            st.subheader("Performance")
            t1, t2, t3 = st.columns(3)
            t1.metric("Updates / Sec (GPU)", state.get("updates_per_sec", 0))
            t2.metric("Elapsed (Total)", format_time(state.get("elapsed_total", 0)))

            # Simple health check calculation
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
                st.dataframe(df.tail(10), use_container_width=True)

                # Updated charts to plot against global steps rather than episodes
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    if 'step_count' in df.columns:
                        st.line_chart(df, x="step_count", y="reward")
                    else:
                        st.line_chart(df, y="reward")  # Fallback
                with chart_col2:
                    if 'step_count' in df.columns:
                        st.line_chart(df, x="step_count", y="avg_loss")
                    else:
                        st.line_chart(df, y="avg_loss")
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        else:
            st.info("No training CSV found yet. Actors might still be playing their first maps.")

    time.sleep(UPDATE_INTERVAL_SEC)
    st.rerun()