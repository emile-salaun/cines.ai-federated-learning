# Concepts

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-clock-outline: 30 min</span>
  <span class="ws-badge">:material-school-outline: Talk</span>
  <span class="ws-badge">:material-book-open-variant: 3 min read</span>
</div>

[:material-presentation: Slides](slides/){ .md-button .md-button--primary }
[:material-file-pdf-box: PDF](slides/talk.pdf){ .md-button }

The written companion of the talk: four ideas you need for the hands-on. Open a
**Learn more** box when you want the details.

## Why federated learning?

**The model's weights travel to the data: each client trains on its own data and only
sends back updated weights.**

<figure class="ws-figure">
<div class="ws-fig-row">
--8<-- "figures/centralised.svg"
--8<-- "figures/federated.svg"
</div>
<figcaption>Same three sites, two ways to train. Only the federated one keeps the data where they are.</figcaption>
</figure>

Some data cannot be moved: patient records, company secrets, datasets too large to copy.
Federated learning (FL) is already used on such data:

<div class="grid cards ws-trio" markdown>

-   :material-cellphone-text: **Keyboards**

    Next-word prediction trained on phones ([Hard et al., 2018](https://arxiv.org/abs/1811.03604)).

-   :material-hospital-building: **Hospitals**

    20 institutes predict oxygen needs of COVID-19 patients ([Dayan et al., 2021](https://doi.org/10.1038/s41591-021-01506-3)).

-   :material-flask-outline: **Pharma**

    10 companies train one drug-discovery model, MELLODDY ([Oldenhof et al., 2022](https://arxiv.org/abs/2210.08871)).

</div>

??? info "Learn more: cross-silo vs cross-device, and privacy"

    | | Cross-silo | Cross-device |
    |---|---|---|
    | Clients | A few institutions: hospitals, labs, HPC centres | Millions of phones or sensors |
    | Data per client | Large | Small |
    | Participation | Reliable, scheduled | Clients come and go |
    | Example | **This workshop** (a handful of clients per federation) | Mobile keyboards |

    **Federated is not private by default.** Model weights still carry traces of the
    training data, so FL is one layer of a privacy design. Two common additions:

    - **Secure aggregation**: the server only learns the sum of the updates, never one
      client's update ([Bonawitz et al., CCS 2017](https://research.google/pubs/practical-secure-aggregation-for-privacy-preserving-machine-learning/)).
    - **Differential privacy**: calibrated noise bounds what anyone can learn about one
      example ([McMahan et al., ICLR 2018](https://arxiv.org/abs/1710.06963)).

    The workshop uses neither: it focuses on the learning side. One more large example:
    71 sites on 6 continents trained a glioblastoma model
    ([Pati et al., 2022](https://doi.org/10.1038/s41467-022-33407-5)).

## How it works

**Training happens in rounds, and every round has the same five steps.**

1. **Send**: the server sends the global model's weights to the clients of the round.
2. **Train**: each client trains it on its own data, for a few epochs.
3. **Return**: each client sends back its updated weights. Never its data.
4. **Aggregate**: the server averages the weights into a new global model (FedAvg).
5. **Evaluate**: the new model is evaluated, and the next round starts.

Two things to keep in mind:

- **Not every client takes part**: the server samples a fraction of the clients each
  round, and a sampled client can fail. The server aggregates what it receives.
- **A round waits for its slowest client**, so one slow client sets the pace.

??? info "Learn more: FedAvg, and compute vs communication"

    **FedAvg** ([McMahan et al., AISTATS 2017](https://arxiv.org/abs/1602.05629)) weights
    each client's model by its amount of data:

    <p class="ws-formula">w<sub>t+1</sub> = Σ<sub>k</sub> (n<sub>k</sub> / n) · w<sup>k</sup><sub>t+1</sub></p>

    w<sup>k</sup><sub>t+1</sub> is client k's model after local training, n<sub>k</sub>
    its number of examples, n the total over the round. A client with twice as much data
    counts twice as much.

    **Compute vs communication.** `num-server-rounds` sets how often the model is
    exchanged, `local-epochs` how much each client trains in between. At an equal budget
    (rounds × epochs), more local epochs means fewer exchanges but more drift toward each
    client's own data; more rounds means more communication but clients that stay
    closer. Which side wins depends on the data: the
    [hands-on](hands-on/index.md) lets you measure it.

    **Failures.** `fraction-train` sets the share of clients sampled per round,
    `dropout-rate` the chance that a sampled client fails. If nobody answers, the global
    model stays unchanged.

## Non-IID data

**Real clients do not see the same data, and their average learns more slowly.**

<figure class="ws-figure">
<div class="ws-fig-row ws-fig-row--3">
--8<-- "figures/alpha-100.svg"
--8<-- "figures/alpha-1.svg"
--8<-- "figures/alpha-01.svg"
</div>
<figcaption>Fashion-MNIST over 5 clients (C1 to C5). Each dot is one class on one client, its area the number of images; bars show client sizes. Seed 42, illustration only.</figcaption>
</figure>

The hands-on splits Fashion-MNIST over its clients in three ways:

=== "IID"

    `partitioning='iid'`: each client gets a random fifth of the data, with the same
    class mix everywhere. The easy case.

=== "Dirichlet"

    `partitioning='dirichlet'`: each class is split over the clients with proportions
    drawn from a Dirichlet distribution of parameter α (`dirichlet-alpha`). Small α gives
    most of a class to one or two clients, and very unequal client sizes. The hands-on
    uses α = 0.1.

=== "Pathological"

    `partitioning='pathological'`: each client holds only 2 classes
    (`classes-per-partition`). The most extreme case.

- **Client drift**: local training pulls each client toward its own data, and the
  average of drifted models is worse.
- **A federation cannot learn what no client has**: a class missing everywhere stays
  unknown, whatever the number of rounds.

??? info "Learn more: where α comes from, and FedProx"

    The Dirichlet scheme comes from [Hsu et al., 2019](https://arxiv.org/abs/1909.06335).
    The figure uses the same scheme as the hands-on partitioner, but it is not the exact
    hands-on split.

    **FedProx** ([Li et al., MLSys 2020](https://arxiv.org/abs/1812.06127)) adds a penalty
    to each client's loss for moving away from the global model w<sub>t</sub>:

    <p class="ws-formula">L<sub>k</sub>(w) + (μ / 2) · ‖w − w<sub>t</sub>‖²</p>

    μ is `proximal-mu` (0 = plain FedAvg). It is not on the main hands-on path: try it
    once you have finished, with `proximal-mu=0.1` on a Dirichlet split.

## Frameworks

**Flower separates your code from the infrastructure that runs it.**

<div class="grid cards" markdown>

-   :material-code-tags: **The app (you write it)**

    ---

    `ServerApp` holds the strategy (FedAvg) and the rounds. `ClientApp` trains and
    evaluates on the client's data.

-   :material-server-network: **The infrastructure (Flower runs it)**

    ---

    `SuperLink` is the hub. One `SuperNode` per client runs your `ClientApp` and only
    connects **out** to the SuperLink.

</div>

<figure class="ws-figure">
--8<-- "figures/hub.svg"
<figcaption>How you join one: <a href="hands-on/index.md">Hands-on</a>.</figcaption>
</figure>

- **Same app in simulation and deployment**: only where the SuperNodes run changes.
- **Every experiment changes the configuration, never the code**:
  `flwr run . --run-config "partitioning='dirichlet'"`.

!!! question "Why Flower here, and NVIDIA FLARE in the demo?"

    They are the two mature general-purpose FL frameworks in 2026
    ([benchmark](https://arxiv.org/html/2611.10688)), each strong at a different job.
    **Flower** is built to write and learn FL apps: the same app runs in a notebook or
    across machines, and each experiment is one `--run-config` change. That is the
    hands-on. **[NVIDIA FLARE](https://nvflare.readthedocs.io/)** is built to operate
    federations between institutions, with per-site certificates and a Slurm launcher,
    and Bristol used it to federate three UK supercomputers
    ([Wright et al., SC26 Workshops](https://arxiv.org/abs/2611.30381)). That is the [demo](demo.md#hpc-context). The two are
    compatible: FLARE can run Flower apps.

??? info "Learn more: Flower vs NVIDIA FLARE"

    | | Flower | NVIDIA FLARE |
    |---|---|---|
    | Focus | Research to production, any ML framework | Production, regulated sectors |
    | Security | TLS, node authentication | Provisioning: startup kits and certificates per site |
    | Operations | SuperLink and SuperNodes | Server, clients, admin console, jobs |
    | On HPC | SuperNodes started as SLURM jobs | SLURM job launcher (version 2.9 and later) |

    The two can work together: [FLARE can run Flower apps](https://nvflare.readthedocs.io/en/main/user_guide/data_scientist_guide/flower_integration/flower_integration.html)
    as FLARE jobs. Documentation: [Flower 1.39](https://flower.ai/docs/framework/1.39/en/).

## On HPC

**HPC centres can be the silos of a federation, but batch queues and closed networks make
it harder than in the cloud.** Argonne, ORNL and EuroHPC projects work on it in 2026; the
[demo](demo.md#hpc-context) shows how, between Adastra and a second centre.

Papers and links to go further are on the [Resources](resources.md#going-further) page.

[:octicons-arrow-right-24: Next: the demo](demo.md){ .md-button }
