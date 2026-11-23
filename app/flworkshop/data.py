"""Offline data loading and federated partitioning.

The data comes from a local file produced by `scripts/prepare_data.py`. Nothing here
contacts Hugging Face: partitioning uses the flwr-datasets partitioners, applied to a
small dataset that holds only the labels.
"""

import os

# Make sure no Hugging Face library tries to contact the Hub.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")

import warnings  # noqa: E402
from functools import lru_cache  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402
from datasets import Dataset, disable_progress_bars  # noqa: E402
from flwr_datasets.partitioner import (  # noqa: E402
    DirichletPartitioner,
    IidPartitioner,
    PathologicalPartitioner,
)
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

disable_progress_bars()
# PathologicalPartitioner warns when some classes end up unused: expected, not an error.
warnings.filterwarnings("ignore", message="Classes: .* will NOT be used")

DEFAULT_DATA_DIR = Path.home() / ".cache" / "fl-workshop"
PARTITIONINGS = ("iid", "dirichlet", "pathological")


def resolve_data_dir(data_dir: str) -> Path:
    """Empty string -> default directory; otherwise the given path (``~`` expanded)."""
    return Path(data_dir).expanduser() if data_dir else DEFAULT_DATA_DIR


@lru_cache(maxsize=4)
def load_arrays(data_dir: str, dataset: str) -> dict:
    """Load the dataset file once per process.

    ``mmap=True`` keeps the tensors on disk and shares them through the page cache, so
    several simulated clients on the same machine do not each hold a full copy.
    """
    path = resolve_data_dir(data_dir) / f"{dataset}.pt"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run first: "
            f"uv run --project app python scripts/prepare_data.py --dataset {dataset}"
        )
    return torch.load(path, mmap=True, weights_only=True)


@lru_cache(maxsize=16)
def partition_indices(
    data_dir: str,
    dataset: str,
    partitioning: str,
    num_partitions: int,
    alpha: float,
    classes_per_partition: int,
    seed: int,
) -> tuple[np.ndarray, ...]:
    """Return, for each partition, the indices of its training samples.

    The computation is deterministic (fixed seed): every simulated client, and every
    participant, gets exactly the same split.
    """
    labels = load_arrays(data_dir, dataset)["train_y"].numpy()
    ds = Dataset.from_dict({"label": labels, "idx": np.arange(len(labels))})

    if partitioning == "iid":
        # IidPartitioner cuts contiguous shards: shuffle first to make them random.
        ds = ds.shuffle(seed=seed)
        partitioner = IidPartitioner(num_partitions=num_partitions)
    elif partitioning == "dirichlet":
        partitioner = DirichletPartitioner(
            num_partitions=num_partitions,
            partition_by="label",
            alpha=alpha,
            min_partition_size=10,
            self_balancing=False,
            seed=seed,
        )
    elif partitioning == "pathological":
        partitioner = PathologicalPartitioner(
            num_partitions=num_partitions,
            partition_by="label",
            num_classes_per_partition=classes_per_partition,
            class_assignment_mode="first-deterministic",
            seed=seed,
        )
    else:
        raise ValueError(f"partitioning={partitioning!r}; allowed values: {PARTITIONINGS}")

    partitioner.dataset = ds
    return tuple(
        np.asarray(partitioner.load_partition(i)["idx"], dtype=np.int64)
        for i in range(num_partitions)
    )


def _cfg(run_config) -> dict:
    """Extract the data-related keys from the run config."""
    return {
        "data_dir": str(run_config.get("data-dir", "")),
        "dataset": str(run_config.get("dataset", "fashion_mnist")),
        "partitioning": str(run_config.get("partitioning", "iid")),
        "alpha": float(run_config.get("dirichlet-alpha", 0.1)),
        "classes_per_partition": int(run_config.get("classes-per-partition", 2)),
        "seed": int(run_config.get("seed", 42)),
    }


def load_partition(partition_id: int, num_partitions: int, run_config, batch_size: int):
    """Train and validation loaders (80/20) for one client."""
    c = _cfg(run_config)
    arrays = load_arrays(c["data_dir"], c["dataset"])
    idx = partition_indices(
        c["data_dir"],
        c["dataset"],
        c["partitioning"],
        num_partitions,
        c["alpha"],
        c["classes_per_partition"],
        c["seed"],
    )[partition_id]

    rng = np.random.default_rng(c["seed"] + partition_id)
    idx = rng.permutation(idx)
    n_val = max(1, int(0.2 * len(idx)))
    val_idx, train_idx = torch.from_numpy(idx[:n_val]), torch.from_numpy(idx[n_val:])

    x, y = arrays["train_x"], arrays["train_y"]
    trainloader = DataLoader(
        TensorDataset(x[train_idx], y[train_idx]), batch_size=batch_size, shuffle=True
    )
    valloader = DataLoader(TensorDataset(x[val_idx], y[val_idx]), batch_size=batch_size)
    return trainloader, valloader


def load_test(run_config, batch_size: int = 256) -> DataLoader:
    """Centralized test set, used by the server for global evaluation."""
    c = _cfg(run_config)
    arrays = load_arrays(c["data_dir"], c["dataset"])
    return DataLoader(TensorDataset(arrays["test_x"], arrays["test_y"]), batch_size=batch_size)


def input_shape(run_config) -> tuple[int, int, int]:
    """(channels, height, width) of the images, to build the model."""
    c = _cfg(run_config)
    return tuple(load_arrays(c["data_dir"], c["dataset"])["train_x"].shape[1:])


def label_distribution(run_config, num_partitions: int) -> np.ndarray:
    """Matrix [partition, class] of sample counts (training part, before the 80/20 split)."""
    c = _cfg(run_config)
    labels = load_arrays(c["data_dir"], c["dataset"])["train_y"].numpy()
    idx = partition_indices(
        c["data_dir"],
        c["dataset"],
        c["partitioning"],
        num_partitions,
        c["alpha"],
        c["classes_per_partition"],
        c["seed"],
    )
    num_classes = int(labels.max()) + 1
    return np.stack([np.bincount(labels[i], minlength=num_classes) for i in idx])


def class_names(run_config) -> list[str]:
    c = _cfg(run_config)
    return list(load_arrays(c["data_dir"], c["dataset"])["classes"])


def load_test_subset(run_config, size: int = 2000, batch_size: int = 500) -> DataLoader:
    """Fixed, class-balanced-by-chance subset of the test set (first `size` images).

    Used by the server to evaluate each client's local model every round: small enough
    to stay cheap, large enough for a per-class accuracy (~200 images per class).
    """
    c = _cfg(run_config)
    arrays = load_arrays(c["data_dir"], c["dataset"])
    n = min(size, len(arrays["test_y"]))
    return DataLoader(
        TensorDataset(arrays["test_x"][:n], arrays["test_y"][:n]), batch_size=batch_size
    )
