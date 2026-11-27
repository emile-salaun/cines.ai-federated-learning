"""Hands-on calibration: run a series of Flower simulations and compare the results.

Run from the repository root, on a machine that has the data (see prepare_data.py),
ideally with the same number of CPUs as planned per participant:

    uv run python scripts/calibrate.py --phase hparams                 # 1. lr x local epochs, IID
    uv run python scripts/calibrate.py --phase noniid                  # 2. IID / non-IID gap
    uv run python scripts/calibrate.py --phase fedprox                 # 3. effect of FedProx
    uv run python scripts/calibrate.py --phase participation           # 4. partial participation
    uv run python scripts/calibrate.py --phase commcomp                # 5. rounds x local epochs, same budget
    uv run python scripts/calibrate.py --phase deadline                # 6. local epochs under a deadline
    uv run python scripts/calibrate.py --phase hparams --dataset fashion_mnist --rounds 5   # quick
    uv run python scripts/calibrate.py --phase fedprox --local-epochs 5 --lr 0.01 --tag ep5  # variant

Each simulation writes a JSON to results/calibration/<phase>/. Finished runs are skipped:
you can interrupt and restart. At the end of each phase, the script prints a table,
writes summary.csv and plots the curves to curves.png.
"""

import argparse
import csv
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"                      # Flower app (pyproject.toml)
RESULTS = REPO_ROOT / "results" / "calibration"
DATASETS = ("fashion_mnist", "cifar10")


# --------------------------------------------------------------------------- grids
def grid_hparams(a):
    for ds, lr, ep in itertools.product(a.datasets, a.lrs, a.epochs_list):
        yield f"{ds}_lr{lr}_ep{ep}", {
            "dataset": ds, "partitioning": "iid", "learning-rate": lr, "local-epochs": ep,
        }


def grid_noniid(a):
    for ds in a.datasets:
        lr, ep = pick_hparams(ds, a)
        base = {"dataset": ds, "learning-rate": lr, "local-epochs": ep}
        yield f"{ds}_iid", {**base, "partitioning": "iid"}
        for alpha in a.alphas:
            yield f"{ds}_dir{alpha}", {**base, "partitioning": "dirichlet", "dirichlet-alpha": alpha}
        yield f"{ds}_patho2", {**base, "partitioning": "pathological", "classes-per-partition": 2}


def grid_fedprox(a):
    for ds, mu in itertools.product(a.datasets, a.mus):
        lr, ep = pick_hparams(ds, a)
        yield f"{ds}_dir{a.prox_alpha}_mu{mu}", {
            "dataset": ds, "learning-rate": lr, "local-epochs": ep,
            "partitioning": "dirichlet", "dirichlet-alpha": a.prox_alpha, "proximal-mu": mu,
        }


def grid_participation(a):
    for ds in a.datasets:
        lr, ep = pick_hparams(ds, a)
        base = {
            "dataset": ds, "learning-rate": lr, "local-epochs": ep,
            "partitioning": "dirichlet", "dirichlet-alpha": a.participation_alpha,
        }
        for frac in a.fractions:
            yield f"{ds}_frac{frac}", {**base, "fraction-train": frac}
        for drop in a.dropouts:
            yield f"{ds}_drop{drop}", {**base, "dropout-rate": drop}


def grid_commcomp(a):
    """Same compute budget (rounds x local epochs), fewer or more communication rounds."""
    for ds in a.datasets:
        lr, _ = pick_hparams(ds, a)
        for part in a.commcomp_partitionings:
            base = {"dataset": ds, "learning-rate": lr, "partitioning": part}
            if part == "dirichlet":
                base["dirichlet-alpha"] = a.participation_alpha
            for rounds, ep in a.rounds_epochs:
                yield f"{ds}_{part}_r{rounds}_ep{ep}", {
                    **base, "num-server-rounds": rounds, "local-epochs": ep,
                }


def grid_deadline(a):
    """Step 3 (scenario B): local epochs under a simulated round deadline (sim-deadline)."""
    for ds in a.datasets:
        lr, _ = pick_hparams(ds, a)
        base = {"dataset": ds, "learning-rate": lr, "partitioning": "dirichlet",
                "dirichlet-alpha": a.participation_alpha}
        for deadline in a.deadlines:
            for ep in a.deadline_epochs:
                yield f"{ds}_dl{deadline}_ep{ep}", {
                    **base, "sim-deadline": deadline, "local-epochs": ep,
                }


GRIDS = {
    "hparams": grid_hparams,
    "noniid": grid_noniid,
    "fedprox": grid_fedprox,
    "participation": grid_participation,
    "commcomp": grid_commcomp,
    "deadline": grid_deadline,
}


_PICKED: dict = {}


