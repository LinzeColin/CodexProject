from __future__ import annotations

import socket
import importlib.util
from dataclasses import dataclass
from typing import Any

from app.config import Settings


@dataclass(frozen=True)
class MoomooHealth:
    available: bool
    status: str
    detail: str
    sdk_available: bool = False
    opend_lifecycle: dict[str, object] | None = None
    cleanup: dict[str, object] | None = None
    opend_lifecycle_handle: Any | None = None
    cleanup_required: bool = False


def healthcheck(
    host: str = "127.0.0.1",
    port: int = 11111,
    timeout: float = 0.5,
    *,
    settings: Settings | None = None,
    auto_start_opend: bool = False,
    keep_auto_started_opend: bool = False,
    opend_wait_seconds: float = 45.0,
) -> MoomooHealth:
    lifecycle_dict: dict[str, object] | None = None
    lifecycle_handle: Any | None = None
    cleanup_required = False
    if auto_start_opend and settings is not None:
        from app.core.moomoo_lifecycle import ensure_opend, lifecycle_to_dict

        lifecycle = ensure_opend(
            settings,
            host=host,
            port=port,
            timeout=timeout,
            auto_start=True,
            cleanup_if_started=not keep_auto_started_opend,
            wait_seconds=opend_wait_seconds,
        )
        lifecycle_handle = lifecycle
        lifecycle_dict = lifecycle_to_dict(lifecycle)
        cleanup_required = bool(not keep_auto_started_opend and lifecycle.started_by_tool)

    sdk_available = importlib.util.find_spec("moomoo") is not None
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return MoomooHealth(
                True,
                "available",
                f"moomoo_OpenD socket reachable at {host}:{port}",
                sdk_available=sdk_available,
                opend_lifecycle=lifecycle_dict,
                cleanup=None,
                opend_lifecycle_handle=lifecycle_handle,
                cleanup_required=cleanup_required,
            )
    except OSError as exc:
        return MoomooHealth(
            False,
            "unavailable",
            f"moomoo_OpenD socket not reachable at {host}:{port}: {exc.__class__.__name__}: {exc}",
            sdk_available=sdk_available,
            opend_lifecycle=lifecycle_dict,
            cleanup=None,
            opend_lifecycle_handle=lifecycle_handle,
            cleanup_required=cleanup_required,
        )
