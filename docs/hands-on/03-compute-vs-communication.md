---
hide:
  - navigation
  - toc
---

# 3. Compute vs communication

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 3 / 5</span>
  <span class="ws-badge">:material-clock-outline: 10 min</span>
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

{% if scenario == "A" %}
## 3.2 Split the runs in your group

Each seat runs one line (in the notebook, each run has its own cell), then shares its
numbers: seat 1 takes run 1, seat 2 run 2, seat 3 run 3, seats 4 and more run 4.
Time left? Run another one.
{% else %}
## 3.2 Split the runs with your neighbours

Each of you runs one line (in the notebook, each run has its own cell), so that the
four runs are covered between you, then share your numbers. Alone? Start with runs 3
and 4. Time left? Run another one.
{% endif %}

| Run | Data | Rounds × local epochs |
|:---:|:---:|:---:|
| 1 | Dirichlet | 20 × 1 |
| 2 | Dirichlet | 5 × 4 |
| 3 | Dirichlet | 2 × 10 |
| 4 | IID | 2 × 10 |

```python
# Run 1
!flwr run app --stream --run-config "run-name='dirichlet_r20_ep1' partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=20 local-epochs=1"
# Run 2
!flwr run app --stream --run-config "run-name='dirichlet_r5_ep4' partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=5 local-epochs=4"
# Run 3
!flwr run app --stream --run-config "run-name='dirichlet_r2_ep10' partitioning='dirichlet' dirichlet-alpha=0.1 num-server-rounds=2 local-epochs=10"
# Run 4
!flwr run app --stream --run-config "run-name='iid_r2_ep10' partitioning='iid' num-server-rounds=2 local-epochs=10"
```

!!! checkpoint "You should see"

    The log ends at the last round of your split (`[ROUND 20/20]`, `[ROUND 5/5]` or
    `[ROUND 2/2]`). Fewer rounds means longer rounds.

## 3.3 Fill in the group table

The **Network** tab gives the volume exchanged by a run; the **Compare** tab gives its
final accuracy. The 10 × 2 row comes from step 2.

| Rounds × local epochs | MB exchanged | Final accuracy, IID | Final accuracy, Dirichlet |
|:---:|:---:|:---:|:---:|
| 20 × 1 | | – | |
| 10 × 2 (step 2) | | | |
| 5 × 4 | | – | |
| 2 × 10 | | | |

## Discuss

1. How does the volume exchanged scale with the number of rounds?
2. On IID data, what does it cost to talk 5 times less? And on Dirichlet data?
3. With many local epochs, each client drifts towards its own data before the next
   average. Where have you met this trade-off between local work and synchronisation
   in HPC?

!!! tip "Keep this in mind for phase 2"

    In the room federation, everyone picks their own local epochs. Your answer to
    question 3 is your strategy.

## Done?

<div class="ws-checklist" markdown>

- [ ] My split reached its last round
- [ ] Our group table is filled in
- [ ] We know when talking less pays off

</div>

??? question "Stuck?"

    - **No solo or centralised curves for these runs**: expected, the references exist
      only for 10 rounds × 2 epochs. Use the **Compare** tab.

[:octicons-arrow-right-24: Step 4: Room federation](04-room-federation.md){ .md-button .md-button--primary }
