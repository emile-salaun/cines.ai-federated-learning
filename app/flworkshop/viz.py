"""Notebook helpers: prepare the environment and open the web dashboard.

    from flworkshop import viz
    viz.setup()                                   # once: federation, data check, dashboard

    !flwr run app --stream --run-config "run-name='iid' partitioning='iid'"

    viz.dashboard("iid", view="network")          # link to one run and one tab

Runs are launched with Flower's own command, `flwr run`, exactly as in a terminal or a
batch script: this module never launches them. The ServerApp writes each run's results
to RUNS_DIR (see `flworkshop.paths`); the dashboard lists that folder and follows the
latest run, round by round.
"""

import os
import shutil
import signal
import subprocess
import sys
import time
import warnings
from pathlib import Path

from flworkshop import dashboard_server
from flworkshop.paths import APP_DIR, REPO_ROOT, RUNS_DIR

# Harmless warning from tqdm in Jupyter without ipywidgets.
warnings.filterwarnings("ignore", message="IProgress not found")

ENV = {
    # Run the app in the project's .venv instead of reinstalling it at every run.
    "FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION": "1",
    # One thread per process: the simulation shares the machine with other people.
    "OMP_NUM_THREADS": "1",
    # CPU only: silences Ray's FutureWarning about GPU visibility in every run log.
    "RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO": "0",
}

_STATE: dict = {}


def _flwr() -> str:
    found = shutil.which("flwr", path=str(Path(sys.executable).parent)) or shutil.which("flwr")
    if not found:
        raise RuntimeError("`flwr` command not found in the notebook environment.")
    return found


def _superlink_pids() -> list[int]:
    if not shutil.which("pgrep"):
        return []
    out = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f", "flower-superlink"],
                         capture_output=True, text=True).stdout
    return [int(p) for p in out.split()]


def _restart_stale_superlink() -> None:
    """Stop a local SuperLink started without our environment variables.

    The local SuperLink runs in the background and keeps the environment it started
    with; the simulation inherits it. Linux only (reads /proc); elsewhere, skipped.
    """
    for pid in _superlink_pids():
        try:
            environ = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
        except OSError:
            continue
        expected = {f"{k}={v}".encode() for k, v in ENV.items()}
        if not expected <= set(environ):
            os.kill(pid, signal.SIGTERM)
            print(f"Local SuperLink restarted (pid {pid}): it did not have the right "
                  "environment variables.")
            time.sleep(2)


def setup(num_clients: int = 5, cpus: int = 2, dashboard_port: int = 8050) -> None:
    """Prepare the session: environment, simulated federation, data check, dashboard.

    Afterwards `!flwr run app ...` works from the notebook as from a terminal: the
    working directory is the repository root, and this environment's `flwr` comes
    first on the PATH.
    """
    from flworkshop.data import DEFAULT_DATA_DIR

    os.environ.update(ENV)
    os.environ.setdefault("COLUMNS", "150")   # wide enough for the `flwr ls` table
    bindir = str(Path(sys.executable).parent)
    if not os.environ.get("PATH", "").startswith(bindir):
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
    os.chdir(REPO_ROOT)
    _restart_stale_superlink()
    subprocess.run(
        [_flwr(), "federation", "simulation-config", "@none/default", "local",
         "--num-supernodes", str(num_clients), "--client-resources-num-cpus", "1",
         "--init-args-num-cpus", str(cpus)],
        cwd=APP_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Simulated federation: {num_clients} clients, {cpus} CPUs in total")
    for name in ("fashion_mnist", "cifar10"):
        path = DEFAULT_DATA_DIR / f"{name}.pt"
        state = "OK" if path.exists() else "missing (uv run --project app python scripts/prepare_data.py)"
        print(f"Data {name:<14}: {state}")
    _STATE["port"] = dashboard_server.start(dashboard_port)
    dashboard()


def dashboard_link(name: str | None = None, view: str = "together") -> str | None:
    """Address of the dashboard, optionally on a given run and tab."""
    port = _STATE.get("port")
    if port is None:
        return None
    query = f"view={view}" + (f"&run={name}" if name else "")
    return f"{dashboard_server.url(port)}#{query}"


def dashboard(name: str | None = None, view: str = "together") -> None:
    """Display a link to the dashboard, on a run and a tab when given.

    `view`: "together" (solo or together?), "run", "network" or "compare". Without a
    run name, the dashboard follows the latest run.
    """
    from IPython.display import HTML, display

    port = _STATE.get("port")
    if port is None:
        print("Dashboard not started: run viz.setup() first.")
        return
    try:  # Google Colab: the kernel's ports are reachable only through Colab's proxy
        from google.colab import output  # type: ignore

        output.serve_kernel_port_as_window(port, path="/" + (
            f"#view={view}" + (f"&run={name}" if name else "")))
        return
    except ImportError:
        pass
    label = f"Open the dashboard{f' on {name}' if name else ''}"
    display(HTML(f'<a href="{dashboard_link(name, view)}" target="_blank" rel="noopener" '
                 f'style="font-family:system-ui,sans-serif;font-size:15px;font-weight:600">'
                 f'{label}</a> <span style="color:#5b6575;font-size:13px">(new tab, '
                 f'updated every round)</span>'))
