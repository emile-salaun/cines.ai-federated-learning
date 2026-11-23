"""Print the class distribution per client for a given partitioning.

    uv run --project app python scripts/show_partitions.py                               # IID, 5 clients
    uv run --project app python scripts/show_partitions.py --partitioning dirichlet --alpha 0.1
    uv run --project app python scripts/show_partitions.py --partitioning pathological --classes-per-partition 2

Uses exactly the same code as the Flower app: what is printed here is what each
simulated client receives.
"""

import argparse

from flworkshop.data import PARTITIONINGS, label_distribution, load_arrays


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dataset", default="fashion_mnist", choices=["fashion_mnist", "cifar10"])
    p.add_argument("--partitioning", default="iid", choices=PARTITIONINGS)
    p.add_argument("--num-partitions", type=int, default=5)
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--classes-per-partition", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--data-dir", default="")
    a = p.parse_args()

    run_config = {
        "data-dir": a.data_dir,
        "dataset": a.dataset,
        "partitioning": a.partitioning,
        "dirichlet-alpha": a.alpha,
        "classes-per-partition": a.classes_per_partition,
        "seed": a.seed,
    }
    counts = label_distribution(run_config, a.num_partitions)
    classes = load_arrays(a.data_dir, a.dataset)["classes"]

    width = max(len(c) for c in classes) + 2
    header = "client".ljust(8) + "".join(c[:width - 1].rjust(width) for c in classes) + "total".rjust(8)
    print(f"{a.dataset} | {a.partitioning}"
          + (f" (alpha={a.alpha})" if a.partitioning == "dirichlet" else "")
          + (f" ({a.classes_per_partition} classes/client)" if a.partitioning == "pathological" else ""))
    print(header)
    for i, row in enumerate(counts):
        print(str(i).ljust(8) + "".join(str(v).rjust(width) for v in row) + str(row.sum()).rjust(8))


if __name__ == "__main__":
    main()
