"""flworkshop: ClientApp (training and evaluation on local data)."""

import random
import socket
import time

import torch
from flwr.app import (
    ArrayRecord,
    ConfigRecord,
    Context,
    Error,
    Message,
    MetricRecord,
    RecordDict,
)
from flwr.clientapp import ClientApp

from flworkshop.data import input_shape, load_partition
from flworkshop.task import build_model
from flworkshop.task import test as test_fn
from flworkshop.task import train as train_fn

app = ClientApp()

DEVICE = torch.device("cpu")


def _local_data(context: Context):
    """Loaders of this client's partition (partition-id comes from the node config)."""
    return load_partition(
        partition_id=int(context.node_config["partition-id"]),
        num_partitions=int(context.node_config["num-partitions"]),
        run_config=context.run_config,
        batch_size=int(context.run_config["batch-size"]),
    )


def _info(context: Context, **extra) -> ConfigRecord:
    """Who answered: lets the server attribute each reply to a client (visualisation).

    Sent in a ConfigRecord, not in the metrics, so FedAvg does not average it.
    """
    return ConfigRecord(
        {"partition-id": int(context.node_config["partition-id"]),
         "host": socket.gethostname(), **extra}
    )


def _model(msg: Message, context: Context):
    model = build_model(input_shape(context.run_config))
    model.load_state_dict(msg.content["arrays"].to_torch_state_dict())
    return model


@app.train()
def train(msg: Message, context: Context):
    """Train the received global model on local data and send back the weights."""
    # Reproducible local training: same seed, round and client -> same batches.
    seed = int(context.run_config.get("seed", 42))
    server_round = int(msg.content["config"].get("server-round", 0))
    partition_id = int(context.node_config["partition-id"])
    round_seed = seed * 100_000 + server_round * 1_000 + partition_id
    torch.manual_seed(round_seed)

    # Simulated disconnection: with probability dropout-rate, this client fails this
    # round. The draw is deterministic (same seed -> same clients drop in same rounds).
    # An error reply is what the server receives when a client fails; returning it
    # directly avoids the long tracebacks an exception would print.
    dropout_rate = float(context.run_config.get("dropout-rate", 0.0))
    if dropout_rate > 0 and random.Random(round_seed).random() < dropout_rate:
        reason = f"client {partition_id} disconnected in round {server_round} (simulated)"
        return Message(error=Error(code=0, reason=reason), reply_to=msg)

    model = _model(msg, context)
    trainloader, _ = _local_data(context)

    start = time.perf_counter()
    train_loss = train_fn(
        model,
        trainloader,
        epochs=int(context.run_config["local-epochs"]),
        lr=float(msg.content["config"]["lr"]),
        device=DEVICE,
        proximal_mu=float(context.run_config.get("proximal-mu", 0.0)),
    )

    metrics = MetricRecord(
        {"train_loss": train_loss, "num-examples": len(trainloader.dataset)}
    )
    content = RecordDict({
        "arrays": ArrayRecord(model.state_dict()),
        "metrics": metrics,
        "info": _info(context, **{"train-time": time.perf_counter() - start}),
    })
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context):
    """Evaluate the received global model on the local validation set."""
    model = _model(msg, context)
    _, valloader = _local_data(context)

    eval_loss, eval_acc = test_fn(model, valloader, DEVICE)

    metrics = MetricRecord(
        {"eval_loss": eval_loss, "eval_acc": eval_acc, "num-examples": len(valloader.dataset)}
    )
    return Message(
        content=RecordDict({"metrics": metrics, "info": _info(context)}), reply_to=msg
    )
