---
hide:
  - navigation
  - toc
---

# 3. Compute vs communication

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 3 / 5</span>
  <span class="ws-badge">:material-clock-outline: 12 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Keep the same compute budget, **20 local epochs per client**, and split it into more
    or fewer rounds. Fewer rounds means fewer messages: when does talking less pay off?

So far, each run used 10 rounds × 2 local epochs. Each round costs one exchange of
models between the server and every client.

## 3.1 Predict

With 2 rounds × 10 local epochs, the clients exchange 5 times fewer messages than in
step 2. Before running, write down in your group:

- whether the accuracy drops, on IID data and on Dirichlet data;
- on which data it drops more, and why.

## 3.2 Run

Run both, then compare with `iid` and `dirichlet` from step 2:

```python
viz.run("iid_r2_ep10", "partitioning='iid' num-server-rounds=2 local-epochs=10", view="compare")
viz.run("dirichlet_r2_ep10", "partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=2 local-epochs=10", view="compare")
```

!!! checkpoint "You should see"

    Two short runs: **round 2 of 2**, each round longer than in step 2. In the
    **Compare** tab, the new runs next to `iid` and `dirichlet`.

## 3.3 Fill in the group table

Complete the budget with two more splits of the same 20 epochs, on Dirichlet data.
**Simulation**: split them across the group (seats 1–2 the first, seats 3–5 the second)
and share your numbers. **Deployed**: the lead runs both if time allows.

```python
viz.run("dirichlet_r20_ep1", "partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=20 local-epochs=1", view="compare")
viz.run("dirichlet_r5_ep4", "partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=5 local-epochs=4", view="compare")
```

| Rounds × local epochs | MB exchanged | Final accuracy, IID | Final accuracy, Dirichlet | Run time |
|:---:|:---:|:---:|:---:|:---:|
| 20 × 1 | | – | | |
| 10 × 2 (step 2) | | | | |
| 5 × 4 | | – | | |
| 2 × 10 | | | | |

!!! checkpoint "You should see"

    The **Network** tab gives the volume exchanged by each run; the **Compare** tab gives
    the final accuracies.

## Discuss

1. How does the volume exchanged scale with the number of rounds?
2. On IID data, what does it cost to talk 5 times less? And on Dirichlet data?
3. With many local epochs, each client drifts towards its own data before the next
   average. Where have you met this trade-off between local work and synchronisation
   in HPC?

## Done?

<div class="ws-checklist" markdown>

- [ ] The 2 × 10 runs reached their last round
- [ ] Our group table is filled in
- [ ] We know when talking less pays off

</div>

??? question "Stuck?"

    - **No solo or centralised curves for these runs**: expected, the references exist
      only for 10 rounds × 2 epochs. Use the **Compare** tab.

[:octicons-arrow-right-24: Step 4: Failures](04-failures.md){ .md-button .md-button--primary }
