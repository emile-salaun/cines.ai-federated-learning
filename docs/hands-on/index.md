---
hide:
  - toc
  - navigation
---

# Hands-on

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-clock-outline: 60 min</span>
  <span class="ws-badge">:material-account-group-outline: Groups of 3–6</span>
  <span class="ws-badge">:material-flower-outline: Flower</span>
</div>

--8<-- "hands-on-stepper.md"

You learn federated learning in two phases. **Phase 1**: everyone simulates a small
federation in their own notebook and puts it under stress (unequal data, slow clients,
costly communication). **Phase 2**: the whole room joins one real federation, and the
server measures what each participant brings. In each step you predict, run, check
in the dashboard and discuss with your group.

## Your group { #your-group }

<!-- Groups and SuperLink addresses: docs/assets/javascripts/groups.js -->
Pick your group and seat. The commands on the next pages will use your values.

<div id="ws-group-picker" class="ws-picker">
  <p class="ws-muted">Loading… (requires JavaScript)</p>
</div>

## Architecture

<!-- TODO: final topology (hosts, ports, seat numbering across the room) after the prototype -->

```mermaid
flowchart LR
    subgraph P1["Phase 1 · your notebook"]
        R1["flwr run"] --> L1["Local SuperLink<br/>5 simulated clients"]
    end
    subgraph P2["Phase 2 · the room"]
        SL["Room SuperLink<br/>(trainers)"]
        N1["SuperNode<br/>seat 1"] --> SL
        N2["SuperNode<br/>seat 2"] --> SL
        N3["SuperNode<br/>seat …"] --> SL
    end
```

## Steps

<div class="grid cards ws-steps" markdown>

-   :material-numeric-0-circle-outline:{ .lg } **Setup**

    ---

    Open the notebook, start the simulated federation and the dashboard.

    <span class="ws-badge">:material-clock-outline: 5 min</span>
    <span class="ws-badge">:material-account-outline: Solo</span>

    [:octicons-arrow-right-24: Start](00-setup.md)

-   :material-numeric-1-circle-outline:{ .lg } **First run**

    ---

    Each client holds two classes. Alone or together, what can a model recognise? What travels on the network?

    <span class="ws-badge">:material-clock-outline: 10 min</span>
    <span class="ws-badge">:material-account-group-outline: Group</span>

    [:octicons-arrow-right-24: Start](01-first-run.md)

-   :material-numeric-2-circle-outline:{ .lg } **Heterogeneity**

    ---

    Unequal data, unequal clients: what happens to accuracy and to the round time?

    <span class="ws-badge">:material-clock-outline: 10 min</span>
    <span class="ws-badge">:material-account-group-outline: Group</span>

    [:octicons-arrow-right-24: Start](02-heterogeneity.md)

-   :material-numeric-3-circle-outline:{ .lg } **Compute vs communication**

    ---

    Same compute budget, fewer or more rounds: when does talking less pay off? The group splits the runs.

    <span class="ws-badge">:material-clock-outline: 10 min</span>
    <span class="ws-badge">:material-account-group-outline: Group</span>

    [:octicons-arrow-right-24: Start](03-compute-vs-communication.md)

-   :material-numeric-4-circle-outline:{ .lg } **Room federation**

    ---

    Phase 2: everyone joins one real federation, picks their local epochs and earns a contribution score.

    <span class="ws-badge">:material-clock-outline: 15 min</span>
    <span class="ws-badge">:material-account-multiple-outline: Everyone</span>

    [:octicons-arrow-right-24: Start](04-room-federation.md)

-   :material-numeric-5-circle-outline:{ .lg } **Debrief**

    ---

    Room results and leaderboard, and the link to the cross-centre demo.

    <span class="ws-badge">:material-clock-outline: 10 min</span>
    <span class="ws-badge">:material-account-multiple-outline: Everyone</span>

    [:octicons-arrow-right-24: Start](05-debrief.md)

</div>

## How these pages work

<div class="grid" markdown>

!!! checkpoint "You should see"

    Expected output after a command. Compare before moving on.

!!! question "Stuck?"

    Collapsed boxes with common issues. Open them before calling a trainer.

!!! tip "Going further"

    Optional extras for groups that finish early.

!!! success "Done?"

    Tick the boxes at the end of each step. The bar at the top marks the step as done.

</div>

## Run-config reference { #run-config }

Each run changes only the `--run-config` string. These are all the keys:

| Key | Values | Default | Used in |
|---|---|---|---|
| `run-name` | Letters, digits, `_`, `-`, `.` | run id | Every step (name in the dashboard) |
| `partitioning` | `iid`, `dirichlet`, `pathological` | `iid` | [Step 1](01-first-run.md), [Step 2](02-heterogeneity.md) |
| `dirichlet-alpha` | > 0; smaller = more uneven | `0.1` | [Step 2](02-heterogeneity.md), [Step 3](03-compute-vs-communication.md) |
| `classes-per-partition` | Classes per client for `pathological` | `2` | [Step 1](01-first-run.md) |
| `num-server-rounds` | Number of rounds | `10` | [Step 3](03-compute-vs-communication.md) |
| `local-epochs` | Local epochs per round | `2` | [Step 3](03-compute-vs-communication.md) |
| `fraction-train` | Share of clients sampled per round, 0 to 1 | `1.0` | [Going further](05-debrief.md) |
| `dropout-rate` | Probability that a sampled client fails, 0 to 1 | `0.0` | [Going further](05-debrief.md) |
| `proximal-mu` | ≥ 0; > 0 turns on FedProx | `0.0` | [Going further](05-debrief.md) |
| `dataset` | `fashion_mnist`, `cifar10` | `fashion_mnist` | [Going further](05-debrief.md) |

Keep `learning-rate` (0.01), `batch-size` (32) and `seed` (42) as they are: the expected
results assume these values. What the keys mean: [Concepts](../concepts.md).

[:octicons-arrow-right-24: Start with step 0](00-setup.md){ .md-button .md-button--primary }
