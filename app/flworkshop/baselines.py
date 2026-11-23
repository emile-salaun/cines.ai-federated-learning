""""Solo" and "centralised" references, to show what FL brings.

For a given configuration (dataset, partitioning, number of clients...), we train with
exactly the same budget as the federated run (rounds x local epochs), the same data, the
same initial model and the same seeds:

- **solo**: each client trains its own model on its own data only, never exchanging
  anything. It is a one-client federated run, without averaging.
- **centralised**: one model trained on the union of all clients' data, as if everything
  had been gathered in one place (what FL avoids).

Each model is evaluated after each "round" on the full test set, like the global model of
the federated run. Results go to references/<key>.json.
"""

import hashlib
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import torch
from torch.utils.data import ConcatDataset, DataLoader

from flworkshop.paths import APP_DIR, REFERENCES_DIR

# Configuration keys that change the result of a reference run.
KEYS = ("dataset", "partitioning", "dirichlet-alpha", "classes-per-partition",
        "num-server-rounds", "local-epochs", "learning-rate", "batch-size", "seed")
DEFAULTS = {
    "dataset": "fashion_mnist", "partitioning": "iid", "dirichlet-alpha": 0.1,
    "classes-per-partition": 2, "num-server-rounds": 10, "local-epochs": 2,
    "learning-rate": 0.01, "batch-size": 32, "seed": 42,
}
CENTRALIZED = -1  # task id of the centralized run


FLOATS = {"dirichlet-alpha", "learning-rate"}
INTS = {"classes-per-partition", "num-server-rounds", "local-epochs", "batch-size", "seed"}


def app_defaults() -> dict:
    """The app's default configuration ([tool.flwr.app.config] in pyproject.toml)."""
    import tomllib

    try:
        data = tomllib.loads((APP_DIR / "pyproject.toml").read_text())
        return {**DEFAULTS, **data["tool"]["flwr"]["app"]["config"]}
    except (OSError, KeyError):
        return dict(DEFAULTS)


def normalize(config: dict, num_clients: int) -> dict:
    """Keep only what matters for the result, with stable types (1 and 1.0 match)."""
    base = app_defaults()
    cfg = {k: config.get(k, base[k]) for k in KEYS}
    for k in FLOATS:
        cfg[k] = float(cfg[k])
    for k in INTS:
        cfg[k] = int(cfg[k])
    if cfg["partitioning"] != "dirichlet":
        cfg.pop("dirichlet-alpha")
    if cfg["partitioning"] != "pathological":
        cfg.pop("classes-per-partition")
    cfg["num-clients"] = num_clients
    return cfg


def key(config: dict, num_clients: int) -> str:
    """Readable, stable file name for a configuration."""
    cfg = normalize(config, num_clients)
    part = cfg["partitioning"]
    if part == "dirichlet":
        part += f"{cfg['dirichlet-alpha']}"
    elif part == "pathological":
        part += f"{cfg['classes-per-partition']}"
    digest = hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8]
    return f"{cfg['dataset']}_{part}_{num_clients}clients_{digest}"


def path_for(config: dict, num_clients: int) -> Path:
    return REFERENCES_DIR / f"{key(config, num_clients)}.json"


def load(config: dict, num_clients: int) -> dict | None:
    path = path_for(config, num_clients)
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _train_task(args) -> dict:
    """Train one model (one client alone, or the centralized model) and evaluate it."""
    task_id, cfg, num_clients, threads = args
    torch.set_num_threads(threads)
    from flworkshop.data import class_names, input_shape, load_partition, load_test
    from flworkshop.task import build_model, test_per_class, train

    seed = int(cfg["seed"])
    batch = int(cfg["batch-size"])
    if task_id == CENTRALIZED:
        parts = [load_partition(p, num_clients, cfg, batch)[0].dataset
                 for p in range(num_clients)]
        trainloader = DataLoader(ConcatDataset(parts), batch_size=batch, shuffle=True)
        seed_offset = 999
    else:
        trainloader = load_partition(task_id, num_clients, cfg, batch)[0]
        seed_offset = task_id

    testloader = load_test(cfg)
    num_classes = len(class_names(cfg))
    torch.manual_seed(seed)            # same initial model as the federated run
    model = build_model(input_shape(cfg))

    def evaluate(rnd: int) -> dict:
        loss, acc, per_class = test_per_class(model, testloader, torch.device("cpu"),
                                              num_classes)
        return {"round": rnd, "accuracy": acc, "loss": loss, "per_class": per_class}

    rounds = [evaluate(0)]
    start = time.time()
    for rnd in range(1, int(cfg["num-server-rounds"]) + 1):
        # Same seed formula as the ClientApp: the client "alone" sees the same batches
        # as in a federated round; only the averaging is missing.
        torch.manual_seed(seed * 100_000 + rnd * 1_000 + seed_offset)
        train(model, trainloader, int(cfg["local-epochs"]), float(cfg["learning-rate"]),
              torch.device("cpu"))
        rounds.append(evaluate(rnd))
    return {"task": task_id, "num_examples": len(trainloader.dataset),
            "seconds": time.time() - start, "rounds": rounds}


def compute(config: dict, num_clients: int = 5, workers: int | None = None,
            threads: int = 1, force: bool = False) -> Path:
    """Compute the references of one configuration (clients in parallel processes)."""
    from flworkshop.data import class_names, label_distribution

    path = path_for(config, num_clients)
    if path.exists() and not force:
        print(f"= {path.name} (already computed)")
        return path
    cfg = {**app_defaults(), **{k: v for k, v in config.items() if k in KEYS}}
    cfg["data-dir"] = config.get("data-dir", "")
    tasks = [(t, cfg, num_clients, threads) for t in [CENTRALIZED, *range(num_clients)]]
    workers = workers or min(len(tasks), max(1, (os.cpu_count() or 1) // threads))
    print(f"> {path.name}: {len(tasks)} trainings, {workers} in parallel ...", flush=True)
    start = time.time()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_train_task, tasks))

    data = {
        "kind": "references",
        "config": normalize(config, num_clients),
        "classes": class_names(cfg),
        "label_counts": label_distribution(cfg, num_clients).tolist(),
        "centralized": next(r for r in results if r["task"] == CENTRALIZED),
        "alone": {str(r["task"]): r for r in results if r["task"] != CENTRALIZED},
        "computed_at": time.time(),
    }
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)
    alone = [r["rounds"][-1]["accuracy"] for r in data["alone"].values()]
    print(f"  centralised {data['centralized']['rounds'][-1]['accuracy']:.1%} · solo "
          f"{min(alone):.1%} to {max(alone):.1%} · {time.time() - start:.0f} s", flush=True)
    return path
