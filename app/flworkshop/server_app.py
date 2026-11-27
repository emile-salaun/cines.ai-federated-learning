"""flworkshop: ServerApp (FedAvg strategy, global evaluation, per-client tracking)."""

import json
import math
import random
import re
import time
from pathlib import Path

import torch
from flwr.app import ArrayRecord, ConfigRecord, Context, MetricRecord
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg

from flworkshop.data import class_names, input_shape, load_test, load_test_subset
from flworkshop.paths import RUNS_DIR
from flworkshop.task import build_model, test_per_class

app = ServerApp()

DEVICE = torch.device("cpu")


def results_path(cfg, run_id: int) -> str:
    """Where this run's results go: `results-file` if set, else RUNS_DIR/<run-name>.json.

    The dashboard lists every JSON in RUNS_DIR, so a run started with a plain
    `flwr run` shows up without any extra option. An empty or invalid `run-name`
    falls back to run-<run id>.
    """
    if cfg.get("results-file"):
        return str(cfg["results-file"])
    name = str(cfg.get("run-name", ""))
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        name = f"run-{run_id}"
    return str(RUNS_DIR / f"{name}.json")


class ResultsWriter:
    """Write per-round results to a JSON file, rewritten after every round.

    The path must be absolute: the app runs from a copy installed under ~/.flwr/apps/,
    not from the project directory (see `results_path`).

    Each round entry holds the global model's results and, per client (partition id),
    what the server saw: status (ok / failed / late / idle), local model accuracy on a
    test subset, per-class accuracy, update divergence, training time, data volume, the
    client's impact (leave-one-out, see `TrackedFedAvg`), and the messages exchanged
    (sizes and timestamps, under "comm").

    "leaderboard" sums, per client, the rounds on time, late and missed, and the impact.
    """

    def __init__(self, path: str, run_config, classes: list[str]):
        self.path = Path(path).expanduser() if path else None
        self.data = {
            "config": {k: v for k, v in run_config.items()},
            "classes": classes,
            "started_at": time.time(),
            "rounds": [],
            "leaderboard": [],
            "finished": False,
        }
        self.node_map: dict[int, int] = {}  # node id -> partition id
        self.pending: dict[int, dict] = {}  # round -> data collected before evaluation
        self._flush()

    # -- collection, called by the strategy during a round ---------------------------
    def _round(self, server_round: int) -> dict:
        return self.pending.setdefault(
            server_round,
            {"sampled": [], "failed_nodes": [], "late_nodes": [], "clients": {},
             "comm": {}, "comm_nodes": {}},
        )

    def set_sampled(self, server_round: int, node_ids: list[int]) -> None:
        self._round(server_round)["sampled"] = list(node_ids)

    def add_failure(self, server_round: int, node_id: int) -> None:
        self._round(server_round)["failed_nodes"].append(node_id)

    def add_late(self, server_round: int, node_id: int) -> None:
        self._round(server_round)["late_nodes"].append(node_id)

    def late_reply(self, server_round: int, node_id: int, pid: int, delay: float,
                   local_epochs: int | None = None) -> None:
        """A reply that arrived after the deadline of its round (found in a later round)."""
        self.node_map[node_id] = pid
        for entry in self.data["rounds"]:
            if entry["round"] == server_round:
                client = entry["clients"].setdefault(str(pid), {})
                client.update(status="late", late_by=delay, local_epochs=local_epochs)
                entry["clients_late"] = sum(
                    c["status"] == "late" for c in entry["clients"].values())
        self._update_leaderboard()
        self._flush()

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
        for node in pending["late_nodes"]:
            pid = self.node_map.get(node)
            if pid is not None:
                clients.setdefault(pid, {})["status"] = "late"
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
            "clients_late": len(pending["late_nodes"]),
            "clients_sampled": len(pending["sampled"]),
            "clients": {str(pid): clients[pid] for pid in sorted(clients)},
            "comm": pending["comm"],
        })
        self._update_leaderboard()
        self._flush()

    def _update_leaderboard(self) -> None:
        """Per client: rounds on time, late, missed (disconnected), total impact."""
        board: dict[str, dict] = {}
        for entry in self.data["rounds"]:
            for pid, c in entry["clients"].items():
                row = board.setdefault(pid, {"client": int(pid), "on_time": 0, "late": 0,
                                             "missed": 0, "impact": 0.0})
                if c["status"] == "ok":
                    row["on_time"] += 1
                    row["impact"] += c.get("impact") or 0.0
                elif c["status"] == "late":
                    row["late"] += 1
                elif c["status"] == "failed":
                    row["missed"] += 1
                if c.get("local_epochs") is not None:
                    row["local_epochs"] = c["local_epochs"]
        rounds = max(sum(e["round"] >= 1 for e in self.data["rounds"]), 1)
        for row in board.values():
            row["presence"] = row["on_time"] / rounds
        self.data["leaderboard"] = sorted(board.values(), key=lambda r: -r["impact"])

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

    Contribution (leave-one-out): each round, the server also evaluates the average
    without each client in turn, on the same subset. A client's impact is the accuracy
    of the full average minus the accuracy without it, in points. With one client only,
    "without it" is the previous global model. Nothing is declared by the clients.

    Round deadline: `start(timeout=...)` stops waiting after `timeout` seconds; a
    sampled client that has not answered by then is "late" for that round and its
    update is ignored. Its reply, if it comes later, is picked up in a later round
    only to record the delay.

    Simulated deadline (`sim-deadline`, phase 1): each client computes its simulated
    training time (data size x local epochs / a fixed speed); a client over the
    deadline answers "late" without training, and the server leaves it out.
    """

    def __init__(self, writer: ResultsWriter, shape, subset_loader, num_classes, **kwargs):
        super().__init__(**kwargs)
        self.writer = writer
        self.shape = shape
        self.subset_loader = subset_loader
        self.num_classes = num_classes
        self._global_state = None
        self._grid = None
        self.sim_deadline = 0.0                    # set by main() from `sim-deadline`
        self._sent: dict[int, list] = {}           # round -> train messages sent
        self._waiting: dict[str, tuple] = {}       # message id -> (round, node, deadline)

    def configure_train(self, server_round, arrays, config, grid):
        self._grid = grid
        self._global_state = arrays.to_torch_state_dict()
        messages = list(super().configure_train(server_round, arrays, config, grid))
        self._sent[server_round] = messages        # message ids are set when pushed
        self.writer.set_sampled(server_round, [m.metadata.dst_node_id for m in messages])
        self.writer.comm_round(server_round, train_sent=time.time())
        for m in messages:
            self.writer.comm_node(server_round, m.metadata.dst_node_id,
                                  train_bytes_down=_bytes(m.content))
        return messages

    def aggregate_train(self, server_round, replies):
        replies = list(replies)
        now = time.time()
        self.writer.comm_round(server_round, train_received=now)
        sent = {m.metadata.message_id: m.metadata.dst_node_id
                for m in self._sent.pop(server_round, [])}
        answered = set()
        on_time = []                               # (node, state, num_examples)
        for msg in replies:
            msg_id = msg.metadata.reply_to_message_id
            answered.add(msg_id)
            # Errors returned by the SuperLink (node offline) come from the SuperLink,
            # not from the node: find the node through the message it answers.
            node = sent.get(msg_id, msg.metadata.src_node_id)
            self.writer.comm_node(
                server_round, node,
                train_reply_at=msg.metadata.created_at,
                train_bytes_up=0 if msg.has_error() else _bytes(msg.content),
            )
            if msg.has_error():
                self.writer.add_failure(server_round, node)
                continue
            info = msg.content["info"]
            if info.get("late"):              # missed the simulated deadline
                self.writer.add_client(server_round, node, int(info["partition-id"]), {
                    "status": "late", "late_by": float(info["sim-time"]) - self.sim_deadline,
                    "local_epochs": int(info.get("local-epochs", 0)) or None,
                })
                continue
            state = msg.content["arrays"].to_torch_state_dict()
            metrics = msg.content["metrics"]
            _, acc, per_class = self._evaluate(state)
            self.writer.add_client(server_round, node, int(info["partition-id"]), {
                "local_acc": acc,
                "local_per_class": per_class,
                "divergence": _distance(state, self._global_state),
                "train_loss": float(metrics["train_loss"]),
                "num_examples": int(metrics["num-examples"]),
                "train_time": float(info["train-time"]),
                "sim_time": float(info.get("sim-time", 0.0)),
                "local_epochs": int(info.get("local-epochs", 0)) or None,
                "host": str(info["host"]),
            })
            on_time.append((node, state, int(metrics["num-examples"])))

        # Sampled but no answer before the deadline: late this round.
        for msg_id, node in sent.items():
            if msg_id not in answered:
                self.writer.add_late(server_round, node)
                self._waiting[msg_id] = (server_round, node, now)
        self._collect_late_replies()

        start = time.time()
        kept = [m for m in replies if m.has_error() or not m.content["info"].get("late")]
        result = super().aggregate_train(server_round, kept)
        self.writer.comm_round(server_round, aggregate_start=start,
                               aggregate_end=time.time())
        self._leave_one_out(server_round, on_time)
        return result

    def _evaluate(self, state):
        model = build_model(self.shape)
        model.load_state_dict(state)
        return test_per_class(model, self.subset_loader, DEVICE, self.num_classes)

    def _leave_one_out(self, server_round, on_time) -> None:
        """Impact of each on-time client: accuracy with it minus accuracy without it."""
        if not on_time:
            return
        start = time.time()
        keys = [k for k, v in on_time[0][1].items() if v.is_floating_point()]
        total = sum(n for _, _, n in on_time)
        weighted = {k: sum(st[k].double() * n for _, st, n in on_time) for k in keys}
        full = {k: (weighted[k] / total).float() for k in keys}
        acc_full = self._evaluate(full)[1]
        for node, state, n in on_time:
            if len(on_time) == 1:
                without = self._global_state
            else:
                without = {k: ((weighted[k] - state[k].double() * n) / (total - n)).float()
                           for k in keys}
            pid = self.writer.node_map[node]
            impact = 100 * (acc_full - self._evaluate(without)[1])
            self.writer.add_client(server_round, node, pid, {"impact": impact})
        self.writer.comm_round(server_round, score_time=time.time() - start)

    def _collect_late_replies(self) -> None:
        """Pick up replies that arrived after their deadline, to record the delay."""
        if not self._waiting or self._grid is None:
            return
        try:
            replies = list(self._grid.pull_messages(list(self._waiting)))
        except Exception:  # noqa: BLE001 - informative only, never stop the run
            return
        for msg in replies:
            server_round, node, deadline = self._waiting.pop(
                msg.metadata.reply_to_message_id, (None, None, None))
            if server_round is None or msg.has_error():
                continue
            info = msg.content["info"]
            self.writer.late_reply(server_round, node, int(info["partition-id"]),
                                   max(0.0, msg.metadata.created_at - deadline),
                                   int(info.get("local-epochs", 0)) or None)

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
    writer = ResultsWriter(results_path(cfg, context.run_id), cfg, classes)

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
    strategy.sim_deadline = float(cfg.get("sim-deadline", 0.0))
    seed = int(cfg.get("seed", 42))
    torch.manual_seed(seed)  # same initial model for every run
    random.seed(seed)        # same sequence of client draws for fraction-train

    timeout = float(cfg.get("round-timeout", 0.0)) or 3600.0  # Flower's default
    result = strategy.start(
        grid=grid,
        timeout=timeout,
        initial_arrays=ArrayRecord(build_model(shape).state_dict()),
        train_config=ConfigRecord({"lr": float(cfg["learning-rate"])}),
        num_rounds=int(cfg["num-server-rounds"]),
        evaluate_fn=global_evaluate,
    )
    writer.finish(result)

    if cfg["save-model"]:
        print("\nSaving final model to disk...")
        torch.save(result.arrays.to_torch_state_dict(), "final_model.pt")
