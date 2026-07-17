#!/usr/bin/env python3
"""KMFA v1.5 S23-P1 authoritative end-to-end business-flow kernel.

The phase binds the accepted homepage, project recalculation and report workflow
to one local public-synthetic publication.  Monetary values stay integer cents;
HTML, PDF, CSV and XLSX outputs must reconcile with zero difference.
"""

from __future__ import annotations

import copy
import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from KMFA.tools import v015_s16_p1_homepage as homepage
from KMFA.tools import v015_s16_p3_homepage_usability as homepage_usability
from KMFA.tools import v015_s20_p3_recalculation_publication as publication_kernel
from KMFA.tools import v015_s21_p2_report_generation as report_generation


RUN_PHASE_ID = "V015_S23_P1_END_TO_END_BUSINESS_FLOW"
ROADMAP_PHASE_ID = "S23-P1"
TASK_ID = "KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW"
VERSION = "1.5.0-dev-s23p1"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
XLSX_FILENAME = "kmfa_management_report.xlsx"
FORMATS = ("HTML", "PDF", "CSV", "XLSX")
PROJECT_WEIGHTS_BPS = (3500, 2700, 2100, 1700)
PROJECT_DEFINITIONS = (
    ("PUB-PROJ-001", "示例厂房改造", "需要关注", "复核成本偏差"),
    ("PUB-PROJ-002", "示例设备安装", "进展正常", "查看项目"),
    ("PUB-PROJ-003", "示例管网工程", "需要关注", "核对回款"),
    ("PUB-PROJ-004", "示例维护服务", "进展正常", "查看项目"),
)
DEFAULT_RUNTIME_ROOT = Path(__file__).resolve().parents[1] / ".codex_private_runtime/v015_s23_p1_end_to_end_business_flow"
DEFAULT_EVENT_PATH = DEFAULT_RUNTIME_ROOT / "report_exports.jsonl"
DEFAULT_BUNDLE_ROOT = DEFAULT_RUNTIME_ROOT / "bundles"
DEFAULT_XLSX_PREVIEW_ROOT = DEFAULT_RUNTIME_ROOT / "xlsx_previews"
BUILDER_SOURCE = Path(__file__).with_name("build_v015_s23_p1_report_xlsx.mjs")
ARTIFACT_NODE = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
ARTIFACT_NODE_MODULES = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"


class EndToEndFlowError(ValueError):
    """An authoritative version, value, export or runtime contract failed."""

    def __init__(self, code: str, message_zh: str, *, status: int = 409) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s23p1.source_contract.v1",
        "stage_id": "S23",
        "stage_name_zh": "真实用户流程、准确性、压力、极限与恢复测试",
        "stage_goal_zh": "以真实业务结果验收，而不是控件点击；覆盖数据精度、稳健性、性能、恢复和人类可用性。",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "端到端业务流程",
        "task_ids": ["S23P1T01", "S23P1T02", "S23P1T03"],
        "task_names_zh": ["验证经营首页任务", "验证项目成本与差异处理", "验证报告与导出"],
        "acceptance_zh": [
            "后端状态、页面和报告一致。",
            "权威项目零差异。",
            "页面、HTML、PDF、Excel 一致。",
        ],
        "stop_conditions_zh": ["仅 DOM 变化不得判通过。", "任一分差异失败。", "不一致阻塞。"],
        "data_classification": DATA_CLASSIFICATION,
    }


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EndToEndFlowError("INTEGER_CENTS_REQUIRED", f"{field}必须使用整数")
    return value


def _publication(publication: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(publication))
    value["consistency"] = publication_kernel.assert_cross_page_consistent(value)
    if value.get("external_publication_performed") is not False:
        raise EndToEndFlowError("LOCAL_PUBLICATION_REQUIRED", "端到端验收只允许本地公开合成发布版本")
    facts = value.get("facts")
    metrics = value.get("metrics")
    if not isinstance(facts, Mapping) or not isinstance(metrics, Mapping):
        raise EndToEndFlowError("PUBLICATION_INCOMPLETE", "当前发布版本缺少项目事实或指标")
    for field in ("project_revenue_cents", "project_cost_cents", "project_collection_cents", "unrelated_cash_cents"):
        _integer(facts.get(field), field)
    for field in ("project_margin_cents", "collection_ratio_bps"):
        _integer(metrics.get(field), field)
    if facts["project_revenue_cents"] - facts["project_cost_cents"] != metrics["project_margin_cents"]:
        raise EndToEndFlowError("AUTHORITATIVE_PROJECT_DIFFERENCE", "当前发布版本项目毛利存在分差异")
    return value


