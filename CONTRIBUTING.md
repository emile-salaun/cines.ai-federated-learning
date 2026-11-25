# Contributing (trainers and maintainers)

Participant instructions live on the site and in `README.md`. This page covers how the
material is built and maintained.

## Rules

- All content in English (site, notebooks, code comments, slides).
- Exercises vary through `--run-config` only, never through code edits.
- Frozen stack: Python 3.12, `flwr[simulation]` 1.39.x, CPU torch/torchvision, uv with
  the committed `app/uv.lock`. Flag any change.
- Never commit secrets or infrastructure details: no tokens, passwords, keys,
  certificates or NVFLARE startup kits; no real hostnames, IPs, logins or SLURM
  accounts (use `<vm-host>`, `<login>`, `<project>`); no datasets, weights, results,
  `.venv` or `site/`. Strip notebook outputs before committing.

## Layout

| Path | Content |
|---|---|
| `app/` | Flower app, a uv project (`pyproject.toml`, `uv.lock`, `LICENSE` copy required by Flower, `flworkshop/`). Details: [`app/README.md`](app/README.md) |
| `notebooks/` | `simulation.ipynb` (fallback); lead and member notebooks to come |
| `dashboard/` | Web dashboard served by `flworkshop/dashboard_server.py` |
| `scripts/` | `prepare_data.py`, `show_partitions.py`, `calibrate.py`, `compute_baselines.py`, `compute_baselines.slurm` |
| `references/` | `calibration/` results; solo/centralised baselines to come |
| `demo-nvflare/` | Description of the NVIDIA FLARE demo across two HPC centres; the demo code lives in a separate private repository |
| `infra/` | JupyterHub (TLJH) setup (to come) |
| `slides/` | Talk slides (Marp: `talk.md`, `themes/cines.css`, `widgets.js`, `images/`) |
| `docs/`, `includes/`, `zensical.toml` | Workshop site (Zensical, classic variant) |
| `.github/workflows/docs.yml` | Builds the site and the slides, deploys GitHub Pages |

## App, data and scripts

All commands run from the repository root.

```bash
uv sync --project app --group notebook
uv run --project app python scripts/prepare_data.py              # once, needs Hugging Face access
uv run --project app flwr run app --stream --run-config "partitioning='dirichlet'"
```

Calibration, the solo/centralised references (`scripts/compute_baselines.py`, or
`sbatch scripts/compute_baselines.slurm` on Adastra after replacing `<project>` locally)
and the Flower 1.39 pitfalls are documented in [`app/README.md`](app/README.md).

## Website

```bash
pip install -r requirements-docs.txt
zensical serve                       # http://127.0.0.1:8000
zensical build --clean --strict      # what CI runs
```

`docs/assets/javascripts/groups.js` holds the groups and SuperLink addresses: fill it in
on the day only, not in a committed change with real hosts.

## Slides

The CI renders `slides/talk.md` with Marp CLI 4.5.1 into `site/slides/index.html` and
`site/slides/talk.pdf`. Local preview:

```bash
npx --yes @marp-team/marp-cli@4.5.1 --html --theme-set slides/themes -s slides/
```

## Deployment

Pushes to `main` that touch `docs/`, `includes/`, `slides/`, `zensical.toml`,
`requirements-docs.txt` or the workflow build and deploy the site (Settings > Pages >
Source: GitHub Actions). Pull requests only build.
