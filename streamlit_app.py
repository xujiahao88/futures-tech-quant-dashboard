"""Streamlit entrypoint.

Run the dashboard script for every Streamlit session/rerun.  A normal module
import is cached by Python and would render only the first connected session.
"""

from pathlib import Path
import runpy


runpy.run_path(
    str(Path(__file__).resolve().parent / "dashboard" / "app.py"),
    run_name="__main__",
)
