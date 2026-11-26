---
hide:
  - navigation
  - toc
---

# 0. Setup

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 0 / 5</span>
  <span class="ws-badge">:material-clock-outline: 10 min</span>
  <span class="ws-badge">:material-account-group-outline: Group</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    A federation of five clients is ready, and the dashboard is open in a tab next to
    your notebook.

!!! info "Your seat"

    Group `__GROUP__` · Seat `__SEAT__` · Your client: **`__CLIENT__`** (clients are
    numbered from 0 in the dashboard). Wrong values? Change them on the
    [overview page](index.md#your-group).

Pick the tab your group uses. The trainers tell you if your group switches to the
simulation.

=== "Deployed (main)"

    <!-- TODO: written with notebooks/lead.ipynb and notebooks/member.ipynb (not written yet). -->

    The group lead starts the group's SuperLink and opens the group dashboard; each
    member starts one SuperNode on their own client.

    ### 0.1 Lead: start the SuperLink

    TBD (`notebooks/lead.ipynb`, SuperLink `__SUPERLINK__`).

    !!! checkpoint "You should see"

        TBD

    ### 0.2 Members: start your SuperNode

    TBD (`notebooks/member.ipynb`, client `__CLIENT__`).

    !!! checkpoint "You should see"

        TBD

    ### 0.3 Lead: check that the five clients are connected

    TBD

    !!! checkpoint "You should see"

        TBD

=== "Simulation (fallback)"

    Everyone simulates the five clients in their own notebook. The app is the same as
    in deployed mode; only the launch differs.

    ### 0.1 Open the notebook

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

        The notebook *Federated learning with Flower*, starting with a **Setup** cell.

    ### 0.2 Run the setup cell

    ```python
    from flworkshop import viz

    viz.setup()
    ```

    !!! checkpoint "You should see"

        ```text
        Simulated federation: 5 clients, 2 CPUs in total
        Data fashion_mnist : OK
        Data cifar10       : missing (uv run --project app python scripts/prepare_data.py)
        ```

        followed by an **Open the dashboard** link. `cifar10` may be missing: it is not
        needed. If `fashion_mnist` is missing, call a trainer.

    ### 0.3 Open the dashboard

    Click **Open the dashboard** and keep the tab open next to the notebook: it updates
    every round.

    !!! checkpoint "You should see"

        Four tabs: **Solo or together?**, **The run**, **Network**, **Compare**. They stay
        empty until the first run.

## Done?

<div class="ws-checklist" markdown>

- [ ] The five clients are ready (connected SuperNodes, or simulated federation)
- [ ] The dashboard is open in a tab
- [ ] I know my client number

</div>

??? question "Stuck?"

    - **Simulation: the first run reinstalls packages** (`uv sync took ...` in the log):
      restart the kernel and run `viz.setup()` again; it restarts the local SuperLink with
      the right settings.
    - **The dashboard link does not open on the hub**: call a trainer (the hub needs
      `jupyter-server-proxy`).

[:octicons-arrow-right-24: Step 1: First run](01-first-run.md){ .md-button .md-button--primary }
