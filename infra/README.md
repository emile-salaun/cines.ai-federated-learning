# infra

Central JupyterHub for the hands-on, scenario B: The Littlest JupyterHub (TLJH) on one
VM. Phase 1: every participant runs a simulation in their own notebook. Phase 2: the
trainers run one room SuperLink on the same VM, and every participant starts one
SuperNode from `notebooks/join.ipynb`. Participants only need a browser; laptops that
join phase 2 open outbound connections only.

Status: the install steps below are a plan, not yet run on the real VM. Use
placeholders such as `<vm-host>` and `<admin>` in committed files, never real
hostnames, IPs, logins or passwords.

## 1. Sizing

| Phase | Per participant | 25 participants | Source |
|---|---|---|---|
| 1, simulation (`viz.setup(cpus=5)`, current choice, still open) | 5 cores while a run is active; ≈ 4.5 GB RAM measured with 2 CPUs, to re-measure with 5 | ≈ 125 cores and > 112 GB at the peak | Measured (2 CPUs), 5 simulated clients |
| 2, one SuperNode | ≈ 0.16 GB idle, ≈ 0.5 GB while training, 1 core | ≈ 13 GB, 25 cores, plus the room SuperLink | Prototype, 2026-11-26 |

Phase 2 is light on memory but needs about one core per SuperNode: with 25 SuperNodes
on 4 cores, every update missed a 40 s deadline. `room.join()` stops the participant's
phase 1 SuperLink to free its memory. Phase 1 dominates the sizing: with 5 CPUs per
participant, not everyone can run at the same time on a realistic VM; runs then share
the cores and take longer. The final size comes from the load test (§ 6).

## 2. Ports

Everything except the Fleet API listens on 127.0.0.1 only.

| Port | Process | Bound to |
|---|---|---|
| 443 | JupyterHub (TLJH) | all interfaces |
| 20000 + 4 × (uid mod 10000), + 1, + 2 | Each user's phase 1 SuperLink (HTTP API, Control API) and dashboard, set by `viz.setup()` | 127.0.0.1 |
| 9092 | Room SuperLink, Fleet API (SuperNodes connect here) | all interfaces (open it in the firewall only if laptops join) |
| 9093 | Room SuperLink, HTTP API (`flwr run`, `flwr ls`) | 127.0.0.1 |
| 9100 + seat | Each participant's SuperNode, local Runtime API | 127.0.0.1 |

Why per-user ports: Flower 1.39 starts the local simulation SuperLink on fixed ports
(39091, 39093). On a shared machine, the second user's `flwr run` then runs inside the
first user's SuperLink, and its results land in the first user's home (reproduced with
two Unix accounts on 2026-11-26). `viz.setup()` sets
`FLWR_LOCAL_SUPERLINK_HTTP_API_PORT` and `FLWR_LOCAL_CONTROL_API_PORT` per user.

## 3. Install (TLJH)

Run as an administrator of the VM, which needs internet access during the install
only.

