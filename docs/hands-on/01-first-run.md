---
hide:
  - navigation
  - toc
---

# 1. First run

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 1 / 5</span>
  <span class="ws-badge">:material-clock-outline: 12 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Run a first federation where each client holds only **2 classes** out of 10, see
    what the clients gain by training together, and what travels on the network.

!!! info "Who runs what"

    **Deployed**: the lead runs the cells, everyone follows the group dashboard.
    **Simulation**: everyone runs the cells in their own notebook.

## 1.1 Predict

Each client holds 2 classes of clothes (one has only T-shirts and sneakers, another only
trousers and shirts…). Before running, write down in your group:

- how many of the 10 classes a client can recognise **alone**;
- how many the **federated** model will recognise after 10 rounds.

## 1.2 Run

```python
viz.run("pathological", "partitioning='pathological'")
```

The cell prints the exact Flower command it runs: the same line would go in a script or
a batch job. Only `--run-config` changes from one step to the next, never the code.

!!! checkpoint "You should see"

    ```text
    flwr run app --stream --run-config "partitioning='pathological'"
    ```

    then a progress line: *starting clients and loading data* (20 to 60 s), then
    **round 10 of 10**, *finished*, in 1 to 2 minutes.

## 1.3 Check in the dashboard

Open the **Solo or together?** tab. It compares the federated model with each client
trained alone ("solo") and with one model trained on all the data ("centralised").

!!! checkpoint "You should see"

    Three curves (solo, together, centralised) and the table *What each model can
    recognise*. In *Each client's data*, find **client `__CLIENT__`**: which two classes
    does it hold?

## 1.4 Look at the network

```python
viz.open("pathological", view="network")
viz.log("pathological")
```

!!! checkpoint "You should see"

    The **Network** tab replays one round as an animation, with its real timeline and the
    volume exchanged; below the cell, the key lines of the Flower server log.

## Discuss

1. How many classes does a client recognise alone? And the federated model? Compare
   with your prediction.
2. Two classes are recognised by nobody, not even the centralised model. Why?
3. Does a client ever talk to another client? In which order do the messages travel?
4. How many MB travelled in 10 rounds? Compare with the volume of the clients' data.

## Done?

<div class="ws-checklist" markdown>

- [ ] The run reached round 10
- [ ] We compared the result with our prediction
- [ ] We know how much data travelled, and how much stayed put

</div>

??? question "Stuck?"

    - **Still "starting clients" after 2 minutes**: `viz.log("pathological")` shows the
      error; call a trainer.
    - **The solo and centralised curves are missing**: the references are computed in
      advance for the step configurations only; check the `--run-config` string.

[:octicons-arrow-right-24: Step 2: Heterogeneity](02-heterogeneity.md){ .md-button .md-button--primary }
