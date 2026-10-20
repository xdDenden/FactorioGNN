import sys
import os
import argparse
import multiprocessing


def resolve_path(relative_path: str) -> str:
    """Finds bundled files inside PyInstaller's _MEIPASS or local directory."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def main():
    # Crucial for PyTorch multiprocessing ('spawn') inside a frozen PyInstaller binary
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Factorio RL Unified Launcher")
    parser.add_argument(
        "--mode",
        choices=["ui", "train", "play"],
        default="ui",
        help="Execution mode: 'ui' launches Streamlit, 'train' runs train_dqn, 'play' runs inference."
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Path to .pth weights file when running in 'play' mode."
    )
    args, _ = parser.parse_known_args()

    if args.mode == "train":
        import train_dqn
        train_dqn.main()

    elif args.mode == "play":
        import PlayFactorioWithWeights
        PlayFactorioWithWeights.play(weights_path=args.weights)

    else:
        # Default mode: Start the Streamlit Dashboard Server
        from streamlit.web import cli as stcli
        script_path = resolve_path("StreamlitUpdate.py")
        sys.argv = [
            "streamlit",
            "run",
            script_path,
            "--global.developmentMode=false",
            "--server.port=8501",
            "--server.headless=false",
        ]
        sys.exit(stcli.main())


if __name__ == "__main__":
    main()