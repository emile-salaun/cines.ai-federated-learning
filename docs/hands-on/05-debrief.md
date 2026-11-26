---
hide:
  - navigation
  - toc
---

# 5. Debrief

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 5 / 5</span>
  <span class="ws-badge">:material-clock-outline: 10 min</span>
  <span class="ws-badge">:material-account-multiple-outline: Everyone</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Read the room result and the leaderboard, compare them with phase 1, and connect
    them with the cross-centre demo.

## The room result

<!-- TODO: projector view (room run curve, leaderboard by seat), after the phase 2 prototype -->

TBD: the room run and the leaderboard, shown on the projector.

## Compare with phase 1

<!-- TODO: filled in live by the trainers -->

| Group | 1. Pathological | 2. IID / Dirichlet | 3. Best rounds × epochs | 4. Epochs picked in the room run |
|:-----:|:---------------:|:------------------:|:-----------------------:|:--------------------------------:|
| 1     |                 |                    |                         |                                  |
| 2     |                 |                    |                         |                                  |
| 3     |                 |                    |                         |                                  |
| 4     |                 |                    |                         |                                  |
| 5     |                 |                    |                         |                                  |
| 6     |                 |                    |                         |                                  |

## From the hands-on to the demo

<!-- TODO: link to the NVFLARE demo between two HPC centres (demo page) -->
The [demo](../demo.md) ran the same idea between two HPC centres. Which of today's
problems (unequal data, slow clients, communication, failures) matter most there?

## Done?

<div class="ws-checklist" markdown>

- [ ] Our group's results are in the table

</div>

??? tip "Going further"

    In the phase 1 notebook (*Going further* section):

    - **Failures, simulated**: only 2 clients out of 5 per round, or a one-in-two chance
      of dropping out.

        ```python
        !flwr run app --stream --run-config "run-name='participation_40' partitioning='dirichlet' dirichlet-alpha=0.1 fraction-train=0.4"
        !flwr run app --stream --run-config "run-name='dropouts_50' partitioning='dirichlet' dirichlet-alpha=0.1 dropout-rate=0.5"
        ```

    - **FedProx** penalises the distance between the local and the global model. Does it
      beat FedAvg here?

        ```python
        !flwr run app --stream --run-config "run-name='fedprox' partitioning='dirichlet' dirichlet-alpha=0.1 proximal-mu=0.1"
        ```

    - **Harder images** (needs the CIFAR-10 data):

        ```python
        !flwr run app --stream --run-config "run-name='cifar' dataset='cifar10' partitioning='pathological'"
        ```

    Every key you can pass to `--run-config` is in the
    [run-config reference](index.md#run-config).
