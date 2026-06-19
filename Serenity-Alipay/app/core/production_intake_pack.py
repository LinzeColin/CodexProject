from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from app.config import Settings
from app.core.intake_validator import validate_intake
from app.core.path_display import display_path


@dataclass(frozen=True)
class IntakePackResult:
    generated_at: str
    output_dir: str
    production_ready: bool
    block_count: int
    warn_count: int
    files: dict[str, str]


def _now(settings: Settings) -> str:
    return datetime.now(ZoneInfo(settings.timezone_primary)).isoformat(timespec="seconds")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _sample_like(value: object) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in ["sample", "demo", "manual", "示例", "样例", "placeholder", "replace_"])


def _alipay_rows(settings: Settings) -> tuple[list[str], list[dict[str, object]]]:
    path = settings.imports_dir / "alipay_positions.csv"
    fieldnames, rows = _read_csv(path)
    todo_rows: list[dict[str, object]] = []
    for row in rows:
        sample = _sample_like(row.get("source_note"))
        todo_rows.append(
            {
                "asset_code": row.get("asset_code", ""),
                "asset_name": row.get("asset_name", ""),
                "platform": row.get("platform", "Alipay") or "Alipay",
                "current_amount": "" if sample else row.get("current_amount", ""),
                "current_weight": "" if sample else row.get("current_weight", ""),
                "cost_basis": "" if sample else row.get("cost_basis", ""),
                "unrealized_pnl": "" if sample else row.get("unrealized_pnl", ""),
                "as_of": "YYYY-MM-DD" if sample else row.get("as_of", ""),
                "source_note": "REPLACE_WITH_REAL_ALIPAY_EXPORT_OR_VERIFIED_CURRENT_HOLDINGS",
            }
        )
    return fieldnames, todo_rows


def _fund_rule_rows(settings: Settings) -> tuple[list[str], list[dict[str, object]]]:
    path = settings.manual_dir / "fund_rules.csv"
    fieldnames, rows = _read_csv(path)
    todo_rows: list[dict[str, object]] = []
    for row in rows:
        source_is_weak = _sample_like(row.get("source_name")) or str(row.get("url_or_path", "")).startswith("data/")
        next_row = dict(row)
        for field in [
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
        ]:
            if not str(next_row.get(field, "")).strip():
                next_row[field] = f"REPLACE_{field.upper()}"
        if source_is_weak:
            next_row["source_name"] = "REPLACE_ALIPAY_OR_FUND_COMPANY_OFFICIAL_RULE_PAGE"
            next_row["source_type"] = "alipay_or_official"
            next_row["source_priority"] = "2"
            next_row["url_or_path"] = "REPLACE_URL_OR_LOCAL_EVIDENCE_PATH"
            next_row["evidence_level"] = "Strong"
            next_row["fallback_aggregated"] = "false"
        next_row["as_of"] = "YYYY-MM-DD" if _sample_like(next_row.get("as_of")) else next_row.get("as_of", "YYYY-MM-DD")
        todo_rows.append(next_row)
    return fieldnames, todo_rows


def _candidate_rows(settings: Settings) -> tuple[list[str], list[dict[str, object]]]:
    path = settings.manual_dir / "candidates.csv"
    fieldnames, rows = _read_csv(path)
    todo_rows: list[dict[str, object]] = []
    for row in rows:
        if str(row.get("is_excluded", "")).lower() in {"true", "1", "yes"}:
            continue
        source_is_weak = _sample_like(row.get("source_name")) or str(row.get("source_url", "")).startswith("data/")
        next_row = dict(row)
        if source_is_weak:
            next_row["official_source_count"] = "2"
            next_row["fallback_aggregated"] = "false"
            next_row["evidence_level"] = "Strong"
            next_row["source_name"] = "REPLACE_MOOMOO_ALIPAY_FUND_COMPANY_OR_OFFICIAL_SOURCE"
            next_row["source_type"] = "alipay_or_official"
            next_row["source_url"] = "REPLACE_URL_OR_LOCAL_EVIDENCE_PATH"
        next_row["missing_nav_days"] = "0"
        next_row["missing_holding_days"] = "0"
        next_row["conflict_flag"] = "false"
        next_row["as_of"] = "YYYY-MM-DD"
        todo_rows.append(next_row)
    return fieldnames, todo_rows


