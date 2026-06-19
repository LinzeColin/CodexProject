from __future__ import annotations

import csv
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.adapters.alipay_importer import read_positions_csv
from app.config import Settings


@dataclass(frozen=True)
class NormalizeIssue:
    row_number: int
    field: str
    severity: str
    message: str


@dataclass(frozen=True)
class NormalizeResult:
    generated_at: str
    status: str
    source_csv: str
    output_csv: str
    evidence_ref: str
    copied_evidence_path: str
    write_pack: bool
    row_count: int
    block_count: int
    warn_count: int
    warnings: list[str]
    issues: list[NormalizeIssue]
    next_command: str


ALIASES: dict[str, tuple[str, ...]] = {
    "asset_code": ("asset_code", "基金代码", "产品代码", "证券代码", "代码", "fund_code", "code"),
    "asset_name": ("asset_name", "基金名称", "产品名称", "持仓名称", "名称", "fund_name", "name"),
    "platform": ("platform", "平台", "来源平台"),
    "current_amount": ("current_amount", "持有金额", "持仓金额", "持有市值", "当前市值", "市值", "资产", "金额"),
    "current_weight": ("current_weight", "持仓占比", "持有占比", "占比", "仓位", "比例", "weight"),
    "cost_basis": ("cost_basis", "成本", "持仓成本", "持有成本", "本金", "cost"),
    "unrealized_pnl": ("unrealized_pnl", "持有收益", "持仓收益", "收益", "浮动盈亏", "盈亏", "pnl"),
    "as_of": ("as_of", "日期", "更新时间", "数据日期", "截图日期", "持仓日期", "更新日期"),
}

OUTPUT_FIELDS = [
    "asset_code",
    "asset_name",
    "platform",
    "current_amount",
    "current_weight",
    "cost_basis",
    "unrealized_pnl",
    "as_of",
    "source_note",
]


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return list(reader.fieldnames or []), list(reader)
        except Exception as exc:
            last_error = exc
    raise ValueError(f"Cannot read Alipay position source CSV {path}: {last_error}")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in OUTPUT_FIELDS})


def _normalized_header_map(fieldnames: list[str]) -> dict[str, str]:
    lookup = {field.strip().lower(): field for field in fieldnames}
    result: dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            key = alias.strip().lower()
            if key in lookup:
                result[canonical] = lookup[key]
                break
    return result


def _cell(row: dict[str, str], header_map: dict[str, str], field: str) -> str:
    source_field = header_map.get(field)
    if not source_field:
        return ""
    return str(row.get(source_field) or "").strip()


def _safe_asset_code(name: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in name.strip())[:80].strip("_")
    return f"ALIPAY_NAME_{safe or 'UNKNOWN'}"


def _clean_number(value: str, *, weight: bool = False) -> str:
    raw = value.strip()
    if not raw:
        return ""
    raw = raw.replace(",", "").replace("，", "")
    raw = raw.replace("￥", "").replace("¥", "").replace("元", "")
    raw = raw.replace("+", "").strip()
    if raw.endswith("%"):
        try:
            return f"{float(raw[:-1].strip()) / 100.0:.8f}".rstrip("0").rstrip(".")
        except ValueError:
            return raw
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return raw
    number = float(match.group(0))
    if weight and number > 1:
        number = number / 100.0
    text = f"{number:.8f}".rstrip("0").rstrip(".")
    return text or "0"


def _copy_or_ref_evidence(settings: Settings, source_csv: Path, evidence: str | None, pack_dir: Path) -> tuple[str, str]:
    raw = (evidence or "").strip()
    if raw:
        parsed = urlparse(raw)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return raw, ""
        source = Path(raw).expanduser()
    else:
        source = source_csv
    if not source.is_absolute():
        source = settings.root_dir / source
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Evidence file does not exist: {source}")
    evidence_dir = pack_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", source.name).strip("._-") or "alipay_positions_evidence.csv"
    destination = evidence_dir / safe_name
    if source.resolve(strict=False) != destination.resolve(strict=False):
        shutil.copy2(source, destination)
    return f"evidence/{safe_name}", str(destination)


