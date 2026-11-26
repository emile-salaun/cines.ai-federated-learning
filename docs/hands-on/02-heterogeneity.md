---
hide:
  - navigation
  - toc
---

# 2. Heterogeneity

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 2 / 5</span>
  <span class="ws-badge">:material-clock-outline: 12 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Compare clients with similar data (**IID**) and clients with very unequal data
    (**Dirichlet**, α = 0.1): what changes for accuracy, and for the time of a round?

## 2.1 Predict

With Dirichlet α = 0.1, each client mostly holds a few classes, and some clients hold far
more images than others. Before running, write down in your group:

- which run reaches the higher accuracy;
- which run has the **longer rounds**, and why.

## 2.2 Run both

```python
viz.run("iid", "partitioning='iid'")
viz.run("dirichlet", "partitioning='dirichlet' dirichlet-alpha=0.1")
```

Run one cell after the other: a new run stops the one in progress.

!!! checkpoint "You should see"

    Two runs at **round 10 of 10**. In the **Compare** tab, the curves of `pathological`,
    `iid` and `dirichlet` on one chart, and a summary table.

## 2.3 Look at the timeline

```python
viz.open("dirichlet", view="network")
```

!!! checkpoint "You should see"

    The timeline of a round: one bar per client, from the moment it receives the model
    to the moment its reply arrives. Compare with the same view on `iid`.

## Discuss

1. Rank the three runs. Compare with your prediction: what makes federated learning
   hard?
2. Timeline of `dirichlet`: why does everyone wait for the same client? Where have you
   seen this pattern on a cluster?
3. **The run** tab, *Client drift*: which client moves furthest from the global model?
   What is special about its data? How much data does client `__CLIENT__` hold?

## Done?

<div class="ws-checklist" markdown>

- [ ] Both runs reached round 10
- [ ] We ranked the three runs
- [ ] We found the slowest client, and why it is the slowest

</div>

??? question "Stuck?"

    - **`viz.run` says the previous run is still running**: it stops it and starts the
      new one. Launch the two runs one after the other, waiting for the end of each.

[:octicons-arrow-right-24: Step 3: Compute vs communication](03-compute-vs-communication.md){ .md-button .md-button--primary }
