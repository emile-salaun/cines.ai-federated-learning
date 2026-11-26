---
hide:
  - navigation
  - toc
---

# 4. Failures

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 4 / 5</span>
  <span class="ws-badge">:material-clock-outline: 9 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    In practice, only part of the clients train in each round, and some do not finish.
    See how the federation copes, on the Dirichlet data of step 2.

## 4.1 Predict

Before running, write down in your group:

- if half of the clients drop out during a round, does the training stop?
- with only 2 clients out of 5 in each round, does the accuracy curve still go up
  smoothly?

## 4.2 Run

**a.** Only 2 clients out of 5, sampled at random, train in each round:

```python
viz.run("participation_40", "partitioning='dirichlet' dirichlet-alpha=0.1 fraction-train=0.4", view="run")
```

**b.** Each client has a one-in-two chance of disconnecting during a round:

```python
viz.run("dropouts_50", "partitioning='dirichlet' dirichlet-alpha=0.1 dropout-rate=0.5", view="run")
```

!!! checkpoint "You should see"

    Both runs reach **round 10 of 10**. In **The run** tab, who took part in each round:
    sampled clients, and disconnected ones for `dropouts_50`. Was client `__CLIENT__`
    often left out?

## Discuss

1. Does the federation stop when a client drops out? What does the server do with the
   missing ones? (**Network** tab on `dropouts_50`.)
2. Why does the global model curve go up in a saw-tooth? Look at who takes part in each
   round and which classes they hold.
3. **Compare** tab with `dirichlet`: why is the last-round accuracy no longer enough to
   compare two runs?

## Done?

<div class="ws-checklist" markdown>

- [ ] Both runs reached round 10
- [ ] We explained the saw-tooth curve

</div>

??? tip "Going further"

    Try another share of clients, `fraction-train=0.2` (1 client per round) or `0.6`, or
    the same participation on IID data (`partitioning='iid'`). The sampled clients change
    from one run to the next: compare shapes, not exact values.

[:octicons-arrow-right-24: Step 5: Debrief](05-debrief.md){ .md-button .md-button--primary }