def normalize_alipay_positions(
    settings: Settings,
    *,
    csv_path: Path,
    evidence: str | None = None,
    as_of: str | None = None,
    output_path: Path | None = None,
    write_pack: bool = False,
) -> dict[str, object]:
    settings.ensure_dirs()
    source_csv = csv_path.expanduser()
    if not source_csv.is_absolute():
        source_csv = settings.root_dir / source_csv
    if not source_csv.exists():
        raise FileNotFoundError(f"Alipay position source CSV does not exist: {source_csv}")

    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    evidence_ref, copied_evidence_path = _copy_or_ref_evidence(settings, source_csv, evidence, pack_dir)
    fieldnames, raw_rows = _read_csv(source_csv)
    header_map = _normalized_header_map(fieldnames)
    output_csv = output_path or (
        pack_dir / "01_alipay_positions_to_fill.csv"
        if write_pack
        else pack_dir / "01_alipay_positions_normalized_candidate.csv"
    )

    issues: list[NormalizeIssue] = []
    if "asset_name" not in header_map:
        issues.append(NormalizeIssue(1, "asset_name", "block", "Missing asset name column; accepted aliases include asset_name, 基金名称, 产品名称, 持仓名称, 名称"))
    if "current_amount" not in header_map:
        issues.append(NormalizeIssue(1, "current_amount", "block", "Missing current amount column; accepted aliases include current_amount, 持有金额, 持仓金额, 市值"))

    rows: list[dict[str, str]] = []
    for index, raw in enumerate(raw_rows, start=2):
        asset_name = _cell(raw, header_map, "asset_name")
        asset_code = _cell(raw, header_map, "asset_code") or _safe_asset_code(asset_name)
        row_as_of = _cell(raw, header_map, "as_of") or (as_of or "")
        current_amount = _clean_number(_cell(raw, header_map, "current_amount"))
        current_weight = _clean_number(_cell(raw, header_map, "current_weight"), weight=True)
        cost_basis = _clean_number(_cell(raw, header_map, "cost_basis"))
        unrealized_pnl = _clean_number(_cell(raw, header_map, "unrealized_pnl"))
        if not asset_name:
            issues.append(NormalizeIssue(index, "asset_name", "block", "Asset name is empty"))
        if not current_amount:
            issues.append(NormalizeIssue(index, "current_amount", "block", "Current amount is empty"))
        if not row_as_of:
            issues.append(NormalizeIssue(index, "as_of", "block", "as_of is empty; pass --as-of YYYY-MM-DD or include a date column"))
        rows.append(
            {
                "asset_code": asset_code,
                "asset_name": asset_name,
                "platform": _cell(raw, header_map, "platform") or "Alipay",
                "current_amount": current_amount or "0",
                "current_weight": current_weight or "0",
                "cost_basis": cost_basis or "0",
                "unrealized_pnl": unrealized_pnl or "0",
                "as_of": row_as_of,
                "source_note": (
                    f"evidence={evidence_ref}; normalized_from={source_csv.name}; "
                    "normalization_profile=alipay_flexible_csv; manual_review_required"
                ),
            }
        )

    _write_csv(output_csv, rows)
    warnings: list[str] = []
    try:
        import_result = read_positions_csv(output_csv)
        warnings.extend(import_result.warnings)
    except Exception as exc:
        issues.append(NormalizeIssue(1, "schema", "block", f"Normalized CSV failed canonical parser: {exc}"))

    block_count = sum(1 for issue in issues if issue.severity == "block")
    warn_count = sum(1 for issue in issues if issue.severity == "warn") + len(warnings)
    status = "pass" if block_count == 0 else "blocked"
    result = NormalizeResult(
        generated_at=_now(settings),
        status=status,
        source_csv=str(source_csv),
        output_csv=str(output_csv),
        evidence_ref=evidence_ref,
        copied_evidence_path=copied_evidence_path,
        write_pack=write_pack,
        row_count=len(rows),
        block_count=block_count,
        warn_count=warn_count,
        warnings=warnings,
        issues=issues,
        next_command="python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --json",
    )
    result_dict = asdict(result)
    output_dir = settings.root_dir / "outputs" / "intake_pack"
    json_path = output_dir / "alipay_positions_normalization_latest.json"
    md_path = output_dir / "alipay_positions_normalization_latest.md"
    json_path.write_text(json.dumps(result_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Alipay Positions Normalization",
        "",
        f"- Generated: {result.generated_at}",
        f"- Status: {result.status}",
        f"- Source CSV: `{source_csv.name}`",
        f"- Output CSV: `{output_csv.relative_to(settings.root_dir) if output_csv.is_relative_to(settings.root_dir) else output_csv}`",
        f"- Evidence reference: `{evidence_ref}`",
        f"- Copied evidence path: `{Path(copied_evidence_path).relative_to(settings.root_dir) if copied_evidence_path and Path(copied_evidence_path).is_relative_to(settings.root_dir) else copied_evidence_path or 'none'}`",
        f"- Write pack: {write_pack}",
        f"- Row count: {len(rows)}",
        f"- Block count: {block_count}",
        f"- Warn count: {warn_count}",
        "",
        "## Boundary",
        "",
        "This command writes an intake-pack candidate only. It does not copy production files, send email, or place trades.",
        "",
        "## Issues",
        "",
    ]
    if issues:
        for issue in issues[:80]:
            lines.append(f"- Row {issue.row_number} `{issue.field}` [{issue.severity}]: {issue.message}")
    else:
        lines.append("- None")
    if warnings:
        lines.extend(["", "## Parser Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(["", "## Next Command", "", "```bash", result.next_command, "```"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result_dict["json_path"] = str(json_path)
    result_dict["markdown_path"] = str(md_path)
    return result_dict
