"""flworkshop: ServerApp (FedAvg strategy, global evaluation, per-client tracking)."""

import json
import math
import random
import time
from pathlib import Path

import torch
from flwr.app import ArrayRecord, ConfigRecord, Context, MetricRecord
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from flworkshop.data import class_names, input_shape, load_test, load_test_subset
from flworkshop.task import build_model, test_per_class

app = ServerApp()

DEVICE = torch.device("cpu")


class ResultsWriter:
    """Write per-round results to a JSON file, rewritten after every round.

    Disabled when ``results-file`` is empty. The path must be absolute: the app runs
    from a copy installed under ~/.flwr/apps/, not from the project directory.

    Each round entry holds the global model's results and, per client (partition id),
    what the server saw: status (ok / failed / idle), local model accuracy on a test
    subset, per-class accuracy, update divergence, training time, data volume, and the
    messages exchanged (sizes and timestamps, under "comm").
    """

    def __init__(self, path: str, run_config, classes: list[str]):
        self.path = Path(path).expanduser() if path else None
        self.data = {
            "config": {k: v for k, v in run_config.items()},
            "classes": classes,
            "started_at": time.time(),
            "rounds": [],
            "finished": False,
        }
        self.node_map: dict[int, int] = {}  # node id -> partition id
        self.pending: dict[int, dict] = {}  # round -> data collected before evaluation
        self._flush()

    # -- collection, called by the strategy during a round ---------------------------
    def _round(self, server_round: int) -> dict:
        return self.pending.setdefault(
            server_round,
            {"sampled": [], "failed_nodes": [], "clients": {}, "comm": {}, "comm_nodes": {}},
        )

    def set_sampled(self, server_round: int, node_ids: list[int]) -> None:
        self._round(server_round)["sampled"] = list(node_ids)

    def add_failure(self, server_round: int, node_id: int) -> None:
        self._round(server_round)["failed_nodes"].append(node_id)

    def add_client(self, server_round: int, node_id: int, pid: int, values: dict) -> None:
        self.node_map[node_id] = pid
        self._round(server_round)["clients"].setdefault(pid, {}).update(values)

    def comm_round(self, server_round: int, **times) -> None:
        """Server-side timestamps of the round phases (send, receive, aggregate...)."""
        self._round(server_round)["comm"].update(times)

    def comm_node(self, server_round: int, node_id: int, **values) -> None:
        """Per-message data (sizes, reply timestamps), keyed by node until mapped."""
        self._round(server_round)["comm_nodes"].setdefault(node_id, {}).update(values)

    # -- one entry per round, written after the global evaluation ---------------------
    def add_round(self, server_round, accuracy, loss, per_class) -> None:
        pending = self.pending.pop(server_round, None) or self._round(server_round)
        self.pending.pop(server_round, None)
        clients = pending["clients"]
        for node, values in pending["comm_nodes"].items():
            pid = self.node_map.get(node)
            if pid is not None:
                clients.setdefault(pid, {})["comm"] = values
        for node in pending["failed_nodes"]:
            pid = self.node_map.get(node)
            if pid is not None:
                clients.setdefault(pid, {})["status"] = "failed"
        for pid, values in clients.items():
            values.setdefault("status", "ok" if "local_acc" in values else "idle")
        for pid in set(self.node_map.values()) - set(clients):
            clients[pid] = {"status": "idle"}
        pending["comm"]["end"] = time.time()

        self.data["rounds"].append({
            "round": server_round,
            "time": time.time(),
            "accuracy": accuracy,
            "loss": loss,
            "per_class": per_class,
            "clients_ok": sum(c["status"] == "ok" for c in clients.values()),
            "clients_failed": len(pending["failed_nodes"]),
            "clients_sampled": len(pending["sampled"]),
            "clients": {str(pid): clients[pid] for pid in sorted(clients)},
            "comm": pending["comm"],
        })
        self._flush()

    def finish(self, result) -> None:
        train = {int(r): dict(m) for r, m in result.train_metrics_clientapp.items()}
        evaluate = {int(r): dict(m) for r, m in result.evaluate_metrics_clientapp.items()}
        for entry in self.data["rounds"]:
            entry["train_loss"] = train.get(entry["round"], {}).get("train_loss")
            entry["client_eval_acc"] = evaluate.get(entry["round"], {}).get("eval_acc")
        self.data["finished"] = True
        self._flush()

    def _flush(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=1))
        tmp.replace(self.path)


