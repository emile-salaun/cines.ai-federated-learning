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

# Simulated compute speed, for `sim-deadline`: every client trains this many images
# per simulated second, so the simulated round time depends only on the client's data
# size and local epochs, not on the load of the machine.
IMAGES_PER_SECOND = 5000


def _partition(context: Context) -> tuple[int, int]:
    """(partition id, number of partitions) of this client.

    Simulation: both come from the node config that Flower gives each virtual client.
    Room federation: the participant's SuperNode sets `seat` (1, 2, ...) in its node
    config, partition = seat - 1, and the trainers set `num-partitions` in the run
    config (the room size), so every SuperNode splits the data the same way.
    """
    node, run = context.node_config, context.run_config
    if "seat" in node:
        pid = int(node["seat"]) - 1
    else:
        pid = int(node["partition-id"])
    num = int(run.get("num-partitions", 0)) or int(node["num-partitions"])
    return pid, num


def _local_epochs(context: Context) -> int:
    """Local epochs: the SuperNode's own choice (room federation) or the run config."""
    return int(context.node_config.get("local-epochs", context.run_config["local-epochs"]))


def _local_data(context: Context):
    """Loaders of this client's partition."""
    pid, num = _partition(context)
    return load_partition(
        partition_id=pid,
        num_partitions=num,
        run_config=context.run_config,
        batch_size=int(context.run_config["batch-size"]),
    )


def _info(context: Context, **extra) -> ConfigRecord:
    """Who answered: lets the server attribute each reply to a client (visualisation).

    Sent in a ConfigRecord, not in the metrics, so FedAvg does not average it.
    """
    pid, _ = _partition(context)
    return ConfigRecord(
        {"partition-id": pid, "local-epochs": _local_epochs(context),
         "host": socket.gethostname(), **extra}
    )


def _check_seat(context: Context, msg: Message) -> Message | None:
    """Error reply if the seat is outside the room (seat > num-partitions)."""
    pid, num = _partition(context)
    if 0 <= pid < num:
        return None
    reason = f"seat {pid + 1} is outside the room (num-partitions = {num})"
    return Message(error=Error(code=0, reason=reason), reply_to=msg)


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
    if (error := _check_seat(context, msg)) is not None:
        return error
    partition_id, _ = _partition(context)
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

    trainloader, _ = _local_data(context)
    epochs = _local_epochs(context)

    # Simulated deadline (phase 1): a client whose simulated training time exceeds it
    # would arrive late, and the server would drop its update. It answers at once
    # with its simulated time only, which saves the training nobody would use.
    sim_time = len(trainloader.dataset) * epochs / IMAGES_PER_SECOND
    sim_deadline = float(context.run_config.get("sim-deadline", 0.0))
    if 0 < sim_deadline < sim_time:
        info = _info(context, **{"sim-time": sim_time, "late": True})
        return Message(content=RecordDict({"info": info}), reply_to=msg)

    model = _model(msg, context)
    start = time.perf_counter()
    train_loss = train_fn(
        model,
        trainloader,
        epochs=epochs,
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
        "info": _info(context, **{"train-time": time.perf_counter() - start,
                                  "sim-time": sim_time}),
    })
    return Message(content=content, reply_to=msg)


@app.evaluate()
def evaluate(msg: Message, context: Context):
    """Evaluate the received global model on the local validation set."""
    if (error := _check_seat(context, msg)) is not None:
        return error
    model = _model(msg, context)
    _, valloader = _local_data(context)

    eval_loss, eval_acc = test_fn(model, valloader, DEVICE)

    metrics = MetricRecord(
        {"eval_loss": eval_loss, "eval_acc": eval_acc, "num-examples": len(valloader.dataset)}
    )
    return Message(
        content=RecordDict({"metrics": metrics, "info": _info(context)}), reply_to=msg
    )
