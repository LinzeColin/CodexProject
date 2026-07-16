#!/usr/bin/env python3
from __future__ import annotations

import inspect
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


PFI_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HASHED_ASSET_SEGMENT = re.compile(r"(?:^|[./_-])[0-9a-f]{8,}(?=[./_-]|$)", re.IGNORECASE)


def validate_candidate_runtime_roots(environ: Mapping[str, str] | None = None) -> None:
    runtime_environment = os.environ if environ is None else environ
    if runtime_environment.get("PFI_STAGE1_CANDIDATE_MODE") != "1":
        return
    isolated_root = Path(runtime_environment.get("PFI_STAGE1_ISOLATED_ROOT", "")).resolve()
    if (
        isolated_root.parent != Path("/private/tmp")
        or not isolated_root.name.startswith("pfi-v025-s1p13-")
        or not isolated_root.is_dir()
        or isolated_root.is_symlink()
    ):
        raise RuntimeError("candidate isolated root is invalid")
    expected = {
        "HOME": isolated_root / "home",
        "PFI_DATA_HOME": isolated_root / "data",
        "PFI_RUNTIME_DIR": isolated_root / "runtime",
        "TMPDIR": isolated_root / "tmp",
        "XDG_CACHE_HOME": isolated_root / "cache",
        "PFI_BROWSER_PROFILE_DIR": isolated_root / "browser-profile",
        "PYTHONPYCACHEPREFIX": isolated_root / "python-pycache",
    }
    for variable, expected_path in expected.items():
        actual = Path(runtime_environment.get(variable, "")).resolve()
        if actual != expected_path or not actual.is_dir() or actual.is_symlink():
            raise RuntimeError(f"candidate {variable} escaped the isolated root")


def cache_control_for_static_path(path: str) -> str:
    normalized = str(path or "").split("?", 1)[0]
    if not normalized or normalized.endswith("/") or normalized.lower().endswith(".html"):
        return "no-cache, private"
    if HASHED_ASSET_SEGMENT.search(normalized):
        return "public, max-age=31536000, immutable"
    return "no-cache, private"


def install_streamlit_cache_headers() -> None:
    from streamlit.web.server.routes import StaticFileHandler

    signature = inspect.signature(StaticFileHandler.set_extra_headers)
    if list(signature.parameters) != ["self", "path"]:
        raise RuntimeError("unsupported Streamlit StaticFileHandler.set_extra_headers signature")
    if getattr(StaticFileHandler.set_extra_headers, "__pfi_v025_cache_headers__", False):
        return

    def set_extra_headers(self: Any, path: str) -> None:
        self.set_header("Cache-Control", cache_control_for_static_path(path))

    set_extra_headers.__pfi_v025_cache_headers__ = True  # type: ignore[attr-defined]
    StaticFileHandler.set_extra_headers = set_extra_headers


def _starlette_argument_value(argv: list[str]) -> str | None:
    for index, value in enumerate(argv):
        if value.startswith("--server.useStarlette="):
            return value.split("=", 1)[1]
        if value == "--server.useStarlette" and index + 1 < len(argv):
            return argv[index + 1]
    return None


def force_tornado_server(argv: list[str]) -> None:
    requested = _starlette_argument_value(argv)
    if requested is not None and requested.strip().lower() not in {"0", "false", "no"}:
        raise RuntimeError("PFI release cache headers require server.useStarlette=false")
    from streamlit import config

    try:
        config.get_option("server.useStarlette")
    except RuntimeError:
        return
    config.set_option("server.useStarlette", False)


def _path_argument(value: object) -> str:
    return "" if value is None else str(Path(value).expanduser().resolve())


def install_read_model_cache_adapter(
    composite_cache_key: str,
    *,
    ttl_seconds: float = 30,
    streamlit_module: Any | None = None,
    read_model_module: Any | None = None,
    original_builder: Callable[..., dict[str, Any]] | None = None,
):
    if not HEX64.fullmatch(str(composite_cache_key or "")):
        raise ValueError("PFI_STREAMLIT_CACHE_KEY must be a 64-character lowercase SHA-256")
    if ttl_seconds <= 0:
        raise ValueError("read-model cache TTL must be positive")

    if streamlit_module is None:
        import streamlit as streamlit_module
    if read_model_module is None:
        from pfi_os.application import read_model_status as read_model_module
    if original_builder is None:
        from pfi_v02.stage_v021_runtime_api import _ORIGINAL_BUILD_V024_READ_MODEL_STATUS

        original_builder = _ORIGINAL_BUILD_V024_READ_MODEL_STATUS

    existing = getattr(read_model_module, "build_v024_read_model_status", None)
    if getattr(existing, "__pfi_streamlit_cache_key__", None) == composite_cache_key:
        return existing

    @streamlit_module.cache_data(ttl=ttl_seconds, show_spinner=False, persist=None)
    def cached_read_model_status(
        project_root_value: str,
        data_root_value: str,
        release_cache_key: str,
    ) -> dict[str, Any]:
        if release_cache_key != composite_cache_key:
            raise RuntimeError("read-model cache namespace mismatch")
        return original_builder(
            project_root_value or None,
            data_root=data_root_value or None,
        )

    def read_model_adapter(project_root=None, *, data_root=None):
        return cached_read_model_status(
            _path_argument(project_root),
            _path_argument(data_root),
            composite_cache_key,
        )

    read_model_adapter.__name__ = "build_v024_read_model_status"
    read_model_adapter.__doc__ = "PFI v0.2.5 composite-key Streamlit read-model cache adapter."
    read_model_adapter.__pfi_streamlit_cache_key__ = composite_cache_key
    read_model_adapter.__pfi_streamlit_cache_ttl_seconds__ = ttl_seconds
    read_model_adapter.clear = cached_read_model_status.clear
    read_model_module.build_v024_read_model_status = read_model_adapter
    return read_model_adapter