class TrackedFedAvg(FedAvg):
    """FedAvg that records, every round, what each client sent back.

    Aggregation itself is unchanged: the extra work only reads the replies. Each local
    model is evaluated on a small fixed test subset, which shows how good every client
    would be on its own, before aggregation.
    """

    def __init__(self, writer: ResultsWriter, shape, subset_loader, num_classes, **kwargs):
        super().__init__(**kwargs)
        self.writer = writer
        self.shape = shape
        self.subset_loader = subset_loader
        self.num_classes = num_classes
        self._global_state = None

    def configure_train(self, server_round, arrays, config, grid):
        self._global_state = arrays.to_torch_state_dict()
        messages = list(super().configure_train(server_round, arrays, config, grid))
        self.writer.set_sampled(server_round, [m.metadata.dst_node_id for m in messages])
        self.writer.comm_round(server_round, train_sent=time.time())
        for m in messages:
            self.writer.comm_node(server_round, m.metadata.dst_node_id,
                                  train_bytes_down=_bytes(m.content))
        return messages

    def aggregate_train(self, server_round, replies):
        replies = list(replies)
        self.writer.comm_round(server_round, train_received=time.time())
        for msg in replies:
            node = msg.metadata.src_node_id
            self.writer.comm_node(
                server_round, node,
                train_reply_at=msg.metadata.created_at,
                train_bytes_up=0 if msg.has_error() else _bytes(msg.content),
            )
            if msg.has_error():
                self.writer.add_failure(server_round, node)
                continue
            info = msg.content["info"]
            state = msg.content["arrays"].to_torch_state_dict()
            model = build_model(self.shape)
            model.load_state_dict(state)
            _, acc, per_class = test_per_class(
                model, self.subset_loader, DEVICE, self.num_classes
            )
            metrics = msg.content["metrics"]
            self.writer.add_client(server_round, node, int(info["partition-id"]), {
                "local_acc": acc,
                "local_per_class": per_class,
                "divergence": _distance(state, self._global_state),
                "train_loss": float(metrics["train_loss"]),
                "num_examples": int(metrics["num-examples"]),
                "train_time": float(info["train-time"]),
                "host": str(info["host"]),
            })
        start = time.time()
        result = super().aggregate_train(server_round, replies)
        self.writer.comm_round(server_round, aggregate_start=start,
                               aggregate_end=time.time())
        return result

    def configure_evaluate(self, server_round, arrays, config, grid):
        messages = list(super().configure_evaluate(server_round, arrays, config, grid))
        self.writer.comm_round(server_round, eval_sent=time.time())
        for m in messages:
            self.writer.comm_node(server_round, m.metadata.dst_node_id,
                                  eval_bytes_down=_bytes(m.content))
        return messages

    def aggregate_evaluate(self, server_round, replies):
        replies = list(replies)
        self.writer.comm_round(server_round, eval_received=time.time())
        for msg in replies:
            self.writer.comm_node(
                server_round, msg.metadata.src_node_id,
                eval_reply_at=msg.metadata.created_at,
                eval_bytes_up=0 if msg.has_error() else _bytes(msg.content),
            )
            if msg.has_error():
                continue
            info = msg.content["info"]
            self.writer.add_client(
                server_round, msg.metadata.src_node_id, int(info["partition-id"]),
                {"global_on_local_acc": float(msg.content["metrics"]["eval_acc"])},
            )
        return super().aggregate_evaluate(server_round, replies)


def _bytes(content) -> int:
    """Size of a message's payload (arrays, config, metrics), in bytes."""
    total = 0
    for record in content.values():
        try:
            total += record.count_bytes()
        except AttributeError:
            pass
    return total


def _distance(state: dict, reference: dict | None) -> float | None:
    """L2 distance between two models' weights (how far a client moved this round)."""
    if reference is None:
        return None
    total = 0.0
    for key, value in state.items():
        if value.is_floating_point():
            total += (value - reference[key]).pow(2).sum().item()
    return math.sqrt(total)


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Entry point of the ServerApp."""
    cfg = context.run_config
    shape = input_shape(cfg)
    classes = class_names(cfg)
    testloader = load_test(cfg)  # loaded once, reused every round
    writer = ResultsWriter(str(cfg.get("results-file", "")), cfg, classes)

    def global_evaluate(server_round: int, arrays: ArrayRecord) -> MetricRecord:
        """Evaluate the global model on the centralized test set."""
        model = build_model(shape)
        model.load_state_dict(arrays.to_torch_state_dict())
        loss, acc, per_class = test_per_class(model, testloader, DEVICE, len(classes))
        writer.add_round(server_round, acc, loss, per_class)
        return MetricRecord({"accuracy": acc, "loss": loss})

    strategy = TrackedFedAvg(
        writer,
        shape,
        load_test_subset(cfg),
        len(classes),
        fraction_train=float(cfg.get("fraction-train", 1.0)),
        fraction_evaluate=float(cfg["fraction-evaluate"]),
        min_train_nodes=1,     # let fraction-train go down to a single client
        min_evaluate_nodes=1,
    )
    seed = int(cfg.get("seed", 42))
    torch.manual_seed(seed)  # same initial model for every run
    random.seed(seed)        # same sequence of client draws for fraction-train

    result = strategy.start(
        grid=grid,
        initial_arrays=ArrayRecord(build_model(shape).state_dict()),
        train_config=ConfigRecord({"lr": float(cfg["learning-rate"])}),
        num_rounds=int(cfg["num-server-rounds"]),
        evaluate_fn=global_evaluate,
    )
    writer.finish(result)

    if cfg["save-model"]:
        print("\nSaving final model to disk...")
        torch.save(result.arrays.to_torch_state_dict(), "final_model.pt")
