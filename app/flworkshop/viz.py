"""Launch simulations from the notebook, and link to the web dashboard.

    from flworkshop import viz
    viz.setup()                                       # once: federation + dashboard
    viz.run("pathological", "partitioning='pathological'")
    viz.open("pathological", view="network")          # link to one dashboard view

The dashboard (dashboard/ folder) opens in a browser tab and updates every round.
The configuration is a `flwr run --run-config` string, in Flower's syntax (the same as in
a terminal, and as in deployed mode); `run()` prints the command it executes. The app
code never changes. Each run writes its results to results/notebook/<name>.json.

The matplotlib figures (`show`, `compare`, `partitions`) remain available outside the
browser, but are no longer part of the hands-on path.
"""

import builtins
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator

from flworkshop import dashboard_server

open_file = builtins.open  # `open` below is the dashboard link

# Harmless warning from tqdm in Jupyter without ipywidgets.
warnings.filterwarnings("ignore", message="IProgress not found")

from flworkshop.paths import APP_DIR  # noqa: E402
from flworkshop.paths import RESULTS_DIR as _RESULTS_ROOT  # noqa: E402

RESULTS_DIR = _RESULTS_ROOT / "notebook"

# Palette: categorical slots in fixed order (one per client), sequential blue ramp for
# magnitudes, reserved status color for failures. Identity is never color-only: client
# lines also differ by marker, and every heatmap cell carries its value.
CLIENT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                 "#e87ba4", "#008300", "#6250d6", "#e34948"]
CLIENT_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
GLOBAL_COLOR = "#0b0b0b"
OTHER_COLOR = "#a3a29c"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e5e4e0"
IDLE = "#f0efec"
FAILED = "#d03b3b"
SEQ = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)

ENV = {
    # Run the app in the project's .venv instead of reinstalling it at every run.
    "FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION": "1",
    # One thread per process: the simulation shares the machine with other people.
    "OMP_NUM_THREADS": "1",
}

_STATE = {"num_clients": 5, "current": None}


