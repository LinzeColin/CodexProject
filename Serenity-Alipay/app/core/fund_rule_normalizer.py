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

from app.adapters.manual_sources import load_fund_rules
from app.config import Settings


@dataclass(frozen=True)
class FundRuleNormalizeIssue:
    row_number: int
    field: str
    severity: str
    message: str


@dataclass(frozen=True)
class FundRuleNormalizeResult:
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
    issues: list[FundRuleNormalizeIssue]
    next_command: str


OUTPUT_FIELDS = [
    "asset_code",
    "subscription_status",
    "redemption_status",
    "cutoff_time",
    "confirm_lag",
    "redeem_lag",
    "subscription_fee",
    "redemption_fee",
    "subscription_fee_schedule",
    "redemption_fee_schedule",
    "management_fee",
    "custody_fee",
    "sales_service_fee",
    "min_purchase_amount",
    "alipay_trade_status",
    "moomoo_trade_status",
    "platform_trade_note",
    "source_name",
    "source_type",
    "source_priority",
    "url_or_path",
    "evidence_level",
    "fallback_aggregated",
    "as_of",
    "fee_schedule_as_of",
    "fee_schedule_note",
]

ALIASES: dict[str, tuple[str, ...]] = {
    "asset_code": ("asset_code", "基金代码", "产品代码", "代码", "fund_code", "code"),
    "subscription_status": ("subscription_status", "申购状态", "买入状态", "购买状态", "是否可申购"),
    "redemption_status": ("redemption_status", "赎回状态", "卖出状态", "是否可赎回"),
    "cutoff_time": ("cutoff_time", "交易截止时间", "截止时间", "申购截止", "买入截止", "T日截止"),
    "confirm_lag": ("confirm_lag", "确认时间", "确认周期", "份额确认", "申购确认", "买入确认"),
    "redeem_lag": ("redeem_lag", "赎回到账", "赎回周期", "卖出到账", "到账时间"),
    "subscription_fee": ("subscription_fee", "申购费", "申购费率", "买入费率", "购买费率"),
    "redemption_fee": ("redemption_fee", "赎回费", "赎回费率", "卖出费率"),
    "subscription_fee_schedule": ("subscription_fee_schedule", "申购费分档", "申购费分档规则", "申购费率分档", "买入费分档", "购买费分档"),
    "redemption_fee_schedule": ("redemption_fee_schedule", "赎回费分档", "赎回费分档规则", "赎回费率分档", "卖出费分档"),
    "management_fee": ("management_fee", "管理费", "管理费率"),
    "custody_fee": ("custody_fee", "托管费", "托管费率"),
    "sales_service_fee": ("sales_service_fee", "销售服务费", "销售服务费率", "C类服务费"),
    "min_purchase_amount": ("min_purchase_amount", "起购金额", "最低申购", "最低买入", "最小申购金额"),
    "alipay_trade_status": ("alipay_trade_status", "支付宝交易可用性", "支付宝可交易", "支付宝交易状态", "支付宝平台状态"),
    "moomoo_trade_status": ("moomoo_trade_status", "MooMoo交易可用性", "moomoo可交易", "MooMoo交易状态", "富途牛牛交易可用性", "moomoo平台状态"),
    "platform_trade_note": ("platform_trade_note", "平台交易备注", "交易平台备注", "交易路径备注", "平台可交易说明"),
    "source_name": ("source_name", "来源名称", "证据来源", "source", "来源"),
    "source_type": ("source_type", "来源类型", "source_type"),
    "source_priority": ("source_priority", "来源优先级", "source_priority"),
    "url_or_path": ("url_or_path", "证据链接", "规则链接", "来源链接", "url", "path", "链接"),
    "evidence_level": ("evidence_level", "证据等级", "evidence_level"),
    "fallback_aggregated": ("fallback_aggregated", "是否聚合源", "fallback_aggregated"),
    "as_of": ("as_of", "日期", "更新时间", "规则日期", "截图日期", "更新日期"),
    "fee_schedule_as_of": ("fee_schedule_as_of", "费率规则时间", "费率更新时间", "费率日期", "费率截图日期"),
    "fee_schedule_note": ("fee_schedule_note", "费率口径说明", "费率备注", "费用说明", "规则备注"),
}


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
    raise ValueError(f"Cannot read fund rule source CSV {path}: {last_error}")


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


