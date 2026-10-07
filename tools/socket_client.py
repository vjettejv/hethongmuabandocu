"""Bounded JSON RPC to the unchanged frontend Socket.IO 4.x client."""

import json
import queue
import subprocess
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SocketClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ["node", str(ROOT / "tools/runtime/socket-client.cjs")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        self.results = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            self.results.put(json.loads(line))

    def call(self, command, **values):
        self.process.stdin.write(json.dumps({"command": command, **values}) + "\n")
        self.process.stdin.flush()
        try:
            response = self.results.get(timeout=20)
        except queue.Empty:
            raise AssertionError("Socket client operation timed out") from None
        assert response["ok"], response.get("error")
        return response["result"]

    def close(self):
        try:
            self.call("close")
        finally:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
