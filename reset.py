#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
from typing import Optional

LOCKFILE = "bot_server.lock"
DISABLE_FILE = "bot_disabled.lock"
SCRIPT_NAMES = ["main_bot.py", "bridge.py"]


def read_lockfile() -> Optional[int]:
    if not os.path.exists(LOCKFILE):
        return None
    try:
        with open(LOCKFILE, "r", encoding="utf-8") as f:
            text = f.read().strip()
            return int(text)
    except Exception:
        return None


def remove_lockfile() -> None:
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
            print(f"Removed lockfile: {LOCKFILE}")
    except Exception as exc:
        print(f"Warning: could not remove lockfile: {exc}")


def create_disable_file() -> None:
    try:
        with open(DISABLE_FILE, "w", encoding="utf-8") as f:
            f.write("disabled")
        print(f"Created disable file: {DISABLE_FILE}")
    except Exception as exc:
        print(f"Warning: could not create disable file: {exc}")


def remove_disable_file() -> None:
    try:
        if os.path.exists(DISABLE_FILE):
            os.remove(DISABLE_FILE)
            print(f"Removed disable file: {DISABLE_FILE}")
    except Exception as exc:
        print(f"Warning: could not remove disable file: {exc}")


def kill_pid(pid: int, name: Optional[str] = None) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        name_str = f" ({name})" if name else ""
        print(f"Sent SIGTERM to PID {pid}{name_str}")
        return True
    except ProcessLookupError:
        return False
    except PermissionError as exc:
        print(f"Permission error killing PID {pid}: {exc}")
        return False
    except Exception as exc:
        print(f"Error killing PID {pid}: {exc}")
        return False


def get_matching_pids() -> set[int]:
    pids: set[int] = set()
    try:
        proc = subprocess.run([
            "pgrep",
            "-f",
            "main_bot.py"
        ], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.splitlines():
                try:
                    pids.add(int(line.strip()))
                except ValueError:
                    pass
    except FileNotFoundError:
        pass

    try:
        proc = subprocess.run([
            "pgrep",
            "-f",
            "bridge.py"
        ], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip():
            for line in proc.stdout.splitlines():
                try:
                    pids.add(int(line.strip()))
                except ValueError:
                    pass
    except FileNotFoundError:
        pass

    if not pids:
        try:
            proc = subprocess.run(["ps", "-eo", "pid,command"], capture_output=True, text=True)
            for line in proc.stdout.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) != 2:
                    continue
                pid_text, cmd = parts
                if any(script in cmd for script in SCRIPT_NAMES):
                    try:
                        pid = int(pid_text)
                        pids.add(pid)
                    except ValueError:
                        pass
        except Exception:
            pass

    own_pid = os.getpid()
    if own_pid in pids:
        pids.remove(own_pid)
    return pids


def kill_matching_processes() -> None:
    pids = get_matching_pids()
    if not pids:
        print("No running main_bot.py or bridge.py processes found.")
        return

    for pid in sorted(pids):
        if kill_pid(pid):
            time.sleep(0.5)
            try:
                os.kill(pid, 0)
                print(f"PID {pid} still alive, sending SIGKILL")
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception as exc:
                print(f"Warning: could not SIGKILL PID {pid}: {exc}")

    print("Process termination requested.")


def print_usage() -> None:
    print("Usage: python3 reset.py [--disable|--enable|--cleanup]")
    print("  --disable  : kill running bot processes and prevent auto-restart")
    print("  --enable   : remove the disable file so bot can start again")
    print("  --cleanup  : kill bot processes and remove only the lockfile")


if __name__ == "__main__":
    action = None
    if len(sys.argv) == 1:
        action = "disable"
    elif len(sys.argv) == 2:
        action = sys.argv[1].lower()
    else:
        print_usage()
        sys.exit(1)

    if action == "--disable" or action == "disable":
        print("Resetting bot server and disabling auto-restart.")
        lock_pid = read_lockfile()
        if lock_pid is not None:
            if kill_pid(lock_pid, name="lockfile"):
                time.sleep(0.5)
            else:
                print(f"Lockfile PID {lock_pid} was not running or could not be killed.")

        kill_matching_processes()
        remove_lockfile()
        create_disable_file()
        print("Reset complete. Bot is disabled until you remove bot_disabled.lock.")
    elif action == "--enable" or action == "enable":
        print("Enabling bot start again.")
        remove_disable_file()
        print("Enable complete. You can now start main_bot.py again.")
    elif action == "--cleanup" or action == "cleanup":
        print("Cleaning up bot processes and lockfile.")
        kill_matching_processes()
        remove_lockfile()
        print("Cleanup complete.")
    else:
        print_usage()
        sys.exit(1)
