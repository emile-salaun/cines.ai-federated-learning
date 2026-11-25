<!--
  Glossary: appended to every page (pymdownx.snippets auto_append in zensical.toml).
  Each term below gets a hover tooltip wherever it appears in page text (not in code).
  Matching is exact and case-sensitive. Keep definitions to one sentence.
-->

*[FL]: Federated learning: training one shared model across machines that keep their data local
*[FedAvg]: Federated Averaging: the server averages the clients' model updates, weighted by their number of examples
*[FedProx]: FedAvg plus a proximal term (proximal-mu) that keeps local models close to the global model on non-IID data
*[IID]: Independent and identically distributed: every client sees the same mix of classes
*[non-IID]: Clients see different mixes of classes, as with the Dirichlet or pathological partitionings
*[SuperLink]: Flower's long-running server process: it receives runs and relays messages between the ServerApp and the SuperNodes
*[SuperNode]: Flower's long-running client process: it connects to the SuperLink and runs the ClientApp on its local data partition
*[ServerApp]: Server side of a Flower app: the strategy that samples clients and aggregates their updates
*[ClientApp]: Client side of a Flower app: local training and evaluation on the client's own data
*[NVFLARE]: NVIDIA FLARE, NVIDIA's federated learning framework, used in the demo
*[HPC]: High-performance computing
*[SLURM]: Job scheduler of the HPC clusters, such as Adastra and Jean Zay
*[JupyterHub]: Multi-user Jupyter server: each participant gets their own notebook environment in the browser
*[Fashion-MNIST]: 70,000 grayscale 28×28 images of clothing items in 10 classes
*[CINES]: Centre Informatique National de l'Enseignement Supérieur, Montpellier: hosts Adastra
*[IDRIS]: Institut du développement et des ressources en informatique scientifique (CNRS), Orsay: hosts Jean Zay
