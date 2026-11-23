"""Precompute the "solo" and "centralised" references of the hands-on.

Run once, on a machine that has the data (see prepare_data.py); results go to
references/ and ship with the project. Participants do not recompute them: the dashboard
overlays them on their federated runs.

    uv run --project app python scripts/compute_baselines.py                    # default set (Fashion-MNIST)
    uv run --project app python scripts/compute_baselines.py --dataset all      # + CIFAR-10
    uv run --project app python scripts/compute_baselines.py --workers 6 --threads 2

On Adastra: sbatch scripts/compute_baselines.slurm (from the repository root)
"""

import argparse

from flworkshop.baselines import compute

# Configurations used in the notebook: the reference must match the run exactly
# (same partitioning, rounds, epochs, learning rate, seed, number of clients).
PRESETS = [
    {"partitioning": "pathological", "classes-per-partition": 2},
    {"partitioning": "dirichlet", "dirichlet-alpha": 0.1},
    {"partitioning": "iid"},
]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dataset", choices=["fashion_mnist", "cifar10", "all"],
                   default="fashion_mnist")
    p.add_argument("--num-clients", type=int, default=5)
    p.add_argument("--workers", type=int, default=None,
                   help="trainings in parallel (default: based on CPUs)")
    p.add_argument("--threads", type=int, default=1, help="PyTorch threads per training")
    p.add_argument("--force", action="store_true", help="recompute even if already present")
    p.add_argument("--data-dir", default="", help="data directory (default: ~/.cache/fl-workshop)")
    a = p.parse_args()

    datasets = ["fashion_mnist", "cifar10"] if a.dataset == "all" else [a.dataset]
    for dataset in datasets:
        for preset in PRESETS:
            compute({"dataset": dataset, "data-dir": a.data_dir, **preset}, a.num_clients,
                    a.workers, a.threads, a.force)


if __name__ == "__main__":
    main()
