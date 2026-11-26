"""Download a dataset once and save it locally for offline use.

Run from the repository root, on a machine with access to Hugging Face:

    uv run python scripts/prepare_data.py                      # CIFAR-10 and Fashion-MNIST
    uv run python scripts/prepare_data.py --dataset cifar10
    uv run python scripts/prepare_data.py --data-dir /srv/fl-workshop/data

Each dataset is saved to a single file `<data-dir>/<name>.pt` holding uint8 tensors
(N×C×H×W images and labels). The Flower app then reads these files without ever
contacting Hugging Face; partitioning (IID, Dirichlet...) is computed at launch, from the
labels only.
"""

import argparse
import hashlib
from pathlib import Path

import numpy as np
import torch

DATASETS = {
    # local name -> Hugging Face id
    "cifar10": "uoft-cs/cifar10",
    "fashion_mnist": "zalando-datasets/fashion_mnist",
}

DEFAULT_DATA_DIR = Path.home() / ".cache" / "fl-workshop"


def _image_column(split) -> str:
    """Return the name of the column holding images (differs between datasets)."""
    for name, feature in split.features.items():
        if type(feature).__name__ == "Image":
            return name
    raise ValueError(f"No image column found in {list(split.features)}")


def _to_uint8(split) -> tuple[torch.Tensor, torch.Tensor]:
    col = _image_column(split)
    images = np.stack([np.asarray(img, dtype=np.uint8) for img in split[col]])
    if images.ndim == 3:  # grayscale: N×H×W -> N×1×H×W
        images = images[:, None, :, :]
    else:  # RGB: N×H×W×C -> N×C×H×W
        images = images.transpose(0, 3, 1, 2)
    labels = np.asarray(split["label"], dtype=np.int64)
    return torch.from_numpy(np.ascontiguousarray(images)), torch.from_numpy(labels)


def prepare(name: str, data_dir: Path) -> Path:
    from datasets import load_dataset  # imported here: only this script needs the Hub

    out = data_dir / f"{name}.pt"
    if out.exists():
        print(f"[{name}] already present: {out}")
        return out

    print(f"[{name}] downloading {DATASETS[name]} ...")
    ds = load_dataset(DATASETS[name])
    train_x, train_y = _to_uint8(ds["train"])
    test_x, test_y = _to_uint8(ds["test"])
    classes = ds["train"].features["label"].names

    data_dir.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    torch.save(
        {
            "name": name,
            "source": DATASETS[name],
            "classes": classes,
            "train_x": train_x,
            "train_y": train_y,
            "test_x": test_x,
            "test_y": test_y,
        },
        tmp,
    )
    tmp.rename(out)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    size_mb = out.stat().st_size / 1e6
    print(
        f"[{name}] saved {out} ({size_mb:.0f} MB, sha256 {digest}) | "
        f"train {tuple(train_x.shape)} | test {tuple(test_x.shape)} | {len(classes)} classes"
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", choices=[*DATASETS, "all"], default="all")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args()

    names = list(DATASETS) if args.dataset == "all" else [args.dataset]
    for name in names:
        prepare(name, args.data_dir.expanduser())


if __name__ == "__main__":
    main()
