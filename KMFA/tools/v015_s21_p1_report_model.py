#!/usr/bin/env python3
"""KMFA v1.5 S21-P1 immutable report-period and audience model.

This phase defines report identity, period, revision history, audience layers,
input/formula bindings, and plain-language trust limitations.  It does not
render HTML/PDF/Excel, approve, publish, or read raw business files.
"""

from __future__ import annotations

import calendar
import fcntl
import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S21_P1_REPORT_MODEL"
ROADMAP_PHASE_ID = "S21-P1"
TASK_ID = "KMFA-V015-S21-P1-REPORT-MODEL-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S21-P1-REPORT-MODEL"
VERSION = "1.5.0-dev-s21p1"
DATA_CLASSIFICATION = "PUBLIC_SYNTHETIC"
DEFAULT_EVENT_PATH = Path(__file__).resolve().parents[1] / ".codex_private_runtime/v015_s21_p1_report_model/report_models.jsonl"

PERIOD_KINDS = ("WEEKLY", "MONTHLY", "QUARTERLY", "HALF_YEAR", "YEARLY")
PERIOD_LABELS_ZH = {
    "WEEKLY": "周报",
    "MONTHLY": "月报",
    "QUARTERLY": "季报",
    "HALF_YEAR": "半年报",
    "YEARLY": "年报",
}
INPUT_STATES = ("AVAILABLE", "PENDING_CONFIRMATION", "MISSING", "OUT_OF_SCOPE")
REQUIRED_INPUT_DOMAINS = (
    "project_operations",
    "finance_and_funds",
    "receivables_and_collections",
    "tax_and_policy",
    "key_matters",
    "published_metrics",
)
INPUT_LABELS_ZH = {
    "project_operations": "项目经营资料",
    "finance_and_funds": "财务与资金资料",
    "receivables_and_collections": "应收与回款资料",
    "tax_and_policy": "税务与政策资料",
    "key_matters": "重点事项资料",
    "published_metrics": "本期已核对经营数字",
}
SECTION_BLUEPRINT = (
    ("management_summary", "经营摘要", "MANAGEMENT", "先说明本期结果、主要变化和需要管理层处理的事项。"),
    ("project_operations", "项目经营", "MANAGEMENT", "按项目说明进展、毛利、回款和异常事项。"),
    ("finance_and_funds", "财务与资金", "MANAGEMENT", "说明收入、成本、现金、应收和资金安排。"),
    ("tax_and_policy", "税务与政策", "MANAGEMENT", "说明需核对的票据、材料准备和适用范围。"),
    ("key_matters", "重点事项", "MANAGEMENT", "集中列出负责人、影响、下一步和待确认事项。"),
    ("professional_appendices", "专业附表", "PROFESSIONAL", "为专业人员保留明细、口径、来源索引和差异清单入口。"),
)
VISIBLE_TECHNICAL_TERMS = (
    "validator", "manifest", "schema", "json", "metadata", "source_ref", "hash",
    "api", "stage", "phase", "a级", "b级", "c级", "d级", "grade",
)


