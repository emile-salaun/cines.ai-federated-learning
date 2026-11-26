# app: the Flower app of the hands-on

Derived from Flower's official `quickstart-pytorch` example at Flower 1.39.0 (tag
`framework-1.39.0`). Simple CNN, FedAvg, offline local data, IID or non-IID partitioning
set by configuration. The same app runs in deployed mode (main path) and in the
Simulation Engine (fallback); only the launch differs.

All commands below run from the **repository root**.

## Pinned versions

| Component | Version |
|---|---|
| Python | 3.12 (`app/.python-version`) |
| flwr[simulation] | 1.39.x (exact version via `app/uv.lock`) |
| ray | 2.55.1 (pinned by Flower) |
| flwr-datasets[vision] | 0.6.1 |
| torch / torchvision | 2.14.1 / 0.29.1, CPU |

## Install

```bash
uv sync --project app                    # app only
uv sync --project app --group notebook   # + JupyterLab and matplotlib
```

## Prepare the data (once, with access to Hugging Face)

```bash
uv run --project app python scripts/prepare_data.py                           # CIFAR-10 + Fashion-MNIST
uv run --project app python scripts/prepare_data.py --data-dir /path/to/shared # elsewhere than ~/.cache/fl-workshop
```

Each dataset becomes one file `<data-dir>/<name>.pt` (uint8 tensors): about 185 MB for
CIFAR-10 and 55 MB for Fashion-MNIST. After that, nothing contacts Hugging Face: the app
forces `HF_HUB_OFFLINE=1`. For a hub or a training room, prepare the files once and copy
the folder to each machine (or share it read-only).

## Run a simulation (fallback path)

Linux / macOS:

```bash
# 1. Do not reinstall the dependencies at every run (see below)
export FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION=1

# 2. Number of simulated clients and Ray CPU cap (once)
#    Without a cap, Ray takes every core of the machine.
uv run --project app flwr federation simulation-config @none/default local \
  --num-supernodes 5 --client-resources-num-cpus 1 --init-args-num-cpus 5

# 3. Run
uv run --project app flwr run app --stream
uv run --project app flwr run app --stream --run-config "partitioning='dirichlet' dirichlet-alpha=0.1"
```

Windows PowerShell:

```powershell
$env:FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION = "1"
uv run --project app flwr federation simulation-config "@none/default" local `
  --num-supernodes 5 --client-resources-num-cpus 1 --init-args-num-cpus 5
