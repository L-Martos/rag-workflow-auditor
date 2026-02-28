import os
import sys
import subprocess

def main():
    """
    Launch Streamlit app.
    """
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "ui_app.py",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        "8501",
    ]
    raise SystemExit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
