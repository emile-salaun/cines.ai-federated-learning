# Federated Learning Workshop (CINES)

Material for a 2-hour federated learning workshop: 30 min talk, 15 min NVIDIA FLARE demo
on Adastra, 15 min break, 60 min hands-on with Flower in groups of 4–5.

Site: https://emile-salaun.github.io/cines.ai-federated-learning/

## Layout

| Folder | Content |
|---|---|
| `app/` | Flower app (uv project: `pyproject.toml`, `uv.lock`, `flworkshop/`) |
| `notebooks/` | Hands-on notebooks: `simulation.ipynb` (fallback); lead and member notebooks to come |
| `dashboard/` | Web dashboard opened next to the notebook (HTML/CSS/JS, no dependencies) |
| `scripts/` | Data preparation, partition viewer, calibration, reference computation (incl. SLURM job) |
| `references/` | Precomputed results: `calibration/` now, solo/centralised baselines later |
| `demo-nvflare/` | NVIDIA FLARE demo on Adastra (to come) |
| `infra/` | JupyterHub (TLJH) setup for the hands-on (to come) |
| `slides/` | Talk slides (to come) |
| `docs/`, `includes/`, `zensical.toml` | Workshop website (Zensical), deployed to GitHub Pages |

## Quick start (simulation, Linux / macOS)

```bash
uv sync --project app --group notebook
uv run --project app python scripts/prepare_data.py --dataset fashion_mnist   # needs internet, once
uv run --project app jupyter lab notebooks/simulation.ipynb
```

Windows PowerShell: same commands. Details and the command-line launch are in
[`app/README.md`](app/README.md).

## Website

```bash
pip install -r requirements-docs.txt
zensical serve                       # http://127.0.0.1:8000
zensical build --clean --strict      # what CI runs
```

Pushes to `main` that touch the site are built and deployed by
`.github/workflows/docs.yml`.

## License

Apache-2.0 (see `LICENSE`). The app is derived from Flower's `quickstart-pytorch` example.
