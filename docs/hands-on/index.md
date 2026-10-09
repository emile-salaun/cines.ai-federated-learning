---
hide:
  - toc
  - navigation
---

# Hands-on

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-clock-outline: 60 min</span>
  <span class="ws-badge">:material-account-group-outline: Groups of 4–5</span>
  <span class="ws-badge">:material-flower-outline: Flower</span>
</div>

--8<-- "hands-on-stepper.md"

<!-- TODO: goal of the hands-on, in one or two sentences -->
<span class="ws-muted">TBD</span>

## Your group { #your-group }

<!-- Groups and SuperLink addresses: docs/assets/javascripts/groups.js -->
Pick your group and seat. The commands on the next pages will use your values.

<div id="ws-group-picker" class="ws-picker">
  <p class="ws-muted">Loading… (requires JavaScript)</p>
</div>

## Architecture

<!-- TODO: final topology (hosts, ports) -->

```mermaid
flowchart LR
    subgraph ORG["Organisers · TBD"]
        SL["SuperLink<br/>group N"]
    end
    subgraph GRP["Your group"]
        N1["SuperNode<br/>seat 1"]
        N2["SuperNode<br/>seat 2"]
        N3["SuperNode<br/>seat …"]
    end
    N1 --> SL
    N2 --> SL
    N3 --> SL
```

## Steps

<div class="grid cards ws-steps" markdown>

-   :material-numeric-1-circle-outline:{ .lg } **Local simulation**

    ---

    <!-- TODO: short description -->
    <span class="ws-muted">TBD</span>

    <span class="ws-badge">:material-clock-outline: TBD</span>
    <span class="ws-badge">:material-account-outline: Solo</span>

    [:octicons-arrow-right-24: Start](01-simulation.md)

-   :material-numeric-2-circle-outline:{ .lg } **Group deployment**

    ---

    <!-- TODO: short description -->
    <span class="ws-muted">TBD</span>

    <span class="ws-badge">:material-clock-outline: TBD</span>
    <span class="ws-badge">:material-account-group-outline: Group</span>

    [:octicons-arrow-right-24: Start](02-deployment.md)

-   :material-numeric-3-circle-outline:{ .lg } **Experiments**

    ---

    <!-- TODO: short description -->
    <span class="ws-muted">TBD</span>

    <span class="ws-badge">:material-clock-outline: TBD</span>
    <span class="ws-badge">:material-account-group-outline: Group</span>

    [:octicons-arrow-right-24: Start](03-experiments.md)

-   :material-numeric-4-circle-outline:{ .lg } **Debrief**

    ---

    <!-- TODO: short description -->
    <span class="ws-muted">TBD</span>

    <span class="ws-badge">:material-clock-outline: TBD</span>
    <span class="ws-badge">:material-account-multiple-outline: Everyone</span>

    [:octicons-arrow-right-24: Start](04-debrief.md)

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

[:octicons-arrow-right-24: Start with step 1](01-simulation.md){ .md-button .md-button--primary }
