from __future__ import annotations

import fnmatch
import json
import os
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings


PACKAGE_ROOTS = (
    "app",
    "tests",
    "data",
    "outputs",
    "README.md",
    "HANDOFF.md",
    "pyproject.toml",
)

GENERAL_EXCLUDES = (
    "work/**",
    ".pytest_cache/**",
    "**/.pytest_cache/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "outputs/package/serenity_daily_analysis_delivery.zip",
    "outputs/package/*.tmp",
    "outputs/package/package_latest.*",
)

PRIVATE_EVIDENCE_EXCLUDES = (
    "evidence/**",
    "outputs/intake_pack/evidence/**",
    "data/backups/**",
)


@dataclass(frozen=True)
class PackageResult:
    generated_at: str
    zip_path: str
    manifest_path: str
    json_path: str
    include_private_evidence: bool
    member_count: int
    size_bytes: int
    excluded_private_patterns: list[str]
    included_private_like_members: list[str]
    status: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in PACKAGE_ROOTS:
        path = root / rel
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return sorted(files)


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _private_like(path: str) -> bool:
    return _matches(path, PRIVATE_EVIDENCE_EXCLUDES)


def _display_path(root: Path, path: str) -> str:
    parsed = Path(path)
    try:
        return parsed.relative_to(root).as_posix()
    except ValueError:
        return parsed.name


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _write_manifest(path: Path, *, result: PackageResult, roots: tuple[str, ...]) -> None:
    lines = [
        "# Delivery Package Build Manifest",
        "",
        f"- Generated: {result.generated_at}",
        f"- Status: {result.status}",
        f"- ZIP: `{_display_path(path.parents[2], result.zip_path)}`",
        f"- Members: {result.member_count}",
        f"- Size bytes: {result.size_bytes}",
        f"- Include private evidence: {result.include_private_evidence}",
        "",
        "## Included Roots",
        "",
    ]
    for root in roots:
        lines.append(f"- `{root}`")
    lines.extend(["", "## Default Exclusions", ""])
    for pattern in GENERAL_EXCLUDES:
        lines.append(f"- `{pattern}`")
    lines.extend(["", "## Private Evidence Exclusions", ""])
    if result.include_private_evidence:
        lines.append("- Private evidence exclusion is disabled for this package build.")
    else:
        for pattern in result.excluded_private_patterns:
            lines.append(f"- `{pattern}`")
    lines.extend(["", "## Private-Like Members Found In ZIP", ""])
    if result.included_private_like_members:
        for member in result.included_private_like_members[:100]:
            lines.append(f"- `{member}`")
        if len(result.included_private_like_members) > 100:
            lines.append(f"- ... {len(result.included_private_like_members) - 100} more")
    else:
        lines.append("- None")
    _atomic_write_text(path, "\n".join(lines) + "\n")


def build_delivery_package(
    settings: Settings,
    *,
    include_private_evidence: bool = False,
    output_path: Path | None = None,
) -> dict[str, object]:
    settings.ensure_dirs()
    output_dir = settings.root_dir / "outputs" / "package"
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_path or (output_dir / "serenity_daily_analysis_delivery.zip")
    manifest_path = output_dir / "package_latest.md"
    json_path = output_dir / "package_latest.json"

    generated_at = _now(settings)
    candidates = _iter_files(settings.root_dir)
    excluded = GENERAL_EXCLUDES
    if not include_private_evidence:
        excluded = excluded + PRIVATE_EVIDENCE_EXCLUDES

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_zip_path = zip_path.with_name(f".{zip_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")

    members: list[str] = []
    try:
        with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in candidates:
                rel = _rel(settings.root_dir, path)
                if _matches(rel, excluded):
                    continue
                archive.write(path, rel)
                members.append(rel)
        os.replace(tmp_zip_path, zip_path)
    finally:
        if tmp_zip_path.exists():
            tmp_zip_path.unlink()

    included_private_like = sorted(member for member in members if _private_like(member))
    status = "pass" if include_private_evidence or not included_private_like else "warn"
    result = PackageResult(
        generated_at=generated_at,
        zip_path=str(zip_path),
        manifest_path=str(manifest_path),
        json_path=str(json_path),
        include_private_evidence=include_private_evidence,
        member_count=len(members),
        size_bytes=zip_path.stat().st_size,
        excluded_private_patterns=list(PRIVATE_EVIDENCE_EXCLUDES if not include_private_evidence else []),
        included_private_like_members=included_private_like,
        status=status,
    )
    _atomic_write_text(json_path, json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n")
    _write_manifest(manifest_path, result=result, roots=PACKAGE_ROOTS)
    return asdict(result)