# ============================================================================ setup
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
    """Prepare the session: environment, simulated federation, data check, dashboard."""
    from flworkshop.data import DEFAULT_DATA_DIR

    os.environ.update(ENV)
    _restart_stale_superlink()
    subprocess.run(
        [_flwr(), "federation", "simulation-config", "@none/default", "local",
         "--num-supernodes", str(num_clients), "--client-resources-num-cpus", "1",
         "--init-args-num-cpus", str(cpus)],
        cwd=APP_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    _STATE["num_clients"] = num_clients
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Simulated federation: {num_clients} clients, {cpus} CPUs in total")
    for name in ("fashion_mnist", "cifar10"):
        path = DEFAULT_DATA_DIR / f"{name}.pt"
        state = "OK" if path.exists() else "missing (uv run --project app python scripts/prepare_data.py)"
        print(f"Data {name:<14}: {state}")
    _STATE["port"] = dashboard_server.start(dashboard_port)
    open()


# ============================================================================ runs
def _flower_config(config: dict) -> dict:
    return {k.replace("_", "-"): v for k, v in config.items()}


def _config_string(config: dict) -> str:
    return " ".join(
        f"{k}='{v}'" if isinstance(v, str) else f"{k}={str(v).lower() if isinstance(v, bool) else v}"
        for k, v in config.items()
    )


def _paths(name: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise ValueError("Run name: letters, digits, '_', '-' or '.' only.")
    return RESULTS_DIR / f"{name}.json", RESULTS_DIR / f"{name}.log"


def _run_id(log: Path) -> int | None:
    if not log.exists():
        return None
    match = re.search(r"Successfully started run (\d+)", log.read_text(errors="ignore"))
    return int(match.group(1)) if match else None


def stop() -> None:
    """Stop the run in progress (the one launched last)."""
    current = _STATE["current"]
    if current is None or current["proc"].poll() is not None:
        print("No run in progress.")
        return
    run_id = _run_id(current["log"])
    if run_id is not None:
        subprocess.run([_flwr(), "stop", str(run_id)], cwd=APP_DIR,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    current["proc"].terminate()
    print(f"Run '{current['name']}' stopped.")


def command(run_config: str = "", **config) -> str:
    """The `flwr run` command that `run()` executes, as you would type it in a terminal."""
    rc = _merge(run_config, config)
    return "flwr run app --stream" + (f' --run-config "{rc}"' if rc else "")


def _merge(run_config: str, config: dict) -> str:
    """One `--run-config` string: Flower syntax first, then keyword arguments."""
    return " ".join(p for p in (run_config.strip(), _config_string(_flower_config(config))) if p)


def run(name: str, run_config: str = "", *, view: str = "together", live: bool = True,
        **config) -> None:
    """Launch a simulation in the background and follow its progress (live=True).

    `run_config` is passed to `flwr run --run-config` unchanged, in Flower's syntax:
    viz.run("dirichlet", "partitioning='dirichlet' dirichlet-alpha=0.1").
    Keyword arguments are also accepted (partitioning="dirichlet", underscores for
    hyphens) and appended to it. The command is printed before the run starts.
    The results appear in the dashboard; `view` picks the tab the link opens:
    "together" (solo or together?), "run", "network" or "compare".
    """
    os.environ.update(ENV)
    current = _STATE["current"]
    if current is not None and current["proc"].poll() is None:
        previous = _load(current["name"])
        if previous and previous.get("finished"):  # finished, just closing its stream
            _wait(current["proc"])
        else:
            print(f"Run '{current['name']}' is still running: stopping it to launch "
                  f"'{name}'.")
            stop()

    result, log = _paths(name)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result.unlink(missing_ok=True)
    rc = _merge(run_config, config)
    print(command(rc))
    # results-file feeds the dashboard; it is added here and kept out of the printed command.
    full = " ".join(p for p in (rc, _config_string({"results-file": str(result)})) if p)
    cmd = [_flwr(), "run", str(APP_DIR), "--stream", "--run-config", full]
    with open_file(log, "w") as out:
        proc = subprocess.Popen(cmd, cwd=APP_DIR, env=os.environ.copy(), stdout=out,
                                stderr=subprocess.STDOUT)
    _STATE["current"] = {"name": name, "proc": proc, "log": log, "run_config": rc}
    if live:
        watch(name, view=view)


def _wait(proc, timeout: float = 20) -> None:
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()


def _load(name: str) -> dict | None:
    path, _ = _paths(name)
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _log_tail(name: str, lines: int = 25) -> str:
    _, log = _paths(name)
    if not log.exists():
        return ""
    text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text(errors="ignore"))
    keep = [line for line in text.splitlines() if not line.startswith(("INFO:flwr", "DEBUG"))]
    return "\n".join(keep[-lines:])


def log(name: str) -> None:
    """Print the key lines of a run's log: sampling, replies, aggregation, evaluation."""
    _, path = _paths(name)
    if not path.exists():
        print(f"No log for '{name}'.")
        return
    text = re.sub(r"\x1b\[[0-9;]*m", "", path.read_text(errors="ignore"))
    keys = ("[ROUND", "configure_train", "aggregate_train", "error in reply",
            "Aggregated MetricRecord", "MetricRecord: {'accuracy", "Initial global")
    for line in text.splitlines():
        if line.startswith("INFO :") and any(k in line for k in keys):
            print(line[len("INFO :"):].strip("\n").replace("      ", "", 1))


def watch(name: str, refresh: float = 1.5, view: str = "together") -> None:
    """Follow a run until it ends: one progress line, with a link to the dashboard."""
    from IPython.display import HTML, display

    handle = display(HTML(_progress_html(name, None, view, "starting…")), display_id=True)
    current = _STATE["current"]
    proc = current["proc"] if current and current["name"] == name else None
    start, shown = time.time(), None
    try:
        while True:
            running = proc is not None and proc.poll() is None
            data = _load(name)
            done = bool(data and data.get("finished"))
            if data and len(data["rounds"]) > 1:
                key = (len(data["rounds"]), done)
                if key != shown:
                    shown = key
                    handle.update(HTML(_progress_html(name, data, view)))
            else:
                waited = int(time.time() - start)
                handle.update(HTML(_progress_html(
                    name, None, view, f"starting clients and loading data "
                    f"({waited} s, expect 20 to 60 s)…")))
            if done:
                if proc is not None:
                    _wait(proc)
                return
            if not running:
                if proc is None and data is None:
                    handle.update(HTML(f"No results for '{name}'."))
                    return
                if proc is not None:
                    time.sleep(1)
                    data = _load(name)
                    if data and data.get("finished"):
                        continue
                    handle.update(HTML(_progress_html(name, data, view,
                                                      "the run stopped before the end")))
                    print(_log_tail(name))
                    return
            time.sleep(refresh)
    except KeyboardInterrupt:
        print(f"Tracking interrupted; the run goes on (see the dashboard). viz.stop() "
              "stops it.")


def _progress_html(name: str, data: dict | None, view: str, message: str = "") -> str:
    """One quiet line: run name, progress bar, global accuracy, link to the dashboard."""
    link = dashboard_link(name, view)
    total, done, acc, state = 0, 0, None, message
    if data:
        rounds = data["rounds"]
        total = int(data["config"].get("num-server-rounds", len(rounds) - 1))
        done = rounds[-1]["round"]
        acc = rounds[-1]["accuracy"]
        if not message:
            state = "finished" if data.get("finished") else "running"
    width = 0 if not total else round(100 * done / total)
    bar = (f'<span style="display:inline-block;width:140px;height:6px;border-radius:3px;'
           f'background:rgba(127,127,127,.25);vertical-align:middle;margin:0 10px">'
           f'<span style="display:block;width:{width}%;height:100%;border-radius:3px;'
           f'background:currentColor"></span></span>')
    figures = (f"round {done} of {total}, global model {acc:.0%}".replace("%", "\u202f%")
               if data else "")
    parts = [f"<b>{name}</b>", bar if data else "", figures, f"<i>{state}</i>" if state else ""]
    open_link = (f'<a href="{link}" target="_blank" rel="noopener">open in the dashboard</a>'
                 if link else "")
    return ('<div style="font-family:system-ui,sans-serif;font-size:14px;padding:4px 0">'
            + " ".join(p for p in parts if p) + (f"   {open_link}" if open_link else "")
            + "</div>")


def dashboard_link(name: str | None = None, view: str = "together") -> str | None:
    """Address of the dashboard, optionally on a given run and tab."""
    port = _STATE.get("port")
    if port is None:
        return None
    query = f"view={view}" + (f"&run={name}" if name else "")
    return f"{dashboard_server.url(port)}#{query}"


def open(name: str | None = None, view: str = "together") -> None:  # noqa: A001
    """Display a link to the dashboard (on a run and a tab when given)."""
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


def show(name: str) -> None:
    """Dashboard of a finished (or partial) run, without waiting."""
    data = _load(name)
    if not data:
        print(f"No results for '{name}'.")
        return
    fig = dashboard(data, status=_status(data, False))
    plt.show()
    plt.close(fig)


def _status(data: dict, running: bool) -> str:
    rounds = data["rounds"]
    total = int(data["config"].get("num-server-rounds", len(rounds) - 1))
    done = rounds[-1]["round"]
    elapsed = rounds[-1]["time"] - data["started_at"]
    state = "finished" if data.get("finished") else ("running" if running else "interrupted")
    return f"round {done}/{total} · {elapsed:.0f} s · {state}"


def _print_summary(name: str, data: dict) -> None:
    accs = [r["accuracy"] for r in data["rounds"]]
    print(f"{name}: global accuracy {accs[1]:.1%} at round 1, {accs[-1]:.1%} at the last "
          f"round (best: {max(accs):.1%}).")


# ============================================================================ figures
def _style(ax, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=10, color=TEXT, pad=8)
    ax.tick_params(colors=TEXT_2, labelsize=8, length=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _client_style(pid: int, n: int) -> dict:
    if n > len(CLIENT_COLORS):  # too many clients for distinct colors: fold to gray
        return {"color": OTHER_COLOR, "marker": None}
    return {"color": CLIENT_COLORS[pid], "marker": CLIENT_MARKERS[pid]}


def _client_ids(data: dict) -> list[int]:
    ids = set()
    for r in data["rounds"]:
        ids.update(int(k) for k in r.get("clients", {}))
    return sorted(ids) or list(range(_STATE["num_clients"]))


def _client_value(round_entry: dict, pid: int, key: str) -> float:
    """Value for a client in a round, NaN if it did not train (breaks plotted lines)."""
    c = round_entry["clients"].get(str(pid), {})
    value = c.get(key) if c.get("status") == "ok" else None
    return float("nan") if value is None else value


def _annotated_heatmap(ax, matrix, row_labels, col_labels, fmt, vmax=None, mask=None):
    shown = np.ma.masked_invalid(matrix.astype(float))
    ax.imshow(shown, cmap=SEQ, vmin=0, vmax=vmax or np.nanmax(matrix) or 1, aspect="auto")
    ax.set_xticks(range(len(col_labels)), col_labels, rotation=40, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(row_labels)), row_labels, fontsize=8)
    top = vmax or np.nanmax(matrix) or 1
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            v = matrix[i, j]
            if np.isnan(v):
                continue
            ink = "white" if v / top > 0.55 else TEXT
            ax.text(j, i, fmt(v), ha="center", va="center", fontsize=7, color=ink)
    ax.set_xticks(np.arange(-0.5, len(col_labels)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(row_labels)), minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)


def _short(label: str, width: int = 10) -> str:
    return label if len(label) <= width else label[: width - 1] + "…"


def dashboard(data: dict, status: str = ""):
    """Six panels: accuracy, participation, time, data, per-class accuracy, drift."""
    from flworkshop.data import label_distribution

    cfg = data["config"]
    rounds = [r for r in data["rounds"] if r["round"] > 0]
    total = int(cfg.get("num-server-rounds", len(rounds)))
    clients = _client_ids(data)
    n = len(clients)
    classes = data.get("classes", [str(i) for i in range(10)])

    fig, axes = plt.subplots(2, 3, figsize=(15.5, 8.8),
                             gridspec_kw={"hspace": 0.55, "wspace": 0.32})
    title = (f"{cfg.get('dataset')} · {cfg.get('partitioning')}"
             + (f" α={cfg.get('dirichlet-alpha')}" if cfg.get("partitioning") == "dirichlet" else "")
             + (f" · fraction-train={cfg.get('fraction-train')}" if float(cfg.get("fraction-train", 1)) < 1 else "")
             + (f" · dropout-rate={cfg.get('dropout-rate')}" if float(cfg.get("dropout-rate", 0)) > 0 else "")
             + (f" · μ={cfg.get('proximal-mu')}" if float(cfg.get("proximal-mu", 0)) > 0 else ""))
    fig.suptitle(f"{title}    {status}", x=0.06, ha="left", fontsize=12, color=TEXT)

    # A. Accuracy: global model vs each client's local model -------------------------
    ax = axes[0, 0]
    _style(ax, "Accuracy: global model and local models")
    for pid in clients:
        # One point per round where the client trained; a gap breaks the line.
        xs = [r["round"] for r in rounds]
        ys = [_client_value(r, pid, "local_acc") for r in rounds]
        st = _client_style(pid, n)
        ax.plot(xs, ys, lw=1.2, alpha=0.9, color=st["color"], marker=st["marker"],
                markersize=4, label=f"client {pid} (local)")
    gx = [r["round"] for r in data["rounds"]]
    gy = [r["accuracy"] for r in data["rounds"]]
    ax.plot(gx, gy, lw=2.6, color=GLOBAL_COLOR, marker="o", markersize=5, label="global model")
    ax.annotate(f"{gy[-1]:.0%}", (gx[-1], gy[-1]), xytext=(6, 0), textcoords="offset points",
                fontsize=8, color=TEXT, va="center")
    ax.set_xlim(-0.3, total + 0.8)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("round", fontsize=8, color=TEXT_2)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.grid(color=GRID, linewidth=0.6)
    ax.legend(fontsize=7, loc="lower right", frameon=False, ncol=2 if n > 3 else 1)

    # B. Participation grid: local accuracy, failures, idle clients -----------------
    ax = axes[0, 1]
    _style(ax, "Participation (local model accuracy, %)")
    cols = list(range(1, total + 1))
    matrix = np.full((n, len(cols)), np.nan)
    by_round = {r["round"]: r for r in rounds}
    for i, pid in enumerate(clients):
        for j, rnd in enumerate(cols):
            c = by_round.get(rnd, {}).get("clients", {}).get(str(pid))
            if c and c.get("status") == "ok":
                matrix[i, j] = c["local_acc"]
    _annotated_heatmap(ax, matrix, [f"client {p}" for p in clients], [str(c) for c in cols],
                       lambda v: f"{v * 100:.0f}", vmax=1)
    for i, pid in enumerate(clients):
        for j, rnd in enumerate(cols):
            c = by_round.get(rnd, {}).get("clients", {}).get(str(pid))
            if not c or c.get("status") == "ok":
                continue
            failed = c.get("status") == "failed"
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color=FAILED if failed else IDLE))
            ax.text(j, i, "×" if failed else "–", ha="center", va="center", fontsize=9,
                    color="white" if failed else TEXT_2)
    ax.set_xlabel("round   (–: not sampled   ×: disconnected)", fontsize=8, color=TEXT_2)
    ax.tick_params(axis="x", rotation=0)

    # C. Training time per client, last round --------------------------------------
    ax = axes[0, 2]
    last = rounds[-1]
    _style(ax, f"Training time at round {last['round']}")
    for i, pid in enumerate(clients):
        c = last["clients"].get(str(pid), {})
        st = _client_style(pid, n)
        if c.get("status") == "ok":
            ax.barh(i, c["train_time"], color=st["color"], height=0.6)
            ax.text(c["train_time"], i, f"  {c['train_time']:.1f} s · {c['num_examples']} images",
                    va="center", fontsize=7.5, color=TEXT)
        else:
            label = "disconnected" if c.get("status") == "failed" else "not sampled"
            ax.text(0, i, f"  {label}", va="center", fontsize=7.5, color=TEXT_2)
    times = [c.get("train_time", 0) for c in last["clients"].values()]
    ax.set_xlim(0, (max(times) if times else 1) * 1.9 or 1)
    ax.set_yticks(range(n), [f"client {p}" for p in clients], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("seconds (the round waits for the slowest client)", fontsize=8, color=TEXT_2)

    # D. Data held by each client ---------------------------------------------------
    ax = axes[1, 0]
    _style(ax, "Data of each client (images per class)")
    counts = label_distribution(cfg, n).astype(float)
    _annotated_heatmap(ax, counts, [f"client {p}" for p in clients],
                       [_short(c) for c in classes],
                       lambda v: f"{v / 1000:.1f}k" if v >= 1000 else f"{v:.0f}")

    # E. Per-class accuracy: each local model and the global model -------------------
    ax = axes[1, 1]
    _style(ax, "Per-class accuracy of each model (%)")
    rows, labels = [], []
    for pid in clients:
        trained = [r for r in rounds if r["clients"].get(str(pid), {}).get("status") == "ok"]
        if trained:
            rows.append(trained[-1]["clients"][str(pid)]["local_per_class"])
            labels.append(f"client {pid} (r{trained[-1]['round']})")
        else:
            rows.append([np.nan] * len(classes))
            labels.append(f"client {pid} (—)")
    rows.append(data["rounds"][-1]["per_class"])
    labels.append("GLOBAL")
    _annotated_heatmap(ax, np.array(rows, dtype=float), labels, [_short(c) for c in classes],
                       lambda v: f"{v * 100:.0f}", vmax=1)
    ax.axhline(len(rows) - 1.5, color=GLOBAL_COLOR, linewidth=1.5)

    # F. Drift: distance between each local model and the global model it started from
    ax = axes[1, 2]
    _style(ax, "Drift: distance to the received global model")
    for pid in clients:
        ys = [_client_value(r, pid, "divergence") for r in rounds]
        if not all(np.isnan(ys)):
            st = _client_style(pid, n)
            ax.plot([r["round"] for r in rounds], ys, lw=1.4, color=st["color"],
                    marker=st["marker"], markersize=4, label=f"client {pid}")
    ax.set_xlim(0.5, total + 0.5)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("round", fontsize=8, color=TEXT_2)
    ax.set_ylabel("L2 distance of the weights", fontsize=8, color=TEXT_2)
    ax.grid(color=GRID, linewidth=0.6)
    ax.legend(fontsize=7, frameon=False)
    return fig


def partitions(**config) -> None:
    """Show how the data is split between clients for a given configuration."""
    from flworkshop.data import class_names, label_distribution

    cfg = _flower_config(config)
    n = _STATE["num_clients"]
    counts = label_distribution(cfg, n).astype(float)
    classes = class_names(cfg)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(14, 0.55 * n + 2.2),
                                 gridspec_kw={"width_ratios": [4, 1], "wspace": 0.08})
    label = cfg.get("partitioning", "iid")
    _style(ax, f"Images per class and per client · {cfg.get('dataset', 'fashion_mnist')} · {label}")
    _annotated_heatmap(ax, counts, [f"client {i}" for i in range(n)],
                       [_short(c, 12) for c in classes],
                       lambda v: f"{v / 1000:.1f}k" if v >= 1000 else f"{v:.0f}")
    _style(bx, "Total")
    totals = counts.sum(axis=1)
    for i, t in enumerate(totals):
        st = _client_style(i, n)
        bx.barh(i, t, color=st["color"], height=0.6)
        bx.text(t, i, f" {t / 1000:.1f}k", va="center", fontsize=7.5, color=TEXT)
    bx.set_ylim(n - 0.5, -0.5)
    bx.set_yticks([])
    bx.set_xlim(0, totals.max() * 1.45)
    bx.set_xticks([])
    plt.show()
    plt.close(fig)