def pick_hparams(dataset, a):
    """lr / epochs for phases 2-3: CLI values, else best result of phase 1, else defaults."""
    if dataset in _PICKED:
        return _PICKED[dataset]
    if a.lr is not None and a.local_epochs is not None:
        _PICKED[dataset] = (a.lr, a.local_epochs)
        return _PICKED[dataset]
    best = recommend(load_rows("hparams"), dataset, a.budget)
    lr = a.lr if a.lr is not None else (best["lr"] if best else 0.05)
    ep = a.local_epochs if a.local_epochs is not None else (best["epochs"] if best else 1)
    origin = "hparams phase" if best else "defaults"
    print(f"[{dataset}] lr={lr}, local-epochs={ep} ({origin})")
    _PICKED[dataset] = (lr, ep)
    return lr, ep


# --------------------------------------------------------------------------- runs
def run_config_string(cfg: dict) -> str:
    parts = []
    for k, v in cfg.items():
        parts.append(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}")
    return " ".join(parts)


def flwr_executable() -> str:
    bindir = Path(sys.executable).parent
    found = shutil.which("flwr", path=str(bindir)) or shutil.which("flwr")
    if not found:
        sys.exit("`flwr` command not found: run this script with `uv run python scripts/calibrate.py`.")
    return found


def configure_federation(num_clients: int, cpus: int) -> None:
    cmd = [
        flwr_executable(), "federation", "simulation-config", "@none/default", "local",
        "--num-supernodes", str(num_clients),
        "--client-resources-num-cpus", "1",
        "--init-args-num-cpus", str(cpus),
    ]
    print(f"Federation: {num_clients} simulated clients, {cpus} CPUs in total")
    subprocess.run(cmd, check=True, cwd=APP_DIR, stdout=subprocess.DEVNULL)


def run_one(phase: str, name: str, cfg: dict, a) -> dict | None:
    out_dir = RESULTS / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    result_file = out_dir / f"{name}.json"
    if result_file.exists() and json.loads(result_file.read_text()).get("finished"):
        print(f"  = {name} (already done)")
        return json.loads(result_file.read_text())

    full = {
        "num-server-rounds": a.rounds,     # a grid may override the number of rounds
        "batch-size": a.batch_size,
        **cfg,
        "results-file": str(result_file),
    }
    if a.data_dir:
        full["data-dir"] = a.data_dir
    cmd = [flwr_executable(), "run", str(APP_DIR), "--stream", "--run-config", run_config_string(full)]
    env = {**os.environ, "FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION": "1"}

    print(f"  > {name} ...", end="", flush=True)
    t0 = time.time()
    with open(out_dir / f"{name}.log", "w") as log:
        try:
            proc = subprocess.run(cmd, cwd=APP_DIR, env=env, stdout=log,
                                  stderr=subprocess.STDOUT, timeout=a.timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = "timeout"
    data = json.loads(result_file.read_text()) if result_file.exists() else None
    if code != 0 or not data or not data.get("finished"):
        print(f" FAILED ({code}), see {out_dir / (name + '.log')}")
        return None
    print(f" {time.time() - t0:.0f} s")
    return data


# --------------------------------------------------------------------------- analysis
def summarize(name: str, data: dict) -> dict:
    cfg = data["config"]
    rounds = sorted(data["rounds"], key=lambda r: r["round"])
    accs = [r["accuracy"] for r in rounds]
    times = [r["time"] for r in rounds]
    durations = [b - a for a, b in zip(times, times[1:])] or [0.0]
    # Round 1 includes the warm-up (Ray workers, imports, data loading): reported apart.
    steady = sorted(durations[1:]) or durations
    sec_per_round = steady[len(steady) // 2]
    return {
        "run": name,
        "dataset": cfg.get("dataset"),
        "partitioning": cfg.get("partitioning"),
        "alpha": cfg.get("dirichlet-alpha") if cfg.get("partitioning") == "dirichlet" else "",
        "lr": cfg.get("learning-rate"),
        "epochs": cfg.get("local-epochs"),
        "mu": cfg.get("proximal-mu", 0.0),
        "frac": cfg.get("fraction-train", 1.0),
        "drop": cfg.get("dropout-rate", 0.0),
        "failed": sum(r.get("clients_failed", 0) or 0 for r in rounds),
        "rounds": len(accs) - 1,
        "acc_r1": round(accs[1], 4) if len(accs) > 1 else None,
        "acc_r5": round(accs[min(5, len(accs) - 1)], 4),
        "acc_final": round(accs[-1], 4),
        "acc_best": round(max(accs), 4),
        "sec_per_round": round(sec_per_round, 1),
        "warmup_s": round(durations[0], 1),
        "total_s": round(times[-1] - data["started_at"], 1),
        "curve": accs,
    }


def load_rows(phase: str) -> list[dict]:
    rows = []
    for f in sorted((RESULTS / phase).glob("*.json")):
        data = json.loads(f.read_text())
        if data.get("finished"):
            rows.append(summarize(f.stem, data))
    return rows


def recommend(rows, dataset, budget):
    """Best final accuracy among the runs of `dataset` that fit the time budget."""
    ok = [r for r in rows if r["dataset"] == dataset and r["sec_per_round"] <= budget]
    return max(ok, key=lambda r: r["acc_final"]) if ok else None


COLS = ("run", "lr", "epochs", "alpha", "mu", "frac", "drop", "failed", "acc_r1", "acc_r5",
        "acc_final", "sec_per_round", "warmup_s", "total_s")


def report(phase: str, rows: list[dict], budget: float) -> None:
    if not rows:
        print("No results.")
        return
    out_dir = RESULTS / phase
    with open(out_dir / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if k != "curve"])
        w.writeheader()
        w.writerows({k: v for k, v in r.items() if k != "curve"} for r in rows)

    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in COLS}
    print()
    print("  ".join(c.ljust(widths[c]) for c in COLS))
    for r in rows:
        flag = "" if r["sec_per_round"] <= budget else "  <- too slow"
        print("  ".join(str(r[c]).ljust(widths[c]) for c in COLS) + flag)

    if phase.startswith("hparams"):
        for ds in sorted({r["dataset"] for r in rows}):
            best = recommend(rows, ds, budget)
            if best:
                print(f"\nRecommended for {ds}: lr={best['lr']}, local-epochs={best['epochs']} "
                      f"({best['acc_final']:.1%} in {best['rounds']} rounds, "
                      f"{best['sec_per_round']} s/round)")
    plot(phase, rows)
    print(f"\nResults: {out_dir / 'summary.csv'}")