def _write_gap_actions(settings: Settings, path: Path, gaps: list[dict[str, object]]) -> None:
    fieldnames = ["area", "severity", "row_id", "field", "message", "action", "path"]
    rows = []
    for gap in gaps:
        item = dict(gap)
        item["path"] = display_path(settings.root_dir, item.get("path"))
        rows.append(item)
    _write_csv(path, fieldnames, rows)


def _write_discovered_files(settings: Settings, path: Path, candidate_files: list[dict[str, object]]) -> None:
    fieldnames = ["path", "name", "suffix"]
    rows = [
        {"path": display_path(settings.root_dir, row.get("path")), "name": row.get("name", ""), "suffix": row.get("suffix", "")}
        for row in candidate_files
    ]
    _write_csv(path, fieldnames, rows)


def _review_matrix_rows(settings: Settings) -> list[dict[str, str]]:
    path = settings.root_dir / "outputs" / "preflight" / "alipay_holdings_review_matrix.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_review_prefill(settings: Settings, path: Path, review_rows: list[dict[str, str]]) -> None:
    fieldnames = [
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
    rows: list[dict[str, object]] = []
    for row in review_rows:
        rows.append(
            {
                "asset_code": row.get("asset_code", ""),
                "asset_name": row.get("asset_name", ""),
                "platform": "Alipay",
                "current_amount": row.get("current_amount", ""),
                "current_weight": row.get("current_weight", ""),
                "cost_basis": "",
                "unrealized_pnl": row.get("unrealized_pnl", ""),
                "as_of": row.get("as_of", ""),
                "source_note": (
                    "REPLACE_WITH_CURRENT_ALIPAY_PAGE_CONFIRMATION; "
                    f"prior_review_action={row.get('review_action', '')}; "
                    f"prior_source_file={display_path(settings.root_dir, row.get('source_file'))}"
                ),
            }
        )
    _write_csv(path, fieldnames, rows)


def _write_special_rule_checklist(settings: Settings, path: Path, review_rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "asset_code",
        "asset_name",
        "special_reason",
        "required_confirmations",
        "preferred_source",
        "prior_as_of",
        "prior_source_file",
    ]
    rows: list[dict[str, object]] = []
    for row in review_rows:
        if str(row.get("special_fund_rule_check_required", "")).strip() not in {"1", "true", "True"}:
            continue
        rows.append(
            {
                "asset_code": row.get("asset_code", ""),
                "asset_name": row.get("asset_name", ""),
                "special_reason": "QDII/global/HK/special fund timing may differ from default 15:00/T+1 rule",
                "required_confirmations": (
                    "Alipay current holding page; subscription_status; redemption_status; cutoff_time; "
                    "confirm_lag; redeem_lag; subscription_fee; redemption_fee; subscription_fee_schedule; redemption_fee_schedule; "
                    "alipay_trade_status; moomoo_trade_status; platform_trade_note; special holiday calendar"
                ),
                "preferred_source": "Alipay fund detail/rule page or fund-company official announcement/prospectus",
                "prior_as_of": row.get("as_of", ""),
                "prior_source_file": display_path(settings.root_dir, row.get("source_file")),
            }
        )
    _write_csv(path, fieldnames, rows)


FUND_COMPANY_HINTS = (
    "前海开源",
    "华泰柏瑞",
    "易方达",
    "华夏",
    "南方",
    "博时",
    "摩根",
    "中金",
    "华安",
    "富国",
    "天弘",
    "广发",
    "国泰",
    "诺安",
)


def _fund_company_hint(asset_name: str) -> str:
    for company in FUND_COMPANY_HINTS:
        if asset_name.startswith(company):
            return company
    return "REPLACE_WITH_FUND_COMPANY_FROM_ALIPAY_OR_OFFICIAL_PAGE"


def _market_theme_hint(asset_name: str) -> tuple[str, str]:
    checks = [
        (("纳斯达克",), "US/QDII", "US technology growth"),
        (("标普500", "标普 500"), "US/QDII", "US broad equity"),
        (("全球", "QDII"), "Global/QDII", "global equity growth"),
        (("恒生",), "HK/QDII", "Hong Kong technology/equity"),
        (("沪港深", "AH"), "CN/HK", "China-Hong Kong equity"),
        (("半导体", "芯片"), "CN", "semiconductor"),
        (("人工智能",), "CN", "AI"),
        (("机器人",), "CN", "robotics"),
        (("科创",), "CN", "STAR/technology"),
        (("农业",), "CN", "agriculture theme"),
        (("石油化工",), "CN", "energy/chemical"),
        (("黄金",), "CN", "gold commodity"),
        (("银行",), "CN", "banking sector"),
        (("红利", "低波", "自由现金流"), "CN", "dividend/quality/low-volatility"),
        (("量化", "多因子"), "CN", "quant equity"),
    ]
    for keywords, market, theme in checks:
        if any(keyword in asset_name for keyword in keywords):
            return market, theme
    return "REPLACE_WITH_MARKET_SCOPE", "REPLACE_WITH_THEME_CLASSIFICATION"


def _filter_review_hint(asset_name: str) -> str:
    if any(keyword in asset_name for keyword in ["债", "货币", "余额宝", "现金"]):
        return "force_exclude_conservative_asset"
    if any(keyword in asset_name for keyword in ["黄金", "银行", "红利", "低波", "自由现金流"]):
        return "manual_review_for_aggressive_growth_fit"
    return "growth_candidate_review_required"


def _write_fund_rule_review_checklist(settings: Settings, path: Path, review_rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "temporary_asset_code",
        "asset_name",
        "production_asset_code_to_confirm",
        "fund_company_hint",
        "special_rule_required",
        "required_rule_fields",
        "source_priority",
        "preferred_sources",
        "default_rule_assumption",
        "alipay_query",
        "official_query",
        "source_evidence_to_attach",
        "prior_as_of",
        "prior_source_file",
    ]
    required_rule_fields = (
        "subscription_status; redemption_status; cutoff_time; confirm_lag; redeem_lag; "
        "subscription_fee; redemption_fee; subscription_fee_schedule; redemption_fee_schedule; management_fee; custody_fee; sales_service_fee; "
        "min_purchase_amount; alipay_trade_status; moomoo_trade_status; platform_trade_note; source_url; as_of"
    )
    rows: list[dict[str, object]] = []
    for row in review_rows:
        asset_name = row.get("asset_name", "").strip()
        if not asset_name:
            continue
        special_required = str(row.get("special_fund_rule_check_required", "")).strip() in {"1", "true", "True"}
        rows.append(
            {
                "temporary_asset_code": row.get("asset_code", ""),
                "asset_name": asset_name,
                "production_asset_code_to_confirm": "REPLACE_WITH_OFFICIAL_FUND_CODE_OR_PLATFORM_ID",
                "fund_company_hint": _fund_company_hint(asset_name),
                "special_rule_required": "true" if special_required else "false",
                "required_rule_fields": required_rule_fields,
                "source_priority": "moomoo > alipay > official_platform > trade_snapshot > public_aggregation",
                "preferred_sources": "Alipay fund rule/detail page; fund-company official page/prospectus/announcement",
                "default_rule_assumption": (
                    "Do not assume production rules from the generic 15:00/T+1 note; confirm the current product page. "
                    "QDII/HK/global/special funds may have different confirmation, redemption, and holiday calendars. "
                    "Platform tradability is advisory only and must not by itself exclude a Serenity candidate."
                ),
                "alipay_query": f"{asset_name} 支付宝 基金 申购 赎回 费率 交易规则",
                "official_query": f"{asset_name} 基金公司 申购赎回 费率 招募说明书",
                "source_evidence_to_attach": "REPLACE_WITH_ALIPAY_OR_FUND_COMPANY_RULE_EVIDENCE",
                "prior_as_of": row.get("as_of", ""),
                "prior_source_file": display_path(settings.root_dir, row.get("source_file")),
            }
        )
    _write_csv(path, fieldnames, rows)


def _write_candidate_source_review_prefill(settings: Settings, path: Path, review_rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "temporary_asset_code",
        "asset_name",
        "production_asset_code_to_confirm",
        "asset_type",
        "market_hint",
        "fund_company_hint",
        "risk_level_target",
        "theme_hint",
        "filter_review_hint",
        "is_off_platform_fund",
        "is_excluded_to_confirm",
        "official_source_count_required",
        "evidence_level_target",
        "source_1_required",
        "source_2_required",
        "moomoo_query",
        "alipay_query",
        "official_query",
        "missing_nav_days_required",
        "missing_holding_days_required",
        "conflict_flag_required",
        "as_of_to_confirm",
        "prior_as_of",
        "prior_source_file",
        "copy_target",
    ]
    rows: list[dict[str, object]] = []
    for row in review_rows:
        asset_name = row.get("asset_name", "").strip()
        if not asset_name:
            continue
        market_hint, theme_hint = _market_theme_hint(asset_name)
        filter_hint = _filter_review_hint(asset_name)
        rows.append(
            {
                "temporary_asset_code": row.get("asset_code", ""),
                "asset_name": asset_name,
                "production_asset_code_to_confirm": "REPLACE_WITH_OFFICIAL_FUND_CODE_OR_PLATFORM_ID",
                "asset_type": "off_platform_fund",
                "market_hint": market_hint,
                "fund_company_hint": _fund_company_hint(asset_name),
                "risk_level_target": "high_or_very_high_after_current_page_confirmation",
                "theme_hint": theme_hint,
                "filter_review_hint": filter_hint,
                "is_off_platform_fund": "true",
                "is_excluded_to_confirm": "true" if filter_hint == "force_exclude_conservative_asset" else "false",
                "official_source_count_required": ">=2",
                "evidence_level_target": "Strong",
                "source_1_required": "REPLACE_WITH_MOOMOO_OR_ALIPAY_CURRENT_SOURCE",
                "source_2_required": "REPLACE_WITH_FUND_COMPANY_OR_OFFICIAL_SOURCE",
                "moomoo_query": f"{asset_name} fund quote holdings nav",
                "alipay_query": f"{asset_name} 支付宝 基金 净值 持仓 费率",
                "official_query": f"{asset_name} 基金公司 定期报告 持仓 净值",
                "missing_nav_days_required": "<=2",
                "missing_holding_days_required": "<=2",
                "conflict_flag_required": "false",
                "as_of_to_confirm": "YYYY-MM-DD",
                "prior_as_of": row.get("as_of", ""),
                "prior_source_file": display_path(settings.root_dir, row.get("source_file")),
                "copy_target": "After verification, map into 03_candidates_to_fill.csv; do not copy this helper directly.",
            }
        )
    _write_csv(path, fieldnames, rows)


def _write_readme(
    path: Path,
    *,
    generated_at: str,
    validation: dict[str, object],
    files: dict[str, str],
) -> None:
    gaps = list(validation.get("gaps", []))
    by_area = Counter(str(gap.get("area", "")) for gap in gaps)
    blockers_by_area: dict[str, list[dict[str, object]]] = defaultdict(list)
    for gap in gaps:
        if gap.get("severity") == "block":
            blockers_by_area[str(gap.get("area", ""))].append(gap)
    lines = [
        "# Serenity Production Intake Pack",
        "",
        f"Generated: {generated_at}",
        "",
        "## Status",
        "",
        f"- Production ready: {validation.get('production_ready')}",
        f"- Block gaps: {validation.get('block_count')}",
        f"- Warn gaps: {validation.get('warn_count')}",
        f"- Gap areas: {dict(by_area)}",
        "",
        "## Files To Fill",
        "",
    ]
    for label, file_path in files.items():
        lines.append(f"- `{label}`: `{display_path(path.parents[2], file_path)}`")
    lines.extend(
        [
            "",
            "## Review-Matrix Assisted Files",
            "",
            "- `review_prefill`: optional stale/manual-review Alipay candidate rows generated from the local holdings review matrix.",
            "- `special_rule_checklist`: QDII/global/HK/special fund rows that must be checked against Alipay/fund-company rules before production.",
            "- `fund_rule_review_checklist`: per-holding rule fields and source queries for filling `02_fund_rules_to_fill.csv`.",
            "- `candidate_source_review_prefill`: per-holding source-chain queries for filling `03_candidates_to_fill.csv`.",
            "- These helper files are not copied by `promote-intake-pack`; they are only aids for filling `01/02/03` after current-page confirmation.",
        ]
    )
    lines.extend(
        [
            "",
            "## Required Fixes",
            "",
        ]
    )
    if blockers_by_area:
        for area, area_gaps in blockers_by_area.items():
            lines.append(f"### {area}")
            for gap in area_gaps[:12]:
                lines.append(
                    f"- `{gap.get('row_id')}` / `{gap.get('field')}`: {gap.get('message')} "
                    f"-> {gap.get('action')}"
                )
            if len(area_gaps) > 12:
                lines.append(f"- ... {len(area_gaps) - 12} more gaps in `gap_actions.csv`")
            lines.append("")
    else:
        lines.append("- No blockers.")
    lines.extend(
        [
            "## Acceptance Commands",
            "",
            "```bash",
            "python -m app.cli promote-intake-pack --json",
            "python -m app.cli promote-intake-pack --apply --json",
            "python -m app.cli import-alipay --csv data/imports/alipay_positions.csv",
            "python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --json",
            "python -m app.cli preflight --require-production --json",
            "```",
            "",
            "Do not run `--apply` until every `REPLACE_...` and `YYYY-MM-DD` marker is replaced. The promotion command blocks placeholders and backs up existing production files before copying.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_field_guide(path: Path) -> None:
    lines = [
        "# Production Intake Field Guide",
        "",
        "## Alipay Positions",
        "",
        "- `asset_code`: same code used in candidates and fund rules.",
        "- `current_amount`: current holding market value from Alipay/fund platform.",
        "- `current_weight`: portfolio weight as decimal or percent.",
        "- `as_of`: source snapshot date, `YYYY-MM-DD`, no more than 2 days stale for production.",
        "- `source_note`: must name real evidence and include a verifiable reference, for example `Alipay export 2026-06-12; evidence=/absolute/path/to/export.csv`; sample/demo/manual placeholder is blocked.",
        "",
        "## Fund Rules",
        "",
        "- Use Alipay fund detail/rule page or fund company official page.",
        "- Required execution fields: subscription/redemption status, cutoff time, confirm/redeem lag, headline fees, amount-tier subscription schedule, holding-period redemption schedule, management/custody fees.",
        "- `source_type` should be `alipay`, `official`, or `moomoo`; aggregated fallback cannot unlock execution rules.",
        "- `source_priority` should be 1-3 for production.",
        "- `url_or_path` must be a valid http(s) URL or an existing local evidence file path, not the production CSV itself.",
        "",
        "## Candidate Universe",
        "",
        "- Exclude bond, money-market, Yu'e Bao, conservative structured, and cash-management products.",
        "- Non-excluded candidates need at least two official-grade sources for Action-Ready eligibility.",
        "- Aggregated fallback can support research view only; it cannot upgrade a candidate to Action-Ready.",
        "- `missing_nav_days` and `missing_holding_days` must be <= 2.",
        "- `source_url` must be a valid http(s) URL or an existing local evidence file path.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_evidence_guide(path: Path) -> None:
    lines = [
        "# Evidence Intake Guide",
        "",
        "Use this guide when attaching real Alipay screenshots/exports, fund-rule pages, or candidate-source files to the intake pack.",
        "",
        "## Recommended Local Layout",
        "",
        "Create this folder when you have evidence files to attach:",
        "",
        "```text",
        "outputs/intake_pack/evidence/",
        "```",
        "",
        "Suggested filenames:",
        "",
        "- `alipay_positions_YYYY-MM-DD.csv` or `alipay_positions_YYYY-MM-DD.png`",
        "- `fund_rules_<asset_code>_YYYY-MM-DD.pdf` or `.png`",
        "- `candidate_source_<asset_code>_YYYY-MM-DD.pdf` or `.png`",
        "",
        "## CSV Reference Rules",
        "",
        "Inside the intake pack, relative references are resolved from `outputs/intake_pack/`.",
        "",
        "- In `01_alipay_positions_to_fill.csv`, set `source_note` like `Alipay current holdings; evidence=evidence/alipay_positions_YYYY-MM-DD.csv`.",
        "- In `02_fund_rules_to_fill.csv`, set `url_or_path` to `evidence/fund_rules_<asset_code>_YYYY-MM-DD.pdf` or a current http(s) URL.",
        "- In `03_candidates_to_fill.csv`, set `source_url` to `evidence/candidate_source_<asset_code>_YYYY-MM-DD.pdf` or a current http(s) URL.",
        "",
        "## Verification Commands",
        "",
        "```bash",
        "python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --json",
        "python -m app.cli promote-intake-pack --json",
        "python -m app.cli promote-intake-pack --apply --json",
        "python -m app.cli preflight --require-production --json",
        "```",
        "",
        "When `promote-intake-pack --apply` passes, files under `outputs/intake_pack/evidence/` are copied into the project-level `evidence/` directory so production CSV references like `evidence/...` remain verifiable after promotion.",
        "",
        "Do not attach private evidence files to a delivery ZIP unless you intentionally want that private evidence packaged.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_production_intake_pack(
    settings: Settings,
    *,
    scan_paths: list[Path] | None = None,
    write_output: bool = True,
) -> dict[str, object]:
    settings.ensure_dirs()
    validation = validate_intake(settings, scan_paths=scan_paths or [], write_output=True)
    output_dir = settings.root_dir / "outputs" / "intake_pack"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = _now(settings)

    alipay_fields, alipay_rows = _alipay_rows(settings)
    fund_fields, fund_rows = _fund_rule_rows(settings)
    candidate_fields, candidate_rows = _candidate_rows(settings)

    files = {
        "README": str(output_dir / "README_PRODUCTION_DATA_INTAKE.md"),
        "field_guide": str(output_dir / "FIELD_GUIDE.md"),
        "evidence_guide": str(output_dir / "EVIDENCE_INTAKE_GUIDE.md"),
        "alipay_positions_to_fill": str(output_dir / "01_alipay_positions_to_fill.csv"),
        "fund_rules_to_fill": str(output_dir / "02_fund_rules_to_fill.csv"),
        "candidates_to_fill": str(output_dir / "03_candidates_to_fill.csv"),
        "gap_actions": str(output_dir / "04_gap_actions.csv"),
        "discovered_files": str(output_dir / "05_discovered_candidate_files.csv"),
        "review_prefill": str(output_dir / "06_alipay_positions_review_prefill.csv"),
        "special_rule_checklist": str(output_dir / "07_special_fund_rule_checklist.csv"),
        "fund_rule_review_checklist": str(output_dir / "08_fund_rules_from_review_checklist.csv"),
        "candidate_source_review_prefill": str(output_dir / "09_candidate_source_review_prefill.csv"),
        "summary_json": str(output_dir / "production_intake_pack_latest.json"),
    }
    review_rows = _review_matrix_rows(settings)

    if write_output:
        _write_csv(Path(files["alipay_positions_to_fill"]), alipay_fields, alipay_rows)
        _write_csv(Path(files["fund_rules_to_fill"]), fund_fields, fund_rows)
        _write_csv(Path(files["candidates_to_fill"]), candidate_fields, candidate_rows)
        _write_gap_actions(settings, Path(files["gap_actions"]), list(validation.get("gaps", [])))
        _write_discovered_files(settings, Path(files["discovered_files"]), list(validation.get("candidate_files_found", [])))
        _write_review_prefill(settings, Path(files["review_prefill"]), review_rows)
        _write_special_rule_checklist(settings, Path(files["special_rule_checklist"]), review_rows)
        _write_fund_rule_review_checklist(settings, Path(files["fund_rule_review_checklist"]), review_rows)
        _write_candidate_source_review_prefill(settings, Path(files["candidate_source_review_prefill"]), review_rows)
        _write_field_guide(Path(files["field_guide"]))
        _write_evidence_guide(Path(files["evidence_guide"]))
        _write_readme(Path(files["README"]), generated_at=generated_at, validation=validation, files=files)

    result = IntakePackResult(
        generated_at=generated_at,
        output_dir=str(output_dir),
        production_ready=bool(validation["production_ready"]),
        block_count=int(validation["block_count"]),
        warn_count=int(validation["warn_count"]),
        files=files,
    )
    if write_output:
        Path(files["summary_json"]).write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return asdict(result)
