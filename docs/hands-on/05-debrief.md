---
hide:
  - navigation
  - toc
---

# 5. Debrief

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 5 / 5</span>
  <span class="ws-badge">:material-clock-outline: 5 min</span>
  <span class="ws-badge">:material-account-multiple-outline: Everyone</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    Put the groups' results side by side, and connect them with the cross-centre demo.

## Compare the groups

<!-- TODO: filled in live by the trainers -->

| Group | Mode | 1. Pathological | 2. IID / Dirichlet | 3. Best rounds × epochs | 4. Survived failures? |
|:-----:|:----:|:---------------:|:------------------:|:-----------------------:|:---------------------:|
| 1     |      |                 |                    |                         |                       |
| 2     |      |                 |                    |                         |                       |
| 3     |      |                 |                    |                         |                       |
| 4     |      |                 |                    |                         |                       |
| 5     |      |                 |                    |                         |                       |
| 6     |      |                 |                    |                         |                       |

## From the hands-on to the demo

<!-- TODO: link to the NVFLARE demo between two HPC centres (demo page) -->
The [demo](../demo.md) ran the same idea between two HPC centres. Which of today's
problems (unequal data, slow clients, communication, failures) matter most there?

## Done?

<div class="ws-checklist" markdown>

- [ ] Our group's results are in the table

</div>

??? tip "Going further"

    - **Harder images**: `viz.run("cifar", "dataset='cifar10' partitioning='pathological'")`
      (needs the CIFAR-10 data).
    - **FedProx** penalises the distance between the local and the global model:
      `viz.run("fedprox", "partitioning='dirichlet' dirichlet-alpha=0.1 proximal-mu=0.1", view="run")`.
      Does it beat FedAvg here?
    - Every key you can pass to `--run-config` is listed in the
      [run-config reference](index.md#run-config) and in the last section of the notebook.
