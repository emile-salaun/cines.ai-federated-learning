"""Small HTTP server for the dashboard: static pages from dashboard/ and a JSON API.

Started in the background by `viz.setup()`, inside the notebook process. It only listens
on 127.0.0.1: open it in a browser on the same machine, or through the JupyterHub proxy
(jupyter-server-proxy) on a hub.

    GET /                 -> dashboard/index.html (and its files)
    GET /api/runs         -> list of runs (results/notebook/*.json)
    GET /api/run/<name>   -> run results + "solo / centralised" references + data
"""

import json
import os
import re
import threading
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from flworkshop.paths import DASHBOARD_DIR as STATIC_DIR
from flworkshop.paths import RESULTS_DIR as _RESULTS_ROOT

RESULTS_DIR = _RESULTS_ROOT / "notebook"
NAME = re.compile(r"^[A-Za-z0-9_.-]+$")

_SERVER: dict = {}


def _num_clients(run: dict) -> int:
    ids = set()
    for r in run.get("rounds", []):
        ids.update(r.get("clients", {}))
    return len(ids)


@lru_cache(maxsize=64)
def _context(config_json: str, num_clients: int) -> dict:
    """What the dashboard needs besides the run itself (cached per configuration)."""
    from flworkshop import baselines
    from flworkshop.data import input_shape, label_distribution

    config = json.loads(config_json)
    counts = label_distribution(config, num_clients)
    per_image = 1
    for d in input_shape(config):
        per_image *= d
    return {
        "references": baselines.load(config, num_clients),
        "label_counts": counts.tolist(),
        "raw_bytes": [float(n) * per_image for n in counts.sum(axis=1)],
    }


def _run_payload(name: str) -> dict | None:
    path = RESULTS_DIR / f"{name}.json"
    try:
        run = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    n = _num_clients(run)
    payload = {"name": name, "run": run}
    if n:
        try:
            payload.update(_context(json.dumps(run["config"], sort_keys=True), n))
        except Exception as exc:  # data missing, etc.: the run is still shown
            payload["context_error"] = str(exc)
    return payload


def _runs_list() -> list[dict]:
    runs = []
    for path in RESULTS_DIR.glob("*.json"):
        try:
            run = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        rounds = run.get("rounds", [])
        cfg = run.get("config", {})
        runs.append({
            "name": path.stem,
            "updated": path.stat().st_mtime,
            "started": run.get("started_at", 0),
            "finished": run.get("finished", False),
            "round": rounds[-1]["round"] if rounds else 0,
            "total": cfg.get("num-server-rounds"),
            "accuracy": rounds[-1]["accuracy"] if rounds else None,
            "dataset": cfg.get("dataset"),
            "partitioning": cfg.get("partitioning"),
        })
    return sorted(runs, key=lambda r: r["started"], reverse=True)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, *args):  # keep the notebook output clean
        pass

    def _json(self, data, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        route = self.path.split("?", 1)[0]
        if route == "/api/runs":
            return self._json(_runs_list())
        if route.startswith("/api/run/"):
            name = route[len("/api/run/"):]
            if not NAME.match(name):
                return self._json({"error": "invalid name"}, 400)
            payload = _run_payload(name)
            return self._json(payload or {"error": "run not found"}, 200 if payload else 404)
        return super().do_GET()

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def start(port: int = 8050) -> int:
    """Start the server once per process; return the port it listens on."""
    if "port" in _SERVER:
        return _SERVER["port"]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            break
        except OSError:
            continue
    else:
        raise RuntimeError(f"No free port between {port} and {port + 19}.")
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    _SERVER.update(port=candidate, server=server)
    return candidate


def url(port: int) -> str:
    """Address to open: through the JupyterHub proxy when running on a hub."""
    prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX")
    if prefix:
        return f"{prefix.rstrip('/')}/proxy/{port}/"
    return f"http://localhost:{port}/"
