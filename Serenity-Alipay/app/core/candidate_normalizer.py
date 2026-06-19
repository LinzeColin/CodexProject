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

from app.adapters.manual_sources import load_candidates
from app.config import Settings


@dataclass(frozen=True)
class CandidateNormalizeIssue:
    row_number: int
    field: str
    severity: str
    message: str


@dataclass(frozen=True)
class CandidateNormalizeResult:
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
    issues: list[CandidateNormalizeIssue]
    next_command: str


OUTPUT_FIELDS = [
    "asset_code",
    "asset_name",
    "asset_type",
    "market",
    "fund_company",
    "risk_level",
    "theme",
    "is_off_platform_fund",
    "is_excluded",
    "exclusion_reason",
    "official_source_count",
    "fallback_aggregated",
    "evidence_level",
    "source_name",
    "source_type",
    "source_url",
    "missing_nav_days",
    "missing_holding_days",
    "conflict_flag",
    "as_of",
]

ALIASES: dict[str, tuple[str, ...]] = {
    "asset_code": ("asset_code", "基金代码", "产品代码", "证券代码", "代码", "fund_code", "code"),
    "asset_name": ("asset_name", "基金名称", "产品名称", "标的名称", "名称", "fund_name", "name"),
    "asset_type": ("asset_type", "资产类型", "基金类型", "类型", "category"),
    "market": ("market", "市场", "投资市场", "market"),
    "fund_company": ("fund_company", "基金公司", "管理人", "基金管理人", "company"),
    "risk_level": ("risk_level", "风险等级", "风险", "risk"),
    "theme": ("theme", "主题", "方向", "赛道", "theme"),
    "is_off_platform_fund": ("is_off_platform_fund", "是否场外基金", "场外基金", "off_platform"),
    "is_excluded": ("is_excluded", "是否排除", "排除", "excluded"),
    "exclusion_reason": ("exclusion_reason", "排除原因", "原因"),
    "official_source_count": ("official_source_count", "官方来源数", "官方源数量", "source_count", "来源数"),
    "fallback_aggregated": ("fallback_aggregated", "是否聚合源", "聚合源", "fallback_aggregated"),
    "evidence_level": ("evidence_level", "证据等级", "证据强度"),
    "source_name": ("source_name", "来源名称", "证据来源", "来源", "source"),
    "source_type": ("source_type", "来源类型", "source_type"),
    "source_url": ("source_url", "证据链接", "来源链接", "url", "path", "链接"),
    "missing_nav_days": ("missing_nav_days", "净值缺失天数", "缺失净值天数"),
    "missing_holding_days": ("missing_holding_days", "持仓缺失天数", "缺失持仓天数"),
    "conflict_flag": ("conflict_flag", "是否冲突", "冲突", "source_conflict"),
    "as_of": ("as_of", "日期", "更新时间", "截图日期", "更新日期"),
}

CONSERVATIVE_MARKERS = ("债券", "货币", "余额宝", "稳健", "现金", "bond", "money", "cash", "yuebao")


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
    raise ValueError(f"Cannot read candidate source CSV {path}: {last_error}")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in OUTPUT_FIELDS})


def _header_map(fieldnames: list[str]) -> dict[str, str]:
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


def _bool(value: str, default: str = "false") -> str:
    text = value.strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "是", "可", "已排除"}:
        return "true"
    if text in {"0", "false", "no", "n", "否", "未排除"}:
        return "false"
    return value.strip()


def _int(value: str, default: str) -> str:
    raw = value.strip()
    if not raw:
        return default
    match = re.search(r"-?\d+", raw)
    return match.group(0) if match else raw


def _source_type(value: str, source_name: str) -> str:
    text = f"{value} {source_name}".strip().lower()
    if "moomoo" in text or "富途" in text:
        return "moomoo"
    if "支付宝" in text or "alipay" in text:
        return "alipay"
    if "aggregated" in text or "聚合" in text or "天天基金" in text:
        return "aggregated"
    if "official" in text or "官网" in text or "基金公司" in text or "公告" in text:
        return "official"
    return value.strip() or "official"


def _asset_type(value: str, asset_name: str) -> str:
    text = f"{value} {asset_name}".lower()
    if any(marker in text for marker in ("债券", "bond")):
        return "bond_fund"
    if any(marker in text for marker in ("货币", "money", "余额宝", "yuebao", "cash")):
        return "money_fund"
    return value.strip() or "off_platform_fund"


def _risk_level(value: str, asset_type: str) -> str:
    text = f"{value} {asset_type}".strip().lower()
    if any(marker in text for marker in ("低", "稳健", "low", "bond", "money", "cash")):
        return "low"
    if any(marker in text for marker in ("中", "medium")):
        return "medium"
    return value.strip() or "high"


def _conservative(asset_name: str, asset_type: str, theme: str) -> bool:
    text = f"{asset_name} {asset_type} {theme}".lower()
    return any(marker in text for marker in CONSERVATIVE_MARKERS)


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
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", source.name).strip("._-") or "candidates_evidence.csv"
    destination = evidence_dir / safe_name
    if source.resolve(strict=False) != destination.resolve(strict=False):
        shutil.copy2(source, destination)
    return f"evidence/{safe_name}", str(destination)


def _rel(settings: Settings, path: Path | str) -> str:
    path_obj = Path(path)
    try:
        return path_obj.relative_to(settings.root_dir).as_posix()
    except ValueError:
        return str(path)


