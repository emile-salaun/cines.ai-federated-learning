# Federated Learning Workshop (CINES)

Train a model across several machines without moving the data. This repository holds
the hands-on material of the workshop: a Flower app, the notebooks and a live dashboard.

**Workshop site (start here):** https://emile-salaun.github.io/cines.ai-federated-learning/

## During the workshop

You do not need to install anything. Follow the **Hands-on** section of the site: your
trainers give you the hub address and your group number on the day.

## Run the hands-on on your own computer

This runs the simulation version (5 virtual clients in one notebook). It needs about
4.5 GB of RAM, 2 CPU cores and internet access for steps 1 to 3.

**1. Install uv** (Python package manager)

Linux / macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

You should see: `uv --version` prints a version number (open a new terminal first).

**2. Get the code and install it**

Linux / macOS and Windows PowerShell:

```bash
git clone https://github.com/emile-salaun/cines.ai-federated-learning.git
cd cines.ai-federated-learning
uv sync --project app --group notebook
```

You should see: uv installs Python 3.12 if needed, then the packages, and ends without
an error.

**3. Download the data (once)**

Linux / macOS and Windows PowerShell:

```bash
uv run --project app python scripts/prepare_data.py --dataset fashion_mnist
```

You should see: a line starting with `[fashion_mnist] saved`. From now on, everything
runs offline.

**4. Open the notebook**

Linux / macOS and Windows PowerShell:

```bash
uv run --project app jupyter lab notebooks/simulation.ipynb
```

You should see: JupyterLab opens in your browser on `simulation.ipynb`. Run the first
cell: it prints `Simulated federation: 5 clients` and a link to open the dashboard.

Then follow the notebook, one cell at a time.

## What is in this repository

| Folder | Content |
|---|---|
| `app/` | The Flower app (model, clients, server) |
| `notebooks/` | Hands-on notebooks |
| `dashboard/` | The dashboard that shows each run live |
| `scripts/` | Data preparation and helper scripts |
| `references/` | Precomputed results used for comparison |
| `slides/` | Slides of the talk |

Trainers and contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache-2.0 (see `LICENSE`). The app is derived from Flower's `quickstart-pytorch` example.
