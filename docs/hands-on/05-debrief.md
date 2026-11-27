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

The projector shows the **Room** tab of the room run: the room model round by round,
and the leaderboard by seat.

1. Find your seat. How many rounds were you on time, late, disconnected?
2. Look at the local epochs of the top seats, and of the seats that were always late.
3. Find a negative impact. What could make an update hurt the room model?

!!! info "Why measure, rather than ask?"

    Consortia that train together (hospitals, pharma, banks) must decide who brings
    what. A client could claim more data or more work than it did. Here the server
    measures each contribution itself, on data that no client holds: leave each update
    out in turn and see how much the model loses.

## Compare with phase 1

<!-- TODO: filled in live by the trainers -->

{% if scenario == "A" %}
| Group | 1. Pathological | 2. IID / Dirichlet | 3. Best rounds × epochs | 4. Epochs picked in the room run |
|:-----:|:---------------:|:------------------:|:-----------------------:|:--------------------------------:|
| 1     |                 |                    |                         |                                  |
| 2     |                 |                    |                         |                                  |
| 3     |                 |                    |                         |                                  |
| 4     |                 |                    |                         |                                  |
| 5     |                 |                    |                         |                                  |
| 6     |                 |                    |                         |                                  |
{% else %}
| Local epochs | Step 3: clients on time (of 5) | Step 3: final accuracy | Room run: seats that picked it | Room run: mean impact |
|:---:|:---:|:---:|:---:|:---:|
| 1 | | | | |
| 2 | | | | |
| 5 | | | | |
| 10 | | | | |
{% endif %}

## From the hands-on to the demo

<!-- TODO: link to the NVFLARE demo between two HPC centres (demo page) -->
The [demo](../demo.md) ran the same idea between two HPC centres. Which of today's
problems (unequal data, slow clients, deadlines, failures) matter most there?

## Done?

<div class="ws-checklist" markdown>

- [ ] I found my seat on the leaderboard and know why it ranks where it does

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
