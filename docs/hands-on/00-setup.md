---
hide:
  - navigation
  - toc
---

# 0. Setup

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 0 / 5</span>
  <span class="ws-badge">:material-clock-outline: 5 min</span>
  <span class="ws-badge">:material-account-outline: Solo</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    The phase 1 notebook is open, a simulated federation of five clients is ready, and
    the dashboard is open in a tab next to the notebook.

!!! info "Your seat"

    Group `__GROUP__` · Seat `__SEAT__` · Your client: **`__CLIENT__`** (clients are
    numbered from 0 in the dashboard). Wrong values? Change them on the
    [overview page](index.md#your-group).

## 0.1 Open the notebook

=== "JupyterHub"

    1. Log in to the workshop hub (address given by the trainers).
    2. In the file browser, open `notebooks/simulation.ipynb`.
    <!-- TODO: folder of the repository on the hub (infra) -->

=== "Your computer"

    Requires [uv](https://docs.astral.sh/uv/) and the data downloaded beforehand
    (see [Setup](../setup.md)). From the repository root:

    === "Linux / macOS"

        ```bash
        uv sync --project app --group notebook
        uv run --project app jupyter lab notebooks/simulation.ipynb
        ```

    === "Windows PowerShell"

        ```powershell
        uv sync --project app --group notebook
        uv run --project app jupyter lab notebooks/simulation.ipynb
        ```

=== "Google Colab"

    <!-- TODO: Colab install cell (open decision: online install on Colab). -->
    TBD

!!! checkpoint "You should see"

    The notebook *Federated learning with Flower: phase 1, simulation*, starting with a
    **Setup** cell.

## 0.2 Run the setup cell

```python
from flworkshop import viz

viz.setup()
```

It sets up a local SuperLink that simulates five clients, checks the data and starts
the dashboard. From now on, `!flwr run app ...` works in the notebook exactly as in a
terminal opened at the repository root.

!!! checkpoint "You should see"

    ```text
    Simulated federation: 5 clients, 2 CPUs in total
    Data fashion_mnist : OK
    Data cifar10       : missing (uv run --project app python scripts/prepare_data.py)
    ```

    followed by an **Open the dashboard** link. `cifar10` may be missing: it is not
    needed. If `fashion_mnist` is missing, call a trainer.

## 0.3 Open the dashboard

Click **Open the dashboard** and keep the tab open next to the notebook. It watches the
results folder and follows the latest run, round by round.

!!! checkpoint "You should see"

    Four tabs: **Solo or together?**, **The run**, **Network**, **Compare**. They stay
    empty until the first run.

## Done?

<div class="ws-checklist" markdown>

- [ ] The setup cell printed the federation and `fashion_mnist : OK`
- [ ] The dashboard is open in a tab
- [ ] I know my client number

</div>

??? question "Stuck?"

    - **The first run reinstalls packages** (`uv sync took ...` in the log): restart the
      kernel and run `viz.setup()` again; it restarts the local SuperLink with the right
      settings.
    - **The dashboard link does not open on the hub**: call a trainer (the hub needs
      `jupyter-server-proxy`).

[:octicons-arrow-right-24: Step 1: First run](01-first-run.md){ .md-button .md-button--primary }
