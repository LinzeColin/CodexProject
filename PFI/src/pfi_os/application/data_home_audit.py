from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from pfi_os.application.operational_store import default_data_home, default_operational_db_path


SCHEMA = "PFIOSPhaseADataHomeBoundaryAuditV1"

FAIL = "Fail"
PASS = "Pass"

IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

FORBIDDEN_RUNTIME_SUFFIXES = (
    ".sqlite",
    ".sqlite-shm",
    ".sqlite-wal",
    ".db",
)

FORBIDDEN_SECRET_SUFFIXES = (
    ".pem",
    ".key",
)

PRIVATE_PATH_PREFIXES = (
    ("data", "private"),
    ("data", "external"),
    ("data", "imports"),
    ("data", "holdings"),
    ("data", "researchBus", "chatInbox"),
    ("shared", "secrets"),
)

PRIVATE_EXACT_ALLOWLIST = {
    ("data", "holdings", ".gitkeep"),
    ("data", "holdings", "imports", ".gitkeep"),
    ("data", "imports", ".gitkeep"),
    ("data", "researchBus", "ResearchBusSnapshot.example.json"),
    ("data", "raw", ".gitkeep"),
    ("data", "processed", ".gitkeep"),
    ("data", "cache", ".gitkeep"),
    ("data", "results", ".gitkeep"),
}


@dataclass(frozen=True)
class DataHomeAuditFinding:
    severity: str
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class DataHomeBoundaryAudit:
    schema: str
    status: str
    project_root: str
    data_home: str
    operational_db_path: str
    scanned_paths: int
    findings: tuple[DataHomeAuditFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "project_root": self.project_root,
            "data_home": self.data_home,
            "operational_db_path": self.operational_db_path,
            "scanned_paths": self.scanned_paths,
            "findings": [asdict(finding) for finding in self.findings],
        }


def build_data_home_boundary_contract(project_root: Path | str, data_home: Path | str | None = None) -> dict[str, Any]:
    resolved_root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home())
    operational_db = _resolve(default_operational_db_path(resolved_data_home))
    return {
        "schema": "PFIOSPhaseADataHomeBoundaryContractV1",
        "project_root": str(resolved_root),
        "data_home": str(resolved_data_home),
        "operational_db_path": str(operational_db),
        "required": [
            "$PFI_DATA_HOME must be outside the public repository.",
            "Operational SQLite must stay under $PFI_DATA_HOME/private/operational.",
            "Public Git must not contain runtime SQLite, secrets, private imports, or private holdings.",
        ],
        "forbidden_runtime_suffixes": list(FORBIDDEN_RUNTIME_SUFFIXES),
        "forbidden_secret_suffixes": list(FORBIDDEN_SECRET_SUFFIXES),
        "private_path_prefixes": ["/".join(parts) for parts in PRIVATE_PATH_PREFIXES],
        "private_exact_allowlist": ["/".join(parts) for parts in PRIVATE_EXACT_ALLOWLIST],
        "no_live_trading": True,
    }


def audit_data_home_boundary(
    project_root: Path | str,
    data_home: Path | str | None = None,
    *,
    tracked_paths: Iterable[Path | str] | None = None,
) -> DataHomeBoundaryAudit:
    resolved_root = _resolve(project_root)
    resolved_data_home = _resolve(data_home) if data_home is not None else _resolve(default_data_home())
    operational_db = _resolve(default_operational_db_path(resolved_data_home))
    findings: list[DataHomeAuditFinding] = []

    if _is_relative_to(resolved_data_home, resolved_root):
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="DATA_HOME_INSIDE_REPO",
                path=str(resolved_data_home),
                message="$PFI_DATA_HOME must not live inside the public repository.",
            )
        )
    if _is_relative_to(operational_db, resolved_root):
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="OPERATIONAL_DB_INSIDE_REPO",
                path=str(operational_db),
                message="Operational SQLite must stay outside public Git under $PFI_DATA_HOME/private/operational.",
            )
        )

    relative_paths = _normalise_tracked_paths(resolved_root, tracked_paths)
    for relative_path in relative_paths:
        findings.extend(_path_findings(relative_path))

    status = FAIL if any(finding.severity == FAIL for finding in findings) else PASS
    return DataHomeBoundaryAudit(
        schema=SCHEMA,
        status=status,
        project_root=str(resolved_root),
        data_home=str(resolved_data_home),
        operational_db_path=str(operational_db),
        scanned_paths=len(relative_paths),
        findings=tuple(findings),
    )


def _path_findings(relative_path: Path) -> list[DataHomeAuditFinding]:
    findings: list[DataHomeAuditFinding] = []
    parts = tuple(relative_path.parts)
    lower_name = relative_path.name.lower()
    display_path = relative_path.as_posix()

    if any(part in IGNORED_DIRS for part in parts):
        return findings
    if parts in PRIVATE_EXACT_ALLOWLIST:
        return findings
    if relative_path.name == ".env":
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="ENV_FILE_IN_GIT",
                path=display_path,
                message="Tracked .env files can expose credentials; keep only .env.example in public Git.",
            )
        )
    if lower_name.endswith(FORBIDDEN_RUNTIME_SUFFIXES):
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="RUNTIME_DATABASE_IN_GIT",
                path=display_path,
                message="Runtime database files belong under $PFI_DATA_HOME, not public Git.",
            )
        )
    if lower_name.endswith(FORBIDDEN_SECRET_SUFFIXES) or "cookie" in lower_name or lower_name == "login data":
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="SECRET_LIKE_FILE_IN_GIT",
                path=display_path,
                message="Secret-like files, cookies, browser login databases, and private keys are not allowed in public Git.",
            )
        )
    if _matches_prefix(parts, PRIVATE_PATH_PREFIXES):
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="PRIVATE_PATH_IN_GIT",
                path=display_path,
                message="Private imports, holdings, secrets, and chat inbox files must stay outside public Git.",
            )
        )
    if parts[:2] == ("data", "researchBus") and relative_path.name == "ResearchBusSnapshot.json":
        findings.append(
            DataHomeAuditFinding(
                severity=FAIL,
                code="RESEARCH_BUS_RUNTIME_SNAPSHOT_IN_GIT",
                path=display_path,
                message="ResearchBus runtime snapshots are private; only public-safe examples may be tracked.",
            )
        )

    return findings


def _normalise_tracked_paths(project_root: Path, tracked_paths: Iterable[Path | str] | None) -> list[Path]:
    if tracked_paths is None:
        return list(_iter_project_files(project_root))
    relative_paths: list[Path] = []
    for raw_path in tracked_paths:
        path = Path(raw_path)
        if path.is_absolute():
            resolved = _resolve(path)
            if not _is_relative_to(resolved, project_root):
                continue
            path = resolved.relative_to(project_root)
        relative_paths.append(Path(*path.parts))
    return sorted(relative_paths, key=lambda item: item.as_posix())


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(project_root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        yield relative


def _matches_prefix(parts: tuple[str, ...], prefixes: tuple[tuple[str, ...], ...]) -> bool:
    for prefix in prefixes:
        if parts[: len(prefix)] == prefix:
            return True
    return False


def _resolve(path: Path | str) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
