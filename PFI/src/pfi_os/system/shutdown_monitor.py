from __future__ import annotations

import argparse
import os
import signal
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HeartbeatState:
    def __init__(self, streamlit_pid: int, terminal_tty: str, timeout: int):
        self.streamlit_pid = streamlit_pid
        self.terminal_tty = terminal_tty
        self.timeout = timeout
        self.last_heartbeat = time.time()
        self.seen_heartbeat = False
        self.lock = threading.Lock()
        self.shutdown_started = False

    def heartbeat(self) -> None:
        with self.lock:
            self.last_heartbeat = time.time()
            self.seen_heartbeat = True

    def should_shutdown(self) -> bool:
        with self.lock:
            return self.seen_heartbeat and not self.shutdown_started and time.time() - self.last_heartbeat > self.timeout

    def mark_shutdown(self) -> bool:
        with self.lock:
            if self.shutdown_started:
                return False
            self.shutdown_started = True
            return True


def run_monitor(port: int, streamlit_pid: int, terminal_tty: str, timeout: int) -> None:
    state = HeartbeatState(streamlit_pid=streamlit_pid, terminal_tty=terminal_tty, timeout=timeout)

    class Handler(BaseHTTPRequestHandler):
        def do_OPTIONS(self):  # noqa: N802
            self._send_ok()

        def do_GET(self):  # noqa: N802
            if self.path.startswith("/heartbeat"):
                state.heartbeat()
                self._send_ok()
            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):  # noqa: N802
            if self.path.startswith("/heartbeat"):
                state.heartbeat()
                self._send_ok()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *_args):
            return

        def _send_ok(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        while _pid_exists(streamlit_pid):
            if state.should_shutdown() and state.mark_shutdown():
                _stop_process(streamlit_pid)
                _close_terminal(terminal_tty)
                break
            time.sleep(1)
    finally:
        server.shutdown()
        server.server_close()


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _stop_process(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    for _ in range(10):
        if not _pid_exists(pid):
            return
        time.sleep(0.5)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return


def _close_terminal(terminal_tty: str) -> None:
    if not terminal_tty:
        return
    script = """
on run argv
  set targetTty to item 1 of argv
  tell application "Terminal"
    set targetWindow to missing value
    repeat with w in windows
      repeat with t in tabs of w
        try
          if (tty of t as text) is targetTty then
            set targetWindow to w
          end if
        end try
      end repeat
    end repeat
    if targetWindow is not missing value then
      close targetWindow saving no
      delay 0.2
    end if
    if (count of windows) is 0 then
      quit
    end if
  end tell
end run
"""
    subprocess.run(["osascript", "-", terminal_tty], input=script, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="PFIOS browser heartbeat shutdown monitor.")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--streamlit-pid", type=int, required=True)
    parser.add_argument("--terminal-tty", default="")
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args()
    run_monitor(args.port, args.streamlit_pid, args.terminal_tty, stable_timeout(args.timeout))


def stable_timeout(timeout: int, minimum: int = 60) -> int:
    return max(int(timeout), int(minimum))


if __name__ == "__main__":
    main()
