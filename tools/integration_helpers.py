"""Shared helpers for the current Python full-system integration suite."""

import json
import subprocess
import time

from verify_runtime import command, container_name


def literal(value):
    return "CONVERT(0x" + value.encode().hex() + " USING utf8mb4)"


def environment(service):
    row = json.loads(command(["docker", "inspect", service]))[0]
    return dict(item.split("=", 1) for item in row["Config"]["Env"] if "=" in item)


def wait_for(check):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError("Canonical side effect missing")


def private_logs(service, since):
    result = subprocess.run(
        ["docker", "logs", "--since", since, container_name(service)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    return result.stdout + result.stderr