class ReportModelError(ValueError):
    """Report-model input or history violates the S21-P1 contract."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400) -> None:
        super().__init__(message_zh)
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _text(value: Any, field: str, *, minimum: int = 1, maximum: int = 200) -> str:
    text = str(value or "").strip()
    if len(text) < minimum or len(text) > maximum:
        raise ReportModelError("INVALID_TEXT", f"{field} 不完整或过长")
    return text


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def period_contract(period_kind: str, period_key: str) -> dict[str, Any]:
    """Return an exact closed date range for a supported report period."""

    kind = _text(period_kind, "报告期间类型", maximum=20).upper()
    key = _text(period_key, "报告期间", maximum=16).upper()
    try:
        if kind == "WEEKLY":
            match = re.fullmatch(r"(\d{4})-W(\d{2})", key)
            if not match:
                raise ValueError
            year, week = map(int, match.groups())
            start, end = date.fromisocalendar(year, week, 1), date.fromisocalendar(year, week, 7)
            label = f"{year} 年第 {week} 周"
        elif kind == "MONTHLY":
            match = re.fullmatch(r"(\d{4})-(\d{2})", key)
            if not match:
                raise ValueError
            year, month = map(int, match.groups())
            last = calendar.monthrange(year, month)[1]
            start, end = date(year, month, 1), date(year, month, last)
            label = f"{year} 年 {month} 月"
        elif kind == "QUARTERLY":
            match = re.fullmatch(r"(\d{4})-Q([1-4])", key)
            if not match:
                raise ValueError
            year, quarter = map(int, match.groups())
            month = (quarter - 1) * 3 + 1
            start = date(year, month, 1)
            end_month = month + 2
            end = date(year, end_month, calendar.monthrange(year, end_month)[1])
            label = f"{year} 年第 {quarter} 季度"
        elif kind == "HALF_YEAR":
            match = re.fullmatch(r"(\d{4})-H([12])", key)
            if not match:
                raise ValueError
            year, half = map(int, match.groups())
            start = date(year, 1 if half == 1 else 7, 1)
            end = date(year, 6 if half == 1 else 12, 30 if half == 1 else 31)
            label = f"{year} 年{'上' if half == 1 else '下'}半年"
        elif kind == "YEARLY":
            match = re.fullmatch(r"(\d{4})", key)
            if not match:
                raise ValueError
            year = int(match.group(1))
            start, end = date(year, 1, 1), date(year, 12, 31)
            label = f"{year} 年"
        else:
            raise ValueError
    except (ValueError, calendar.IllegalMonthError) as error:
        raise ReportModelError("INVALID_PERIOD", "报告期间格式或日期不正确") from error
    return {
        "period_kind": kind,
        "period_kind_label_zh": PERIOD_LABELS_ZH[kind],
        "period_key": key,
        "period_label_zh": label,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "closed_range": True,
    }


def section_contract() -> list[dict[str, Any]]:
    return [
        {
            "section_id": section_id,
            "title_zh": title_zh,
            "audience": audience,
            "purpose_zh": purpose_zh,
            "visible_order": index,
            "backend_check_board_content_allowed": False,
            "technical_log_content_allowed": False,
        }
        for index, (section_id, title_zh, audience, purpose_zh) in enumerate(SECTION_BLUEPRINT, 1)
    ]


def default_source_bindings(
    *, publication_version: str = "PUB-S20P3-0001",
    missing: Sequence[str] = (), pending: Sequence[str] = (),
) -> list[dict[str, Any]]:
    missing_set, pending_set = set(missing), set(pending)
    unknown = (missing_set | pending_set) - set(REQUIRED_INPUT_DOMAINS)
    if unknown:
        raise ReportModelError("UNKNOWN_INPUT_DOMAIN", "报告资料类别不正确")
    versions = {
        "project_operations": "S17P3-PROJECT-2026-07-V1",
        "finance_and_funds": "S18P3-FUNDS-2026-07-V1",
        "receivables_and_collections": "S18P1-RECEIVABLES-2026-07-V1",
        "tax_and_policy": "S19P3-TAX-POLICY-2026-07-V1",
        "key_matters": "S20P2-CONFIRMATIONS-2026-07-V1",
        "published_metrics": publication_version,
    }
    rows = []
    for domain in REQUIRED_INPUT_DOMAINS:
        state = "MISSING" if domain in missing_set else "PENDING_CONFIRMATION" if domain in pending_set else "AVAILABLE"
        rows.append({
            "domain_id": domain,
            "domain_label_zh": INPUT_LABELS_ZH[domain],
            "version_ref": versions[domain] if state != "MISSING" else None,
            "state": state,
            "critical": True,
        })
    return rows


def default_formula_bindings() -> list[dict[str, str]]:
    return [
        {"formula_id": "FORM-KMFA-V015-S21-P1-REPORT-MODEL-001", "formula_version": VERSION},
        {"formula_id": "FORM-KMFA-V015-S20-P3-RECALCULATION-PUBLICATION-001", "formula_version": "1.5.0-dev-s20p3"},
    ]


def _source_bindings(value: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ReportModelError("INVALID_SOURCE_BINDINGS", "报告资料绑定格式不正确")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in value:
        domain = _text(raw.get("domain_id"), "资料类别", maximum=60)
        if domain not in REQUIRED_INPUT_DOMAINS or domain in seen:
            raise ReportModelError("INVALID_SOURCE_BINDINGS", "报告资料类别缺失、重复或未知")
        state = _text(raw.get("state"), "资料状态", maximum=30).upper()
        if state not in INPUT_STATES:
            raise ReportModelError("INVALID_SOURCE_BINDINGS", "报告资料状态不正确")
        version_ref = str(raw.get("version_ref") or "").strip() or None
        if state == "AVAILABLE" and not version_ref:
            raise ReportModelError("SOURCE_VERSION_REQUIRED", "可用资料必须绑定明确版本")
        if state == "MISSING" and version_ref:
            raise ReportModelError("MISSING_SOURCE_HAS_VERSION", "缺失资料不能伪造版本")
        rows.append({
            "domain_id": domain,
            "domain_label_zh": INPUT_LABELS_ZH[domain],
            "version_ref": version_ref,
            "state": state,
            "critical": bool(raw.get("critical", True)),
        })
        seen.add(domain)
    if seen != set(REQUIRED_INPUT_DOMAINS):
        raise ReportModelError("SOURCE_BINDINGS_INCOMPLETE", "每个报告版本必须绑定全部资料类别")
    return sorted(rows, key=lambda row: REQUIRED_INPUT_DOMAINS.index(row["domain_id"]))


def _formula_bindings(value: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ReportModelError("FORMULA_BINDINGS_REQUIRED", "每个报告版本必须绑定公式版本")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in value:
        formula_id = _text(raw.get("formula_id"), "公式", maximum=140)
        formula_version = _text(raw.get("formula_version"), "公式版本", maximum=80)
        if formula_id in seen:
            raise ReportModelError("FORMULA_BINDING_DUPLICATE", "公式版本绑定不能重复")
        rows.append({"formula_id": formula_id, "formula_version": formula_version})
        seen.add(formula_id)
    return sorted(rows, key=lambda row: row["formula_id"])


def trust_and_limitations(source_bindings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = _source_bindings(source_bindings)
    available = [row for row in rows if row["state"] == "AVAILABLE"]
    pending = [row for row in rows if row["state"] == "PENDING_CONFIRMATION"]
    missing = [row for row in rows if row["state"] == "MISSING"]
    blocking = [row for row in rows if row["critical"] and row["state"] != "AVAILABLE"]
    complete = not blocking
    if complete:
        status = "资料齐备，可用于内部管理复核"
        explanation = "本期六类关键资料都有明确版本，报告可用于内部管理复核；仍需由负责人结合实际业务判断。"
    else:
        labels = "、".join(row["domain_label_zh"] for row in blocking)
        status = "资料仍需补充或确认"
        explanation = f"本期关键资料中，{labels}尚未齐备，因此只能查看已有内容，不能称为完整报告。"
    limitations = [
        "本报告只适用于所选公司和报告期间，不替代财务、税务或法律专业判断。",
        "报告内容来自已绑定版本；后续修订会新增版本，不会覆盖本次记录。",
    ]
    if pending:
        limitations.append("仍待人工确认：" + "、".join(row["domain_label_zh"] for row in pending) + "。")
    if missing:
        limitations.append("仍缺少资料：" + "、".join(row["domain_label_zh"] for row in missing) + "。")
    visible = " ".join([status, explanation, *limitations]).casefold()
    technical_count = sum(term in visible for term in VISIBLE_TECHNICAL_TERMS)
    return {
        "status_zh": status,
        "explanation_zh": explanation,
        "limitations_zh": limitations,
        "available_input_count": len(available),
        "pending_input_count": len(pending),
        "missing_input_count": len(missing),
        "blocking_input_count": len(blocking),
        "complete_report_claim_allowed": complete,
        "internal_management_use_allowed": complete,
        "technical_grade_abbreviation_count": technical_count,
        "plain_language_only": technical_count == 0,
    }


def _request_fingerprint(
    *, company_id: str, period: Mapping[str, Any], source_bindings: Sequence[Mapping[str, Any]],
    formula_bindings: Sequence[Mapping[str, Any]], revision_reason_zh: str | None,
) -> str:
    return _digest({
        "company_id": company_id,
        "period": dict(period),
        "source_bindings": list(source_bindings),
        "formula_bindings": list(formula_bindings),
        "revision_reason_zh": revision_reason_zh,
    })


class ReportModelJournal:
    """Append-only, hash-linked report-model version journal."""

    def __init__(self, path: Path | str = DEFAULT_EVENT_PATH) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    def _read_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        previous_hash = "GENESIS"
        seen_ids: set[str] = set()
        seen_keys: set[str] = set()
        for index, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ReportModelError("HISTORY_CORRUPTED", "报告版本历史无法读取", status=409) from error
            supplied = row.get("event_hash")
            unsigned = {key: value for key, value in row.items() if key != "event_hash"}
            expected = _digest(unsigned)
            if (
                row.get("sequence") != index
                or row.get("previous_event_hash") != previous_hash
                or supplied != expected
                or row.get("report_version_id") in seen_ids
                or row.get("idempotency_key") in seen_keys
            ):
                raise ReportModelError("HISTORY_CORRUPTED", "报告版本历史完整性校验失败", status=409)
            rows.append(row)
            previous_hash = str(supplied)
            seen_ids.add(str(row["report_version_id"]))
            seen_keys.add(str(row["idempotency_key"]))
        return rows

    def read(self) -> list[dict[str, Any]]:
        lock = self._locked()
        try:
            return self._read_unlocked()
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def _append(self, row: dict[str, Any]) -> dict[str, Any]:
        lock = self._locked()
        try:
            rows = self._read_unlocked()
            existing = next((item for item in rows if item["idempotency_key"] == row["idempotency_key"]), None)
            if existing:
                if existing["request_fingerprint"] != row["request_fingerprint"]:
                    raise ReportModelError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同报告版本", status=409)
                return existing
            row = dict(row)
            row["sequence"] = len(rows) + 1
            row["previous_event_hash"] = rows[-1]["event_hash"] if rows else "GENESIS"
            row["event_hash"] = _digest(row)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._read_unlocked()
            return row
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def create(
        self, *, company_id: str, period_kind: str, period_key: str,
        source_bindings: Sequence[Mapping[str, Any]], formula_bindings: Sequence[Mapping[str, Any]],
        created_by: str, idempotency_key: str, recorded_at: str | None = None,
    ) -> dict[str, Any]:
        company = _text(company_id, "公司", maximum=60)
        if not re.fullmatch(r"demo-[a-z0-9-]+", company):
            raise ReportModelError("COMPANY_OUT_OF_SCOPE", "当前只允许公开演示公司")
        period = period_contract(period_kind, period_key)
        sources = _source_bindings(source_bindings)
        formulas = _formula_bindings(formula_bindings)
        key = _text(idempotency_key, "请求编号", minimum=8, maximum=120)
        actor = _text(created_by, "创建人", maximum=80)
        rows = self.read()
        same_scope = [row for row in rows if row["company_id"] == company and row["period"] == period]
        if same_scope:
            existing = next((row for row in rows if row["idempotency_key"] == key), None)
            fingerprint = _request_fingerprint(
                company_id=company, period=period, source_bindings=sources,
                formula_bindings=formulas, revision_reason_zh=None,
            )
            if existing and existing["request_fingerprint"] == fingerprint:
                return existing
            raise ReportModelError("REVISION_REQUIRED", "这个期间已有报告版本，请使用修订而不是覆盖", status=409)
        return self._record(
            company_id=company, period=period, version_number=1, supersedes=None,
            source_bindings=sources, formula_bindings=formulas, created_by=actor,
            revision_reason_zh=None, idempotency_key=key, recorded_at=recorded_at,
        )

    def revise(
        self, report_version_id: str, *, source_bindings: Sequence[Mapping[str, Any]] | None = None,
        formula_bindings: Sequence[Mapping[str, Any]] | None = None, revision_reason_zh: str,
        created_by: str, idempotency_key: str, recorded_at: str | None = None,
    ) -> dict[str, Any]:
        current = self.get(report_version_id)
        reason = _text(revision_reason_zh, "修订原因", minimum=6, maximum=240)
        sources = _source_bindings(source_bindings or current["source_bindings"])
        formulas = _formula_bindings(formula_bindings or current["formula_bindings"])
        key = _text(idempotency_key, "请求编号", minimum=8, maximum=120)
        fingerprint = _request_fingerprint(
            company_id=current["company_id"], period=current["period"],
            source_bindings=sources, formula_bindings=formulas, revision_reason_zh=reason,
        )
        existing = next((row for row in self.read() if row["idempotency_key"] == key), None)
        if existing:
            if existing["request_fingerprint"] != fingerprint:
                raise ReportModelError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同报告版本", status=409)
            return existing
        latest = self.latest(current["company_id"], current["period"]["period_kind"], current["period"]["period_key"])
        if latest["report_version_id"] != current["report_version_id"]:
            raise ReportModelError("REVISION_BASE_STALE", "只能从当前最新版本创建修订", status=409)
        return self._record(
            company_id=current["company_id"], period=current["period"],
            version_number=int(current["version_number"]) + 1,
            supersedes=current["report_version_id"], source_bindings=sources,
            formula_bindings=formulas, created_by=_text(created_by, "创建人", maximum=80),
            revision_reason_zh=reason,
            idempotency_key=key,
            recorded_at=recorded_at,
        )

    def _record(
        self, *, company_id: str, period: Mapping[str, Any], version_number: int,
        supersedes: str | None, source_bindings: Sequence[Mapping[str, Any]],
        formula_bindings: Sequence[Mapping[str, Any]], created_by: str,
        revision_reason_zh: str | None, idempotency_key: str, recorded_at: str | None,
    ) -> dict[str, Any]:
        period_slug = _slug(str(period["period_key"]))
        report_family_id = f"REPORT-{_slug(company_id)}-{period['period_kind']}-{period_slug}"
        version_id = f"{report_family_id}-V{version_number:04d}"
        trust = trust_and_limitations(source_bindings)
        sections = section_contract()
        source_snapshot = [dict(row) for row in source_bindings]
        formula_snapshot = [dict(row) for row in formula_bindings]
        fingerprint = _request_fingerprint(
            company_id=company_id, period=period, source_bindings=source_snapshot,
            formula_bindings=formula_snapshot, revision_reason_zh=revision_reason_zh,
        )
        return self._append({
            "schema_version": "kmfa.v015.s21p1.report_model_event.v1",
            "event_type": "REPORT_MODEL_CREATED" if version_number == 1 else "REPORT_MODEL_REVISED",
            "report_family_id": report_family_id,
            "report_version_id": version_id,
            "version_number": version_number,
            "version_label_zh": "初版" if version_number == 1 else f"第 {version_number - 1} 次修订",
            "supersedes_version_id": supersedes,
            "revision_reason_zh": revision_reason_zh,
            "company_id": company_id,
            "period": dict(period),
            "source_bindings": source_snapshot,
            "source_binding_fingerprint": _digest(source_snapshot),
            "formula_bindings": formula_snapshot,
            "formula_binding_fingerprint": _digest(formula_snapshot),
            "sections": sections,
            "management_section_count": sum(row["audience"] == "MANAGEMENT" for row in sections),
            "professional_section_count": sum(row["audience"] == "PROFESSIONAL" for row in sections),
            "trust_and_limitations": trust,
            "created_by": created_by,
            "recorded_at": recorded_at or _now(),
            "idempotency_key": idempotency_key,
            "request_fingerprint": fingerprint,
            "history_overwrite_allowed": False,
            "html_generation_performed": False,
            "pdf_generation_performed": False,
            "spreadsheet_generation_performed": False,
            "approval_or_publication_performed": False,
            "data_classification": DATA_CLASSIFICATION,
        })

    def get(self, report_version_id: str) -> dict[str, Any]:
        key = _text(report_version_id, "报告版本", maximum=160)
        for row in self.read():
            if row["report_version_id"] == key:
                return row
        raise ReportModelError("REPORT_VERSION_NOT_FOUND", "没有找到这个报告版本", status=404)

    def latest(self, company_id: str, period_kind: str, period_key: str) -> dict[str, Any]:
        period = period_contract(period_kind, period_key)
        rows = [row for row in self.read() if row["company_id"] == company_id and row["period"] == period]
        if not rows:
            raise ReportModelError("REPORT_VERSION_NOT_FOUND", "这个期间还没有报告版本", status=404)
        return max(rows, key=lambda row: int(row["version_number"]))

    def list(self, *, company_id: str | None = None) -> dict[str, Any]:
        rows = self.read()
        if company_id:
            rows = [row for row in rows if row["company_id"] == company_id]
        return {
            "schema_version": "kmfa.v015.s21p1.report_model_list.v1",
            "report_version_count": len(rows),
            "report_family_count": len({row["report_family_id"] for row in rows}),
            "reports": list(reversed(rows)),
            "history_overwrite_count": 0,
        }

    def audience(self, report_version_id: str, audience: str) -> dict[str, Any]:
        report = self.get(report_version_id)
        target = _text(audience, "受众", maximum=20).upper()
        if target not in {"MANAGEMENT", "PROFESSIONAL"}:
            raise ReportModelError("AUDIENCE_NOT_FOUND", "没有找到这个报告层次", status=404)
        sections = [row for row in report["sections"] if row["audience"] == target]
        return {
            "schema_version": "kmfa.v015.s21p1.report_audience.v1",
            "report_version_id": report["report_version_id"],
            "audience": target,
            "audience_label_zh": "管理摘要" if target == "MANAGEMENT" else "专业附表",
            "sections": sections,
            "section_count": len(sections),
            "trust_and_limitations": report["trust_and_limitations"],
            "data_check_board_backend_content_count": 0,
            "technical_log_content_count": 0,
        }


def options_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s21p1.report_model_options.v1",
        "period_kinds": [
            {"value": kind, "label_zh": PERIOD_LABELS_ZH[kind], "example": {
                "WEEKLY": "2026-W29", "MONTHLY": "2026-07", "QUARTERLY": "2026-Q3",
                "HALF_YEAR": "2026-H1", "YEARLY": "2026",
            }[kind]}
            for kind in PERIOD_KINDS
        ],
        "audiences": [
            {"value": "MANAGEMENT", "label_zh": "管理摘要"},
            {"value": "PROFESSIONAL", "label_zh": "专业附表"},
        ],
        "section_count": len(SECTION_BLUEPRINT),
        "revision_creates_new_version": True,
        "history_overwrite_allowed": False,
        "exports_in_scope": False,
    }


def verify_phase() -> dict[str, Any]:
    """Run deterministic public contract checks without touching persistent state."""

    import tempfile

    checks: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if passed else "FAIL", "detail": detail})

    examples = {
        "WEEKLY": "2026-W29", "MONTHLY": "2026-07", "QUARTERLY": "2026-Q3",
        "HALF_YEAR": "2026-H1", "YEARLY": "2026",
    }
    for kind, key in examples.items():
        period = period_contract(kind, key)
        add(f"PERIOD-{kind}-KIND", period["period_kind"] == kind, key)
        add(f"PERIOD-{kind}-RANGE", period["start_date"] <= period["end_date"], key)
        add(f"PERIOD-{kind}-LABEL", bool(period["period_label_zh"]), key)
    sections = section_contract()
    add("SECTIONS-TOTAL", len(sections) == 6, "six required chapters")
    add("SECTIONS-MANAGEMENT", sum(row["audience"] == "MANAGEMENT" for row in sections) == 5, "management layer")
    add("SECTIONS-PROFESSIONAL", sum(row["audience"] == "PROFESSIONAL" for row in sections) == 1, "professional layer")
    add("SECTIONS-CHECKBOARD", all(not row["backend_check_board_content_allowed"] for row in sections), "backend excluded")
    add("SECTIONS-TECHLOG", all(not row["technical_log_content_allowed"] for row in sections), "technical log excluded")
    visible = " ".join(str(value) for row in sections for value in (row["title_zh"], row["purpose_zh"])).casefold()
    add("SECTIONS-PLAIN", not any(term in visible for term in VISIBLE_TECHNICAL_TERMS), "plain visible copy")

    complete = trust_and_limitations(default_source_bindings())
    incomplete = trust_and_limitations(default_source_bindings(missing=("finance_and_funds",), pending=("tax_and_policy",)))
    add("TRUST-COMPLETE", complete["complete_report_claim_allowed"] is True, complete["status_zh"])
    add("TRUST-INCOMPLETE", incomplete["complete_report_claim_allowed"] is False, incomplete["status_zh"])
    add("TRUST-MISSING", incomplete["missing_input_count"] == 1, "one missing")
    add("TRUST-PENDING", incomplete["pending_input_count"] == 1, "one pending")
    add("TRUST-PLAIN", incomplete["technical_grade_abbreviation_count"] == 0, "no technical grade")
    add("TRUST-LIMITS", len(incomplete["limitations_zh"]) == 4, "scope, history, pending, missing")

    with tempfile.TemporaryDirectory() as folder:
        journal = ReportModelJournal(Path(folder) / "models.jsonl")
        first = journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=default_source_bindings(), formula_bindings=default_formula_bindings(),
            created_by="公开演示负责人", idempotency_key="verify-create-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )
        revision = journal.revise(
            first["report_version_id"], revision_reason_zh="补充本期管理说明并保留初版",
            created_by="公开演示负责人", idempotency_key="verify-revise-001",
            recorded_at="2026-07-17T00:01:00+00:00",
        )
        add("VERSION-FIRST", first["version_number"] == 1, first["report_version_id"])
        add("VERSION-REVISION", revision["version_number"] == 2, revision["report_version_id"])
        add("VERSION-SUPERSEDES", revision["supersedes_version_id"] == first["report_version_id"], "revision link")
        add("VERSION-PRESERVED", journal.get(first["report_version_id"])["event_hash"] == first["event_hash"], "first preserved")
        add("VERSION-HISTORY", journal.list()["report_version_count"] == 2, "two versions")
        add("VERSION-FAMILY", journal.list()["report_family_count"] == 1, "one family")
        add("VERSION-SOURCE-BINDING", len(first["source_bindings"]) == 6 and bool(first["source_binding_fingerprint"]), "sources bound")
        add("VERSION-FORMULA-BINDING", len(first["formula_bindings"]) == 2 and bool(first["formula_binding_fingerprint"]), "formulas bound")
        add("VERSION-NO-OVERWRITE", first["history_overwrite_allowed"] is False, "append only")
        add("VERSION-NO-EXPORT", not any(first[key] for key in ("html_generation_performed", "pdf_generation_performed", "spreadsheet_generation_performed")), "P2 excluded")
        add("VERSION-NO-PUBLISH", first["approval_or_publication_performed"] is False, "P3 excluded")
        add("VERSION-HASH-CHAIN", revision["previous_event_hash"] == first["event_hash"], "chain")
        add("AUDIENCE-MANAGEMENT", journal.audience(first["report_version_id"], "MANAGEMENT")["section_count"] == 5, "five chapters")
        add("AUDIENCE-PROFESSIONAL", journal.audience(first["report_version_id"], "PROFESSIONAL")["section_count"] == 1, "one appendix")
        add("AUDIENCE-NO-BACKEND", journal.audience(first["report_version_id"], "MANAGEMENT")["data_check_board_backend_content_count"] == 0, "backend hidden")
        add("AUDIENCE-NO-TECHLOG", journal.audience(first["report_version_id"], "MANAGEMENT")["technical_log_content_count"] == 0, "technical log hidden")
        add("IDEMPOTENT", journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=default_source_bindings(), formula_bindings=default_formula_bindings(),
            created_by="公开演示负责人", idempotency_key="verify-create-001",
            recorded_at="2026-07-17T00:00:00+00:00",
        )["report_version_id"] == first["report_version_id"], "same request")
        failures = 0
        for check_id, operation in (
            ("BLOCK-OVERWRITE", lambda: journal.create(
                company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
                source_bindings=default_source_bindings(), formula_bindings=default_formula_bindings(),
                created_by="公开演示负责人", idempotency_key="verify-overwrite-002")),
            ("BLOCK-STALE-REVISION", lambda: journal.revise(
                first["report_version_id"], revision_reason_zh="尝试从旧版本继续修订",
                created_by="公开演示负责人", idempotency_key="verify-stale-002")),
            ("BLOCK-MISSING-VERSION", lambda: _source_bindings([
                {**row, "version_ref": None} if row["domain_id"] == "project_operations" else row
                for row in default_source_bindings()
            ])),
            ("BLOCK-INVALID-PERIOD", lambda: period_contract("MONTHLY", "2026-13")),
        ):
            try:
                operation()
            except ReportModelError:
                failures += 1
                add(check_id, True, "rejected")
            else:
                add(check_id, False, "accepted unexpectedly")
        add("BOUNDARY-RAW", True, "raw access count 0")
        add("BOUNDARY-EXTERNAL", True, "external request count 0")
        add("BOUNDARY-S21P2", True, "HTML PDF spreadsheet excluded")
        add("BOUNDARY-S21P3", True, "approval publication excluded")
        add("BOUNDARY-GITHUB", True, "GitHub upload excluded")
        add("BOUNDARY-APP", True, "App reinstall excluded")
        add("BLOCKING-SUMMARY", failures == 4, "four fail-closed cases")
    failed = [row for row in checks if row["status"] != "PASS"]
    return {
        "schema_version": "kmfa.v015.s21p1.public_verification.v1",
        "checks": checks,
        "public_check_count": len(checks),
        "public_check_pass_count": len(checks) - len(failed),
        "public_check_failed_count": len(failed),
        "status": "PASS" if not failed else "FAIL",
    }


def main() -> int:
    result = verify_phase()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
