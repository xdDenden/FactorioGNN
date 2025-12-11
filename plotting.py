import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

#delete file if exists
if os.path.exists("training_log.csv"):
    os.remove("training_log.csv")

LOG_FILE = "training_log.csv"


class TrainingLogger:
    def __init__(self, filename=LOG_FILE):
        self.filename = filename
        self.buffer = []

        # Initialize file with headers if it doesn't exist
        if not os.path.exists(self.filename):
            df = pd.DataFrame(columns=[
                "episode", "step_count", "reward", "avg_loss",
                "epsilon", "max_production", "max_edges",
                "milestone_count", "milestones_list"
            ])
            df.to_csv(self.filename, index=False)

    def log_episode(self, episode, step_count, reward, avg_loss, epsilon,
                    max_production, max_edges, milestones):
        """
        Buffers data from a single episode.
        """
        # Convert set of milestones to string for CSV storage
        milestones_str = "|".join(sorted(list(milestones)))

        record = {
            "episode": episode,
            "step_count": step_count,
            "reward": reward,
            "avg_loss": avg_loss,
            "epsilon": epsilon,
            "max_production": max_production,
            "max_edges": max_edges,
            "milestone_count": len(milestones),
            "milestones_list": milestones_str
        }
        self.buffer.append(record)
        self.save_buffer()

    def save_buffer(self):
        """Appends buffered data to the CSV file."""
        if not self.buffer:
            return

        df = pd.DataFrame(self.buffer)
        df.to_csv(self.filename, mode='a', header=False, index=False)
        self.buffer = []
        print(f"Logged episode data to {self.filename}")


def plot_training_data(filename=LOG_FILE):
    if not os.path.exists(filename):
        print(f"No log file found at {filename}")
        return

    df = pd.read_csv(filename)

    if df.empty:
        print("Log file is empty.")
        return

    # Create a 3x2 grid of subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Total Reward per Episode", "Average Loss per Episode",
            "Max Production Score", "Max Functional Edges",
            "Unique Milestones Reached", "Epsilon Decay"
        ),
        vertical_spacing=0.12
    )

    # 1. Reward
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['reward'], mode='lines+markers', name='Reward', line=dict(color='green')),
        row=1, col=1
    )

    # 2. Loss
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['avg_loss'], mode='lines', name='Loss', line=dict(color='red')),
        row=1, col=2
    )

    # 3. Production (Anti-Hack Score)
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['max_production'], mode='lines+markers', name='Production',
                   line=dict(color='blue')),
        row=2, col=1
    )

    # 4. Edges
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['max_edges'], mode='lines+markers', name='Edges', line=dict(color='orange')),
        row=2, col=2
    )

    # 5. Milestones
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['milestone_count'], mode='lines+markers', name='Milestones',
                   line=dict(color='purple')),
        row=3, col=1
    )

    # 6. Epsilon
    fig.add_trace(
        go.Scatter(x=df['episode'], y=df['epsilon'], mode='lines', name='Epsilon',
                   line=dict(color='gray', dash='dash')),
        row=3, col=2
    )

    fig.update_layout(
        height=900,
        width=1200,
        title_text="FactorioHGNN Training Metrics",
        showlegend=False,
        template="plotly_dark"
    )

    fig.show()


if __name__ == "__main__":
    plot_training_data()