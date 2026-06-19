from __future__ import annotations

import socket
import importlib.util
from dataclasses import dataclass


@dataclass(frozen=True)
class MoomooHealth:
    available: bool
    status: str
    detail: str
    sdk_available: bool = False


def healthcheck(host: str = "127.0.0.1", port: int = 11111, timeout: float = 0.5) -> MoomooHealth:
    sdk_available = importlib.util.find_spec("moomoo") is not None
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return MoomooHealth(
                True,
                "available",
                f"OpenD socket reachable at {host}:{port}",
                sdk_available=sdk_available,
            )
    except OSError as exc:
        return MoomooHealth(
            False,
            "unavailable",
            f"OpenD socket not reachable at {host}:{port}: {exc.__class__.__name__}: {exc}",
            sdk_available=sdk_available,
        )