def plot(phase: str, rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MaxNLocator
    except ImportError:
        print("(matplotlib missing: no figure)")
        return
    datasets = sorted({r["dataset"] for r in rows})
    fig, axes = plt.subplots(1, len(datasets), figsize=(6.5 * len(datasets), 4.5), squeeze=False)
    for ax, ds in zip(axes[0], datasets):
        for r in (r for r in rows if r["dataset"] == ds):
            label = r["run"].removeprefix(f"{ds}_")
            ax.plot(range(len(r["curve"])), r["curve"], marker="o", markersize=3, label=label)
        ax.set_title(ds)
        ax.set_xlabel("round")
        ax.set_ylabel("global accuracy (test)")
        ax.set_ylim(0, 1)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle(f"Calibration — phase {phase}")
    fig.tight_layout()
    path = RESULTS / phase / "curves.png"
    fig.savefig(path, dpi=120)
    print(f"Curves: {path}")


# --------------------------------------------------------------------------- main
def floats(s):
    return [float(x) for x in s.split(",")]


def pairs(s):
    return [tuple(int(x) for x in p.split("x")) for p in s.split(",")]


def ints(s):
    return [int(x) for x in s.split(",")]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--phase", choices=GRIDS, required=True)
    p.add_argument("--dataset", choices=[*DATASETS, "all"], default="all")
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--num-clients", type=int, default=5)
    p.add_argument("--cpus", type=int, default=5, help="CPUs given to Ray (match the hub)")
    p.add_argument("--budget", type=float, default=30.0, help="max seconds per round")
    p.add_argument("--timeout", type=int, default=1800, help="max seconds per simulation")
    p.add_argument("--data-dir", default="")
    # phase hparams
    p.add_argument("--lrs", type=floats, default=[0.01, 0.03, 0.1])
    p.add_argument("--epochs-list", type=ints, default=[1, 2])
    # phases noniid / fedprox
    p.add_argument("--lr", type=float, default=None, help="default: best of the hparams phase")
    p.add_argument("--local-epochs", type=int, default=None)
    p.add_argument("--alphas", type=floats, default=[1.0, 0.3, 0.1])
    p.add_argument("--prox-alpha", type=float, default=0.1)
    p.add_argument("--mus", type=floats, default=[0.0, 0.01, 0.1, 1.0])
    # phase participation
    p.add_argument("--participation-alpha", type=float, default=0.1)
    p.add_argument("--fractions", type=floats, default=[1.0, 0.6, 0.4, 0.2])
    p.add_argument("--dropouts", type=floats, default=[0.2, 0.5])
    # phase commcomp
    p.add_argument("--rounds-epochs", type=pairs, default=[(20, 1), (10, 2), (5, 4), (2, 10)],
                   help="rounds x local epochs pairs, e.g. 20x1,10x2,5x4")
    p.add_argument("--commcomp-partitionings", type=lambda s: s.split(","),
                   default=["iid", "dirichlet"])
    # phase deadline
    p.add_argument("--deadlines", type=floats, default=[10.0],
                   help="simulated round deadlines in seconds (5,000 images/s per client)")
    p.add_argument("--deadline-epochs", type=ints, default=[1, 2, 5, 10])
    p.add_argument("--report-only", action="store_true", help="run nothing, print the report again")
    p.add_argument("--tag", default="", help="separate subfolder: results/calibration/<phase>-<tag>")
    a = p.parse_args()
    a.datasets = list(DATASETS) if a.dataset == "all" else [a.dataset]
    folder = f"{a.phase}-{a.tag}" if a.tag else a.phase

    if not a.report_only:
        configure_federation(a.num_clients, a.cpus)
        runs = list(GRIDS[a.phase](a))
        print(f"Phase {a.phase}: {len(runs)} simulations of {a.rounds} rounds")
        for name, cfg in runs:
            run_one(folder, name, cfg, a)

    report(folder, load_rows(folder), a.budget)


if __name__ == "__main__":
    main()
