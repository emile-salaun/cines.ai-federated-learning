"""Phase 2 helpers: join the room federation with one real SuperNode.

    from flworkshop import room
    room.join(epochs=2)        # start your SuperNode on your seat, with your local epochs
    room.status()              # is it running, how many rounds has it trained?
    room.leave()               # stop it (failure exercise); room.join(...) again to rejoin

`join` runs Flower's own command, `flower-supernode`, in the background and prints it:
the same line works in a terminal. Your seat number is
your partition of the data (seat 1 = partition 0); the trainers' run sets how many
partitions the room has (`num-partitions`), so every seat gets the same data whatever
the headcount.

Defaults, for a SuperNode on the hub: the seat comes from the digits at the end of the
user name (`user07` -> seat 7) or from FL_WORKSHOP_SEAT, the SuperLink address from
FL_WORKSHOP_SUPERLINK (default 127.0.0.1:9092, the room SuperLink on the same machine).
On a laptop, pass both: room.join(epochs=2, seat=7, superlink="<vm-host>:9092").
"""

import getpass
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from flworkshop.viz import ENV

STATE_DIR = Path("~/.cache/fl-workshop").expanduser()
PID_FILE = STATE_DIR / "supernode.pid"
LOG_FILE = STATE_DIR / "supernode.log"
EPOCHS = (1, 2, 5, 10)
BASE_PORT = 9100   # each SuperNode's local Runtime API port: 9100 + seat


def _seat(seat: int | None) -> int:
    if seat is not None:
        return int(seat)
    if os.environ.get("FL_WORKSHOP_SEAT"):
        return int(os.environ["FL_WORKSHOP_SEAT"])
    match = re.search(r"(\d+)$", getpass.getuser())
    if not match:
        raise ValueError("No seat number in your user name: pass it, e.g. room.join(seat=7)")
    return int(match.group(1))


def _running_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def _stop_local_simulation() -> None:
    """Stop your phase 1 SuperLink (simulation mode) to free memory for phase 2.

    Only processes of your own user started with `--simulation`; the next `flwr run`
    in the phase 1 notebook starts it again.
    """
    if not shutil.which("pkill"):
        return
    subprocess.run(["pkill", "-u", str(os.getuid()), "-f", "flower-superlink.*--simulation"],
                   capture_output=True)


def command(epochs: int, seat: int, superlink: str) -> list[str]:
    """The `flower-supernode` command line for this seat."""
    exe = shutil.which("flower-supernode", path=str(Path(sys.executable).parent)) \
        or "flower-supernode"
    return [exe, "--insecure", "--superlink", superlink,
            "--port", str(BASE_PORT + seat),
            "--node-config", f"seat={seat} local-epochs={epochs}"]


def join(epochs: int = 2, seat: int | None = None, superlink: str | None = None) -> None:
    """Start your SuperNode in the background (one per seat)."""
    if epochs not in EPOCHS:
        raise ValueError(f"epochs must be one of {EPOCHS}")
    seat = _seat(seat)
    superlink = superlink or os.environ.get("FL_WORKSHOP_SUPERLINK", "127.0.0.1:9092")
    if (pid := _running_pid()) is not None:
        print(f"Your SuperNode is already running (pid {pid}). room.leave() first to "
              "change your local epochs.")
        return
    _stop_local_simulation()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    cmd = command(epochs, seat, superlink)
    bindir = str(Path(sys.executable).parent)   # the SuperNode starts Flower's helpers
    env = {**os.environ, **ENV, "PATH": bindir + os.pathsep + os.environ.get("PATH", "")}
    with LOG_FILE.open("w") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env,
                                start_new_session=True)
    PID_FILE.write_text(str(proc.pid))
    time.sleep(3)
    shown = " ".join(["flower-supernode", *cmd[1:-1], f'"{cmd[-1]}"'])
    if proc.poll() is not None:
        print(f"The SuperNode stopped at once. Last lines of {LOG_FILE}:\n")
        print("\n".join(LOG_FILE.read_text().splitlines()[-10:]))
        return
    print(f"Seat {seat}, {epochs} local epoch(s), SuperLink {superlink}")
    print(f"Running: {shown}")
    print("Check it with room.status(); it waits for the trainers' run.")


def status() -> None:
    """Is your SuperNode running, and how many rounds has it trained?"""
    pid = _running_pid()
    text = LOG_FILE.read_text() if LOG_FILE.exists() else ""
    received = text.count("Receiving: train message")
    sent = text.count("Sending: train message")
    connected = "SuperNode ID" in text
    if pid is None:
        print("Your SuperNode is not running." + (" Start it with room.join(...)."
                                                  if not text else " See room.log()."))
        return
    if "Traceback" in text:
        print(f"Your SuperNode hit an error (pid {pid}). Last lines of its log:\n")
        log(8)
        return
    state = "connected" if connected else "connecting to the SuperLink..."
    print(f"SuperNode running (pid {pid}), {state}")
    print(f"Rounds received: {received}, updates sent: {sent}")


def log(lines: int = 20) -> None:
    """Last lines of your SuperNode's log."""
    if not LOG_FILE.exists():
        print("No log yet: start your SuperNode with room.join(...).")
        return
    clean = re.sub(r"\x1b\[[0-9;]*m", "", LOG_FILE.read_text())
    kept = [line for line in clean.splitlines() if line.strip(" INFO:")]
    print("\n".join(kept[-lines:]))


def leave() -> None:
    """Stop your SuperNode (the server sees it as disconnected)."""
    pid = _running_pid()
    if pid is None:
        print("Your SuperNode is not running.")
        return
    os.killpg(pid, signal.SIGTERM)
    PID_FILE.unlink(missing_ok=True)
    print(f"SuperNode stopped (pid {pid}). Rejoin with room.join(epochs=...).")