uv run --project app flwr run app --stream --run-config "partitioning='dirichlet' dirichlet-alpha=0.1"
```

String values in `--run-config` take single quotes. Exercises change only the run
config, never the code.

The deployed mode (one SuperLink per group, one SuperNode per member) is documented
with the lead and member notebooks (not written yet).

## Configuration (`[tool.flwr.app.config]`, overridable with `--run-config`)

| Key | Default | Role |
|---|---|---|
| `num-server-rounds` | 10 | Number of federated rounds |
| `local-epochs` | 2 | Local epochs per round |
| `learning-rate` | 0.01 | Client SGD learning rate (0.1 diverges) |
| `batch-size` | 32 | Batch size |
| `fraction-train` | 1.0 | Share of clients sampled for training in each round |
| `fraction-evaluate` | 1.0 | Share of clients asked to evaluate |
| `dropout-rate` | 0.0 | Probability that a sampled client "disconnects" during a round |
| `proximal-mu` | 0.0 | > 0 enables the FedProx proximal term |
| `dataset` | `fashion_mnist` | `fashion_mnist` or `cifar10` |
| `partitioning` | `iid` | `iid`, `dirichlet` or `pathological` |
| `dirichlet-alpha` | 0.1 | Smaller = more unbalanced (0.1: very non-IID) |
| `classes-per-partition` | 2 | Classes per client with `pathological` |
| `seed` | 42 | Seed of the partitioning, the initial model and training (reproducible runs) |
| `data-dir` | `""` | Folder of the `.pt` files; empty = `~/.cache/fl-workshop` |
| `results-file` | `""` | Absolute path of a per-round results JSON; empty = disabled |

## See what each client receives

```bash
uv run --project app python scripts/show_partitions.py
uv run --project app python scripts/show_partitions.py --partitioning dirichlet --alpha 0.1
uv run --project app python scripts/show_partitions.py --partitioning pathological --classes-per-partition 2
```

The script uses the same code as the app: the table is exactly the class split between
the simulated clients.

## Calibration

`scripts/calibrate.py` chains simulations, stores results in
`results/calibration/<phase>/` (one JSON and one log per run) and produces a table
(`summary.csv`) and curves (`curves.png`). Finished runs are skipped: you can interrupt
and restart. The committed results are in `references/calibration/`.

```bash
uv run --project app python scripts/calibrate.py --phase hparams        # lr x local epochs, IID, 10 rounds
uv run --project app python scripts/calibrate.py --phase noniid         # IID, Dirichlet 1.0 / 0.3 / 0.1, pathological
uv run --project app python scripts/calibrate.py --phase fedprox        # Dirichlet 0.1 with mu = 0, 0.01, 0.1, 1
uv run --project app python scripts/calibrate.py --phase participation  # fraction-train and dropout-rate, Dirichlet 0.1
uv run --project app python scripts/calibrate.py --phase commcomp       # rounds x local epochs at equal budget, IID and Dirichlet 0.1
uv run --project app python scripts/calibrate.py --phase noniid --report-only   # print again without running
```

The `noniid` and `fedprox` phases reuse the best (lr, epochs) pair of the `hparams` phase
that fits the budget (`--budget`, 30 s per round by default). `--cpus` (5 by default)
sets the CPUs given to Ray: match what a participant will have, so the measured times
are representative.

Table columns: `acc_r1` / `acc_r5` / `acc_final` (global test accuracy after round 1, 5
and the last one), `sec_per_round` (median, first round excluded), `warmup_s` (first
round, which includes Ray start-up and data loading), `total_s` (total run time).

On a shared compute node, run the calibration inside an allocation rather than on a
login node, for example `srun -c 8 --time 02:00:00 uv run --project app python scripts/calibrate.py ...`.

## Pitfalls (Flower 1.39)

- **`flwr new` is no longer offline.** The command downloads apps from Flower Hub
  (`api.flower.ai`). This project was taken from Flower's GitHub repository instead.
- **Dependency reinstall at every run.** By default, each `flwr run` recreates an
  environment under `~/.flwr/runtime-envs/` and reinstalls all dependencies of
  `pyproject.toml` with `uv sync`. Offline, or without the uv cache, this fails or
  downloads several GB. `FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION=1` runs the app
  directly in the project's `.venv`. The variable must be set when the local SuperLink
  starts (at the first `flwr run`, in the background): it then keeps the environment it
  started with. If the log shows `uv sync took ...`, stop the SuperLink
  (`pkill -u $USER -f flower-superlink`), export the variable, run again.
- **`flwr` must be declared with `>=`.** Flower refuses `==` on its own dependency
  (`fab-format-version = 1`). The exact version is guaranteed by `uv.lock`.
- **Number of simulated clients.** It is no longer set in `pyproject.toml` but on the
  local SuperLink (command above).
- **Data path.** The app runs from an installed copy in `~/.flwr/apps/`, not from this
  folder: a relative path such as `data/` would not work. Hence an absolute default
  folder (`~/.cache/fl-workshop`).

## Structure

```
app/
├── flworkshop/
│   ├── client_app.py        # ClientApp: training and evaluation on local data
│   ├── server_app.py        # ServerApp: FedAvg, global evaluation, per-client and per-message tracking
│   ├── data.py              # Offline loading and partitioning (flwr-datasets)
│   ├── task.py              # Model, train (optional FedProx) and test
│   ├── baselines.py         # "Solo" and "centralised" references
│   ├── dashboard_server.py  # Local HTTP server of the dashboard (files + JSON API)
│   ├── paths.py             # Where dashboard/, references/ and results/ live
│   └── viz.py               # Launch runs from the notebook, links to the dashboard
├── pyproject.toml           # Dependencies, app configuration, CPU PyTorch index
├── uv.lock
└── .python-version
```

`paths.py` locates the repository root as the parent of `app/`; set `FL_WORKSHOP_ROOT`
to use another root.

## "Solo" and "centralised" references

To show what FL brings, each federated run is compared with two references computed
with exactly the same data, initial model, seeds and budget (rounds x local epochs):

- **solo**: each client trains its own model on its own data, exchanging nothing (a
  one-client federated run, without averaging);
- **centralised**: one model trained on the union of the clients' data, the upper bound
  that FL tries to approach without gathering the data.

They are **precomputed once** and shipped in `references/`: participants do not
recompute them. It takes a few CPU minutes per configuration:

```bash
uv run --project app python scripts/compute_baselines.py                 # Fashion-MNIST: pathological, Dirichlet 0.1, IID
uv run --project app python scripts/compute_baselines.py --dataset all   # + CIFAR-10
sbatch scripts/compute_baselines.slurm                                   # on Adastra (replace <project>)
```

A reference is used only if its configuration matches the run exactly (dataset,
partitioning, rounds, epochs, learning rate, batch, seed, number of clients). After a
change of the defaults in `pyproject.toml`, recompute it (`--force`).

## Notebook and dashboard

```bash
uv sync --project app --group notebook
uv run --project app jupyter lab notebooks/simulation.ipynb
```

The notebook launches the experiments; the results show up in a **web dashboard**,
opened in a tab next to it and updated every round. `viz.setup()` starts its server (on
`127.0.0.1:8050`, or the next free port) and prints the link.

| Tab | Content |
|---|---|
| Solo or together? | Federated model versus the "solo" and "centralised" references: curves, classes recognised by each model, each client's data |
| The run | Local models in each round, participation (sampled, disconnected), drift, per-class accuracy |
| Network | One round replayed as an animation: server ↔ client messages, real timeline, volumes exchanged versus data kept |
| Compare | Several runs overlaid and a summary table |

| Function | Role |
|---|---|
| `viz.setup(num_clients=5, cpus=2)` | Environment variables, simulated federation, data check, dashboard start; restarts a local SuperLink started without the right variables |
| `viz.run(name, run_config="", view="together")` | Prints and launches `flwr run app --stream --run-config "<run_config>"`, shows its progress, with a link to the `view` tab (`together`, `run`, `network`, `compare`) |
| `viz.command(run_config)` | The `flwr run` command for a run config, without launching it |
| `viz.open(name, view=...)` | Link to a run and a dashboard tab |
| `viz.log(name)` | Key lines of the Flower log |
| `viz.stop()` | Stops the run in progress |
| `viz.show(name)`, `viz.compare(*names)`, `viz.partitions(**config)` | matplotlib figures, outside the browser (not in the hands-on path) |

The run config is written as in a terminal, e.g.
`viz.run("dirichlet", "partitioning='dirichlet' dirichlet-alpha=0.1")`; keyword arguments
with underscores (`fraction_train=0.4`) are still accepted and appended. Results and logs: `results/notebook/<name>.json` and `.log`. `setup()`
also sets `OMP_NUM_THREADS=1`: one thread per process, to share the machine.

**Dashboard access.** The server only listens on the local machine:
- notebook on your own computer: the `http://localhost:8050/` link opens directly;
- JupyterHub: the link goes through `jupyter-server-proxy` (`…/user/<name>/proxy/8050/`),
  to install on the hub;
- Google Colab: `viz.open()` goes through Colab's proxy;
- remote JupyterLab over an SSH tunnel: add `-L 8050:localhost:8050` to the tunnel.

**What the Network tab shows.** The server receives a round's replies as one batch; the
timeline is rebuilt after each round from the message timestamps (`created_at`), then
replayed faster (3.5 to 7 s). In deployed mode, these timestamps come from the client
machines' clocks: they must be synchronised (NTP).

**Where the per-client data come from.** Each client attaches to its replies its
partition id, training time and host name (a `ConfigRecord`, which FedAvg does not
aggregate); the server evaluates each received local model on 2,000 test images before
aggregation and records the size and timestamp of each message. Aggregation itself is
unchanged, and everything works the same way in deployed mode.