def _rate(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    raw = raw.replace(",", "").replace("，", "").replace("约", "").replace("不超过", "")
    if raw in {"无", "免", "免费", "0费率"}:
        return "0"
    if raw.endswith("%"):
        try:
            return f"{float(raw[:-1].strip()) / 100.0:.8f}".rstrip("0").rstrip(".")
        except ValueError:
            return raw
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return raw
    number = float(match.group(0))
    if number > 1:
        number = number / 100.0
    return f"{number:.8f}".rstrip("0").rstrip(".") or "0"


def _amount(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""
    raw = raw.replace(",", "").replace("，", "").replace("￥", "").replace("¥", "").replace("元", "")
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    return match.group(0) if match else raw


def _status(value: str, default: str = "open") -> str:
    text = value.strip().lower()
    if not text:
        return default
    if any(token in text for token in ["限额", "限制", "受限", "limited"]):
        return "limited"
    if any(token in text for token in ["开放", "可", "open", "正常"]):
        return "open"
    if any(token in text for token in ["暂停", "关闭", "不可", "closed", "suspend"]):
        return "closed"
    return value.strip()


def _default_alipay_trade_status(subscription_status: str, redemption_status: str) -> str:
    sub = subscription_status.lower()
    red = redemption_status.lower()
    if sub == "open" and red == "open":
        return "待支付宝交易页确认（基金本身申赎开放）"
    if sub == "limited" or red == "limited":
        return "待支付宝交易页确认（基金本身申赎存在额度或时段限制）"
    return "待支付宝交易页确认（基金本身申购或赎回受限）"


def _default_moomoo_trade_status() -> str:
    return "未验证MooMoo场外基金交易；MooMoo仅作行情/代理数据参考"


def _default_platform_trade_note() -> str:
    return "平台交易可用性只作建议；不支持支付宝或MooMoo交易不能单独排除候选；执行前以支付宝交易确认页或基金公司官方平台为准"


def _source_type(value: str, source_name: str) -> str:
    text = f"{value} {source_name}".strip().lower()
    if "moomoo" in text:
        return "moomoo"
    if "支付宝" in text or "alipay" in text:
        return "alipay"
    if "official" in text or "官网" in text or "基金公司" in text:
        return "official"
    return "alipay"


def _source_priority(source_type: str, raw_priority: str) -> str:
    if raw_priority.strip():
        return raw_priority.strip()
    return {"moomoo": "1", "alipay": "2", "official": "3"}.get(source_type, "3")


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
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", source.name).strip("._-") or "fund_rules_evidence.csv"
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


def normalize_fund_rules(
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
        raise FileNotFoundError(f"Fund rule source CSV does not exist: {source_csv}")

    pack_dir = settings.root_dir / "outputs" / "intake_pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    evidence_ref, copied_evidence_path = _copy_or_ref_evidence(settings, source_csv, evidence, pack_dir)
    fieldnames, raw_rows = _read_csv(source_csv)
    header_map = _header_map(fieldnames)
    output_csv = output_path or (
        pack_dir / "02_fund_rules_to_fill.csv"
        if write_pack
        else pack_dir / "02_fund_rules_normalized_candidate.csv"
    )

    issues: list[FundRuleNormalizeIssue] = []
    if "asset_code" not in header_map:
        issues.append(FundRuleNormalizeIssue(1, "asset_code", "block", "Missing asset code column; accepted aliases include asset_code, 基金代码, 产品代码"))

    rows: list[dict[str, str]] = []
    for index, raw in enumerate(raw_rows, start=2):
        asset_code = _cell(raw, header_map, "asset_code")
        source_name = _cell(raw, header_map, "source_name") or "Alipay or fund-company rule page"
        source_type = _source_type(_cell(raw, header_map, "source_type"), source_name)
        row_as_of = _cell(raw, header_map, "as_of") or (as_of or "")
        subscription_status = _status(_cell(raw, header_map, "subscription_status"))
        redemption_status = _status(_cell(raw, header_map, "redemption_status"))
        next_row = {
            "asset_code": asset_code,
            "subscription_status": subscription_status,
            "redemption_status": redemption_status,
            "cutoff_time": _cell(raw, header_map, "cutoff_time") or "15:00",
            "confirm_lag": _cell(raw, header_map, "confirm_lag") or "T+1",
            "redeem_lag": _cell(raw, header_map, "redeem_lag") or "T+3",
            "subscription_fee": _rate(_cell(raw, header_map, "subscription_fee")),
            "redemption_fee": _rate(_cell(raw, header_map, "redemption_fee")),
            "subscription_fee_schedule": _cell(raw, header_map, "subscription_fee_schedule"),
            "redemption_fee_schedule": _cell(raw, header_map, "redemption_fee_schedule"),
            "management_fee": _rate(_cell(raw, header_map, "management_fee")),
            "custody_fee": _rate(_cell(raw, header_map, "custody_fee")),
            "sales_service_fee": _rate(_cell(raw, header_map, "sales_service_fee")) or "0",
            "min_purchase_amount": _amount(_cell(raw, header_map, "min_purchase_amount")) or "10",
            "alipay_trade_status": _cell(raw, header_map, "alipay_trade_status")
            or _default_alipay_trade_status(subscription_status, redemption_status),
            "moomoo_trade_status": _cell(raw, header_map, "moomoo_trade_status") or _default_moomoo_trade_status(),
            "platform_trade_note": _cell(raw, header_map, "platform_trade_note") or _default_platform_trade_note(),
            "source_name": source_name,
            "source_type": source_type,
            "source_priority": _source_priority(source_type, _cell(raw, header_map, "source_priority")),
            "url_or_path": _cell(raw, header_map, "url_or_path") or evidence_ref,
            "evidence_level": _cell(raw, header_map, "evidence_level") or "Strong",
            "fallback_aggregated": _cell(raw, header_map, "fallback_aggregated") or "false",
            "as_of": row_as_of,
            "fee_schedule_as_of": _cell(raw, header_map, "fee_schedule_as_of") or row_as_of,
            "fee_schedule_note": _cell(raw, header_map, "fee_schedule_note"),
        }
        for field in [
            "asset_code",
            "subscription_fee",
            "redemption_fee",
            "subscription_fee_schedule",
            "redemption_fee_schedule",
            "management_fee",
            "custody_fee",
            "as_of",
        ]:
            if not next_row[field]:
                issues.append(FundRuleNormalizeIssue(index, field, "block", f"{field} is required for production fund-rule intake"))
        rows.append(next_row)

    _write_csv(output_csv, rows)
    try:
        load_fund_rules(output_csv)
    except Exception as exc:
        issues.append(FundRuleNormalizeIssue(1, "schema", "block", f"Normalized CSV failed canonical parser: {exc}"))

    block_count = sum(1 for issue in issues if issue.severity == "block")
    warn_count = sum(1 for issue in issues if issue.severity == "warn")
    status = "pass" if block_count == 0 else "blocked"
    result = FundRuleNormalizeResult(
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
    json_path = output_dir / "fund_rules_normalization_latest.json"
    md_path = output_dir / "fund_rules_normalization_latest.md"
    json_path.write_text(json.dumps(result_dict, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Fund Rules Normalization",
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
