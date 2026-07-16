from __future__ import annotations

import importlib.util
import hashlib
import inspect
import json
import os
import plistlib
import re
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path
from types import ModuleType
from typing import Callable

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SRC_ROOT = PFI_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
CANDIDATE_MODULE_PATH = PFI_ROOT / "scripts" / "v025" / "stage1_phase13_candidate.py"
CANDIDATE_ENV_PATH = PFI_ROOT / "scripts" / "v025" / "stage1_phase13_candidate_env.sh"
BROWSER_VALIDATOR_PATH = PFI_ROOT / "scripts" / "v025" / "browser_validate_stage1_phase13.mjs"
OFFICIAL_APP_PATH = PFI_ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py"
SHUTDOWN_MONITOR_PATH = PFI_ROOT / "src" / "pfi_os" / "system" / "shutdown_monitor.py"
LSREGISTER = Path(
    "/System/Library/Frameworks/CoreServices.framework/Frameworks/"
    "LaunchServices.framework/Support/lsregister"
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPORTED_CANDIDATE_PATHS = (
    "HOME",
    "PFI_DATA_HOME",
    "PFI_RUNTIME_DIR",
    "TMPDIR",
    "XDG_CACHE_HOME",
    "PFI_BROWSER_PROFILE_DIR",
    "PYTHONPYCACHEPREFIX",
)
EXPORTED_CANDIDATE_IDENTITY = (
    "PFI_CANDIDATE_APP_PATH_SHA256",
    "PFI_CANDIDATE_EXECUTABLE_SHA256",
    "PFI_CANDIDATE_BUNDLE_SHA256",
)
CANONICAL_SYMBOLS = {
    "applications": "${APPLICATIONS}/PFI.app",
    "desktop": "${HOME}/Desktop/PFI.app",
    "downloads": "${HOME}/Downloads/PFI.app",
}


def _node_binary() -> str:
    candidate = os.environ.get("PFI_NODE_EXE") or shutil.which("node")
    if not candidate or not Path(candidate).is_file():
        pytest.fail("Node.js is required for the Stage 1 Phase 1.3 browser contract tests")
    return candidate


def load_candidate_module() -> ModuleType:
    if not CANDIDATE_MODULE_PATH.is_file():
        pytest.fail("S1-P3 requires the isolated-candidate Python module")
    spec = importlib.util.spec_from_file_location("pfi_v025_stage1_phase13_candidate", CANDIDATE_MODULE_PATH)
    assert spec and spec.loader, "S1-P3 candidate module must be importable"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def external_evidence_factory() -> Callable[[], Path]:
    roots: list[Path] = []

    def create() -> Path:
        root = Path(
            tempfile.mkdtemp(
                prefix="pfi-v025-s1p13-evidence-",
                dir="/private/tmp",
            )
        ).resolve()
        root.chmod(0o700)
        roots.append(root)
        return root

    yield create
    for root in roots:
        shutil.rmtree(root, ignore_errors=True)


def _parse_exports(stdout: str) -> dict[str, str]:
    exports: dict[str, str] = {}
    for line in stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator and key:
            exports[key] = value
    return exports


def _synthetic_runtime_api_port(state: dict[str, object]) -> int:
    reserved = {
        int(state[key])
        for key in ("streamlit_port", "app_port", "heartbeat_port")
        if key in state
    }
    return next(port for port in range(49154, 65535) if port not in reserved)


def _runtime_config_from_markup(markup: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" id="pfi-runtime-config">(.*?)</script>',
        markup,
        flags=re.DOTALL,
    )
    assert match, "official candidate must embed its real runtime configuration"
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def _populate_minimal_candidate_bundle(app_path: Path) -> Path:
    contents = app_path / "Contents"
    resources = contents / "Resources"
    executable = contents / "MacOS" / "PFI"
    code_resources = contents / "_CodeSignature" / "CodeResources"
    resources.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"#!/bin/zsh\nexit 0\n")
    executable.chmod(0o755)
    code_resources.parent.mkdir(parents=True)
    code_resources.write_bytes(b"phase13-fixture-code-resources\n")
    with (contents / "Info.plist").open("wb") as file_obj:
        plistlib.dump(
            {
                "CFBundleExecutable": "PFI",
                "CFBundleIdentifier": "com.linze.pfi.fixture",
                "CFBundleShortVersionString": "0.2.5",
                "CFBundleVersion": "20260712.1",
            },
            file_obj,
            sort_keys=True,
        )
    return resources


def _write_candidate_markers(
    resources: Path,
    *,
    isolated_root: Path,
    app_port: int | str = 49152,
    heartbeat_port: int | str = 49153,
) -> None:
    marker_values = {
        "PFI_STAGE1_ISOLATED_ROOT": str(isolated_root),
        "PFI_STAGE1_STREAMLIT_PORT": str(app_port),
        "PFI_STAGE1_HEARTBEAT_PORT": str(heartbeat_port),
        "PFI_PROJECT_ROOT": str(PFI_ROOT),
    }
    for name, value in marker_values.items():
        (resources / name).write_text(f"{value}\n", encoding="utf-8")


def _run_candidate_shell(app_path: Path, body: str, **extra_env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "/bin/zsh",
            "-f",
            "-c",
            (
                'source "$PFI_TEST_CANDIDATE_ENV"\n'
                'pfi_stage1_candidate_configure "$PFI_TEST_PROJECT_ROOT"\n'
                "candidate_status=$?\n"
                '[[ "$candidate_status" == "0" ]] || exit "$candidate_status"\n'
                f"{body}\n"
            ),
        ],
        env={
            **os.environ,
            "PFI_LAUNCHER_APP_PATH": str(app_path),
            "PFI_TEST_CANDIDATE_ENV": str(CANDIDATE_ENV_PATH),
            "PFI_TEST_PROJECT_ROOT": str(PFI_ROOT),
            **extra_env,
        },
        check=False,
        text=True,
        capture_output=True,
    )


