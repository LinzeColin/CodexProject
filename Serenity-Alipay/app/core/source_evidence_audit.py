from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.config import Settings
from app.db import connect, init_db, insert_row


EVIDENCE_REF_PATTERN = re.compile(r"(?:evidence|evidence_path|source_path|source_url)=([^;,\n]+)", re.IGNORECASE)
PLACEHOLDER_MARKERS = ("REPLACE_", "YYYY-MM-DD", "placeholder", "sample", "demo", "manual sample", "示例", "样例")
PASS_STATUSES = {"valid_url", "hashed_local_file"}


@dataclass(frozen=True)
class EvidenceRow:
    area: str
    row_id: str
    field: str
    source_file: str
    raw_value: str
    evidence_ref: str
    ref_type: str
    status: str
    message: str
    resolved_path: str
    sha256: str
    size_bytes: str
    mtime: str


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _rel(settings: Settings, path: Path) -> str:
    try:
        return str(path.relative_to(settings.root_dir))
    except ValueError:
        return str(path)


def _looks_placeholder(value: str) -> bool:
    lower = value.lower()
    return any(marker.lower() in lower for marker in PLACEHOLDER_MARKERS)


def _extract_source_note_ref(value: str) -> str:
    match = EVIDENCE_REF_PATTERN.search(value)
    return match.group(1).strip() if match else value.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _classify_ref(
    settings: Settings,
    source_file: Path,
    evidence_ref: str,
    *,
    base_dir: Path | None = None,
) -> tuple[str, str, str, str, str, str, str]:
    value = evidence_ref.strip()
    if not value:
        return "missing", "missing_reference", "reference is empty", "", "", "", ""
    if _looks_placeholder(value):
        return "missing", "placeholder_reference", "reference still contains placeholder/sample marker", "", "", "", ""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc:
            return "url", "valid_url", "valid http(s) URL; not fetched during local audit", "", "", "", ""
        return "url", "invalid_url", "URL is missing host", "", "", "", ""
    if parsed.scheme:
        return "url", "unsupported_scheme", f"unsupported URL scheme: {parsed.scheme}", "", "", "", ""

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (base_dir or settings.root_dir) / path
    resolved = path.resolve(strict=False)
    if resolved == source_file.resolve(strict=False):
        return "local_file", "self_reference", "reference points to the production CSV itself", str(resolved), "", "", ""
    if not path.exists():
        return "local_file", "missing_local_file", "local evidence file does not exist", str(resolved), "", "", ""
    if not path.is_file():
        return "local_file", "not_a_file", "local evidence reference is not a file", str(resolved), "", "", ""
    stat = path.stat()
    return (
        "local_file",
        "hashed_local_file",
        "local evidence file exists and was hashed",
        str(resolved),
        _sha256(path),
        str(stat.st_size),
        datetime.fromtimestamp(stat.st_mtime, ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds"),
    )


def _make_row(
    settings: Settings,
    *,
    area: str,
    row_id: str,
    field: str,
    source_file: Path,
    raw_value: str,
    evidence_ref: str,
    base_dir: Path | None = None,
) -> EvidenceRow:
    ref_type, status, message, resolved, sha256, size, mtime = _classify_ref(settings, source_file, evidence_ref, base_dir=base_dir)
    return EvidenceRow(
        area=area,
        row_id=row_id,
        field=field,
        source_file=_rel(settings, source_file),
        raw_value=raw_value,
        evidence_ref=evidence_ref,
        ref_type=ref_type,
        status=status,
        message=message,
        resolved_path=resolved,
        sha256=sha256,
        size_bytes=size,
        mtime=mtime,
    )


def _collect_rows(settings: Settings, *, pack_dir: Path | None = None) -> list[EvidenceRow]:
    rows: list[EvidenceRow] = []
    fund_path = (pack_dir / "02_fund_rules_to_fill.csv") if pack_dir else (settings.manual_dir / "fund_rules.csv")
    candidate_path = (pack_dir / "03_candidates_to_fill.csv") if pack_dir else (settings.manual_dir / "candidates.csv")
    source_base_dir = pack_dir if pack_dir else settings.root_dir
    benchmark_path = settings.manual_dir / "benchmark_price_history.csv"
    if not benchmark_path.exists():
        benchmark_path = settings.manual_dir / "price_history.csv"
    price_history_path = settings.manual_dir / "price_history.csv"

    for row in _read_csv(fund_path):
        raw = str(row.get("url_or_path", ""))
        rows.append(
            _make_row(
                settings,
                area="fund_rules",
                row_id=str(row.get("asset_code", "")),
                field="url_or_path",
                source_file=fund_path,
                raw_value=raw,
                evidence_ref=raw.strip(),
                base_dir=source_base_dir,
            )
        )

    for row in _read_csv(candidate_path):
        excluded = str(row.get("is_excluded", "")).strip().lower() in {"1", "true", "yes", "y"}
        if excluded:
            continue
        raw = str(row.get("source_url", ""))
        rows.append(
            _make_row(
                settings,
                area="candidate_universe",
                row_id=str(row.get("asset_code", "")),
                field="source_url",
                source_file=candidate_path,
                raw_value=raw,
                evidence_ref=raw.strip(),
                base_dir=source_base_dir,
            )
        )

    seen_nav: set[tuple[str, str]] = set()
    for row in _read_csv(price_history_path):
        asset_code = str(row.get("asset_code", ""))
        raw = str(row.get("url_or_path", ""))
        key = (asset_code, raw)
        if key in seen_nav:
            continue
        seen_nav.add(key)
        rows.append(
            _make_row(
                settings,
                area="candidate_nav_history",
                row_id=asset_code,
                field="url_or_path",
                source_file=price_history_path,
                raw_value=raw,
                evidence_ref=raw.strip(),
                base_dir=settings.root_dir,
            )
        )

    seen_benchmark: set[tuple[str, str]] = set()
    for row in _read_csv(benchmark_path):
        asset_code = str(row.get("asset_code", ""))
        raw = str(row.get("url_or_path", ""))
        key = (asset_code, raw)
        if key in seen_benchmark:
            continue
        seen_benchmark.add(key)
        rows.append(
            _make_row(
                settings,
                area="benchmark_history",
                row_id=asset_code,
                field="url_or_path",
                source_file=benchmark_path,
                raw_value=raw,
                evidence_ref=raw.strip(),
                base_dir=settings.root_dir,
            )
        )

    return rows


def _write_csv(path: Path, rows: list[EvidenceRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else list(EvidenceRow.__dataclass_fields__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _write_markdown(path: Path, *, settings: Settings, result: dict[str, object], rows: list[EvidenceRow]) -> None:
    status_counts = Counter(row.status for row in rows)
    area_counts = Counter(row.area for row in rows)
    lines = [
        "# Source Evidence Audit",
        "",
        f"- Generated: {result['generated_at']}",
        f"- Audit run ID: {result['audit_run_id']}",
        f"- Status: {result['status']}",
        f"- Row count: {result['row_count']}",
        f"- Valid reference count: {result['valid_count']}",
        f"- Invalid reference count: {result['invalid_count']}",
        f"- Local hashed file count: {result['local_hashed_count']}",
        f"- URL count: {result['url_count']}",
        f"- SQLite rows written: {result['db_rows_written']}",
        f"- Status counts: {dict(status_counts)}",
        f"- Area counts: {dict(area_counts)}",
        "",
        "## Scope",
        "",
        "This audit records source references from production intake files or a selected intake pack. It hashes local evidence files and validates URL shape, but it does not fetch remote URLs or treat public aggregation as official evidence. When `--pack-dir` is used, relative local evidence paths resolve from that pack directory.",
        "",
        "## Failed Or Weak References",
        "",
    ]
    failures = [row for row in rows if row.status not in PASS_STATUSES]
    if failures:
        lines.append("| Area | Row | Field | Status | Reference | Message |")
        lines.append("|---|---|---|---|---|---|")
        for row in failures[:80]:
            ref = row.evidence_ref.replace("|", "/")
            msg = row.message.replace("|", "/")
            lines.append(f"| {row.area} | {row.row_id} | {row.field} | {row.status} | {ref} | {msg} |")
        if len(failures) > 80:
            lines.append(f"| ... | ... | ... | ... | {len(failures) - 80} more rows in CSV | ... |")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Local Evidence Hashes",
            "",
        ]
    )
    hashed = [row for row in rows if row.status == "hashed_local_file"]
    if hashed:
        lines.append("| Area | Row | File | SHA256 | Bytes | MTime |")
        lines.append("|---|---|---|---|---|---|")
        for row in hashed[:80]:
            display_file = _rel(settings, Path(row.resolved_path)) if row.resolved_path else ""
            lines.append(f"| {row.area} | {row.row_id} | `{display_file}` | `{row.sha256}` | {row.size_bytes} | {row.mtime} |")
        if len(hashed) > 80:
            lines.append(f"| ... | ... | ... | {len(hashed) - 80} more rows in CSV | ... | ... |")
    else:
        lines.append("- None")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _persist_rows(settings: Settings, *, audit_run_id: str, generated_at: str, rows: list[EvidenceRow]) -> int:
    init_db(settings.db_path)
    created_at = _now(settings)
    with connect(settings.db_path) as conn:
        conn.execute("DELETE FROM source_evidence_audit_snapshot WHERE audit_run_id=?", (audit_run_id,))
        for row in rows:
            payload = asdict(row)
            insert_row(
                conn,
                "source_evidence_audit_snapshot",
                {
                    "audit_run_id": audit_run_id,
                    "generated_at": generated_at,
                    "area": payload["area"],
                    "row_id": payload["row_id"],
                    "field": payload["field"],
                    "source_file": payload["source_file"],
                    "raw_value": payload["raw_value"],
                    "evidence_ref": payload["evidence_ref"],
                    "ref_type": payload["ref_type"],
                    "status": payload["status"],
                    "message": payload["message"],
                    "resolved_path": payload["resolved_path"],
                    "sha256": payload["sha256"],
                    "size_bytes": payload["size_bytes"],
                    "mtime": payload["mtime"],
                    "created_at": created_at,
                },
            )
    return len(rows)


def build_source_evidence_audit(
    settings: Settings,
    *,
    pack_dir: Path | None = None,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    rows = _collect_rows(settings, pack_dir=pack_dir)
    status_counts = Counter(row.status for row in rows)
    invalid_count = sum(1 for row in rows if row.status not in PASS_STATUSES)
    local_hashed_count = status_counts.get("hashed_local_file", 0)
    url_count = status_counts.get("valid_url", 0)
    generated_at = _now(settings)
    audit_run_id = "source_evidence_" + generated_at.replace(":", "").replace("-", "").replace("+", "_").replace("T", "_")
    output_dir = settings.root_dir / "outputs" / "preflight"
    files = {
        "markdown": str(output_dir / "source_evidence_audit_latest.md"),
        "csv": str(output_dir / "source_evidence_audit_latest.csv"),
        "json": str(output_dir / "source_evidence_audit_latest.json"),
    }
    db_rows_written = _persist_rows(settings, audit_run_id=audit_run_id, generated_at=generated_at, rows=rows) if write_output else 0
    result: dict[str, object] = {
        "generated_at": generated_at,
        "audit_run_id": audit_run_id,
        "status": "pass" if rows and invalid_count == 0 else "blocked",
        "row_count": len(rows),
        "valid_count": len(rows) - invalid_count,
        "invalid_count": invalid_count,
        "local_hashed_count": local_hashed_count,
        "url_count": url_count,
        "db_rows_written": db_rows_written,
        "status_counts": dict(status_counts),
        "area_counts": dict(Counter(row.area for row in rows)),
        "pack_dir": str(pack_dir) if pack_dir else None,
        "files": files,
    }
    if write_output:
        _write_csv(Path(files["csv"]), rows)
        _write_markdown(Path(files["markdown"]), settings=settings, result=result, rows=rows)
        Path(files["json"]).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
