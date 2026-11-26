# Demo

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-clock-outline: 15 min</span>
  <span class="ws-badge">:material-play-circle-outline: Live</span>
</div>

<!-- TODO: what the demo shows -->

A federated job with NVFLARE across two HPC centres. Each centre trains on its own
data; only model updates travel between them.

<!-- Partner centre not official yet: data-tbc marks it "to be confirmed" on the map.
     Remove data-tbc once confirmed. Sites are defined in assets/javascripts/widgets.js. -->
<figure class="ws-map" data-ws-widget="demo-map" data-sites="adastra,jeanzay" data-tbc="jeanzay">
  <p class="ws-muted">Map of the two demo sites (requires JavaScript).</p>
</figure>

## HPC context { #hpc-context }

HPC plays two roles in federated learning. As a **simulator**, one machine runs hundreds
of virtual clients to compare algorithms. As **silos**, each centre keeps its data and
trains locally: that is this demo.

Silos on HPC meet constraints the cloud does not have:

- **Batch queues**: a round can wait hours for a client job to start.
- **Closed networks**: compute nodes have no internet access and accept no inbound
  connections, so clients connect out to the server and data are staged beforehand.
- **Identity**: accounts, certificates and allowed hosts differ between centres.

??? info "Learn more: FL on HPC in 2026"

    - **Argonne** ran APPFL across four DOE supercomputers (Polaris, Aurora, Frontier,
      Perlmutter), with asynchronous aggregation to cope with queue waits
      ([Li et al., 2026](https://arxiv.org/abs/2603.19544); [FedQueue](https://arxiv.org/abs/2605.02125)).
    - **ORNL** ran 96 FL clients on Frontier and found that orchestration, not the model,
      limits scaling ([EuroMLSys 2026](https://impact.ornl.gov/en/publications/scalable-federated-learning-for-scientific-foundation-models-on-l/)).
    - In Europe, the EuroHPC project [xFFL](https://www.eurohpc-ju.europa.eu/cross-facility-federated-learning_en)
      targets LLM training across supercomputers, and the IT4LIA AI Factory offers
      [federated training](https://it4lia-aifactory.eu/services/federated-training/) as a service.

## Setup

<!-- TODO -->

## Run

```bash
# TODO
```

## What to look at

<!-- TODO -->