def _pycache_fingerprint(root: Path) -> dict[str, tuple[int, int, str]]:
    result: dict[str, tuple[int, int, str]] = {}
    for path in sorted(root.rglob("*.pyc")):
        metadata = path.stat()
        result[path.relative_to(root).as_posix()] = (
            metadata.st_size,
            metadata.st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return result


def _active_candidate_marker_matches(
    *,
    marker_overrides: dict[str, str] | None = None,
    current_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    current = {
        "PFI_STAGE1_CANDIDATE_MODE": "1",
        "PFI_CANDIDATE_APP_PATH_SHA256": "1" * 64,
        "PFI_CANDIDATE_EXECUTABLE_SHA256": "2" * 64,
        "PFI_CANDIDATE_BUNDLE_SHA256": "3" * 64,
    }
    marker = {
        "PFI_ACTIVE_CANDIDATE_MODE": "1",
        "PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256": "1" * 64,
        "PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256": "2" * 64,
        "PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256": "3" * 64,
    }
    current.update(current_overrides or {})
    marker.update(marker_overrides or {})
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-marker-test-", dir="/private/tmp") as raw_root:
        marker_path = Path(raw_root) / "active.env"
        marker_path.write_text(
            "".join(f"{key}={value}\n" for key, value in marker.items()),
            encoding="utf-8",
        )
        return subprocess.run(
            [
                "/bin/zsh",
                "-f",
                "-c",
                (
                    'source "$PFI_TEST_CANDIDATE_ENV"\n'
                    'pfi_stage1_candidate_active_marker_matches "$PFI_TEST_ACTIVE_MARKER"'
                ),
            ],
            env={
                **os.environ,
                **current,
                "PFI_TEST_CANDIDATE_ENV": str(CANDIDATE_ENV_PATH),
                "PFI_TEST_ACTIVE_MARKER": str(marker_path),
            },
            check=False,
            text=True,
            capture_output=True,
        )


def load_candidate_env() -> Callable[..., tuple[subprocess.CompletedProcess[str], dict[str, str]]]:
    if not CANDIDATE_ENV_PATH.is_file():
        pytest.fail("S1-P3 requires the isolated-candidate environment loader")

    def configure(
        *,
        declared_root: str = "actual",
        app_port: int | str = 49152,
        heartbeat_port: int | str = 49153,
        marker_present: bool = True,
        malformed_marker: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
        with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-test-", dir="/private/tmp") as raw_root:
            isolated_root = Path(raw_root).resolve()
            app_path = isolated_root / "PFI.app"
            resources = _populate_minimal_candidate_bundle(app_path)

            if declared_root == "actual":
                marker_root = isolated_root
            elif declared_root == "wrong-prefix":
                marker_root = Path("/private/tmp/pfi-wrong-prefix")
            elif declared_root == "symlink-escape":
                marker_root = isolated_root / "escape"
                marker_root.symlink_to("/Applications", target_is_directory=True)
            elif declared_root == "desktop":
                marker_root = Path.home() / "Desktop"
            elif declared_root == "downloads":
                marker_root = Path.home() / "Downloads"
            else:
                marker_root = Path(declared_root)

            if marker_present:
                _write_candidate_markers(
                    resources,
                    isolated_root=Path(marker_root),
                    app_port=app_port,
                    heartbeat_port=heartbeat_port,
                )
                root_marker = resources / "PFI_STAGE1_ISOLATED_ROOT"
                if malformed_marker == "multiline":
                    root_marker.write_text(f"{marker_root}\nsecond-line\n", encoding="utf-8")
                elif malformed_marker == "control":
                    root_marker.write_bytes(os.fsencode(str(marker_root)) + b"\x01\n")
                elif malformed_marker == "nul":
                    root_marker.write_bytes(os.fsencode(str(marker_root)) + b"\x00\n")
                elif malformed_marker == "symlink":
                    target = resources / "PFI_STAGE1_ISOLATED_ROOT.target"
                    target.write_text(f"{marker_root}\n", encoding="utf-8")
                    root_marker.unlink()
                    root_marker.symlink_to(target.name)
                elif malformed_marker == "public-root":
                    isolated_root.chmod(0o755)

            completed = subprocess.run(
                [
                    "/bin/zsh",
                    "-f",
                    "-c",
                    (
                        'source "$PFI_TEST_CANDIDATE_ENV"\n'
                        'pfi_stage1_candidate_configure "$PFI_TEST_PROJECT_ROOT"\n'
                        'candidate_status=$?\n'
                        'printf "PFI_TEST_STATUS=%s\\n" "$candidate_status"\n'
                        'if [[ "$candidate_status" == "0" ]]; then\n'
                        "  /bin/zsh -f -c '\n"
                        '    printf "PFI_STAGE1_CANDIDATE_MODE=%s\\n" "${PFI_STAGE1_CANDIDATE_MODE-}"\n'
                        '    if [[ "${PFI_STAGE1_CANDIDATE_MODE-}" == "1" ]]; then\n'
                        '      for key in HOME PFI_DATA_HOME PFI_RUNTIME_DIR TMPDIR XDG_CACHE_HOME '
                        'PFI_BROWSER_PROFILE_DIR PYTHONPYCACHEPREFIX PFI_STREAMLIT_PORT '
                        'PFI_HEARTBEAT_PORT PYTHONDONTWRITEBYTECODE PFI_CANDIDATE_APP_PATH_SHA256 '
                        'PFI_CANDIDATE_EXECUTABLE_SHA256 PFI_CANDIDATE_BUNDLE_SHA256; do\n'
                        '        eval "value=\\${${key}-}"\n'
                        '        printf "%s=%s\\n" "$key" "$value"\n'
                        '      done\n'
                        '      printf "PFI_TEST_ROOT_MODE=%s\\n" "$(stat -f %Lp "${HOME:h}")"\n'
                        '      for key in HOME PFI_DATA_HOME PFI_RUNTIME_DIR TMPDIR XDG_CACHE_HOME '
                        'PFI_BROWSER_PROFILE_DIR PYTHONPYCACHEPREFIX; do\n'
                        '        eval "value=\\${${key}-}"\n'
                        '        printf "PFI_TEST_MODE_%s=%s\\n" "$key" "$(stat -f %Lp "$value")"\n'
                        '      done\n'
                        '    fi\n'
                        "  '\n"
                        'fi\n'
                        'exit "$candidate_status"'
                    ),
                ],
                env={
                    **os.environ,
                    "PFI_LAUNCHER_APP_PATH": str(app_path),
                    "PFI_TEST_CANDIDATE_ENV": str(CANDIDATE_ENV_PATH),
                    "PFI_TEST_PROJECT_ROOT": str(PFI_ROOT),
                },
                check=False,
                text=True,
                capture_output=True,
            )
            exports = _parse_exports(completed.stdout)
            if exports.get("PFI_STAGE1_CANDIDATE_MODE") == "1":
                exports["PFI_TEST_ISOLATED_ROOT"] = str(isolated_root)
            return completed, exports

    return configure


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _xattr_hash(path: Path) -> str:
    args = ["/usr/bin/xattr", "-l", "-x"]
    if path.is_symlink():
        args.append("-s")
    completed = subprocess.run([*args, str(path)], check=False, capture_output=True)
    return _sha256_bytes(
        b"\0".join(
            (
                str(completed.returncode).encode("ascii"),
                completed.stdout,
                completed.stderr,
            )
        )
    )


def _metadata_record(path: Path, *, relative: str) -> bytes:
    metadata = path.lstat()
    values = (
        relative,
        str(stat.S_IFMT(metadata.st_mode)),
        str(stat.S_IMODE(metadata.st_mode)),
        str(metadata.st_uid),
        str(metadata.st_gid),
        str(metadata.st_size),
        str(metadata.st_mtime_ns),
        str(getattr(metadata, "st_flags", 0)),
        str(getattr(metadata, "st_birthtime", 0)),
        _xattr_hash(path),
    )
    return ("\0".join(values) + "\n").encode("utf-8")


def _read_only_tree_hash(root: Path) -> str:
    records: list[bytes] = []
    paths = [root, *root.rglob("*")] if root.exists() and not root.is_symlink() else [root]
    for path in sorted(paths, key=lambda item: item.relative_to(root.parent).as_posix()):
        metadata = path.lstat()
        relative = path.relative_to(root.parent).as_posix()
        records.append(_metadata_record(path, relative=relative))
        records.append(f"A\0{relative}\0{_acl_hash(path)}\n".encode("utf-8"))
        if stat.S_ISLNK(metadata.st_mode):
            payload = f"L\0{relative}\0{_sha256_bytes(os.readlink(path).encode('utf-8'))}\n"
        elif stat.S_ISDIR(metadata.st_mode):
            payload = f"D\0{relative}\n"
        elif stat.S_ISREG(metadata.st_mode):
            payload = f"F\0{relative}\0{_sha256_bytes(path.read_bytes())}\n"
        else:
            payload = f"O\0{relative}\0{stat.S_IFMT(metadata.st_mode)}\n"
        records.append(payload.encode("utf-8"))
    return _sha256_bytes(b"".join(records))


def _acl_hash(path: Path) -> str:
    completed = subprocess.run(
        ["/bin/ls", "-ldeO@", str(path)],
        check=False,
        capture_output=True,
    )
    return _sha256_bytes(
        b"\0".join(
            (
                str(completed.returncode).encode("ascii"),
                completed.stdout,
                completed.stderr,
            )
        )
    )


def _bundle_identity(bundle: Path) -> dict[str, object]:
    plist_path = bundle / "Contents" / "Info.plist"
    with plist_path.open("rb") as file_obj:
        plist = plistlib.load(file_obj)
    executable = bundle / "Contents" / "MacOS" / str(plist["CFBundleExecutable"])
    codesign = subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(bundle)],
        check=False,
        capture_output=True,
    )
    return {
        "tree_sha256": _read_only_tree_hash(bundle),
        "executable_sha256": _sha256_bytes(executable.read_bytes()),
        "plist_identity": {
            "bundle_identifier": str(plist["CFBundleIdentifier"]),
            "short_version": str(plist["CFBundleShortVersionString"]),
            "build_version": str(plist["CFBundleVersion"]),
        },
        "codesign_valid": codesign.returncode == 0,
    }


def _independent_canonical_fingerprint(home: Path) -> dict[str, dict[str, object]]:
    entries = {
        "applications": Path("/Applications/PFI.app"),
        "desktop": home / "Desktop" / "PFI.app",
        "downloads": home / "Downloads" / "PFI.app",
    }
    known_bundle_targets = {
        path.resolve(strict=True): CANONICAL_SYMBOLS[label]
        for label, path in entries.items()
        if path.exists() and not path.is_symlink()
    }
    fingerprints: dict[str, dict[str, object]] = {}
    for label, path in entries.items():
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            fingerprints[label] = {"kind": "missing"}
            continue
        if stat.S_ISLNK(metadata.st_mode):
            resolved = path.resolve(strict=True)
            fingerprints[label] = {
                "kind": "symlink",
                "link_sha256": _sha256_bytes(os.readlink(path).encode("utf-8")),
                "symbolic_target": known_bundle_targets.get(
                    resolved,
                    f"unknown_sha256:{_sha256_bytes(str(resolved).encode('utf-8'))}",
                ),
                "entry_metadata_sha256": _sha256_bytes(_metadata_record(path, relative=label)),
                "entry_acl_sha256": _acl_hash(path),
                **_bundle_identity(resolved),
            }
        elif stat.S_ISDIR(metadata.st_mode):
            fingerprints[label] = {
                "kind": "bundle",
                "entry_metadata_sha256": _sha256_bytes(_metadata_record(path, relative=label)),
                "entry_acl_sha256": _acl_hash(path),
                **_bundle_identity(path),
            }
        else:
            fingerprints[label] = {
                "kind": "other",
                "entry_metadata_sha256": _sha256_bytes(_metadata_record(path, relative=label)),
                "entry_acl_sha256": _acl_hash(path),
                "content_sha256": _read_only_tree_hash(path),
            }
    return fingerprints


def test_candidate_module_exposes_prepare_snapshot_and_finalize() -> None:
    module = load_candidate_module()
    expected_parameters = {
        "prepare_candidate": ("project_root",),
        "snapshot_canonical_entries": ("home",),
        "finalize_candidate": ("state_path", "evidence_dir"),
    }
    for name, parameters in expected_parameters.items():
        function = getattr(module, name, None)
        assert callable(function), name
        assert tuple(inspect.signature(function).parameters) == parameters, name


def test_stage1_candidate_env_is_noop_without_marker_and_strict_when_valid() -> None:
    configure = load_candidate_env()
    no_marker, no_marker_exports = configure(marker_present=False)
    assert no_marker.returncode == 0, no_marker.stderr
    assert no_marker_exports == {
        "PFI_TEST_STATUS": "0",
        "PFI_STAGE1_CANDIDATE_MODE": "0",
    }

    valid, exports = configure()
    assert valid.returncode == 0, valid.stderr
    assert exports["PFI_TEST_STATUS"] == "0"
    assert exports["PFI_STAGE1_CANDIDATE_MODE"] == "1"
    isolated_root = Path(exports.pop("PFI_TEST_ISOLATED_ROOT")).resolve()
    for key in EXPORTED_CANDIDATE_PATHS:
        exported = Path(exports[key]).resolve()
        assert exported.is_relative_to(isolated_root), (key, exported)
        assert exports[f"PFI_TEST_MODE_{key}"] == "700", key
    assert exports["PFI_TEST_ROOT_MODE"] == "700"
    assert exports["PYTHONDONTWRITEBYTECODE"] == "1"
    for key in EXPORTED_CANDIDATE_IDENTITY:
        assert HEX64.fullmatch(exports[key]), key
    assert exports["PFI_STREAMLIT_PORT"] == "49152"
    assert exports["PFI_HEARTBEAT_PORT"] == "49153"
    assert exports["PFI_STREAMLIT_PORT"] != exports["PFI_HEARTBEAT_PORT"]
    assert {exports["PFI_STREAMLIT_PORT"], exports["PFI_HEARTBEAT_PORT"]}.isdisjoint({"8501", "8502"})
    candidate_env_source = CANDIDATE_ENV_PATH.read_text(encoding="utf-8")
    assert "PFI_STAGE1_FINALIZING_FILE" in candidate_env_source
    assert "candidate finalization is in progress" in candidate_env_source


def test_stage1_candidate_rejects_canonical_roots_and_live_ports() -> None:
    configure = load_candidate_env()
    rejected = (
        {"declared_root": "/Applications"},
        {"declared_root": "desktop"},
        {"declared_root": "downloads"},
        {"declared_root": "wrong-prefix"},
        {"declared_root": "symlink-escape"},
        {"app_port": 8501},
        {"heartbeat_port": 8502},
        {"app_port": 49152, "heartbeat_port": 49152},
        {"app_port": -1},
        {"heartbeat_port": 65536},
        {"app_port": "not-a-port"},
        {"heartbeat_port": "4915x"},
        {"malformed_marker": "multiline"},
        {"malformed_marker": "control"},
        {"malformed_marker": "nul"},
        {"malformed_marker": "symlink"},
        {"malformed_marker": "public-root"},
    )
    for arguments in rejected:
        completed, _ = configure(**arguments)
        assert completed.returncode != 0, arguments


def test_candidate_env_rejects_a_finalizing_tombstone() -> None:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-finalizing-test-", dir="/private/tmp") as raw_root:
        isolated_root = Path(raw_root).resolve()
        isolated_root.chmod(0o700)
        app_path = isolated_root / "PFI.app"
        resources = _populate_minimal_candidate_bundle(app_path)
        _write_candidate_markers(resources, isolated_root=isolated_root)
        tombstone = isolated_root / "PFI_STAGE1_FINALIZING"
        tombstone.write_text("PFI_STAGE1_FINALIZING_V1\n", encoding="ascii")
        tombstone.chmod(0o600)
        completed = _run_candidate_shell(app_path, "true")
        assert completed.returncode != 0
        assert "candidate finalization is in progress" in completed.stderr


def test_candidate_python_bytecode_stays_off_repository_sources() -> None:
    import_target = PFI_ROOT / "scripts" / "v025" / "release_cache_contract.py"
    source_root = import_target.parent
    before = _pycache_fingerprint(source_root)
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-bytecode-test-", dir="/private/tmp") as raw_root:
        isolated_root = Path(raw_root).resolve()
        app_path = isolated_root / "PFI.app"
        resources = _populate_minimal_candidate_bundle(app_path)
        _write_candidate_markers(resources, isolated_root=isolated_root)
        completed = _run_candidate_shell(
            app_path,
            (
                "\"$PFI_TEST_PYTHON\" -c 'import importlib.util, pathlib, sys; "
                'target=pathlib.Path(sys.argv[1]); '
                'spec=importlib.util.spec_from_file_location("pfi_stage1_bytecode_probe", target); '
                "module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)' "
                '"$PFI_TEST_IMPORT_TARGET"'
            ),
            PFI_TEST_PYTHON=str(PFI_ROOT / ".venv" / "bin" / "python"),
            PFI_TEST_IMPORT_TARGET=str(import_target),
        )
        assert completed.returncode == 0, completed.stderr
        assert Path(isolated_root / "python-pycache").is_dir()
        assert all(
            path.resolve().is_relative_to(isolated_root)
            for path in isolated_root.rglob("*.pyc")
        )
    after = _pycache_fingerprint(source_root)
    assert after == before, "candidate import changed bytecode beside repository sources"


def test_active_service_reuse_requires_exact_candidate_identity() -> None:
    assert _active_candidate_marker_matches().returncode == 0
    mismatches = (
        ({"PFI_ACTIVE_CANDIDATE_MODE": "0"}, {}),
        ({"PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256": "9" * 64}, {}),
        ({"PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256": "9" * 64}, {}),
        ({"PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256": "9" * 64}, {}),
        ({}, {"PFI_STAGE1_CANDIDATE_MODE": "0"}),
        ({}, {"PFI_CANDIDATE_APP_PATH_SHA256": "9" * 64}),
        ({}, {"PFI_CANDIDATE_EXECUTABLE_SHA256": "9" * 64}),
        ({}, {"PFI_CANDIDATE_BUNDLE_SHA256": "9" * 64}),
    )
    for marker_overrides, current_overrides in mismatches:
        completed = _active_candidate_marker_matches(
            marker_overrides=marker_overrides,
            current_overrides=current_overrides,
        )
        assert completed.returncode != 0, (marker_overrides, current_overrides)

    normal = _active_candidate_marker_matches(
        marker_overrides={"PFI_ACTIVE_CANDIDATE_MODE": "0"},
        current_overrides={"PFI_STAGE1_CANDIDATE_MODE": "0"},
    )
    assert normal.returncode == 0


def test_prepare_and_finalize_disposable_candidate_without_finder(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    prepare_candidate = getattr(module, "prepare_candidate")
    finalize_candidate = getattr(module, "finalize_candidate")
    git_before = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    canonical_before = _independent_canonical_fingerprint(Path.home())

    state = prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    emergency_evidence = external_evidence_factory()

    def emergency_cleanup() -> None:
        if state_path.is_file():
            try:
                finalize_candidate(state_path, emergency_evidence)
            except Exception:
                subprocess.run(
                    [str(LSREGISTER), "-u", str(candidate_app)],
                    check=False,
                    capture_output=True,
                )
                shutil.rmtree(isolated_root, ignore_errors=True)

    request.addfinalizer(emergency_cleanup)
    assert state_path == isolated_root / "state.json"
    assert isolated_root.parent == Path("/private/tmp")
    assert isolated_root.name.startswith("pfi-v025-s1p13-")
    assert stat.S_IMODE(isolated_root.stat().st_mode) == 0o700
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert candidate_app == isolated_root / "PFI.app"
    assert subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(candidate_app)],
        check=False,
        capture_output=True,
    ).returncode == 0
    assert state["streamlit_port"] not in {8501, 8502}
    assert state["heartbeat_port"] not in {8501, 8502, state["streamlit_port"]}
    assert state["launchservices_registered"] is True
    assert state["launchservices_registration_verified"] is True
    assert state["launchservices_registration_record_count"] >= 1
    assert HEX64.fullmatch(state["launchservices_registration_record_sha256"])
    for key in (
        "source_app_tree_sha256",
        "copied_app_tree_sha256",
        "candidate_app_path_sha256",
        "candidate_executable_sha256",
        "candidate_bundle_sha256",
        "checkout_commit",
    ):
        assert state[key]

    resources = candidate_app / "Contents" / "Resources"
    assert (resources / "PFI_PROJECT_ROOT").read_text(encoding="utf-8").strip() == str(PFI_ROOT)
    assert (resources / "PFI_STAGE1_ISOLATED_ROOT").read_text(encoding="utf-8").strip() == str(isolated_root)
    assert int((resources / "PFI_STAGE1_STREAMLIT_PORT").read_text(encoding="utf-8")) == state["streamlit_port"]
    assert int((resources / "PFI_STAGE1_HEARTBEAT_PORT").read_text(encoding="utf-8")) == state["heartbeat_port"]

    runtime_dir = isolated_root / "runtime"
    runtime_dir.mkdir(mode=0o700, exist_ok=True)
    active_marker = runtime_dir / "pfi_active_service.env"
    runtime_api_port = _synthetic_runtime_api_port(state)
    active_marker.write_text(
        "".join(
            (
                "PFI_ACTIVE_CANDIDATE_MODE=1\n",
                f"PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256={state['candidate_app_path_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256={state['candidate_executable_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256={state['candidate_bundle_sha256']}\n",
                "PFI_ACTIVE_PID=999999\n",
                f"PFI_ACTIVE_PORT={state['streamlit_port']}\n",
                f"PFI_ACTIVE_RUNTIME_API_PORT={runtime_api_port}\n",
                f"PFI_ACTIVE_URL=http://localhost:{state['streamlit_port']}\n",
            )
        ),
        encoding="utf-8",
    )

    evidence_dir = external_evidence_factory()
    result = finalize_candidate(state_path, evidence_dir)
    assert result["cleanup_complete"] is True
    assert result["owned_process_stopped"] is False
    assert result["canonical_unchanged"] is True
    assert result["protected_metadata_unchanged"] is True
    assert result["launchservices_unregistered"] is True
    assert result["launchservices_final_absent"] is True
    assert result["streamlit_port_released"] is True
    assert result["runtime_api_port_released"] is True
    assert result["heartbeat_port_released"] is True
    assert result["finalization_tombstone_published"] is True
    assert result["root_retained_for_retry"] is False
    assert not isolated_root.exists()
    for name in ("candidate_app.json", "entry_matrix.json", "launchservices_cleanup.json"):
        payload = json.loads((evidence_dir / name).read_text(encoding="utf-8"))
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert str(Path.home()) not in serialized
        assert str(isolated_root) not in serialized
        assert '"pid"' not in serialized

    assert _independent_canonical_fingerprint(Path.home()) == canonical_before
    git_after = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    assert git_after == git_before