def compare(*names: str) -> None:
    """Overlay the global accuracy of several runs and print a summary table."""
    loaded = [(n, _load(n)) for n in names]
    loaded = [(n, d) for n, d in loaded if d]
    if not loaded:
        print("No results to compare.")
        return
    fig, ax = plt.subplots(figsize=(9, 4.6))
    _style(ax, "Global model accuracy")
    for i, (name, d) in enumerate(loaded):
        color = CLIENT_COLORS[i] if len(loaded) <= len(CLIENT_COLORS) else OTHER_COLOR
        xs = [r["round"] for r in d["rounds"]]
        ys = [r["accuracy"] for r in d["rounds"]]
        ax.plot(xs, ys, lw=2, color=color, marker=CLIENT_MARKERS[i % len(CLIENT_MARKERS)],
                markersize=5, label=name)
        ax.annotate(f"{name} {ys[-1]:.0%}", (xs[-1], ys[-1]), xytext=(6, 0),
                    textcoords="offset points", fontsize=8, color=TEXT, va="center")
    total = max(r["round"] for _, d in loaded for r in d["rounds"])
    ax.set_xlim(-0.3, total + max(1.5, 0.3 * total))
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_xlabel("round", fontsize=8, color=TEXT_2)
    ax.grid(color=GRID, linewidth=0.6)
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    plt.show()
    plt.close(fig)

    header = f"{'run':<16}{'round 1':>9}{'round 5':>9}{'last':>9}{'best':>10}{'s/round':>9}"
    print(header)
    for name, d in loaded:
        accs = [r["accuracy"] for r in d["rounds"]]
        times = [r["time"] for r in d["rounds"]]
        steps = sorted(b - a for a, b in zip(times[1:], times[2:])) or [0]
        print(f"{name:<16}{accs[1]:>9.1%}{accs[min(5, len(accs) - 1)]:>9.1%}"
              f"{accs[-1]:>9.1%}{max(accs):>10.1%}{steps[len(steps) // 2]:>9.1f}")
