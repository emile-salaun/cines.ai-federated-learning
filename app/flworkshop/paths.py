"""Where things live in the repository.

The Flower app is the uv project in `app/`; the dashboard, the precomputed references
and the run results live at the repository root. Set FL_WORKSHOP_ROOT to use another
root (e.g. a read-only copy of `references/` on a hub).
"""

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]          # app/: pyproject.toml, `flwr run`
REPO_ROOT = Path(os.environ.get("FL_WORKSHOP_ROOT", APP_DIR.parent)).resolve()

DASHBOARD_DIR = REPO_ROOT / "dashboard"
REFERENCES_DIR = REPO_ROOT / "references"
RESULTS_DIR = REPO_ROOT / "results"
