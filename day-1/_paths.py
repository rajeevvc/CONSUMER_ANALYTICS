"""Shared Day 1 paths (data / output / toy shared).

Lab scripts and examples live one level under day-1/<context>/,
so they import this module after putting day-1 on sys.path.
"""

from __future__ import annotations

from pathlib import Path

DAY1 = Path(__file__).resolve().parent
DATA = DAY1 / "data"
OUTPUT = DAY1 / "output"
SHARED = DAY1 / "_shared"

CONTEXT_DIRS = {
    "sessionize": DAY1 / "01_sessionize",
    "journey": DAY1 / "02_journey",
    "state_modeling": DAY1 / "03_state_modeling",
    "feature_engineering": DAY1 / "04_feature_engineering",
    "segmentation": DAY1 / "05_segmentation",
}


def ensure_day1_on_path() -> Path:
    """Insert day-1 onto sys.path so sibling context packages can import."""
    import sys

    day1 = str(DAY1)
    if day1 not in sys.path:
        sys.path.insert(0, day1)
    return DAY1


def add_context_to_path(context_key: str) -> Path:
    """Allow `from step0N_... import ...` across context folders."""
    import sys

    ensure_day1_on_path()
    folder = CONTEXT_DIRS[context_key]
    path = str(folder)
    if path not in sys.path:
        sys.path.insert(0, path)
    return folder