def ensure_ephemeral_runtime_api_owner(
    *,
    environ: Mapping[str, str] | None = None,
    ensure_server: Callable[[], str] | None = None,
) -> str:
    runtime_environment = os.environ if environ is None else environ
    if runtime_environment.get("PFI_V021_RUNTIME_API_PORT") != "0":
        raise RuntimeError("PFI_V021_RUNTIME_API_PORT must be exactly 0")
    if ensure_server is None:
        from pfi_v02.stage_v021_runtime_api import ensure_v021_runtime_api_server

        ensure_server = ensure_v021_runtime_api_server

    base_url = str(ensure_server())
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("runtime API owner must bind an HTTP loopback address")
    if parsed.port is None or parsed.port <= 0:
        raise RuntimeError("runtime API owner did not return a valid port")
    excluded_ports = {
        8501,
        8502,
        8766,
        *(
            int(value)
            for value in (
                runtime_environment.get("PFI_STREAMLIT_PORT", ""),
                runtime_environment.get("PFI_HEARTBEAT_PORT", ""),
            )
            if str(value).isdigit()
        ),
    }
    if parsed.port in excluded_ports:
        raise RuntimeError("runtime API owner selected a protected or reserved port")
    return base_url


def publish_candidate_runtime_api_marker(base_url: str) -> None:
    if os.environ.get("PFI_STAGE1_CANDIDATE_MODE") != "1":
        return
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port:
        raise RuntimeError("candidate runtime API marker requires an exact loopback endpoint")
    isolated_root = Path(os.environ.get("PFI_STAGE1_ISOLATED_ROOT", "")).resolve()
    runtime_dir = Path(os.environ.get("PFI_RUNTIME_DIR", "")).resolve()
    if (
        isolated_root.parent != Path("/private/tmp")
        or runtime_dir != isolated_root / "runtime"
        or not runtime_dir.is_dir()
        or runtime_dir.is_symlink()
    ):
        raise RuntimeError("candidate runtime API marker escaped the isolated root")
    marker = runtime_dir / "pfi_runtime_api.env"
    temporary = runtime_dir / f".pfi_runtime_api.env.tmp.{os.getpid()}"
    payload = (
        "PFI_RUNTIME_API_SCHEMA=PFIV025Stage1OfficialCandidateRuntimeAPIV1\n"
        f"PFI_RUNTIME_API_PORT={parsed.port}\n"
    ).encode("ascii")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary, flags, 0o600)
    complete = False
    try:
        os.fchmod(descriptor, 0o600)
        if os.write(descriptor, payload) != len(payload):
            raise RuntimeError("candidate runtime API marker write was incomplete")
        os.fsync(descriptor)
        complete = True
    finally:
        os.close(descriptor)
        if not complete:
            temporary.unlink(missing_ok=True)
    temporary.replace(marker)
    marker.chmod(0o600)


def install_release_runtime_guards(composite_cache_key: str) -> str:
    """Install the same cache and runtime-API guards for canonical and candidate UI."""

    validate_candidate_runtime_roots()
    original_builder = None
    if os.environ.get("PFI_STAGE1_CANDIDATE_MODE") == "1":
        from pfi_v02.stage_v021_runtime_api import (
            build_v025_stage1_candidate_read_model_status,
        )

        def candidate_builder(_project_root=None, *, data_root=None):
            del data_root
            return build_v025_stage1_candidate_read_model_status()

        original_builder = candidate_builder
    install_read_model_cache_adapter(
        composite_cache_key,
        original_builder=original_builder,
    )
    base_url = ensure_ephemeral_runtime_api_owner()
    publish_candidate_runtime_api_marker(base_url)
    return base_url


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cache_key = str(os.environ.get("PFI_STREAMLIT_CACHE_KEY") or "")
    if not HEX64.fullmatch(cache_key):
        print("PFI_STREAMLIT_CACHE_KEY is missing or invalid; refusing to start Streamlit.", file=sys.stderr)
        return 2
    try:
        force_tornado_server(args)
        install_streamlit_cache_headers()
        install_release_runtime_guards(cache_key)
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"PFI Streamlit release cache guard failed: {exc}", file=sys.stderr)
        return 2

    from streamlit.web import cli

    result = cli.main(args=args, prog_name="streamlit", standalone_mode=False)
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