def test_launchservices_candidate_routes_every_mutable_surface_under_temp_root() -> None:
    source = (PFI_ROOT / "StartPFI.command").read_text(encoding="utf-8")
    required_lines = (
        'source "$PROJECT_DIR/scripts/v025/stage1_phase13_candidate_env.sh"',
        'pfi_stage1_candidate_configure "$PROJECT_DIR"',
        'LOG_DIR="${PFI_RUNTIME_DIR:-$PROJECT_DIR/data/cache}"',
        'LOCK_DIR="$LOG_DIR/pfi_launch.lockdir"',
        'PORT="${PFI_STREAMLIT_PORT:-8501}"',
        'HEARTBEAT_PORT="${PFI_HEARTBEAT_PORT:-$((PORT + 1000))}"',
        'candidate_runtime_api_port() {',
        'printf "PFI_ACTIVE_RUNTIME_API_PORT=%s\\n" "$runtime_api_port"',
        'printf "PFI_ACTIVE_HEARTBEAT_PORT=%s\\n" "$heartbeat_port"',
        'printf "PFI_ACTIVE_MONITOR_PID=%s\\n" "$monitor_pid"',
        'printf "PFI_ACTIVE_LAUNCHER_PID=%s\\n" "$$"',
        'printf "PFI_ACTIVE_PROCESS_GROUP_ID=%s\\n" "$CANDIDATE_PROCESS_GROUP_ID"',
        'stop_launcher_children() {',
        'trap cleanup_launcher_on_exit EXIT',
        'if ! write_active_service_marker',
        'PFI_STAGE1_FINALIZING_FILE',
    )
    for required in required_lines:
        assert required in source, required
    helper = re.search(r"pfi_open_url_if_enabled\(\) \{(?P<body>.*?)\n\}", source, re.DOTALL)
    assert helper, "StartPFI.command requires one gated browser-open helper"
    helper_body = helper.group("body")
    assert '"${PFI_START_OPEN_BROWSER:-1}"' in helper_body
    assert "return 0" in helper_body
    assert re.search(r"\bopen\s+\"\$url\"", helper_body)
    assert helper_body.index("PFI_START_OPEN_BROWSER") < helper_body.index('open "$url"')
    assert not re.search(r"(?m)^\s*open\s+\"\$OPEN_URL\"", source)
    assert source.count("pfi_open_url_if_enabled() {") == 1
    assert source.count('open "$url"') == 1
    assert source.count('pfi_open_url_if_enabled "$OPEN_URL"') == 2
    assert source.count('pfi_stage1_candidate_active_marker_matches "$PFI_ACTIVE_SERVICE_FILE"') == 1
    for key in (
        "PFI_ACTIVE_CANDIDATE_MODE",
        "PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256",
        "PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256",
        "PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256",
        "PFI_ACTIVE_RUNTIME_API_PORT",
        "PFI_ACTIVE_HEARTBEAT_PORT",
        "PFI_ACTIVE_MONITOR_PID",
        "PFI_ACTIVE_LAUNCHER_PID",
        "PFI_ACTIVE_PROCESS_GROUP_ID",
    ):
        assert key in source

    with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-open-test-", dir="/private/tmp") as raw_root:
        capture = Path(raw_root) / "open-calls.txt"
        completed = subprocess.run(
            [
                "/bin/zsh",
                "-f",
                "-c",
                (
                    'open() { printf "%s\\n" "$1" >> "$PFI_TEST_OPEN_CAPTURE"; }\n'
                    'eval "$PFI_TEST_OPEN_HELPER"\n'
                    'PFI_START_OPEN_BROWSER=0 pfi_open_url_if_enabled "http://disabled.invalid"\n'
                    'PFI_START_OPEN_BROWSER=1 pfi_open_url_if_enabled "http://enabled.invalid"'
                ),
            ],
            env={
                **os.environ,
                "PFI_TEST_OPEN_CAPTURE": str(capture),
                "PFI_TEST_OPEN_HELPER": helper.group(0),
            },
            check=False,
            text=True,
            capture_output=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert capture.read_text(encoding="utf-8").splitlines() == ["http://enabled.invalid"]


def test_runtime_resolution_does_not_refresh_the_install_ready_marker() -> None:
    source = (PFI_ROOT / "scripts" / "pfiRuntime.sh").read_text(encoding="utf-8")
    match = re.search(r"pfi_os_ensure_app_python\(\) \{(?P<body>.*?)\n\}", source, re.DOTALL)
    assert match, "pfi_os_ensure_app_python must remain a focused callable"
    assert ".pfi_os_app_ready" not in match.group("body")


def test_entry_snapshot_uses_symbolic_labels_and_hashes_only() -> None:
    module = load_candidate_module()
    snapshot_canonical_entries = getattr(module, "snapshot_canonical_entries", None)
    assert callable(snapshot_canonical_entries), "snapshot_canonical_entries"
    home = Path.home()
    before = _independent_canonical_fingerprint(home)
    snapshot = snapshot_canonical_entries(home)
    after = _independent_canonical_fingerprint(home)
    assert after == before, "snapshot_canonical_entries mutated a protected canonical entry"
    assert set(snapshot) == {"applications", "desktop", "downloads"}
    allowed_keys = {
        "kind",
        "symbolic_path",
        "symbolic_target",
        "tree_sha256",
        "executable_sha256",
        "plist_identity",
        "codesign_valid",
    }
    for label, row in snapshot.items():
        assert set(row).issubset(allowed_keys), (label, sorted(set(row) - allowed_keys))
        assert row["kind"] in {"bundle", "symlink", "missing"}
        assert row["kind"] == before[label]["kind"], label
        assert row["symbolic_path"] == CANONICAL_SYMBOLS[label]
        if row["kind"] == "missing":
            assert set(row) == {"kind", "symbolic_path"}
            continue
        assert HEX64.fullmatch(str(row["tree_sha256"])), label
        assert HEX64.fullmatch(str(row["executable_sha256"])), label
        assert isinstance(row["codesign_valid"], bool), label
        assert set(row["plist_identity"]) == {"bundle_identifier", "short_version", "build_version"}
        assert all(isinstance(value, str) and value for value in row["plist_identity"].values())
        if row["kind"] == "symlink":
            assert row["symbolic_target"] in set(CANONICAL_SYMBOLS.values())
            assert row["symbolic_target"] == before[label]["symbolic_target"], label
        else:
            assert "symbolic_target" not in row
        assert row["tree_sha256"] == before[label]["tree_sha256"], label
        assert row["executable_sha256"] == before[label]["executable_sha256"], label
        assert row["plist_identity"] == before[label]["plist_identity"], label
        assert row["codesign_valid"] == before[label]["codesign_valid"], label

    serialized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
    forbidden_values = (
        str(home),
        "/Users/",
        "raw_pid",
        '"pid"',
        "process_command",
        "credential",
        "password",
        "token",
        "browser_history",
        "private_value",
    )
    assert all(value.lower() not in serialized.lower() for value in forbidden_values)


def test_prepare_fake_marker_finalize_is_private_signed_and_non_mutating(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    prepare_candidate = getattr(module, "prepare_candidate")
    finalize_candidate = getattr(module, "finalize_candidate")
    canonical_before = _independent_canonical_fingerprint(Path.home())
    git_status_before = subprocess.run(
        ["/usr/bin/git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout

    state = prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["temp_root"])
    candidate_app = Path(state["app_path"])
    emergency_evidence = external_evidence_factory()

    def emergency_cleanup() -> None:
        if state_path.is_file():
            try:
                finalize_candidate(state_path, emergency_evidence)
            except Exception:
                subprocess.run(
                    [str(LSREGISTER), "-u", str(candidate_app)],
                    check=False,
                    capture_output=True,
                )
                shutil.rmtree(isolated_root, ignore_errors=True)

    request.addfinalizer(emergency_cleanup)
    assert state_path == isolated_root / "state.json"
    assert isolated_root.parent == Path("/private/tmp")
    assert isolated_root.name.startswith("pfi-v025-s1p13-")
    assert stat.S_IMODE(isolated_root.stat().st_mode) == 0o700
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert candidate_app == isolated_root / "PFI.app"
    assert state["app_port"] != state["heartbeat_port"]
    assert {state["app_port"], state["heartbeat_port"]}.isdisjoint({8501, 8502})
    assert state["launchservices_registered"] is True
    assert state["launchservices_registration_verified"] is True
    assert state["launchservices_registration_record_count"] >= 1
    assert HEX64.fullmatch(state["launchservices_registration_record_sha256"])
    for key in (
        "source_tree_sha256",
        "source_executable_sha256",
        "copied_tree_sha256",
        "candidate_executable_sha256",
        "candidate_bundle_sha256",
        "checkout_binding_sha256",
        "git_status_sha256_before",
    ):
        assert HEX64.fullmatch(str(state[key])), key
    codesign = subprocess.run(
        ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(candidate_app)],
        check=False,
        capture_output=True,
    )
    assert codesign.returncode == 0, codesign.stderr.decode("utf-8", errors="replace")
    resources = candidate_app / "Contents" / "Resources"
    assert (resources / "PFI_PROJECT_ROOT").read_text(encoding="utf-8") == f"{PFI_ROOT}\n"
    assert (resources / "PFI_STAGE1_ISOLATED_ROOT").read_text(encoding="utf-8") == f"{isolated_root}\n"
    assert (resources / "PFI_STAGE1_STREAMLIT_PORT").read_text(encoding="utf-8") == f"{state['app_port']}\n"
    assert (resources / "PFI_STAGE1_HEARTBEAT_PORT").read_text(encoding="utf-8") == f"{state['heartbeat_port']}\n"
    assert (resources / "PFI_STAGE1_CHECKOUT_COMMIT").read_text(encoding="utf-8") == f"{state['checkout_commit']}\n"

    marker_path = Path(state["active_marker_path"])
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_api_port = _synthetic_runtime_api_port(state)
    marker_path.write_text(
        "".join(
            (
                "PFI_ACTIVE_SCHEMA=PFIActiveServiceV1\n",
                f"PFI_ACTIVE_PROJECT_DIR={PFI_ROOT}\n",
                "PFI_ACTIVE_PID=1073741823\n",
                f"PFI_ACTIVE_PORT={state['app_port']}\n",
                f"PFI_ACTIVE_RUNTIME_API_PORT={runtime_api_port}\n",
                f"PFI_ACTIVE_URL=http://127.0.0.1:{state['app_port']}\n",
                "PFI_ACTIVE_CANDIDATE_MODE=1\n",
                f"PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256={state['candidate_app_path_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256={state['candidate_executable_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256={state['candidate_bundle_sha256']}\n",
            )
        ),
        encoding="utf-8",
    )
    marker_path.chmod(0o600)

    evidence_dir = external_evidence_factory()
    result = finalize_candidate(state_path, evidence_dir)
    assert result["process_stop_status"] == "not_started"
    assert result["pid_observed"] is True
    assert result["canonical_unchanged"] is True
    assert result["git_status_unchanged"] is True
    assert result["launchservices_unregistered"] is True
    assert result["launchservices_final_absent"] is True
    assert result["streamlit_port_released"] is True
    assert result["runtime_api_port_released"] is True
    assert result["heartbeat_port_released"] is True
    assert result["finalization_tombstone_published"] is True
    assert result["root_retained_for_retry"] is False
    assert result["temp_root_deleted"] is True
    assert not isolated_root.exists()

    expected_evidence = {
        "candidate_app.json",
        "entry_matrix.json",
        "launchservices_cleanup.json",
        "protected_metadata.json",
    }
    assert {path.name for path in evidence_dir.iterdir()} == expected_evidence
    cleanup = json.loads((evidence_dir / "launchservices_cleanup.json").read_text(encoding="utf-8"))
    assert cleanup["process_stop_status"] == "not_started"
    assert cleanup["pid_observed"] is True
    assert cleanup["launchservices_unregistered"] is True
    assert cleanup["temp_root_deleted"] is True
    candidate_record = json.loads((evidence_dir / "candidate_app.json").read_text(encoding="utf-8"))
    assert candidate_record["active_marker_observed"] is True
    assert candidate_record["launchservices_runtime_verified"] is False
    assert candidate_record.get("finder_marker_observed") is not True
    entry_matrix = json.loads((evidence_dir / "entry_matrix.json").read_text(encoding="utf-8"))
    assert entry_matrix["before"] == entry_matrix["after"]
    assert entry_matrix["canonical_unchanged"] is True
    serialized_evidence = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(evidence_dir.iterdir())
    )
    for forbidden in (str(Path.home()), str(PFI_ROOT), str(isolated_root), "1073741823", '"pid"'):
        assert forbidden not in serialized_evidence

    assert _independent_canonical_fingerprint(Path.home()) == canonical_before
    git_status_after = subprocess.run(
        ["/usr/bin/git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert git_status_after == git_status_before


def test_finalize_retains_candidate_when_evidence_write_fails_then_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])

    def fail_write_json(_path: Path, _payload: dict[str, object]) -> None:
        raise OSError("injected evidence failure")

    monkeypatch.setattr(module, "_write_json", fail_write_json)
    failed_evidence = external_evidence_factory()
    retry_evidence = external_evidence_factory()
    try:
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, failed_evidence)
        assert isolated_root.is_dir()
        assert (isolated_root / "PFI_STAGE1_FINALIZING").is_file()
        monkeypatch.undo()
        retry = module.finalize_candidate(state_path, retry_evidence)
        assert retry["runtime_cleanup_checkpoint_reused"] is True
        assert retry["temp_root_deleted"] is True
        assert not isolated_root.exists()
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_finalize_retains_candidate_when_evidence_directory_is_invalid_then_retries(
    tmp_path: Path,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    invalid_evidence = tmp_path / "evidence-is-a-file"
    invalid_evidence.write_text("not a directory\n", encoding="utf-8")
    try:
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, invalid_evidence)
        assert isolated_root.is_dir()
        retry = module.finalize_candidate(state_path, external_evidence_factory())
        assert retry["runtime_cleanup_checkpoint_reused"] is True
        assert retry["temp_root_deleted"] is True
        assert not isolated_root.exists()
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_concurrent_finalize_is_refused_without_mutating_candidate(
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    lock_path = isolated_root / ".pfi_stage1_finalize.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        module.fcntl.flock(descriptor, module.fcntl.LOCK_EX | module.fcntl.LOCK_NB)
        with pytest.raises(module.CandidateError, match="finalization is already active"):
            module.finalize_candidate(state_path, external_evidence_factory())
        assert isolated_root.is_dir()
        assert not (isolated_root / "PFI_STAGE1_FINALIZING").exists()
    finally:
        module.fcntl.flock(descriptor, module.fcntl.LOCK_UN)
        os.close(descriptor)
    try:
        result = module.finalize_candidate(state_path, external_evidence_factory())
        assert result["temp_root_deleted"] is True
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_post_root_validation_failure_records_deleted_truth_not_retry(
    monkeypatch: pytest.MonkeyPatch,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    evidence_dir = external_evidence_factory()
    real_wait = module._wait_for_port_release
    calls = 0

    def fail_first_post_root_port(port: int, *, timeout_seconds: float = 15) -> bool:
        nonlocal calls
        calls += 1
        if calls == 3:
            return False
        return real_wait(port, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(module, "_wait_for_port_release", fail_first_post_root_port)
    try:
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, evidence_dir)
        assert not isolated_root.exists()
        cleanup = json.loads(
            (evidence_dir / "launchservices_cleanup.json").read_text(encoding="utf-8")
        )
        assert cleanup["cleanup_complete"] is False
        assert cleanup["temp_root_deleted"] is True
        assert cleanup["root_retained_for_retry"] is False
        assert cleanup["streamlit_port_released_after_cleanup"] is False
        assert cleanup["runtime_api_port_released_after_cleanup"] is True
        assert cleanup["runtime_api_port_released"] is True
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_pending_cleanup_publish_failure_records_deleted_truth(
    monkeypatch: pytest.MonkeyPatch,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    evidence_dir = external_evidence_factory()
    real_replace = Path.replace

    def fail_pending_replace(source: Path, target: Path) -> Path:
        if source.name == ".launchservices_cleanup.pending.json":
            raise OSError("injected pending publish failure")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_pending_replace)
    try:
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, evidence_dir)
        assert not isolated_root.exists()
        cleanup = json.loads(
            (evidence_dir / "launchservices_cleanup.json").read_text(encoding="utf-8")
        )
        assert cleanup["cleanup_complete"] is False
        assert cleanup["temp_root_deleted"] is True
        assert cleanup["root_retained_for_retry"] is False
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_pending_cleanup_journal_never_claims_unperformed_success(
    monkeypatch: pytest.MonkeyPatch,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    evidence_dir = external_evidence_factory()

    def interrupt_before_root_delete(*_args: object, **_kwargs: object) -> bool:
        raise SystemExit(99)

    monkeypatch.setattr(module, "_quarantine_and_remove_root", interrupt_before_root_delete)
    try:
        with pytest.raises(SystemExit, match="99"):
            module.finalize_candidate(state_path, evidence_dir)
        assert isolated_root.is_dir()
        pending = json.loads(
            (evidence_dir / ".launchservices_cleanup.pending.json").read_text(
                encoding="utf-8"
            )
        )
        assert pending["schema"] == "PFIV025Stage1Phase13CleanupPendingV1"
        assert pending["transaction_state"] == "PRE_ROOT_DELETE"
        for key in (
            "cleanup_complete",
            "temp_root_deleted",
            "post_root_launchservices_absent",
            "streamlit_port_released_after_cleanup",
            "heartbeat_port_released_after_cleanup",
            "runtime_api_port_released",
        ):
            assert pending[key] is False, key
        assert pending["runtime_api_port_released_after_cleanup"] is True
        assert pending["root_retained_for_retry"] is True
    finally:
        if isolated_root.exists():
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_verified_cleanup_failure_retains_tombstoned_state_for_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["observed_pid"] = 1073741823
    payload["observed_monitor_pid"] = 1073741822
    payload["inspection"] = {
        "launchservices_started": True,
        "process_identity_sha256": "a" * 64,
        "monitor_identity_sha256": "b" * 64,
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    state_path.chmod(0o600)
    evidence_dir = external_evidence_factory()
    retry_evidence = external_evidence_factory()
    try:
        monkeypatch.setattr(
            module,
            "_stop_owned_process",
            lambda _state, _marker: ("not_owned_not_signaled", True),
        )
        monkeypatch.setattr(
            module,
            "_stop_owned_monitor",
            lambda _state, _marker: ("observed_exited_before_signal", True, True),
        )
        monkeypatch.setattr(module, "_wait_for_port_release", lambda _port: True)
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, evidence_dir)
        assert isolated_root.is_dir()
        tombstone = isolated_root / "PFI_STAGE1_FINALIZING"
        assert tombstone.read_bytes() == b"PFI_STAGE1_FINALIZING_V1\n"
        assert stat.S_IMODE(tombstone.stat().st_mode) == 0o600
        cleanup = json.loads(
            (evidence_dir / "launchservices_cleanup.json").read_text(encoding="utf-8")
        )
        assert cleanup["runtime_process_cleanup_verified"] is False
        assert cleanup["root_retained_for_retry"] is True
        assert cleanup["temp_root_deleted"] is False

        monkeypatch.undo()
        with pytest.raises(module.CandidateError, match="finalization evidence failed"):
            module.finalize_candidate(state_path, retry_evidence)
        assert isolated_root.is_dir(), "invalid raw ownership proof must remain fail-closed"
        retry_cleanup = json.loads(
            (retry_evidence / "launchservices_cleanup.json").read_text(
                encoding="utf-8"
            )
        )
        assert retry_cleanup["root_retained_for_retry"] is True
        assert retry_cleanup["runtime_process_cleanup_verified"] is False
        assert retry_cleanup["process_group_identity_unchanged_before_cleanup"] is False
    finally:
        if isolated_root.exists():
            monkeypatch.undo()
            subprocess.run(
                [str(LSREGISTER), "-u", str(candidate_app)],
                check=False,
                capture_output=True,
            )
            shutil.rmtree(isolated_root, ignore_errors=True)


def test_sigkill_is_refused_when_process_identity_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_candidate_module()
    identities = iter(
        (
            (True, "stable-start-time-digest"),
            (True, "stable-start-time-digest"),
            (True, "reused-pid-digest"),
        )
    )
    signals: list[int] = []
    monotonic_values = iter((0.0, 11.0))
    monkeypatch.setattr(module, "_process_owns_candidate", lambda _state, _pid: next(identities))
    monkeypatch.setattr(module.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(module.os, "kill", lambda _pid, sent_signal: signals.append(sent_signal))
    state = {"streamlit_port": 49152, "project_root": str(PFI_ROOT)}
    marker = {"PFI_ACTIVE_PID": "424242"}
    process_status, pid_observed = module._stop_owned_process(state, marker)
    assert process_status == "identity_changed_not_signaled"
    assert pid_observed is True
    assert signals == [signal.SIGTERM]


def test_monitor_signal_is_refused_when_identity_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_candidate_module()
    identities = iter(
        (
            (True, "stable-monitor-digest"),
            (True, "reused-monitor-digest"),
        )
    )
    signals: list[int] = []
    monkeypatch.setattr(module, "_pid_exists", lambda _pid: True)
    monkeypatch.setattr(module, "_wait_for_pid_exit", lambda _pid, timeout_seconds: False)
    monkeypatch.setattr(module, "_process_owns_monitor", lambda _state, _monitor, _streamlit: next(identities))
    monkeypatch.setattr(module.os, "kill", lambda _pid, sent_signal: signals.append(sent_signal))
    state = {
        "observed_pid": 424241,
        "heartbeat_port": 49153,
        "project_root": str(PFI_ROOT),
    }
    marker = {"PFI_ACTIVE_MONITOR_PID": "424242", "PFI_ACTIVE_PID": "424241"}
    status, monitor_pid_observed, stopped = module._stop_owned_monitor(state, marker)
    assert status == "identity_changed_not_signaled"
    assert monitor_pid_observed is True
    assert stopped is False
    assert signals == []


@pytest.mark.parametrize(
    ("command", "expected"),
    (
        (
            f"{PFI_ROOT / '.venv/bin/python'} "
            f"{SHUTDOWN_MONITOR_PATH} --port 49153 --streamlit-pid 424241",
            True,
        ),
        (
            f"{PFI_ROOT / '.venv/bin/python'} -m pfi_os.system.shutdown_monitor "
            "--port 49153 --streamlit-pid 424241",
            False,
        ),
        (
            f"{PFI_ROOT / '.venv/bin/python'} {SHUTDOWN_MONITOR_PATH}.evil "
            "--port 49153 --streamlit-pid 424241",
            False,
        ),
    ),
)
def test_monitor_ownership_requires_the_exact_direct_script_token(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    expected: bool,
) -> None:
    module = load_candidate_module()

    def fake_run(*args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "ps":
            return subprocess.CompletedProcess(args, 0, stdout=command, stderr="")
        if args[0] == "lsof":
            return subprocess.CompletedProcess(args, 0, stdout="n127.0.0.1:49153\n", stderr="")
        raise AssertionError(args)

    monkeypatch.setattr(module, "_pid_exists", lambda _pid: True)
    monkeypatch.setattr(module, "_process_cwd", lambda _pid: str(PFI_ROOT))
    monkeypatch.setattr(module, "_run", fake_run)
    state = {
        "project_root": str(PFI_ROOT),
        "heartbeat_port": 49153,
    }
    owned, digest = module._process_owns_monitor(state, 424242, 424241)
    assert owned is expected
    assert bool(digest) is expected


@pytest.mark.parametrize(
    ("entry_token", "listener_address", "expected"),
    (
        ("src/pfi_os/app/streamlit_app.py", "127.0.0.1", True),
        ("src/pfi_os/app/streamlit_app.py.evil", "127.0.0.1", False),
        ("src/pfi_os/app/streamlit_app.py", "*", False),
        ("src/pfi_os/app/streamlit_app.py", "[::1]", False),
    ),
)
def test_candidate_ownership_requires_official_entry_and_two_loopback_endpoints(
    monkeypatch: pytest.MonkeyPatch,
    entry_token: str,
    listener_address: str,
    expected: bool,
) -> None:
    module = load_candidate_module()
    wrapper = PFI_ROOT / "scripts" / "v025" / "run_streamlit_with_release_cache.py"
    command = (
        f"{PFI_ROOT / '.venv/bin/python'} {wrapper} run {entry_token} "
        "--server.port 49152 --server.address 127.0.0.1"
    )

    def fake_run(*args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if args[0] == "ps":
            return subprocess.CompletedProcess(args, 0, stdout=command, stderr="")
        if args[0] == "lsof":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=(
                    f"n{listener_address}:49152\n"
                    f"n{listener_address}:49154\n"
                ),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr(module.os, "kill", lambda _pid, _signal: None)
    monkeypatch.setattr(module, "_process_cwd", lambda _pid: str(PFI_ROOT))
    monkeypatch.setattr(module, "_run", fake_run)
    owned, digest = module._process_owns_candidate(
        {
            "project_root": str(PFI_ROOT),
            "streamlit_port": 49152,
            "heartbeat_port": 49153,
        },
        424242,
    )
    assert owned is expected
    assert bool(digest) is expected
    assert '"-i4TCP"' not in CANDIDATE_MODULE_PATH.read_text(encoding="utf-8")


def test_launchservices_dump_timeout_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_candidate_module()

    def timeout(*_args: str, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="lsregister", timeout=10)

    monkeypatch.setattr(module, "_run", timeout)
    query_ok, count, digest = module._launchservices_exact_path_status(
        Path("/private/tmp/pfi-v025-s1p13-timeout/PFI.app")
    )
    assert query_ok is False
    assert count == 0
    assert digest == ""


def test_candidate_cli_malformed_state_error_is_sanitized() -> None:
    with tempfile.TemporaryDirectory(prefix="pfi-v025-s1p13-cli-test-", dir="/private/tmp") as raw_root:
        isolated_root = Path(raw_root)
        isolated_root.chmod(0o700)
        state_path = isolated_root / "state.json"
        state_path.write_text("not-json\n", encoding="utf-8")
        state_path.chmod(0o600)
        completed = subprocess.run(
            [
                str(PFI_ROOT / ".venv" / "bin" / "python"),
                "-B",
                str(CANDIDATE_MODULE_PATH),
                "finalize",
                "--state",
                str(state_path),
                "--evidence-dir",
                str(isolated_root.parent / "unused-evidence"),
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        assert completed.returncode == 1
        assert "Traceback" not in completed.stderr
        assert str(Path.home()) not in completed.stderr
        assert str(isolated_root) not in completed.stderr
        assert completed.stderr.startswith("PFI_STAGE1_CANDIDATE_ERROR:")


def test_phase13_browser_validator_has_attach_only_runtime_contract() -> None:
    assert BROWSER_VALIDATOR_PATH.is_file(), "S1-P3 requires the attach-only browser validator"
    source = BROWSER_VALIDATOR_PATH.read_text(encoding="utf-8")
    required_contract = (
        "PFIV025Stage1Phase13CandidateStateV1",
        "PFI_PLAYWRIGHT_MODULE_DIR",
        "PFI_BROWSER_PROFILE_DIR",
        "launchPersistentContext",
        "Network.clearBrowserCache",
        "context.tracing.start",
        "context.tracing.stop",
        "frameElement",
        "shellElement.screenshot",
        "pageshow",
        "persisted",
        "page.reload",
        "page.goBack",
        "page.goForward",
        "PFI_ACTIVE_CANDIDATE_MODE",
        "PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256",
        "PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256",
        "PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256",
        "PFI_ACTIVE_PORT",
        "PFI_ACTIVE_RUNTIME_API_PORT",
        "PFI_ACTIVE_HEARTBEAT_PORT",
        "PFI_ACTIVE_MONITOR_PID",
        "PFI_ACTIVE_LAUNCHER_PID",
        "PFI_ACTIVE_PROCESS_GROUP_ID",
        "/_stcore/health",
        "/api/release-manifest",
        "/api/release-cache-policy",
        "/api/read-model-status",
        "X-PFI-Running-Backend-SHA256",
        "X-PFI-Release-Manifest-SHA256",
        "X-PFI-Streamlit-Cache-Key",
        "pfi-runtime-config",
        "PFIV025Stage1ReleaseCachePolicyV1",
        "runtimeApiEnabled",
        "Accessibility.getFullAXTree",
        "browser_official_ui.png",
        "browser_release_identity.png",
        "browser_validation.json",
        "accessibility_tree.json",
        "playwright_trace.zip",
        "scanTraceArchiveEntries",
    )
    for required in required_contract:
        assert required in source, required

    expected_checks = (
        "official_shell_contract_verified",
        "frontend_source_set_exact_14",
        "frontend_source_bytes_match",
        "frontend_bundle_hash_recomputed",
        "frontend_bundle_hash_cross_surface_match",
        "frontend_modules_executed",
        "three_loopback_endpoints_owned",
        "manifest_api_real",
        "cache_policy_api_real",
        "read_model_status_api_real",
        "read_model_status_drives_ui",
        "running_backend_header_verified",
        "ordinary_reload_revalidated",
        "cache_cleared_reload_revalidated",
        "back_forward_revalidated",
        "pageshow_real_observed",
        "pageshow_persisted_guard_verified",
        "service_worker_and_cache_storage_empty",
        "accessibility_tree_captured",
        "accessibility_contract_verified",
        "network_allowlist_exact",
        "no_console_page_request_http_ws_errors",
        "isolated_empty_runtime_verified",
        "isolated_candidate_availability_truthful",
        "visible_dom_privacy_verified",
        "no_private_runtime_leakage",
    )
    for check in expected_checks:
        assert check in source, check

    assert 'from "node:child_process"' not in source
    assert "from 'node:child_process'" not in source
    assert not re.search(r"\b(?:spawn|spawnSync|exec|execFile|execFileSync)\s*\(", source)
    assert not re.search(r"\b(?:npm|npx|pnpm|yarn)\b", source, re.IGNORECASE)
    assert "http.createServer" not in source
    assert "server.listen" not in source
    assert 'serviceWorkers: "allow"' in source
    assert 'serviceWorkers: "block"' not in source
    assert "setInterval" in source
    assert "heartbeatTimer" in source


def test_phase13_browser_validator_missing_marker_fails_sanitized_before_playwright(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    emergency_evidence = external_evidence_factory()

    def emergency_cleanup() -> None:
        if state_path.is_file():
            try:
                module.finalize_candidate(state_path, emergency_evidence)
            except Exception:
                subprocess.run(
                    [str(LSREGISTER), "-u", str(candidate_app)],
                    check=False,
                    capture_output=True,
                )
                shutil.rmtree(isolated_root, ignore_errors=True)

    request.addfinalizer(emergency_cleanup)
    completed = subprocess.run(
        [
            _node_binary(),
            str(BROWSER_VALIDATOR_PATH),
            "--state",
            str(state_path),
            "--output-dir",
            str(tmp_path / "browser-missing-marker-output"),
        ],
        env={key: value for key, value in os.environ.items() if key != "PFI_PLAYWRIGHT_MODULE_DIR"},
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 1
    assert completed.stderr.startswith("PFI_STAGE1_BROWSER_ERROR: active marker is unavailable")
    assert "PFI_PLAYWRIGHT_MODULE_DIR" not in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "file://" not in completed.stderr
    assert str(Path.home()) not in completed.stderr
    assert str(PFI_ROOT) not in completed.stderr
    assert str(isolated_root) not in completed.stderr


def test_phase13_browser_validator_rejects_fake_marker_without_starting_service(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    emergency_evidence = external_evidence_factory()

    def emergency_cleanup() -> None:
        if state_path.is_file():
            try:
                module.finalize_candidate(state_path, emergency_evidence)
            except Exception:
                subprocess.run(
                    [str(LSREGISTER), "-u", str(candidate_app)],
                    check=False,
                    capture_output=True,
                )
                shutil.rmtree(isolated_root, ignore_errors=True)

    request.addfinalizer(emergency_cleanup)
    marker_path = Path(state["active_marker_path"])
    marker_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime_api_port = _synthetic_runtime_api_port(state)
    marker_path.write_text(
        "".join(
            (
                "PFI_ACTIVE_SCHEMA=PFIActiveServiceV1\n",
                f"PFI_ACTIVE_PROJECT_DIR={PFI_ROOT}\n",
                "PFI_ACTIVE_PID=1073741823\n",
                f"PFI_ACTIVE_PORT={state['streamlit_port']}\n",
                f"PFI_ACTIVE_RUNTIME_API_PORT={runtime_api_port}\n",
                f"PFI_ACTIVE_URL=http://127.0.0.1:{state['streamlit_port']}\n",
                "PFI_ACTIVE_CANDIDATE_MODE=1\n",
                f"PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256={state['candidate_app_path_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256={state['candidate_executable_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256={'9' * 64}\n",
            )
        ),
        encoding="utf-8",
    )
    marker_path.chmod(0o600)
    completed = subprocess.run(
        [
            _node_binary(),
            str(BROWSER_VALIDATOR_PATH),
            "--state",
            str(state_path),
            "--output-dir",
            str(tmp_path / "browser-fake-marker-output"),
        ],
        env={key: value for key, value in os.environ.items() if key != "PFI_PLAYWRIGHT_MODULE_DIR"},
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 1
    assert completed.stderr.startswith("PFI_STAGE1_BROWSER_ERROR: active marker identity mismatch")
    assert "PFI_PLAYWRIGHT_MODULE_DIR" not in completed.stderr
    assert "Traceback" not in completed.stderr
    assert str(Path.home()) not in completed.stderr
    assert str(PFI_ROOT) not in completed.stderr
    assert str(isolated_root) not in completed.stderr


def test_phase13_browser_validator_accepts_real_localhost_marker_then_requires_live_inspection(
    tmp_path: Path,
    request: pytest.FixtureRequest,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    state = module.prepare_candidate(PFI_ROOT)
    state_path = Path(state["state_path"])
    isolated_root = Path(state["isolated_root"])
    candidate_app = Path(state["candidate_app"])
    emergency_evidence = external_evidence_factory()

    def emergency_cleanup() -> None:
        if state_path.is_file():
            try:
                module.finalize_candidate(state_path, emergency_evidence)
            except Exception:
                subprocess.run(
                    [str(LSREGISTER), "-u", str(candidate_app)],
                    check=False,
                    capture_output=True,
                )
                shutil.rmtree(isolated_root, ignore_errors=True)

    request.addfinalizer(emergency_cleanup)
    marker_path = Path(state["active_marker_path"])
    marker_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    runtime_api_port = _synthetic_runtime_api_port(state)
    marker_path.write_text(
        "".join(
            (
                "PFI_ACTIVE_SCHEMA=PFIActiveServiceV1\n",
                f"PFI_ACTIVE_PROJECT_DIR={PFI_ROOT}\n",
                "PFI_ACTIVE_PID=1073741823\n",
                f"PFI_ACTIVE_PORT={state['streamlit_port']}\n",
                f"PFI_ACTIVE_RUNTIME_API_PORT={runtime_api_port}\n",
                f"PFI_ACTIVE_URL=http://localhost:{state['streamlit_port']}\n",
                f"PFI_ACTIVE_HEARTBEAT_PORT={state['heartbeat_port']}\n",
                "PFI_ACTIVE_MONITOR_PID=1073741822\n",
                "PFI_ACTIVE_LAUNCHER_PID=1073741821\n",
                "PFI_ACTIVE_PROCESS_GROUP_ID=1073741821\n",
                "PFI_ACTIVE_CANDIDATE_MODE=1\n",
                f"PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256={state['candidate_app_path_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256={state['candidate_executable_sha256']}\n",
                f"PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256={state['candidate_bundle_sha256']}\n",
            )
        ),
        encoding="ascii",
    )
    marker_path.chmod(0o600)
    completed = subprocess.run(
        [
            _node_binary(),
            str(BROWSER_VALIDATOR_PATH),
            "--state",
            str(state_path),
            "--output-dir",
            str(tmp_path / "browser-uninspected-output"),
        ],
        env={key: value for key, value in os.environ.items() if key != "PFI_PLAYWRIGHT_MODULE_DIR"},
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 1
    assert completed.stderr.startswith("PFI_STAGE1_BROWSER_ERROR: LaunchServices inspection proof is unavailable")
    assert "PFI_PLAYWRIGHT_MODULE_DIR" not in completed.stderr
    assert "Traceback" not in completed.stderr
    assert str(Path.home()) not in completed.stderr
    assert str(PFI_ROOT) not in completed.stderr
    assert str(isolated_root) not in completed.stderr
    assert not (tmp_path / "browser-uninspected-output").exists()

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["observed_pid"] = 1073741823
    payload["observed_monitor_pid"] = 1073741822
    payload["inspection"] = {
        "schema": "PFIV025Stage1Phase13CandidateInspectionV1",
        "launchservices_started": True,
        "candidate_mode": True,
        "candidate_path_symbolic": "${ISOLATED_ROOT}/PFI.app",
        "streamlit_port": state["streamlit_port"],
        "runtime_api_port": runtime_api_port,
        "heartbeat_port": state["heartbeat_port"],
        "pid_observed": True,
        "process_identity_sha256": "a" * 64,
        "monitor_pid_observed": True,
        "monitor_identity_sha256": "b" * 64,
        "health_ready": True,
        "runtime_api_ready": True,
        "heartbeat_ready": True,
        "launchservices_registration_verified": True,
        "candidate_app_path_sha256": state["candidate_app_path_sha256"],
        "candidate_executable_sha256": state["candidate_executable_sha256"],
        "candidate_bundle_sha256": state["candidate_bundle_sha256"],
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    state_path.chmod(0o600)
    dead_process = subprocess.run(
        [
            _node_binary(),
            str(BROWSER_VALIDATOR_PATH),
            "--state",
            str(state_path),
            "--output-dir",
            str(tmp_path / "browser-dead-inspection-output"),
        ],
        env={key: value for key, value in os.environ.items() if key != "PFI_PLAYWRIGHT_MODULE_DIR"},
        check=False,
        text=True,
        capture_output=True,
    )
    assert dead_process.returncode == 1
    assert dead_process.stderr.startswith("PFI_STAGE1_BROWSER_ERROR: LaunchServices inspection proof is unavailable")
    assert "PFI_PLAYWRIGHT_MODULE_DIR" not in dead_process.stderr
    assert str(Path.home()) not in dead_process.stderr
    assert str(PFI_ROOT) not in dead_process.stderr
    assert str(isolated_root) not in dead_process.stderr
    assert not (tmp_path / "browser-dead-inspection-output").exists()


def test_phase13_browser_validator_static_privacy_and_trace_contract() -> None:
    assert BROWSER_VALIDATOR_PATH.is_file(), "S1-P3 browser validator is missing"
    source = BROWSER_VALIDATOR_PATH.read_text(encoding="utf-8")
    required_privacy_contract = (
        "redactPrivateText",
        "assertPublicArtifact",
        "scanTraceArchiveEntries",
        "for (const entry of traceEntries)",
        "entry.fileName",
        "entry.uncompressedSize",
        "authorization",
        "cookie",
        "credential",
        "password",
        "token",
        "${HOME}",
        "${PROJECT_ROOT}",
        "${ISOLATED_ROOT}",
        "pid_observed",
        "monitor_pid_observed",
        "launcher_pid_observed",
        "monitor_identity_sha256",
        "launcher_identity_sha256",
        "process_group_identity_sha256",
        "listener_endpoint_set_sha256",
        "activeMonitorPid",
        "activeLauncherPid",
        "real_persisted_observed",
        "redactTraceCookieValues",
        "assertNoFinancialEvidence",
        "visibleDomPrivacyAudit",
        "accessibility_tree.json",
        "X-PFI-Running-Backend-SHA256",
    )
    for required in required_privacy_contract:
        assert required in source, required
    assert "real_persisted_observed: true" not in source
    assert re.search(r"real_persisted_observed\s*:\s*.*\.some\(", source)
    assert 'snapshots: true' in source
    assert 'screenshots: true' in source
    assert 'sources: false' in source


def test_phase13_browser_validator_sanitizes_every_synthetic_trace_member(tmp_path: Path) -> None:
    trace_path = tmp_path / "synthetic-trace.zip"
    module_url = BROWSER_VALIDATOR_PATH.as_uri()
    script = f"""
import {{ readFile, writeFile }} from "node:fs/promises";
import {{ __test }} from {json.dumps(module_url)};

const privacy = {{
  home: "/Users/private-owner",
  projectRoot: "/Users/private-owner/project",
  isolatedRoot: "/private/tmp/pfi-v025-s1p13-private",
  activePid: "424242",
  activeMonitorPid: "434343",
  activeLauncherPid: "444444",
}};
const payload = Buffer.from(JSON.stringify({{
  home: privacy.home,
  project: privacy.projectRoot,
  isolated: privacy.isolatedRoot,
  authorization: "top-secret",
  pid: 424242,
  workerProcess: 424242,
  safeNumber: 424241,
}}));
const archive = __test.buildTraceArchive([{{
  fileName: "trace.trace",
  content: payload,
  uncompressedSize: payload.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]);
const publicCounterJson = '{{"html_secret_finding_count":0}}';
if (__test.redactPrivateText(publicCounterJson, privacy) !== publicCounterJson) {{
  throw new Error("public counter was treated as a secret");
}}
const secretJson = '{{"token":"raw-secret","access_token":"access-secret","refresh_token":"refresh-secret","api_secret":"api-secret"}}';
const redactedSecretJson = __test.redactPrivateText(secretJson, privacy);
if (["raw-secret", "access-secret", "refresh-secret", "api-secret"].some((secret) => redactedSecretJson.includes(secret)) || !redactedSecretJson.includes("${{REDACTED}}")) {{
  throw new Error("exact secret key was not redacted");
}}
const namedByLabel = {{
  hidden: false,
  textContent: "",
  labels: [{{ textContent: "选择上传文件" }}],
  getAttribute: () => null,
}};
const trulyUnnamed = {{
  hidden: false,
  textContent: "",
  labels: [],
  getAttribute: () => null,
}};
const unnamedCount = __test.collectFocusableWithoutNameCount({{
  querySelectorAll: () => [namedByLabel, trulyUnnamed],
}});
if (unnamedCount !== 1) throw new Error("associated label was ignored");
await writeFile({json.dumps(str(trace_path))}, archive);
await __test.scanTraceArchiveEntries({json.dumps(str(trace_path))}, privacy, true);
const [entry] = __test.parseTraceArchive(await readFile({json.dumps(str(trace_path))}));
const sanitized = entry.content.toString("utf8");
for (const raw of Object.values(privacy)) {{
  if (sanitized.includes(raw)) throw new Error("raw private path survived");
}}
for (const required of ["${{HOME}}", "${{PROJECT_ROOT}}", "${{ISOLATED_ROOT}}", "${{REDACTED}}", "${{REDACTED_PID}}"] ) {{
  if (!sanitized.includes(required)) throw new Error(`missing ${{required}}`);
}}
if (sanitized.includes("424242")) throw new Error("raw PID survived");
const parsed = JSON.parse(sanitized);
if (parsed.safeNumber !== 424241) throw new Error("safe numeric value changed");
"""
    completed = subprocess.run(
        [_node_binary(), "--input-type=module", "--eval", script],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert trace_path.is_file()
    with zipfile.ZipFile(trace_path) as archive:
        assert archive.testzip() is None
        assert archive.namelist() == ["trace.trace"]
        payload = json.loads(archive.read("trace.trace"))
    assert payload["home"] == "${HOME}"
    assert payload["project"] == "${PROJECT_ROOT}"
    assert payload["isolated"] == "${ISOLATED_ROOT}"
    assert payload["authorization"] == "${REDACTED}"
    assert payload["pid"] == "${REDACTED_PID}"


def test_phase13_browser_validator_rejects_binary_pid_and_png_text_metadata(tmp_path: Path) -> None:
    binary_trace = tmp_path / "binary-private-trace.zip"
    binary_collision_trace = tmp_path / "binary-pid-substring-collision-trace.zip"
    png_path = tmp_path / "metadata.png"
    module_url = BROWSER_VALIDATOR_PATH.as_uri()
    binary_script = f"""
import {{ writeFile }} from "node:fs/promises";
import {{ __test }} from {json.dumps(module_url)};
const privacy = {{
  home: "/Users/private-owner",
  projectRoot: "/Users/private-owner/project",
  isolatedRoot: "/private/tmp/pfi-v025-s1p13-private",
  activePid: "4242",
}};
const payload = Buffer.concat([Buffer.from([255]), Buffer.from("pid=4242"), Buffer.from([254])]);
await writeFile({json.dumps(str(binary_trace))}, __test.buildTraceArchive([{{
  fileName: "resources/private-binary",
  content: payload,
  uncompressedSize: payload.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]));
let rejected = false;
try {{
  await __test.scanTraceArchiveEntries({json.dumps(str(binary_trace))}, privacy, true);
}} catch (_error) {{
  rejected = true;
}}
if (!rejected) throw new Error("binary active PID was not rejected");
const collisionPayload = Buffer.concat([
  Buffer.from([255]),
  Buffer.from("timestamp=14242425"),
  Buffer.from([254]),
]);
await writeFile({json.dumps(str(binary_collision_trace))}, __test.buildTraceArchive([{{
  fileName: "resources/safe-binary-pid-substring",
  content: collisionPayload,
  uncompressedSize: collisionPayload.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]));
await __test.scanTraceArchiveEntries(
  {json.dumps(str(binary_collision_trace))},
  privacy,
  true,
);
"""
    binary_result = subprocess.run(
        [_node_binary(), "--input-type=module", "--eval", binary_script],
        check=False,
        text=True,
        capture_output=True,
    )
    assert binary_result.returncode == 0, binary_result.stderr

    def png_chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    png_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + png_chunk(b"zTXt", b"Comment\x00\x00" + zlib.compress(b"/Users/private-owner token=abc"))
        + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\x00"))
        + png_chunk(b"IEND", b"")
    )
    png_script = f"""
import {{ readFile }} from "node:fs/promises";
import {{ __test }} from {json.dumps(module_url)};
let rejected = false;
try {{
  __test.assertPngMetadata(await readFile({json.dumps(str(png_path))}), {{
    home: "/Users/private-owner",
    projectRoot: "/Users/private-owner/project",
    isolatedRoot: "/private/tmp/pfi-v025-s1p13-private",
    activePid: "4242",
  }});
}} catch (_error) {{
  rejected = true;
}}
if (!rejected) throw new Error("compressed PNG text metadata was not rejected");
"""
    png_result = subprocess.run(
        [_node_binary(), "--input-type=module", "--eval", png_script],
        check=False,
        text=True,
        capture_output=True,
    )
    assert png_result.returncode == 0, png_result.stderr


def test_official_candidate_contract_uses_empty_status_and_full_release_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract_path = PFI_ROOT / "scripts" / "v025" / "release_cache_contract.py"
    spec = importlib.util.spec_from_file_location("pfi_v025_candidate_release_contract", contract_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    captured: dict[str, object] = {}

    def fake_full_contract(
        project_root: Path,
        *,
        read_model_status: dict[str, object] | None = None,
    ) -> tuple[str, dict[str, object]]:
        captured["project_root"] = project_root
        captured["read_model_status"] = read_model_status
        return "a" * 64, {
            "schema": "PFIV025Stage1ReleaseCachePolicyV1",
            "streamlit_cache_key": "a" * 64,
            "process_cache_key": "a" * 64,
            "persistent": False,
            "valid": True,
        }

    monkeypatch.setattr(module, "build_contract", fake_full_contract)
    build = getattr(module, "build_official_candidate_contract", None)
    assert callable(build), "candidate mode needs the full official release cache contract"
    key, policy = build(PFI_ROOT)
    assert HEX64.fullmatch(key)
    assert policy["schema"] == "PFIV025Stage1ReleaseCachePolicyV1"
    assert policy["persistent"] is False
    status = captured["read_model_status"]
    assert isinstance(status, dict)
    assert status["isolated_candidate"] is True
    assert status["source"]["storage_mode"] == "isolated_empty"
    assert all(metric["value"] is None for metric in status["core_metric_states"])
    assert captured["project_root"] == PFI_ROOT


def test_candidate_wrapper_installs_read_model_cache_and_ephemeral_runtime_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper_path = PFI_ROOT / "scripts" / "v025" / "run_streamlit_with_release_cache.py"
    spec = importlib.util.spec_from_file_location("pfi_v025_candidate_wrapper", wrapper_path)
    assert spec and spec.loader
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setenv("PFI_STREAMLIT_CACHE_KEY", "a" * 64)
    monkeypatch.setenv("PFI_V021_RUNTIME_API_PORT", "0")
    calls: list[tuple[str, object]] = []

    def capture_adapter(cache_key: str, **kwargs: object) -> None:
        calls.append(("cache", cache_key))
        builder = kwargs.get("original_builder")
        assert callable(builder)
        status = builder(PFI_ROOT, data_root=Path("/private/tmp/unused"))
        assert status["source"]["storage_mode"] == "isolated_empty"

    monkeypatch.setattr(
        wrapper,
        "install_read_model_cache_adapter",
        capture_adapter,
    )
    monkeypatch.setattr(
        wrapper,
        "ensure_ephemeral_runtime_api_owner",
        lambda: calls.append(("api", "ephemeral")) or "http://127.0.0.1:49154",
    )
    monkeypatch.setattr(
        wrapper,
        "publish_candidate_runtime_api_marker",
        lambda base_url: calls.append(("marker", base_url)),
    )
    install = getattr(wrapper, "install_release_runtime_guards", None)
    assert callable(install)
    with tempfile.TemporaryDirectory(
        prefix="pfi-v025-s1p13-wrapper-test-",
        dir="/private/tmp",
    ) as raw_root:
        isolated_root = Path(raw_root).resolve()
        isolated_root.chmod(0o700)
        candidate_paths = {
            "HOME": isolated_root / "home",
            "PFI_DATA_HOME": isolated_root / "data",
            "PFI_RUNTIME_DIR": isolated_root / "runtime",
            "TMPDIR": isolated_root / "tmp",
            "XDG_CACHE_HOME": isolated_root / "cache",
            "PFI_BROWSER_PROFILE_DIR": isolated_root / "browser-profile",
            "PYTHONPYCACHEPREFIX": isolated_root / "python-pycache",
        }
        for path in candidate_paths.values():
            path.mkdir(mode=0o700)
        monkeypatch.setenv("PFI_STAGE1_ISOLATED_ROOT", str(isolated_root))
        for variable, path in candidate_paths.items():
            monkeypatch.setenv(variable, str(path))
        assert install("a" * 64) == "http://127.0.0.1:49154"
    assert calls == [
        ("cache", "a" * 64),
        ("api", "ephemeral"),
        ("marker", "http://127.0.0.1:49154"),
    ]


def test_candidate_launcher_uses_only_the_official_production_entrypoint() -> None:
    launcher = (PFI_ROOT / "StartPFI.command").read_text(encoding="utf-8")
    assert 'APP_ENTRY="src/pfi_os/app/streamlit_app.py"' in launcher
    assert "isolated_candidate_app.py" not in launcher
    assert '"$APP_ENTRY"' in launcher
    assert "run_streamlit_with_release_cache.py" in launcher
    assert OFFICIAL_APP_PATH.is_file()
    source = OFFICIAL_APP_PATH.read_text(encoding="utf-8")
    for required in (
        "OperationalStore",
        "build_stage1_candidate_home_summary",
        "build_stage1_candidate_read_model_status",
        "stage1OfficialCandidate",
        "candidateDataMode",
        "web/app/shell.js",
        "web/app/pages/home.js",
        "web/app/pages/reports.js",
    ):
        assert required in source, required


def test_candidate_main_bypasses_env_and_query_legacy_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pfi_os.app import streamlit_app

    calls: list[str] = []

    class CandidateStreamlit:
        query_params = {"pfi_legacy": "1"}

        def set_page_config(self, **_kwargs: object) -> None:
            calls.append("page_config")

    def forbidden_legacy_entry() -> None:
        raise AssertionError("official candidate entered the legacy server-side branch")

    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setenv("PFI_UI_V2", "0")
    monkeypatch.setattr(streamlit_app, "st", CandidateStreamlit())
    monkeypatch.setattr(
        streamlit_app,
        "install_streamlit_runtime_compat",
        lambda: calls.append("runtime_compat"),
    )
    monkeypatch.setattr(
        streamlit_app,
        "render_pfi_ui_v2_shell",
        lambda: calls.append("official_shell"),
    )
    monkeypatch.setattr(streamlit_app, "install_shutdown_heartbeat", forbidden_legacy_entry)

    streamlit_app.main()

    assert calls == ["page_config", "runtime_compat", "official_shell"]


def test_official_candidate_html_uses_full_frontend_and_empty_runtime_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pfi_os.app import streamlit_app
    from pfi_v02 import stage_v021_runtime_api as runtime_api

    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setattr(
        runtime_api,
        "ensure_v021_runtime_api_server",
        lambda: "http://127.0.0.1:49154",
    )
    monkeypatch.setattr(
        runtime_api,
        "v021_runtime_api_client_token",
        lambda: "isolated-candidate-test-token",
    )
    status = streamlit_app.build_stage1_candidate_read_model_status()
    rendered = streamlit_app._pfi_web_shell_html(
        streamlit_app.build_stage1_candidate_home_summary(),
        read_model_status=status,
    )
    config = _runtime_config_from_markup(rendered)
    assert config["stage1OfficialCandidate"] is True
    assert config["candidateDataMode"] == "isolated_empty"
    assert config["runtimeApiEnabled"] is True
    assert config["releaseManifestApi"] is True
    assert config["releaseCachePolicyApi"] is True
    assert config["readModelStatusApi"] is True
    assert config["apiBaseUrl"] == "http://127.0.0.1:49154"
    assert config["projectRoot"] == ""
    embedded_sources = set(re.findall(r'data-pfi-source="([^"]+)"', rendered))
    _frontend_hash, frontend_paths = runtime_api._v025_frontend_bundle_hash(PFI_ROOT)
    expected_sources = {
        str(Path(path).relative_to("PFI").as_posix())
        for path in frontend_paths
        if path != "PFI/web/index.html"
    }
    assert len(frontend_paths) == 15
    assert embedded_sources == expected_sources
    assert status["source"]["storage_mode"] == "isolated_empty"
    assert all(metric["value"] is None for metric in status["core_metric_states"])
    assert "release-only" not in rendered
    assert "市场与研究" in rendered
    assert 'data-source-availability-label>等待 read model 状态<' in rendered
    assert 'source.storage_mode === "isolated_empty"' in rendered
    assert "隔离候选未加载真实数据" in rendered
    assert "只读空数据 · 未访问财务数据" in rendered
    assert "/Users/" not in rendered


def test_official_candidate_render_never_opens_the_canonical_operational_store(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from pfi_os.app import streamlit_app
    from pfi_v02 import stage_v021_runtime_api as runtime_api

    data_home = tmp_path / "isolated-data"
    captured: list[str] = []
    monkeypatch.setenv("PFI_STAGE1_CANDIDATE_MODE", "1")
    monkeypatch.setenv("PFI_DATA_HOME", str(data_home))
    monkeypatch.setattr(
        runtime_api,
        "ensure_v021_runtime_api_server",
        lambda: "http://127.0.0.1:49154",
    )
    monkeypatch.setattr(
        runtime_api,
        "v021_runtime_api_client_token",
        lambda: "isolated-candidate-test-token",
    )
    monkeypatch.setattr(
        streamlit_app,
        "OperationalStore",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("official candidate opened the canonical operational store")
        ),
    )
    monkeypatch.setattr(streamlit_app, "_render_pfi_native_shell_style", lambda: None)
    monkeypatch.setattr(
        streamlit_app,
        "_render_html_frame",
        lambda markup, **_kwargs: captured.append(markup),
    )
    streamlit_app.render_pfi_ui_v2_shell()
    assert len(captured) == 1
    config = _runtime_config_from_markup(captured[0])
    assert config["stage1OfficialCandidate"] is True
    assert config["candidateDataMode"] == "isolated_empty"
    assert not data_home.exists()
    read_model_match = re.search(
        r'<script type="application/json" id="pfi-read-model-status">(.*?)</script>',
        captured[0],
        flags=re.DOTALL,
    )
    home_match = re.search(
        r'<script type="application/json" id="pfi-home-summary">(.*?)</script>',
        captured[0],
        flags=re.DOTALL,
    )
    assert read_model_match and home_match
    runtime_payloads = {
        "config": config,
        "read_model": json.loads(read_model_match.group(1)),
        "home": json.loads(home_match.group(1)),
    }
    serialized_runtime = json.dumps(runtime_payloads, ensure_ascii=False, sort_keys=True)
    for forbidden in ("MetaDatabase/PFI", "pfi.sqlite", str(Path.home()), str(PFI_ROOT)):
        assert forbidden not in serialized_runtime


def test_trace_sanitizer_redacts_secrets_rejects_finance_and_accepts_safe_snapshots(
    tmp_path: Path,
) -> None:
    cookie_trace = tmp_path / "cookie-trace.zip"
    finance_trace = tmp_path / "finance-trace.zip"
    text_resource_trace = tmp_path / "text-resource-trace.zip"
    module_url = BROWSER_VALIDATOR_PATH.as_uri()
    script = f"""
import {{ readFile, writeFile }} from "node:fs/promises";
import {{ __test }} from {json.dumps(module_url)};
const privacy = {{
  home: "/Users/private-owner",
  projectRoot: "/Users/private-owner/project",
  isolatedRoot: "/private/tmp/pfi-v025-s1p13-private",
}};
const cookiePayload = Buffer.from(JSON.stringify({{
  type: "resource-snapshot",
  request: {{ cookies: [{{ name: "_streamlit_xsrf", value: "raw-cookie-value" }}] }},
}}));
await writeFile({json.dumps(str(cookie_trace))}, __test.buildTraceArchive([{{
  fileName: "trace.network",
  content: cookiePayload,
  uncompressedSize: cookiePayload.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]));
await __test.scanTraceArchiveEntries({json.dumps(str(cookie_trace))}, privacy, true);
const [cookieEntry] = __test.parseTraceArchive(await readFile({json.dumps(str(cookie_trace))}));
const sanitizedCookie = cookieEntry.content.toString("utf8");
if (sanitizedCookie.includes("raw-cookie-value")) throw new Error("cookie value survived");
if (!sanitizedCookie.includes("${{REDACTED}}")) throw new Error("cookie redaction missing");

const financePayload = Buffer.from(JSON.stringify({{ visibleText: "CNY 123.45" }}));
await writeFile({json.dumps(str(finance_trace))}, __test.buildTraceArchive([{{
  fileName: "trace.trace",
  content: financePayload,
  uncompressedSize: financePayload.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]));
let rejected = false;
try {{
  await __test.scanTraceArchiveEntries({json.dumps(str(finance_trace))}, privacy, true);
}} catch (_error) {{
  rejected = true;
}}
if (!rejected) throw new Error("financial evidence was accepted");

const textResource = Buffer.from("apparently harmless utf8 resource");
await writeFile({json.dumps(str(text_resource_trace))}, __test.buildTraceArchive([{{
  fileName: "resources/plain-text-resource",
  content: textResource,
  uncompressedSize: textResource.length,
  modifiedTime: 0,
  modifiedDate: 0,
  externalAttributes: 0,
}}]));
await __test.scanTraceArchiveEntries({json.dumps(str(text_resource_trace))}, privacy, true);
const [safeEntry] = __test.parseTraceArchive(await readFile({json.dumps(str(text_resource_trace))}));
if (safeEntry.content.toString("utf8") !== textResource.toString("utf8")) {{
  throw new Error("safe trace snapshot was not preserved");
}}

const makeControl = (label, value, attributeValue = "", tagName = "INPUT", type = "number") => ({{
  tagName,
  type,
  hidden: false,
  value,
  labels: [],
  getClientRects: () => [{{ width: 1, height: 1 }}],
  getAttribute: (name) => ({{
    "aria-label": label,
    value: attributeValue,
  }})[name] || null,
}});
const safeLiveAudit = await __test.collectLiveFormControlPrivacyAudit({{
  querySelectorAll: () => [
    makeControl("成本", ""),
    makeControl("组合 个人财务 投资复盘 消费复盘", "个人财务", "", "SELECT", "select-one"),
  ],
}});
if (safeLiveAudit.finding_count !== 0) throw new Error("blank live control was rejected");
if (safeLiveAudit.sensitive_control_count !== 1) throw new Error("categorical select was treated as financial input");
const privateLiveAudit = await __test.collectLiveFormControlPrivacyAudit({{
  querySelectorAll: () => [
    makeControl("数量", "12.3"),
    makeControl("成本", "123.45"),
    makeControl("价格", "98.76"),
    makeControl("成本", "1e5"),
    makeControl("价格", "123.45 元"),
    makeControl("数量", "(123.45)"),
    makeControl("净资产", "12.3", "", "SELECT", "select-one"),
    makeControl("净资产", "1e5", "", "SELECT", "select-one"),
    makeControl("净资产", "123.45 元", "", "SELECT", "select-one"),
    makeControl("净资产", "(123.45)", "", "SELECT", "select-one"),
  ],
}});
if (privateLiveAudit.finding_count !== 10) throw new Error("property-only finance values were accepted");

const safeDom = __test.visibleDomPrivacyAudit({{
  visible_text: "AUD/CNY=未加载\\n净资产 暂无真实数据\\n现金余额 未读取状态",
  full_html: "<html><body>isolated empty candidate</body></html>",
  live_form_control_audit: safeLiveAudit,
}});
if (!safeDom.safe || safeDom.finding_count !== 0) throw new Error("safe visible DOM was rejected");
const staleFxDom = __test.visibleDomPrivacyAudit({{
  visible_text: "AUD/CNY=4.69（2026/06/28 06:00）",
  full_html: "<html><body>stale cached FX</body></html>",
  live_form_control_audit: safeLiveAudit,
}});
if (staleFxDom.safe || staleFxDom.finding_count < 1) {{
  throw new Error("stale cached FX evidence was accepted");
}}
const privateDom = __test.visibleDomPrivacyAudit({{
  visible_text: "账户 6222020202020202 余额 ¥123456 样本量：8815\\n现金余额 123.45 元\\n净资产：998.88\\n投资市值 12.3 万元",
  full_html: '<html><body><input aria-label="成本"></body></html>',
  live_form_control_audit: privateLiveAudit,
}});
if (privateDom.safe || privateDom.finding_count < 16) throw new Error("private visible DOM was accepted");
if (privateDom.finding_counts.live_financial_form_value !== 10) {{
  throw new Error("live financial input values were accepted");
}}
"""
    completed = subprocess.run(
        [_node_binary(), "--input-type=module", "--eval", script],
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_candidate_listener_census_observes_the_complete_pid_listener_set() -> None:
    module = load_candidate_module()
    census = getattr(module, "_process_tcp_listen_ports", None)
    assert callable(census), "candidate inspection needs a complete PID listener census"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = int(listener.getsockname()[1])
        assert port in census(os.getpid())


def test_candidate_process_tree_census_binds_listener_owner_and_port() -> None:
    module = load_candidate_module()
    census = getattr(module, "_process_tree_tcp_listeners", None)
    assert callable(census), "candidate inspection needs a process-tree owner/port census"
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import socket,sys; "
                "s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(1); "
                "print(s.getsockname()[1], flush=True); sys.stdin.readline()"
            ),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        port = int(child.stdout.readline().strip())
        assert (child.pid, port) in census({os.getpid()})
    finally:
        if child.stdin is not None:
            child.stdin.write("stop\n")
            child.stdin.flush()
        child.wait(timeout=5)


def test_candidate_process_group_census_binds_loopback_endpoint() -> None:
    module = load_candidate_module()
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import socket,sys; "
                "s=socket.socket(); s.bind(('127.0.0.1',0)); s.listen(1); "
                "print(s.getsockname()[1], flush=True); sys.stdin.readline()"
            ),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        assert child.stdout is not None
        port = int(child.stdout.readline().strip())
        assert module._process_group_pids(child.pid) == {child.pid}
        assert module._process_group_tcp_listeners(child.pid) == {
            (child.pid, "127.0.0.1", port)
        }
    finally:
        if child.stdin is not None:
            child.stdin.write("stop\n")
            child.stdin.flush()
        child.wait(timeout=5)


def test_candidate_root_removal_gate_requires_stable_tree_and_listener_proof() -> None:
    module = load_candidate_module()
    gate = getattr(module, "_candidate_root_removal_safe", None)
    assert callable(gate), "candidate cleanup needs one fail-closed root-removal gate"
    passing = {
        "shutdown_monitor_stopped": True,
        "streamlit_port_released": True,
        "runtime_api_port_released": True,
        "heartbeat_port_released": True,
        "launchservices_absent": True,
        "runtime_cleanup_verified": True,
        "listener_set_unchanged": True,
        "process_tree_cleanup_verified": True,
        "evidence_records_written": True,
    }
    assert gate(**passing) is True
    for required in (
        "runtime_api_port_released",
        "listener_set_unchanged",
        "process_tree_cleanup_verified",
        "evidence_records_written",
    ):
        failing = {**passing, required: False}
        assert gate(**failing) is False, required


def test_finalizer_requires_a_precreated_owner_only_external_evidence_root(
    tmp_path: Path,
    external_evidence_factory: Callable[[], Path],
) -> None:
    module = load_candidate_module()
    isolated_root = Path(
        tempfile.mkdtemp(prefix="pfi-v025-s1p13-", dir="/private/tmp")
    ).resolve()
    isolated_root.chmod(0o700)
    accepted = external_evidence_factory()
    try:
        assert module._validate_external_evidence_directory(accepted, isolated_root) == accepted
        wrong_prefix = Path(tempfile.mkdtemp(prefix="not-pfi-evidence-", dir="/private/tmp"))
        wrong_mode = external_evidence_factory()
        wrong_mode.chmod(0o755)
        symlink = tmp_path / "evidence-link"
        symlink.symlink_to(accepted, target_is_directory=True)
        for rejected in (tmp_path / "missing", tmp_path, wrong_prefix, wrong_mode, symlink):
            with pytest.raises(module.CandidateError):
                module._validate_external_evidence_directory(rejected, isolated_root)
        shutil.rmtree(wrong_prefix)
    finally:
        shutil.rmtree(isolated_root, ignore_errors=True)


def test_candidate_inspect_and_finalize_use_the_unique_process_group_gate() -> None:
    source = CANDIDATE_MODULE_PATH.read_text(encoding="utf-8")
    launcher_source = (PFI_ROOT / "macos" / "PFI_launcher.c").read_text(encoding="utf-8")
    launcher = (PFI_ROOT / "StartPFI.command").read_text(encoding="utf-8")
    assert "-DPFI_STAGE1_ISOLATED_PROCESS_GROUP=1" in source
    assert "POSIX_SPAWN_SETPGROUP" in launcher_source
    assert "posix_spawnattr_setpgroup" in launcher_source
    assert "PFI_ACTIVE_PROCESS_GROUP_ID" in launcher
    assert "_process_group_tcp_listeners(process_group_id)" in source
    assert "_stop_owned_process_group(state, marker)" in source
    assert "_stop_owned_launcher_group(state, launch_lock_pid)" in source
    assert "process_group_cleanup_verified" in source


def test_shutdown_monitor_runs_as_a_business_free_direct_script(tmp_path: Path) -> None:
    launcher = (PFI_ROOT / "StartPFI.command").read_text(encoding="utf-8")
    direct_command = (
        '"$PYTHON_BIN" "$PROJECT_DIR/src/pfi_os/system/shutdown_monitor.py" '
        '--port "$HEARTBEAT_PORT"'
    )
    assert direct_command in launcher
    assert "-m pfi_os.system.shutdown_monitor" not in launcher

    audit_script = f"""
import json, os, pathlib, runpy, sys
root = pathlib.Path({json.dumps(str(PFI_ROOT))}).resolve()
venv = root / ".venv"
target = pathlib.Path({json.dumps(str(SHUTDOWN_MONITOR_PATH))}).resolve()
reads = []
sqlite_events = []
def audit(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        try:
            path = pathlib.Path(args[0]).expanduser().resolve(strict=False)
            if (path == root or root in path.parents) and path != venv and venv not in path.parents:
                reads.append(path.relative_to(root).as_posix())
        except Exception:
            pass
    if event.startswith("sqlite3.connect"):
        sqlite_events.append(event)
sys.addaudithook(audit)
sys.argv = [str(target), "--help"]
exit_code = 0
try:
    runpy.run_path(str(target), run_name="__main__")
except SystemExit as error:
    exit_code = int(error.code or 0)
forbidden_modules = sorted(name for name in sys.modules if name.startswith("pfi_os"))
print(json.dumps({{"reads": sorted(set(reads)), "sqlite_events": sqlite_events, "forbidden_modules": forbidden_modules, "exit_code": exit_code}}))
"""
    completed = subprocess.run(
        [str(PFI_ROOT / ".venv" / "bin" / "python"), "-B", "-c", audit_script],
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(tmp_path / "pycache"),
        },
        check=False,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload == {
        "reads": ["src/pfi_os/system/shutdown_monitor.py"],
        "sqlite_events": [],
        "forbidden_modules": [],
        "exit_code": 0,
    }
