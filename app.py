"""Compatibility entrypoint for existing Codespace commands."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name('streamlit_app.py')), run_name='__main__')