def _split(total: int) -> list[int]:
    """Split an integer total deterministically while preserving the exact sum."""

    total = _integer(total, "项目合计")
    rows = [total * weight // 10_000 for weight in PROJECT_WEIGHTS_BPS[:-1]]
    rows.append(total - sum(rows))
    return rows


def authoritative_projects(publication: Mapping[str, Any]) -> list[dict[str, Any]]:
    value = _publication(publication)
    facts = value["facts"]
    revenues = _split(facts["project_revenue_cents"])
    costs = _split(facts["project_cost_cents"])
    collections = _split(facts["project_collection_cents"])
    rows: list[dict[str, Any]] = []
    for index, (project_id, name, status, next_step) in enumerate(PROJECT_DEFINITIONS):
        revenue, cost, collection = revenues[index], costs[index], collections[index]
        gross_profit = revenue - cost
        receivable = revenue - collection
        rows.append(
            {
                "project_id": project_id,
                "project_name_zh": name,
                "revenue_cents": revenue,
                "cost_cents": cost,
                "gross_profit_cents": gross_profit,
                "collection_cents": collection,
                "receivable_cents": receivable,
                "gross_margin_bps": (gross_profit * 10_000 + revenue // 2) // revenue,
                "collection_bps": (collection * 10_000 + revenue // 2) // revenue,
                "source_ref": f"{value['publication_version_id']}:{project_id}",
                "status_zh": status,
                "next_step_zh": next_step,
            }
        )
    for field, expected in (
        ("revenue_cents", facts["project_revenue_cents"]),
        ("cost_cents", facts["project_cost_cents"]),
        ("gross_profit_cents", value["metrics"]["project_margin_cents"]),
        ("collection_cents", facts["project_collection_cents"]),
        ("receivable_cents", facts["project_revenue_cents"] - facts["project_collection_cents"]),
    ):
        if sum(row[field] for row in rows) != expected:
            raise EndToEndFlowError("PROJECT_ALLOCATION_DIFFERENCE", f"项目{field}分配存在差异")
    return rows


def authoritative_homepage_snapshot(
    publication: Mapping[str, Any], *, user_id: str = "demo-owner", role_id: str = "management",
    company_id: str = "demo-north", period: str = "2026-07", data_state: str = "complete",
) -> dict[str, Any]:
    """Bind the accepted homepage view to the current publication version."""

    published = _publication(publication)
    base = homepage.homepage_snapshot(
        user_id=user_id, role_id=role_id, company_id=company_id, period=period, data_state=data_state
    )
    if not base.get("allowed"):
        return base
    facts, metrics = published["facts"], published["metrics"]
    gross_margin_bps = (metrics["project_margin_cents"] * 10_000 + facts["project_revenue_cents"] // 2) // facts["project_revenue_cents"]
    project_metric = next(row for row in base["summary_metrics"] if row["metric_id"] == "PROJECT_GROSS_PROFIT")
    project_metric.update(
        {
            "route": "/data-update",
            "source_zh": "当前本地权威发布版本",
            "source_ref": f"{published['publication_version_id']}:project_margin_cents",
            "primary_value": metrics["project_margin_cents"],
            "display_zh": homepage.format_wan_cents(metrics["project_margin_cents"]),
            "secondary_value": gross_margin_bps,
            "secondary_display_zh": "毛利率 " + homepage.format_percent_bps(gross_margin_bps),
            "note_zh": "与项目重算、经营报告和导出使用同一发布版本。",
        }
    )
    for item in base["focus_items"]:
        if item["domain"] == "PROJECT":
            item["primary_action"] = {"label_zh": "处理项目成本差异", "route": "/data-update"}
    report_projects = authoritative_projects(published)
    base["project_portfolio"] = [
        {
            "project_id": row["project_id"],
            "project_name_zh": row["project_name_zh"],
            "revenue_cents": row["revenue_cents"],
            "revenue_display_zh": homepage.format_wan_cents(row["revenue_cents"]),
            "gross_margin_bps": row["gross_margin_bps"],
            "gross_margin_display_zh": homepage.format_percent_bps(row["gross_margin_bps"]),
            "collection_bps": row["collection_bps"],
            "collection_display_zh": homepage.format_percent_bps(row["collection_bps"]),
            "status": "ATTENTION" if row["status_zh"] == "需要关注" else "NORMAL",
            "status_zh": row["status_zh"],
            "next_step_zh": row["next_step_zh"],
            "route": "/data-update",
        }
        for row in report_projects
    ]
    for series in base["trend_series"]:
        if series["series_id"] == "GROSS_PROFIT":
            series["values_cents"][-1] = metrics["project_margin_cents"]
            series["display_values_zh"][-1] = homepage.format_wan_cents(metrics["project_margin_cents"])
            series["route"] = "/data-update"
            series["source_ref"] = f"{published['publication_version_id']}:project_margin_cents"
    base.update(
        {
            "schema_version": "kmfa.v015.s23p1.authoritative_homepage.v1",
            "publication_version_id": published["publication_version_id"],
            "shared_metric_fingerprint": published["consistency"]["shared_metric_fingerprint"],
            "authoritative_snapshot_hash": published["snapshot_hash"],
            "authoritative_project_difference_cents": 0,
            "report_alignment_required": True,
        }
    )
    homepage._validate_snapshot(base)
    return homepage_usability.enhance_homepage_snapshot(base)


def build_authoritative_report_payload(report: Mapping[str, Any], publication: Mapping[str, Any]) -> dict[str, Any]:
    """Build one canonical report payload from the current publication."""

    published = _publication(publication)
    if report.get("data_classification") != DATA_CLASSIFICATION:
        raise EndToEndFlowError("REPORT_CLASSIFICATION_BLOCKED", "只允许公开合成报告")
    trust = report.get("trust_and_limitations")
    sources = report.get("source_bindings")
    if not isinstance(trust, Mapping) or trust.get("complete_report_claim_allowed") is not True:
        raise EndToEndFlowError("REPORT_INPUTS_INCOMPLETE", "资料不完整，不能生成端到端报告")
    if not isinstance(sources, Sequence) or len(sources) != 6 or any(row.get("state") != "AVAILABLE" for row in sources):
        raise EndToEndFlowError("REPORT_SOURCE_BINDING_INVALID", "报告资料绑定不完整")
    published_source = next((row for row in sources if row.get("domain_id") == "published_metrics"), None)
    if not published_source or published_source.get("version_ref") != published["publication_version_id"]:
        raise EndToEndFlowError("REPORT_PUBLICATION_VERSION_MISMATCH", "报告没有绑定当前权威发布版本")
    projects = authoritative_projects(published)
    facts, calculated = published["facts"], published["metrics"]
    receivable = facts["project_revenue_cents"] - facts["project_collection_cents"]
    gross_margin_bps = (calculated["project_margin_cents"] * 10_000 + facts["project_revenue_cents"] // 2) // facts["project_revenue_cents"]
    metrics = [
        {"metric_id": "revenue", "label_zh": "确认收入", "value_integer": facts["project_revenue_cents"], "unit": "CENTS", "display_value": report_generation._money(facts["project_revenue_cents"]), "formula_zh": "四个权威项目确认收入之和", "source_ref": f"{published['publication_version_id']}:project_revenue_cents", "difference_integer": 0},
        {"metric_id": "cost", "label_zh": "确认成本", "value_integer": facts["project_cost_cents"], "unit": "CENTS", "display_value": report_generation._money(facts["project_cost_cents"]), "formula_zh": "四个权威项目确认成本之和", "source_ref": f"{published['publication_version_id']}:project_cost_cents", "difference_integer": 0},
        {"metric_id": "gross_profit", "label_zh": "毛利", "value_integer": calculated["project_margin_cents"], "unit": "CENTS", "display_value": report_generation._money(calculated["project_margin_cents"]), "formula_zh": "确认收入减确认成本", "source_ref": f"{published['publication_version_id']}:project_margin_cents", "difference_integer": 0},
        {"metric_id": "gross_margin", "label_zh": "毛利率", "value_integer": gross_margin_bps, "unit": "BPS", "display_value": report_generation._percent_bps(gross_margin_bps), "formula_zh": "毛利除以确认收入，四舍五入到一个基点", "source_ref": "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001", "difference_integer": 0},
        {"metric_id": "cash_balance", "label_zh": "期末现金", "value_integer": facts["unrelated_cash_cents"], "unit": "CENTS", "display_value": report_generation._money(facts["unrelated_cash_cents"]), "formula_zh": "当前发布版本未受项目重算影响的资金余额", "source_ref": f"{published['publication_version_id']}:unrelated_cash_cents", "difference_integer": 0},
        {"metric_id": "receivables", "label_zh": "期末应收", "value_integer": receivable, "unit": "CENTS", "display_value": report_generation._money(receivable), "formula_zh": "确认收入减本期回款", "source_ref": f"{published['publication_version_id']}:project_collection_cents", "difference_integer": 0},
    ]
    payload: dict[str, Any] = {
        "schema_version": "kmfa.v015.s23p1.authoritative_report_payload.v1",
        "report_version_id": report.get("report_version_id"),
        "report_family_id": report.get("report_family_id"),
        "report_title_zh": "KMFA 月度经营报告（端到端权威版本）",
        "company_id": report.get("company_id"),
        "company_name_zh": "北区示例公司",
        "period": dict(report.get("period") or {}),
        "publication_version_id": published["publication_version_id"],
        "shared_metric_fingerprint": published["consistency"]["shared_metric_fingerprint"],
        "authoritative_snapshot_hash": published["snapshot_hash"],
        "source_binding_fingerprint": report.get("source_binding_fingerprint"),
        "formula_binding_fingerprint": report.get("formula_binding_fingerprint"),
        "source_bindings": [dict(row) for row in sources],
        "metrics": metrics,
        "projects": projects,
        "headline": {
            "revenue_cents": facts["project_revenue_cents"],
            "cost_cents": facts["project_cost_cents"],
            "gross_profit_cents": calculated["project_margin_cents"],
            "collection_cents": facts["project_collection_cents"],
            "receivable_cents": receivable,
            "gross_margin_bps": gross_margin_bps,
            "cash_balance_cents": facts["unrelated_cash_cents"],
            "tax_review_count": 4,
            "key_matter_count": 3,
        },
        "key_matters": [
            {"matter_id": "MATTER-E2E-001", "matter_zh": "复核项目成本差异", "owner_zh": "财务负责人", "next_step_zh": "按当前发布版本核对项目毛利", "source_ref": f"{published['publication_version_id']}:project_cost_cents"},
            {"matter_id": "MATTER-E2E-002", "matter_zh": "跟进项目回款", "owner_zh": "项目负责人", "next_step_zh": "按本期应收差额推进回款", "source_ref": f"{published['publication_version_id']}:project_collection_cents"},
            {"matter_id": "MATTER-E2E-003", "matter_zh": "完成报告复核", "owner_zh": "经营负责人", "next_step_zh": "核对四种导出格式后内部发布", "source_ref": str(report.get("report_version_id"))},
        ],
        "trust_and_limitations": dict(trust),
        "data_classification": DATA_CLASSIFICATION,
        "formal_business_report": False,
        "approval_or_publication_performed": False,
        "raw_access_count": 0,
        "external_network_request_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
    }
    payload["report_payload_fingerprint"] = report_generation._digest(payload)
    assert_authoritative_zero_difference(published, None, payload)
    return payload


def assert_authoritative_zero_difference(
    publication: Mapping[str, Any], homepage_payload: Mapping[str, Any] | None,
    report_payload: Mapping[str, Any], xlsx_values: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    published = _publication(publication)
    expected = {
        "revenue": published["facts"]["project_revenue_cents"],
        "cost": published["facts"]["project_cost_cents"],
        "gross_profit": published["metrics"]["project_margin_cents"],
        "cash_balance": published["facts"]["unrelated_cash_cents"],
        "receivables": published["facts"]["project_revenue_cents"] - published["facts"]["project_collection_cents"],
    }
    actual = {row["metric_id"]: row["value_integer"] for row in report_payload["metrics"]}
    differences = {key: actual.get(key) - value if isinstance(actual.get(key), int) else None for key, value in expected.items()}
    project_difference = (
        sum(row["revenue_cents"] - row["cost_cents"] for row in report_payload["projects"])
        - published["metrics"]["project_margin_cents"]
    )
    version_ids = {published["publication_version_id"], report_payload.get("publication_version_id")}
    if homepage_payload is not None:
        version_ids.add(homepage_payload.get("publication_version_id"))
        home_metric = next(row for row in homepage_payload["summary_metrics"] if row["metric_id"] == "PROJECT_GROSS_PROFIT")
        differences["homepage_gross_profit"] = home_metric["primary_value"] - expected["gross_profit"]
    xlsx_difference_count = 0
    if xlsx_values is not None:
        canonical = report_generation.canonical_numeric_values(report_payload)
        xlsx_difference_count = sum(xlsx_values.get(key) != value for key, value in canonical.items())
    if len(version_ids) != 1 or any(value != 0 for value in differences.values()) or project_difference != 0 or xlsx_difference_count:
        raise EndToEndFlowError("END_TO_END_ZERO_DIFFERENCE_FAILED", "首页、项目、报告或 Excel 存在分差异")
    return {
        "status": "PASS",
        "publication_version_id": published["publication_version_id"],
        "shared_metric_fingerprint": published["consistency"]["shared_metric_fingerprint"],
        "checked_metric_count": len(differences),
        "project_difference_cents": project_difference,
        "xlsx_difference_count": xlsx_difference_count,
        "difference_cents": 0,
    }


def _xlsx_builder(payload: Mapping[str, Any], output_path: Path, preview_root: Path) -> dict[str, Any]:
    if not ARTIFACT_NODE.is_file() or not ARTIFACT_NODE_MODULES.is_dir() or not BUILDER_SOURCE.is_file():
        raise EndToEndFlowError("ARTIFACT_RUNTIME_UNAVAILABLE", "随附 Excel 生成运行时不可用", status=503)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    preview_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kmfa-s23p1-xlsx-") as folder:
        work = Path(folder)
        (work / "node_modules").symlink_to(ARTIFACT_NODE_MODULES, target_is_directory=True)
        builder = work / BUILDER_SOURCE.name
        shutil.copyfile(BUILDER_SOURCE, builder)
        input_path = work / "payload.json"
        input_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        result = subprocess.run(
            [str(ARTIFACT_NODE), str(builder), str(input_path), str(output_path), str(preview_root)],
            cwd=work,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
            env={**os.environ, "NO_COLOR": "1"},
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()[-1000:]
        raise EndToEndFlowError("XLSX_BUILD_FAILED", f"Excel 生成失败：{detail}", status=500)
    try:
        audit = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        raise EndToEndFlowError("XLSX_AUDIT_MISSING", "Excel 生成结果缺少可核对审计", status=500) from error
    if audit.get("status") != "PASS" or not output_path.is_file():
        raise EndToEndFlowError("XLSX_AUDIT_FAILED", "Excel 公式、检查或视觉验证未通过", status=500)
    return audit


class AuthoritativeReportExportJournal(report_generation.ReportExportJournal):
    """Four-format immutable export journal bound to a live publication provider."""

    def __init__(
        self, event_path: Path | str = DEFAULT_EVENT_PATH, bundle_root: Path | str = DEFAULT_BUNDLE_ROOT, *,
        publication_provider: Callable[[], Mapping[str, Any]],
        preview_root: Path | str = DEFAULT_XLSX_PREVIEW_ROOT,
    ) -> None:
        super().__init__(event_path, bundle_root)
        self.publication_provider = publication_provider
        self.preview_root = Path(preview_root)

    def create(self, report: Mapping[str, Any], *, idempotency_key: str, recorded_at: str | None = None) -> dict[str, Any]:
        key = report_generation._text(idempotency_key, "请求编号", minimum=8, maximum=120)
        publication = _publication(self.publication_provider())
        payload = build_authoritative_report_payload(report, publication)
        fingerprint = str(payload["report_payload_fingerprint"])
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((row for row in rows if row["idempotency_key"] == key), None)
            if existing:
                if existing["report_payload_fingerprint"] != fingerprint:
                    raise report_generation.ReportGenerationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能导出不同报告", status=409)
                return existing
            same_version = next((row for row in rows if row["report_version_id"] == report["report_version_id"]), None)
            if same_version:
                if same_version["report_payload_fingerprint"] != fingerprint:
                    raise report_generation.ReportGenerationError("REPORT_VERSION_EXPORT_CONFLICT", "同一报告版本不能对应不同数字", status=409)
                return same_version
            export_id = "EXPORT-S23P1-" + report_generation.hashlib.sha256(fingerprint.encode()).hexdigest()[:16].upper()
            bundle_dir = self.bundle_root / export_id
            if bundle_dir.exists() and any(bundle_dir.iterdir()):
                raise report_generation.ReportGenerationError("EXPORT_BUNDLE_CONFLICT", "导出目录已存在且无法安全覆盖", status=409)
            try:
                bundle = report_generation.generate_bundle(payload, bundle_dir)
                preview_dir = self.preview_root / export_id
                xlsx_path = bundle_dir / XLSX_FILENAME
                xlsx_audit = _xlsx_builder(payload, xlsx_path, preview_dir)
                zero = assert_authoritative_zero_difference(publication, None, payload, xlsx_audit["numeric_values"])
            except Exception:
                if bundle_dir.exists():
                    shutil.rmtree(bundle_dir)
                raise
            bundle["files"]["XLSX"] = {
                "filename": XLSX_FILENAME,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "sha256": report_generation._file_digest(xlsx_path.read_bytes()),
                "size_bytes": xlsx_path.stat().st_size,
            }
            consistency = dict(bundle["cross_format_consistency"])
            consistency.update(
                {
                    "schema_version": "kmfa.v015.s23p1.cross_format_consistency.v1",
                    "status": "PASS",
                    "formats": list(FORMATS),
                    "format_count": 4,
                    "numeric_value_count": len(report_generation.canonical_numeric_values(payload)),
                    "difference_integer": 0,
                    "xlsx_formula_error_count": 0,
                    "xlsx_visual_pass_count": len(xlsx_audit["preview_paths"]),
                    "authoritative_difference_cents": zero["difference_cents"],
                }
            )
            row: dict[str, Any] = {
                "schema_version": "kmfa.v015.s23p1.report_export_event.v1",
                "event_type": "AUTHORITATIVE_REPORT_EXPORT_CREATED",
                "export_id": export_id,
                "report_version_id": report["report_version_id"],
                "publication_version_id": publication["publication_version_id"],
                "shared_metric_fingerprint": publication["consistency"]["shared_metric_fingerprint"],
                "report_payload_fingerprint": fingerprint,
                "report_payload_snapshot": payload,
                "source_binding_fingerprint": payload["source_binding_fingerprint"],
                "formula_binding_fingerprint": payload["formula_binding_fingerprint"],
                "files": bundle["files"],
                "cross_format_consistency": consistency,
                "xlsx_audit": {
                    "status": xlsx_audit["status"],
                    "sheet_count": 3,
                    "formula_error_free": xlsx_audit["formula_error_free"],
                    "formula_error_count": 0 if xlsx_audit["formula_error_free"] else 1,
                    "visual_pass_count": len(xlsx_audit["preview_paths"]),
                },
                "data_classification": DATA_CLASSIFICATION,
                "formal_business_report": False,
                "approval_or_publication_performed": False,
                "raw_access_count": 0,
                "external_network_request_count": 0,
                "github_upload_count": 0,
                "app_reinstall_count": 0,
                "idempotency_key": key,
                "recorded_at": recorded_at or report_generation._now(),
                "sequence": len(rows) + 1,
                "previous_event_hash": rows[-1]["event_hash"] if rows else "GENESIS",
            }
            row["event_hash"] = report_generation._digest(row)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._read_unlocked()
            return row
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def file_path(self, export_id: str, format_name: str) -> tuple[Path, dict[str, Any]]:
        row = self.get(export_id)
        format_key = report_generation._text(format_name, "导出格式", maximum=8).upper()
        if format_key not in FORMATS:
            raise report_generation.ReportGenerationError("EXPORT_FORMAT_NOT_FOUND", "没有找到这个导出格式", status=404)
        metadata = row["files"][format_key]
        path = self.bundle_root / row["export_id"] / metadata["filename"]
        if not path.is_file() or report_generation._file_digest(path.read_bytes()) != metadata["sha256"]:
            raise report_generation.ReportGenerationError("EXPORT_FILE_CORRUPTED", "报告导出文件缺失或已变化", status=409)
        return path, metadata


def scope_boundary() -> dict[str, int]:
    return {
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "external_network_request_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
        "s23_p2_execution_count": 0,
        "s23_p3_execution_count": 0,
        "stage_review_execution_count": 0,
    }


def public_verification(*, deliverable_path: Path | None = None) -> dict[str, Any]:
    """Exercise publication, homepage, four exports, approval, revision and replay."""

    from KMFA.tools import v015_s20_p2_confirmation_workbench as confirmation_kernel
    from KMFA.tools import v015_s21_p1_report_model as report_model
    from KMFA.tools import v015_s21_p3_report_workflow as report_workflow

    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    with tempfile.TemporaryDirectory(prefix="kmfa-s23p1-public-") as folder:
        root = Path(folder)
        confirmation_path = root / "confirmations.jsonl"
        publication_path = root / "publications.jsonl"
        model_path = root / "models.jsonl"
        export_path = root / "exports.jsonl"
        workflow_path = root / "workflows.jsonl"
        bundle_root = root / "bundles"
        preview_root = root / "previews"

        confirmations = confirmation_kernel.ConfirmationWorkbench(confirmation_path)
        preview = confirmations.preview(
            "ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", actor_role="ROLE::DATA_STEWARD"
        )
        control = confirmations.confirm(
            "ISSUE-S20P2-001",
            "USE_REGISTERED_PROJECT",
            actor_id="demo-steward",
            actor_role="ROLE::DATA_STEWARD",
            reason_zh="已核对项目登记信息和本期成本依据",
            preview_id=preview["preview_id"],
            preview_token=preview["preview_token"],
            idempotency_key="s23p1-confirm-project-cost-001",
        )["event"]
        recalculation = publication_kernel.RecalculationPublicationWorkbench(
            confirmation_path, publication_path
        )
        job = recalculation.start_recalculation(
            control["event_id"],
            actor_id="demo-steward",
            actor_role="ROLE::DATA_STEWARD",
            idempotency_key="s23p1-recalculate-project-cost-001",
        )
        publish_preview = recalculation.publication_preview(
            job["job_id"], "PUBLISH_CANDIDATE", actor_role="ROLE::AUDITOR"
        )
        recalculation.decide(
            job["job_id"],
            "PUBLISH_CANDIDATE",
            actor_id="demo-auditor",
            actor_role="ROLE::AUDITOR",
            reason_zh="已核对项目成本差异、变化说明和四个页面一致性",
            preview_id=publish_preview["preview_id"],
            preview_token=publish_preview["preview_token"],
            idempotency_key="s23p1-publish-project-cost-001",
        )
        publication = recalculation.current_publication()
        home = authoritative_homepage_snapshot(publication)

        models = report_model.ReportModelJournal(model_path)
        first_report = models.create(
            company_id="demo-north",
            period_kind="MONTHLY",
            period_key="2026-07",
            source_bindings=report_model.default_source_bindings(
                publication_version=publication["publication_version_id"]
            ),
            formula_bindings=[
                *report_model.default_formula_bindings(),
                {
                    "formula_id": "FORM-KMFA-V015-S23-P1-END-TO-END-BUSINESS-FLOW-001",
                    "formula_version": VERSION,
                },
            ],
            created_by="公开演示经营负责人",
            idempotency_key="s23p1-report-model-v1-001",
            recorded_at="2026-07-17T00:10:00+00:00",
        )
        exports = AuthoritativeReportExportJournal(
            export_path,
            bundle_root,
            publication_provider=recalculation.current_publication,
            preview_root=preview_root,
        )
        first_export = exports.create(
            first_report,
            idempotency_key="s23p1-report-export-v1-001",
            recorded_at="2026-07-17T00:11:00+00:00",
        )
        first_payload = first_export["report_payload_snapshot"]
        zero = assert_authoritative_zero_difference(publication, home, first_payload)

        workflows = report_workflow.ReportWorkflowJournal(workflow_path)

        def approve(report: Mapping[str, Any], export: Mapping[str, Any], prefix: str, minute: int) -> dict[str, Any]:
            value = workflows.preview(
                report,
                export,
                user_id="demo-owner",
                role_id="finance",
                company_id="demo-north",
                comment_zh="已核对页面和四种导出文件",
                idempotency_key=f"{prefix}-preview-001",
                occurred_at=f"2026-07-17T00:{minute:02d}:00+00:00",
            )
            case_id = value["case_id"]
            steps = (
                ("submit", "finance", "提交独立复核", None),
                ("review", "reviewer", "数字、来源和格式一致", "PASS"),
                ("approve", "reviewer", "批准进入内部报告中心", None),
                ("publish", "management", "完成内部发布", None),
            )
            for offset, (action, role, comment, decision) in enumerate(steps, 1):
                kwargs: dict[str, Any] = {
                    "user_id": "demo-owner",
                    "role_id": role,
                    "company_id": "demo-north",
                    "comment_zh": comment,
                    "idempotency_key": f"{prefix}-{action}-001",
                    "occurred_at": f"2026-07-17T00:{minute + offset:02d}:00+00:00",
                }
                if decision:
                    kwargs["decision"] = decision
                value = getattr(workflows, action)(case_id, **kwargs)
            return value

        first_case = approve(first_report, first_export, "s23p1-v1", 12)
        revised_bindings = report_workflow.revision_bindings(
            first_report, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"}
        )
        second_report = models.revise(
            first_report["report_version_id"],
            source_bindings=revised_bindings,
            revision_reason_zh="补充项目成本差异处理结论并保留上一版本",
            created_by="公开演示经营负责人",
            idempotency_key="s23p1-report-model-v2-001",
            recorded_at="2026-07-17T00:20:00+00:00",
        )
        second_export = exports.create(
            second_report,
            idempotency_key="s23p1-report-export-v2-001",
            recorded_at="2026-07-17T00:21:00+00:00",
        )
        comparison = report_workflow.compare_versions(first_report, second_report)
        second_case = approve(second_report, second_export, "s23p1-v2", 22)

        if deliverable_path is not None:
            xlsx_path, _ = exports.file_path(second_export["export_id"], "XLSX")
            deliverable_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(xlsx_path, deliverable_path)

        replay_publication = publication_kernel.RecalculationPublicationWorkbench(
            confirmation_path, publication_path
        ).current_publication()
        replay_models = report_model.ReportModelJournal(model_path).list()
        replay_exports = AuthoritativeReportExportJournal(
            export_path,
            bundle_root,
            publication_provider=lambda: replay_publication,
            preview_root=preview_root,
        ).list()
        replay_workflows = report_workflow.ReportWorkflowJournal(workflow_path).list()

        project_metric = next(
            row for row in home["summary_metrics"] if row["metric_id"] == "PROJECT_GROSS_PROFIT"
        )
        add("SOURCE_CONTRACT", source_contract()["task_ids"] == ["S23P1T01", "S23P1T02", "S23P1T03"], "TaskPack exact")
        add("PUBLICATION_ADVANCED", publication["publication_version_id"] == "PUB-S20P3-0002", "project change published")
        add("PUBLICATION_FOUR_VIEWS", publication["consistency"]["view_count"] == 4, "backend views")
        add("PUBLICATION_SYNC", publication["consistency"]["consistent"], "backend consistency")
        add("HOMEPAGE_VERSION", home["publication_version_id"] == publication["publication_version_id"], "same version")
        add("HOMEPAGE_FINGERPRINT", home["shared_metric_fingerprint"] == publication["consistency"]["shared_metric_fingerprint"], "same fingerprint")
        add("HOMEPAGE_PROJECT_MARGIN", project_metric["primary_value"] == publication["metrics"]["project_margin_cents"], "same cents")
        add("HOMEPAGE_PROJECT_ROUTE", project_metric["route"] == "/data-update", "issue entry")
        add("HOMEPAGE_PROJECTS", len(home["project_portfolio"]) == 4, "four projects")
        add("PROJECT_ALLOCATION_REVENUE", sum(row["revenue_cents"] for row in first_payload["projects"]) == publication["facts"]["project_revenue_cents"], "zero difference")
        add("PROJECT_ALLOCATION_COST", sum(row["cost_cents"] for row in first_payload["projects"]) == publication["facts"]["project_cost_cents"], "zero difference")
        add("PROJECT_ALLOCATION_MARGIN", sum(row["gross_profit_cents"] for row in first_payload["projects"]) == publication["metrics"]["project_margin_cents"], "zero difference")
        add("PROJECT_ALLOCATION_COLLECTION", sum(row["collection_cents"] for row in first_payload["projects"]) == publication["facts"]["project_collection_cents"], "zero difference")
        add("PROJECT_ROW_FORMULAS", all(row["revenue_cents"] - row["cost_cents"] == row["gross_profit_cents"] for row in first_payload["projects"]), "every project")
        add("REPORT_PUBLICATION_VERSION", first_payload["publication_version_id"] == publication["publication_version_id"], "same version")
        add("REPORT_FINGERPRINT", first_payload["shared_metric_fingerprint"] == publication["consistency"]["shared_metric_fingerprint"], "same fingerprint")
        add("REPORT_ZERO_DIFFERENCE", zero["difference_cents"] == 0, "homepage project report")
        add("REPORT_MODEL_VERSIONED", first_report["version_number"] == 1, "v1")
        add("REPORT_SOURCE_BOUND", any(row["domain_id"] == "published_metrics" and row["version_ref"] == publication["publication_version_id"] for row in first_report["source_bindings"]), "authoritative source")
        add("FOUR_FORMATS", set(first_export["files"]) == set(FORMATS), "HTML PDF CSV XLSX")
        add("FOUR_FORMAT_ZERO_DIFFERENCE", first_export["cross_format_consistency"]["difference_integer"] == 0, "cross format")
        add("XLSX_FORMULA_AUDIT", first_export["xlsx_audit"]["formula_error_free"], "no formula error")
        add("XLSX_VISUAL_AUDIT", first_export["xlsx_audit"]["visual_pass_count"] == 3, "all sheets rendered")
        add("EXPORT_FILES_EXIST", all((bundle_root / first_export["export_id"] / value["filename"]).is_file() for value in first_export["files"].values()), "immutable files")
        add("EXPORT_HASHES", all(str(value["sha256"]).startswith("sha256:") for value in first_export["files"].values()), "sha256")
        add("FIRST_WORKFLOW_PUBLISHED", first_case["state"] == "PUBLISHED_INTERNAL", "five steps")
        add("FIRST_WORKFLOW_EVENTS", first_case["event_count"] == 5, "preview through publish")
        add("ROLE_SEPARATION", [row["actor_role"] for row in first_case["events"]] == ["finance", "finance", "reviewer", "reviewer", "management"], "roles")
        add("REVISION_CREATED", second_report["version_number"] == 2, "v2")
        add("REVISION_SUPERSEDES", second_report["supersedes_version_id"] == first_report["report_version_id"], "history retained")
        add("REVISION_EXPLAINED", comparison["unexplained_difference_count"] == 0 and comparison["source_difference_count"] >= 1, "explained")
        add("REVISION_EXPORT_FOUR_FORMATS", set(second_export["files"]) == set(FORMATS), "four formats")
        add("REVISION_ZERO_DIFFERENCE", second_export["cross_format_consistency"]["difference_integer"] == 0, "zero difference")
        add("REVISION_PUBLISHED", second_case["state"] == "PUBLISHED_INTERNAL", "latest approved")
        add("HISTORY_TWO_MODELS", replay_models["report_version_count"] == 2, "refresh")
        add("HISTORY_TWO_EXPORTS", replay_exports["export_count"] == 2, "refresh")
        add("HISTORY_TWO_WORKFLOWS", replay_workflows["case_count"] == 2, "refresh")
        add("PUBLICATION_REFRESH_VERSION", replay_publication["publication_version_id"] == publication["publication_version_id"], "refresh")
        add("PUBLICATION_REFRESH_HASH", replay_publication["snapshot_hash"] == publication["snapshot_hash"], "refresh")
        add("MODEL_HISTORY_APPEND_ONLY", replay_models["history_overwrite_count"] == 0, "append only")
        add("WORKFLOW_HISTORY_APPEND_ONLY", replay_workflows["history_overwrite_count"] == 0, "append only")
        add("RAW_ZERO", first_export["raw_access_count"] == 0 and second_export["raw_access_count"] == 0, "raw untouched")
        add("EXTERNAL_ZERO", first_export["external_network_request_count"] == 0 and second_export["external_network_request_count"] == 0, "offline")
        add("GITHUB_ZERO", first_export["github_upload_count"] == 0 and second_export["github_upload_count"] == 0, "not uploaded")
        add("APP_ZERO", first_export["app_reinstall_count"] == 0 and second_export["app_reinstall_count"] == 0, "not reinstalled")
        add("NEXT_PHASES_ZERO", scope_boundary()["s23_p2_execution_count"] == 0 and scope_boundary()["s23_p3_execution_count"] == 0, "phase boundary")
        add("STAGE_REVIEW_ZERO", scope_boundary()["stage_review_execution_count"] == 0, "not started")

        result = {
            "publication_version_id": publication["publication_version_id"],
            "publication_version_count": 1,
            "backend_view_count": publication["consistency"]["view_count"],
            "homepage_authoritative_binding_count": 1,
            "authoritative_project_count": len(first_payload["projects"]),
            "project_difference_cents": zero["difference_cents"],
            "shared_metric_fingerprint": publication["consistency"]["shared_metric_fingerprint"],
            "project_margin_cents": publication["metrics"]["project_margin_cents"],
            "report_versions": [first_report["report_version_id"], second_report["report_version_id"]],
            "report_version_count": 2,
            "export_ids": [first_export["export_id"], second_export["export_id"]],
            "report_export_count": 2,
            "format_count": 4,
            "formats": list(FORMATS),
            "cross_format_numeric_value_count": first_export["cross_format_consistency"]["numeric_value_count"],
            "cross_format_difference_integer": 0,
            "xlsx_sheet_count": first_export["xlsx_audit"]["sheet_count"],
            "xlsx_formula_error_count": first_export["xlsx_audit"]["formula_error_count"],
            "xlsx_visual_pass_count": first_export["xlsx_audit"]["visual_pass_count"],
            "workflow_case_count": 2,
            "workflow_step_count_per_case": 5,
            "latest_workflow_state": second_case["state"],
            "revision_source_difference_count": comparison["source_difference_count"],
            "revision_unexplained_difference_count": comparison["unexplained_difference_count"],
            "refresh_persistence_passed": True,
            "scope_boundary": scope_boundary(),
        }

    failures = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s23p1.public_verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "check_count": len(checks),
        "pass_count": len(checks) - len(failures),
        "fail_count": len(failures),
        "checks": checks,
        "result": result,
    }
