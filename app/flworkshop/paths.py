"""Where things live in the repository.

The Flower app is the uv project in `app/`; the dashboard, the precomputed references
and the run results live at the repository root. Set FL_WORKSHOP_ROOT to use another
root (e.g. a read-only copy of `references/` on a hub).

Run results live outside the repository, in RUNS_DIR: the ServerApp writes one JSON per
run there and the dashboard lists them. Set FL_WORKSHOP_RUNS (for the SuperLink and the
dashboard alike) to share one folder between users, e.g. on a hub.
"""

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]          # app/: pyproject.toml, `flwr run`
REPO_ROOT = Path(os.environ.get("FL_WORKSHOP_ROOT", APP_DIR.parent)).resolve()

DASHBOARD_DIR = REPO_ROOT / "dashboard"
REFERENCES_DIR = REPO_ROOT / "references"
RESULTS_DIR = REPO_ROOT / "results"
RUNS_DIR = Path(os.environ.get("FL_WORKSHOP_RUNS", "~/.cache/fl-workshop/runs")).expanduser()