1. Install TLJH ([docs](https://tljh.jupyter.org/en/latest/install/custom-server.html)):

    ```bash
    curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - --admin <admin>
    ```

2. Shared copy of the repository, its environment and the data (read-only for
   participants):

    ```bash
    sudo mkdir -p /srv/fl-workshop && cd /srv/fl-workshop
    sudo git clone https://github.com/emile-salaun/cines.ai-federated-learning.git repo
    cd repo && sudo uv sync --group notebook
    sudo .venv/bin/python scripts/prepare_data.py --data-dir /srv/fl-workshop/data
    sudo chmod -R a+rX /srv/fl-workshop
    ```

3. Kernel and dashboard proxy for every user. The kernel takes the default name,
   `python3`, which the notebooks ask for:

    ```bash
    sudo /srv/fl-workshop/repo/.venv/bin/python -m ipykernel install \
        --prefix /opt/tljh/user --name python3 --display-name "Python 3 (FL workshop)"
    sudo /opt/tljh/user/bin/pip install jupyter-server-proxy
    ```

4. What each new account gets (TLJH creates the Unix user at first login, from
   `/etc/skel`): the two notebooks, and a link to the data file. Link the file, not the
   whole folder: each user's runs folder (`~/.cache/fl-workshop/runs`) must stay their
   own.

    ```bash
    sudo mkdir -p /etc/skel/notebooks /etc/skel/.cache/fl-workshop
    sudo cp /srv/fl-workshop/repo/notebooks/*.ipynb /etc/skel/notebooks/
    sudo ln -s /srv/fl-workshop/data/fashion_mnist.pt /etc/skel/.cache/fl-workshop/
    ```

5. Accounts `user01`, `user02`, …: the digits are the seat in phase 2 (`room.join()`
   reads them). Authenticator and passwords: OPEN, kept out of the repository.

## 4. Room SuperLink (trainers, on the day)

In a terminal of a trainer account on the hub:

```bash
cd /srv/fl-workshop/repo && source .venv/bin/activate
export FLWR_DISABLE_RUNTIME_DEPENDENCY_INSTALLATION=1 FLWR_TELEMETRY_ENABLED=0
flower-superlink --insecure --disable-runtime-dependency-installation --port 9093
```

Once, in the trainer's `~/.flwr/config.toml`:

```toml
[superlink.room]
address = "127.0.0.1:9093"
insecure = true
```

When the SuperNodes have joined (`flwr supernode ls room`), start the run. Set
`num-partitions` to the number of seats handed out, not to the number connected:
seats that never join are data nobody holds.

```bash
flwr run app room --stream --run-config "run-name='room' partitioning='pathological' num-partitions=<seats> sim-deadline=2.0 round-timeout=30 num-server-rounds=30 fraction-evaluate=0.0"
```

Projector: a trainer notebook with `viz.setup()`, then the **Room** tab of the
dashboard.

## 5. Room run settings

| Key | Value | Why |
|---|---|---|
| `partitioning` | `'pathological'` (2 classes per seat) | Parts of similar size (1,925 to 3,206 images for 25 seats, against 78 to 6,799 with Dirichlet 0.1), so the epochs choice, not luck, decides who is late; impact then reflects rare classes |
| `num-partitions` | Seats handed out | Same split whatever the headcount |
| `sim-deadline` | `2.0`, to calibrate | Simulated deadline, the step 3 rule (decision 2026-11-27): 1 and 2 epochs always on time, 5 epochs on time for the smaller seats (17 of 25), 10 never. A wall-clock deadline would rank noise: 10 epochs take 1.4 s on a free core, against about 8 s of fixed cost per round (one ClientApp process per message, 3 s polling) |
| `round-timeout` | `30` | Safety net only: a frozen or vanished SuperNode never blocks a round longer |
| `num-server-rounds` | `30`, to calibrate | Rounds last about 10–15 s: 3 min to join, about 7 min of training, 3 min to read the leaderboard |
| `fraction-evaluate` | `0.0` | The server evaluates the room model itself; no client evaluation to wait for |

Calibrate in the load test: the round time (for `num-server-rounds`) with 25 SuperNodes.

## 6. Load test (before the January rehearsal)

1. Create 25 test accounts; in each, run the phase 1 notebook up to step 2 at the same
   time. Watch memory and run times.
2. Start the room SuperLink; in each account, `room.join(epochs=...)` with a mix of 1,
   2, 5 and 10; run a room run of 5 rounds. Read the late counts in the Room tab.
3. Stop half of the SuperNodes (`room.leave()`) mid-run and check that the rounds go
   on.

## 7. Open points

- VM: machine, specs, availability window.
- Authenticator, account creation, passwords.
- Firewall for port 9092 if laptops join; room network.
- TLS for the room SuperLink (currently `--insecure`).
