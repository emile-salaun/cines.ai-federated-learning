---
hide:
  - navigation
  - toc
---

# 1. First run

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 1 / 5</span>
  <span class="ws-badge">:material-clock-outline: 10 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Launch a first federation with Flower's own command, where each client holds only
    **2 classes** out of 10. See what the clients gain by training together, and what
    travels on the network.

Everyone runs the cells in their own notebook; the group predicts and discusses
together.

## 1.1 Predict

Each client holds 2 classes of clothes (one has only T-shirts and sneakers, another only
trousers and shirts…). Before running, write down in your group:

- how many of the 10 classes a client can recognise **alone**;
- how many the **federated** model will recognise after 10 rounds.

## 1.2 Run

```python
!flwr run app --stream --run-config "run-name='pathological' partitioning='pathological'"
```

`flwr run` sends the app in `app/` and its settings to the SuperLink, which runs the
server and the clients. The same line would go in a terminal or a batch job. Only the
`--run-config` string changes from one step to the next; `run-name` only names the run
in the dashboard.

!!! checkpoint "You should see"

    ```text
    Successfully started run 3097669194608828641
    INFO :      Starting Flower Simulation
    ...
    INFO :      [ROUND 1/10]
    INFO :      configure_train: Sampled 5 nodes (out of 5)
    INFO :      aggregate_train: Received 5 results and 0 failures
    ```

    then the same lines for each round, up to `[ROUND 10/10]` and a summary of the
    metrics, in 1 to 2 minutes. Your run id differs. A few `Manually terminating
    ClientAppActor` warnings at the very end are normal: the simulated clients stop.

## 1.3 Check in the dashboard

```python
viz.dashboard("pathological")
```

The **Solo or together?** tab compares the federated model with each client trained
alone ("solo") and with one model trained on all the data ("centralised").

!!! checkpoint "You should see"

    Three curves (solo, together, centralised) and the table *What each model can
    recognise*. In *Each client's data*, {% if scenario == "A" %}find **client `__CLIENT__`**{% else %}pick one client{% endif %}:
    which two classes does it hold?

## 1.4 The run lives on the SuperLink

```python
!flwr ls
viz.dashboard("pathological", view="network")
```

!!! checkpoint "You should see"

    A table of runs with their id and status `finished:completed`: the SuperLink keeps a
    record of every run, whoever launched it. The **Network** tab replays one round as an
    animation, with its real timeline and the volume exchanged.

## Discuss

1. How many classes does a client recognise alone? And the federated model? Compare
   with your prediction.
2. Two classes are recognised by nobody, not even the centralised model. Why?
3. Does a client ever talk to another client? Find `Sampled`, `Received` and
   `Aggregated` in the log of 1.2: which step of the animation does each match?
4. How many MB travelled in 10 rounds? Compare with the volume of the clients' data.

## Done?

<div class="ws-checklist" markdown>

- [ ] The run reached round 10
- [ ] We compared the result with our prediction
- [ ] We know how much data travelled, and how much stayed put

</div>

??? question "Stuck?"

    - **Still nothing after 2 minutes**: read the last lines of the cell output; call a
      trainer if there is an error.
    - **You interrupted the cell**: the run goes on in the SuperLink. Stop it with
      `!flwr stop <run id>` (the id is in `!flwr ls`).
    - **The solo and centralised curves are missing**: the references are computed in
      advance for the step configurations only; check the `--run-config` string.

[:octicons-arrow-right-24: Step 2: Heterogeneity](02-heterogeneity.md){ .md-button .md-button--primary }