def normalize_candidates(
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
        raise FileNotFoundError(f"Candidate source CSV does not exist: {source_csv}")

    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    evidence_ref, copied_evidence_path = _copy_or_ref_evidence(settings, source_csv, evidence, pack_dir)
    fieldnames, raw_rows = _read_csv(source_csv)
    header_map = _header_map(fieldnames)
    output_csv = output_path or (
        pack_dir / "03_candidates_to_fill.csv"
        if write_pack
        else pack_dir / "03_candidates_normalized_candidate.csv"
    )

    issues: list[CandidateNormalizeIssue] = []
    if "asset_code" not in header_map:
        issues.append(CandidateNormalizeIssue(1, "asset_code", "block", "Missing asset code column; accepted aliases include asset_code, 基金代码, 产品代码"))
    if "asset_name" not in header_map:
        issues.append(CandidateNormalizeIssue(1, "asset_name", "block", "Missing asset name column; accepted aliases include asset_name, 基金名称, 产品名称"))

    rows: list[dict[str, str]] = []
    for index, raw in enumerate(raw_rows, start=2):
        asset_code = _cell(raw, header_map, "asset_code")
        asset_name = _cell(raw, header_map, "asset_name")
        asset_type = _asset_type(_cell(raw, header_map, "asset_type"), asset_name)
        theme = _cell(raw, header_map, "theme") or "growth"
        source_name = _cell(raw, header_map, "source_name") or "MooMoo/Alipay/official candidate evidence"
        source_type = _source_type(_cell(raw, header_map, "source_type"), source_name)
        conservative = _conservative(asset_name, asset_type, theme)
        row_as_of = _cell(raw, header_map, "as_of") or (as_of or "")
        official_count = _int(_cell(raw, header_map, "official_source_count"), "1")
        fallback_aggregated = _bool(_cell(raw, header_map, "fallback_aggregated"), "true" if source_type == "aggregated" else "false")
        is_excluded = _bool(_cell(raw, header_map, "is_excluded"), "true" if conservative else "false")
        exclusion_reason = _cell(raw, header_map, "exclusion_reason")
        if conservative and not exclusion_reason:
            exclusion_reason = "conservative asset exclusion"
        next_row = {
            "asset_code": asset_code,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "market": _cell(raw, header_map, "market") or "CN/US",
            "fund_company": _cell(raw, header_map, "fund_company") or "manual_review_required",
            "risk_level": _risk_level(_cell(raw, header_map, "risk_level"), asset_type),
            "theme": theme,
            "is_off_platform_fund": _bool(_cell(raw, header_map, "is_off_platform_fund"), "true"),
            "is_excluded": is_excluded,
            "exclusion_reason": exclusion_reason,
            "official_source_count": official_count,
            "fallback_aggregated": fallback_aggregated,
            "evidence_level": _cell(raw, header_map, "evidence_level") or "Strong",
            "source_name": source_name,
            "source_type": source_type,
            "source_url": _cell(raw, header_map, "source_url") or evidence_ref,
            "missing_nav_days": _int(_cell(raw, header_map, "missing_nav_days"), "0"),
            "missing_holding_days": _int(_cell(raw, header_map, "missing_holding_days"), "0"),
            "conflict_flag": _bool(_cell(raw, header_map, "conflict_flag"), "false"),
            "as_of": row_as_of,
        }
        for field in ["asset_code", "asset_name", "source_url", "as_of"]:
            if not next_row[field]:
                issues.append(CandidateNormalizeIssue(index, field, "block", f"{field} is required for candidate-universe intake"))
        if not next_row["is_excluded"] == "true":
            try:
                if int(next_row["official_source_count"]) < settings.min_official_sources_action_ready:
                    issues.append(
                        CandidateNormalizeIssue(
                            index,
                            "official_source_count",
                            "warn",
                            f"official_source_count {next_row['official_source_count']} is below production threshold {settings.min_official_sources_action_ready}",
                        )
                    )
            except ValueError:
                issues.append(CandidateNormalizeIssue(index, "official_source_count", "block", "official_source_count must be an integer"))
            if next_row["source_type"] not in {"moomoo", "alipay", "official"}:
                issues.append(CandidateNormalizeIssue(index, "source_type", "warn", f"source_type {next_row['source_type']} will not unlock production"))
            if next_row["fallback_aggregated"] == "true":
                issues.append(CandidateNormalizeIssue(index, "fallback_aggregated", "warn", "aggregated fallback cannot unlock production candidate"))
        rows.append(next_row)

    _write_csv(output_csv, rows)
    try:
        load_candidates(output_csv)
    except Exception as exc:
        issues.append(CandidateNormalizeIssue(1, "schema", "block", f"Normalized CSV failed canonical parser: {exc}"))

    block_count = sum(1 for issue in issues if issue.severity == "block")
    warn_count = sum(1 for issue in issues if issue.severity == "warn")
    status = "pass" if block_count == 0 else "blocked"
    result = CandidateNormalizeResult(
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
        issues=issues,
        next_command="python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --json",
    )
    result_dict = asdict(result)
    output_dir = settings.root_dir / "outputs" / "intake_pack"
    json_path = output_dir / "candidates_normalization_latest.json"
    md_path = output_dir / "candidates_normalization_latest.md"
    json_path.write_text(json.dumps(result_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Candidate Universe Normalization",
        "",
        f"- Generated: {result.generated_at}",
        f"- Status: {result.status}",
        f"- Source CSV: `{source_csv.name}`",
        f"- Output CSV: `{_rel(settings, output_csv)}`",
        f"- Evidence reference: `{evidence_ref}`",
        f"- Copied evidence path: `{_rel(settings, copied_evidence_path) if copied_evidence_path else 'none'}`",
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
    lines.extend(["", "## Next Command", "", "```bash", result.next_command, "```"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result_dict["json_path"] = str(json_path)
    result_dict["markdown_path"] = str(md_path)
    return result_dict
