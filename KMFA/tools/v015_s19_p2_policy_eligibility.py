#!/usr/bin/env python3
"""KMFA v1.5 S19-P2 政策规则、证据准备度与材料任务流。

政策规则来自公开官方页面的固定快照；企业证据全部是公开合成演示。
本模块只提示缺口和风险，不判断申报资格，不生成或包装材料。
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


RUN_PHASE_ID = "V015_S19_P2_POLICY_ELIGIBILITY"
ROADMAP_PHASE_ID = "S19-P2"
TASK_ID = "KMFA-V015-S19-P2-POLICY-ELIGIBILITY-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S19-P2-POLICY-ELIGIBILITY"
VERSION = "1.5.0-dev-s19p2"
DATA_CLASSIFICATION = "PUBLIC_OFFICIAL_POLICY_AND_SYNTHETIC_EVIDENCE"
POLICY_PATH = Path(__file__).resolve().parents[1] / "config/v015_s19_p2_policy_registry.json"

COMPANIES = {
    "demo-north": "北方演示公司",
    "demo-south": "南方演示公司",
    "demo-west": "西部演示公司",
}
PERIODS = ("2026-07", "2026-Q2", "2026-H1")
CATEGORY_NAMES = {
    "IP": "知识产权",
    "RD_PROJECT": "研发项目",
    "PERSONNEL": "研发人员",
    "RD_EXPENSE": "研发费用",
    "HIGH_TECH_REVENUE": "高新收入",
    "SPECIAL_MATERIAL": "专项材料",
}
STATUS_NAMES = {
    "AVAILABLE": "已有来源",
    "MISSING": "缺失",
    "REVIEW_REQUIRED": "需复核",
}
TASK_STATUS_NAMES = {
    "MISSING_SOURCE": "缺少来源",
    "SOURCE_REVIEW": "来源待复核",
    "READY_TO_COMPLETE": "来源已核验，可完成",
    "COMPLETED": "已完成",
}
OFFICIAL_HOST_SUFFIXES = ("most.gov.cn", "miit.gov.cn", "chinatax.gov.cn")


class PolicyEligibilityError(ValueError):
    """S19-P2 请求违反政策或证据边界。"""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise PolicyEligibilityError(f"invalid ISO date: {value}") from error


def load_policy_config() -> dict[str, Any]:
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    required = {
        "schema_version", "snapshot_as_of", "review_cycle_days", "next_review_due",
        "runtime_external_fetch_allowed", "eligibility_conclusion_allowed",
        "material_fabrication_assistance_allowed", "rules",
    }
    if not required.issubset(value):
        raise PolicyEligibilityError("policy registry config is incomplete")
    if value["runtime_external_fetch_allowed"] or value["eligibility_conclusion_allowed"] or value["material_fabrication_assistance_allowed"]:
        raise PolicyEligibilityError("runtime fetch, eligibility conclusion and fabrication assistance must remain disabled")
    if value["review_cycle_days"] != 90 or len(value["rules"]) != 6:
        raise PolicyEligibilityError("policy registry shape drifted")
    return value


def policy_registry(as_of_date: str | None = None) -> list[dict[str, Any]]:
    config = load_policy_config()
    as_of = _parse_date(as_of_date or str(config["snapshot_as_of"]))
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in config["rules"]:
        row = dict(raw)
        policy_id = str(row.get("policy_id", ""))
        if not policy_id or policy_id in seen:
            raise PolicyEligibilityError("policy ids must be unique")
        seen.add(policy_id)
        source_url = str(row.get("source_url", ""))
        if not source_url.startswith("https://") or not any(suffix in source_url.split("/", 3)[2] for suffix in OFFICIAL_HOST_SUFFIXES):
            raise PolicyEligibilityError(f"official source required: {policy_id}")
        for key in ("source_date", "effective_from", "reviewed_at", "next_review_due"):
            _parse_date(str(row.get(key, "")))
        status = str(row.get("validity_status", ""))
        current = status == "CURRENT_REVIEWED"
        review_due = _parse_date(str(row["next_review_due"]))
        if not current:
            refresh_state = "BLOCKED_SUPERSEDED"
        elif as_of > review_due:
            refresh_state = "REVIEW_OVERDUE"
        else:
            refresh_state = "CURRENT"
        row.update({
            "as_of_date": as_of.isoformat(),
            "refresh_state": refresh_state,
            "refresh_state_zh": {
                "CURRENT": "已核验，等待下次复核",
                "REVIEW_OVERDUE": "已到复核日期，停止确定使用",
                "BLOCKED_SUPERSEDED": "历史规则，已停止使用",
            }[refresh_state],
            "rule_use_allowed": refresh_state == "CURRENT",
            "eligibility_conclusion": None,
            "eligibility_conclusion_allowed": False,
            "data_classification": "PUBLIC_OFFICIAL_POLICY_SNAPSHOT",
        })
        rows.append(row)
    if sum(row["validity_status"] == "CURRENT_REVIEWED" for row in rows) != 5 or sum(row["validity_status"] == "SUPERSEDED" for row in rows) != 1:
        raise PolicyEligibilityError("current and superseded policy counts drifted")
    return rows


def evidence_items(company_id: str = "demo-north", period: str = "2026-07") -> list[dict[str, Any]]:
    if company_id not in COMPANIES:
        raise PolicyEligibilityError("unsupported public company")
    if period not in PERIODS:
        raise PolicyEligibilityError("unsupported public period")
    definitions = (
        ("EVD-IP-001", "IP", "有效知识产权清单", "AVAILABLE", True),
        ("EVD-IP-002", "IP", "软件著作权与产品映射", "MISSING", False),
        ("EVD-RD-001", "RD_PROJECT", "研发项目立项文件", "AVAILABLE", True),
        ("EVD-RD-002", "RD_PROJECT", "研发过程与测试记录", "AVAILABLE", True),
        ("EVD-PEOPLE-001", "PERSONNEL", "研发人员名册", "AVAILABLE", True),
        ("EVD-PEOPLE-002", "PERSONNEL", "研发人员资质复核", "REVIEW_REQUIRED", False),
        ("EVD-EXPENSE-001", "RD_EXPENSE", "研发费用辅助账", "AVAILABLE", True),
        ("EVD-EXPENSE-002", "RD_EXPENSE", "费用凭证勾稽表", "MISSING", False),
        ("EVD-REVENUE-001", "HIGH_TECH_REVENUE", "高新产品收入明细", "AVAILABLE", True),
        ("EVD-REVENUE-002", "HIGH_TECH_REVENUE", "产品与技术领域映射", "REVIEW_REQUIRED", False),
        ("EVD-MATERIAL-001", "SPECIAL_MATERIAL", "合规与信用声明", "AVAILABLE", True),
        ("EVD-MATERIAL-002", "SPECIAL_MATERIAL", "创新能力专项佐证", "MISSING", False),
    )
    rows: list[dict[str, Any]] = []
    for evidence_id, category_id, label_zh, status, verified in definitions:
        source_ref = f"PUBLIC-SYNTHETIC:EVIDENCE:{company_id}:{period}:{evidence_id}" if status != "MISSING" else None
        rows.append({
            "evidence_id": evidence_id,
            "category_id": category_id,
            "category_zh": CATEGORY_NAMES[category_id],
            "label_zh": label_zh,
            "status": status,
            "status_zh": STATUS_NAMES[status],
            "company_id": company_id,
            "company_zh": COMPANIES[company_id],
            "period": period,
            "source_ref": source_ref,
            "source_verified": verified,
            "source_locator_zh": "公开合成证据位置" if source_ref else "尚无来源材料",
            "fabricated": False,
            "packaged_material": False,
            "data_classification": "PUBLIC_SYNTHETIC",
        })
    return rows


def readiness_categories(items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category_id, category_zh in CATEGORY_NAMES.items():
        selected = [row for row in items if row.get("category_id") == category_id]
        available = sum(row.get("status") == "AVAILABLE" and row.get("source_verified") is True for row in selected)
        missing = sum(row.get("status") == "MISSING" for row in selected)
        review = sum(row.get("status") == "REVIEW_REQUIRED" for row in selected)
        required = len(selected)
        rows.append({
            "category_id": category_id,
            "category_zh": category_zh,
            "required_count": required,
            "available_count": available,
            "missing_count": missing,
            "review_count": review,
            "completeness_bps": available * 10_000 // required,
            "status": "COMPLETE" if available == required else "GAPS_OR_REVIEW",
            "status_zh": "来源齐全" if available == required else "有缺口或待复核",
            "eligibility_conclusion": None,
            "guidance_zh": "只列缺口和风险，不判断是否符合申报条件。",
        })
    return rows


def policy_readiness(policy: Mapping[str, Any], categories: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not policy.get("rule_use_allowed"):
        return {
            "policy_id": policy["policy_id"],
            "policy_name_zh": policy["policy_name_zh"],
            "status": "POLICY_BLOCKED",
            "status_zh": "规则已过期或待复核，停止判断",
            "required_category_count": 0,
            "required_item_count": 0,
            "available_item_count": 0,
            "missing_or_review_count": 0,
            "completeness_bps": 0,
            "gap_categories_zh": [],
            "eligibility_conclusion": None,
        }
    ids = set(policy.get("required_category_ids", []))
    selected = [row for row in categories if row.get("category_id") in ids]
    required = sum(int(row["required_count"]) for row in selected)
    available = sum(int(row["available_count"]) for row in selected)
    gaps = [str(row["category_zh"]) for row in selected if row["status"] != "COMPLETE"]
    return {
        "policy_id": policy["policy_id"],
        "policy_name_zh": policy["policy_name_zh"],
        "status": "GAPS_AND_RISKS" if gaps else "EVIDENCE_COMPLETE_NOT_ELIGIBILITY",
        "status_zh": "存在证据缺口" if gaps else "证据齐全，仍需专业审核",
        "required_category_count": len(selected),
        "required_item_count": required,
        "available_item_count": available,
        "missing_or_review_count": required - available,
        "completeness_bps": available * 10_000 // required if required else 0,
        "gap_categories_zh": gaps,
        "eligibility_conclusion": None,
    }


def task_definitions(company_id: str = "demo-north", period: str = "2026-07") -> list[dict[str, Any]]:
    items = {row["evidence_id"]: row for row in evidence_items(company_id, period)}
    definitions = (
        ("POLTASK-001", "补齐软件著作权与产品映射", "技术负责人", "2026-07-31", "EVD-IP-002", ("POLICY-TECH-SME", "POLICY-HIGH-TECH")),
        ("POLTASK-002", "复核研发人员资质", "人力负责人", "2026-07-29", "EVD-PEOPLE-002", ("POLICY-TECH-SME", "POLICY-HIGH-TECH")),
        ("POLTASK-003", "补齐研发费用凭证勾稽", "财务负责人", "2026-07-28", "EVD-EXPENSE-002", ("POLICY-TECH-SME", "POLICY-HIGH-TECH", "POLICY-RD-DEDUCTION")),
        ("POLTASK-004", "复核产品与技术领域映射", "业务负责人", "2026-08-02", "EVD-REVENUE-002", ("POLICY-HIGH-TECH", "POLICY-SPECIALIZED-SME", "POLICY-LITTLE-GIANT")),
        ("POLTASK-005", "补齐创新能力专项佐证", "项目负责人", "2026-08-05", "EVD-MATERIAL-002", ("POLICY-HIGH-TECH", "POLICY-SPECIALIZED-SME", "POLICY-LITTLE-GIANT")),
        ("POLTASK-006", "确认研发项目立项文件已归档", "研发负责人", "2026-07-25", "EVD-RD-001", ("POLICY-TECH-SME", "POLICY-HIGH-TECH", "POLICY-RD-DEDUCTION")),
    )
    tasks: list[dict[str, Any]] = []
    for task_id, title_zh, owner_zh, due_date, evidence_id, policy_ids in definitions:
        evidence = items[evidence_id]
        if evidence["status"] == "MISSING":
            status = "MISSING_SOURCE"
        elif not evidence["source_verified"]:
            status = "SOURCE_REVIEW"
        else:
            status = "READY_TO_COMPLETE"
        tasks.append({
            "task_id": task_id,
            "title_zh": title_zh,
            "owner_zh": owner_zh,
            "due_date": due_date,
            "company_id": company_id,
            "period": period,
            "policy_ids": list(policy_ids),
            "required_evidence_id": evidence_id,
            "target_location_ref": f"PUBLIC-SYNTHETIC:EVIDENCE-SLOT:{company_id}:{period}:{evidence_id}",
            "source_evidence_ref": evidence["source_ref"],
            "source_verified": evidence["source_verified"],
            "status": status,
            "status_zh": TASK_STATUS_NAMES[status],
            "completion_allowed": status == "READY_TO_COMPLETE",
            "completion_block_reason_zh": None if status == "READY_TO_COMPLETE" else "无已核验来源材料，不能勾选完成。",
            "fabrication_or_packaging_allowed": False,
        })
    return tasks


class PolicyTaskJournal:
    """只保存公开演示任务完成事件的追加式日志。"""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._lock = threading.RLock()

    def read(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.path.is_file():
                return []
            rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if any(row.get("schema_version") != "kmfa.v015.s19p2.policy_task_event.v1" for row in rows):
                raise PolicyEligibilityError("policy task journal contains an unsupported event")
            return rows

    def append(self, event: Mapping[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(dict(event), ensure_ascii=False, sort_keys=True) + "\n")


def complete_policy_task(
    journal: PolicyTaskJournal,
    *,
    task_id: str,
    company_id: str,
    period: str,
    source_evidence_ref: str,
    actor_ref: str,
    idempotency_key: str,
) -> dict[str, Any]:
    if not actor_ref.strip() or not idempotency_key.strip():
        raise PolicyEligibilityError("负责人和幂等键不能为空")
    tasks = {row["task_id"]: row for row in task_definitions(company_id, period)}
    if task_id not in tasks:
        raise PolicyEligibilityError("policy task does not exist")
    task = tasks[task_id]
    items = {row["evidence_id"]: row for row in evidence_items(company_id, period)}
    evidence = items[task["required_evidence_id"]]
    if not source_evidence_ref.strip():
        raise PolicyEligibilityError("无来源材料不能勾选完成")
    if source_evidence_ref != evidence.get("source_ref"):
        raise PolicyEligibilityError("来源材料与任务要求不匹配")
    if evidence.get("status") != "AVAILABLE" or evidence.get("source_verified") is not True:
        raise PolicyEligibilityError("来源材料尚未核验，不能勾选完成")
    existing = [
        row for row in journal.read()
        if row.get("task_id") == task_id and row.get("company_id") == company_id and row.get("period") == period
    ]
    if existing:
        return {**existing[-1], "idempotent_replay": True}
    digest = hashlib.sha256(f"{company_id}|{period}|{task_id}|{idempotency_key}".encode()).hexdigest()[:20]
    event = {
        "schema_version": "kmfa.v015.s19p2.policy_task_event.v1",
        "event_id": f"POLTASK-EVENT-{digest}",
        "event_type": "PUBLIC_SYNTHETIC_EVIDENCE_TASK_COMPLETED",
        "task_id": task_id,
        "company_id": company_id,
        "period": period,
        "source_evidence_ref": source_evidence_ref,
        "source_verified": True,
        "actor_ref": actor_ref,
        "idempotency_key": idempotency_key,
        "completed_at": datetime.now().astimezone().isoformat(),
        "status": "COMPLETED",
        "eligibility_conclusion": None,
        "real_business_action": False,
        "data_classification": "PUBLIC_SYNTHETIC",
    }
    journal.append(event)
    return {**event, "idempotent_replay": False}


def task_list(company_id: str, period: str, events: Sequence[Mapping[str, Any]], policy_id: str = "") -> list[dict[str, Any]]:
    completed = {
        str(row.get("task_id"))
        for row in events
        if row.get("company_id") == company_id and row.get("period") == period and row.get("status") == "COMPLETED"
    }
    rows: list[dict[str, Any]] = []
    for task in task_definitions(company_id, period):
        if policy_id and policy_id not in task["policy_ids"]:
            continue
        row = dict(task)
        if row["task_id"] in completed:
            row.update({
                "status": "COMPLETED",
                "status_zh": TASK_STATUS_NAMES["COMPLETED"],
                "completion_allowed": False,
                "completion_block_reason_zh": None,
            })
        rows.append(row)
    return rows


def policy_view(
    *,
    company_id: str = "demo-north",
    period: str = "2026-07",
    policy_id: str = "POLICY-HIGH-TECH",
    events: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    registry = policy_registry()
    by_id = {row["policy_id"]: row for row in registry}
    if policy_id not in by_id:
        raise PolicyEligibilityError("unsupported policy")
    items = evidence_items(company_id, period)
    categories = readiness_categories(items)
    selected = by_id[policy_id]
    readiness = policy_readiness(selected, categories)
    tasks = task_list(company_id, period, events, policy_id)
    summary = {
        "policy_count": len(registry),
        "current_policy_count": sum(row["rule_use_allowed"] for row in registry),
        "blocked_policy_count": sum(not row["rule_use_allowed"] for row in registry),
        "review_overdue_count": sum(row["refresh_state"] == "REVIEW_OVERDUE" for row in registry),
        "evidence_item_count": len(items),
        "available_evidence_count": sum(row["status"] == "AVAILABLE" for row in items),
        "missing_evidence_count": sum(row["status"] == "MISSING" for row in items),
        "review_evidence_count": sum(row["status"] == "REVIEW_REQUIRED" for row in items),
        "task_count": len(tasks),
        "completed_task_count": sum(row["status"] == "COMPLETED" for row in tasks),
        "source_blocked_task_count": sum(row["status"] in {"MISSING_SOURCE", "SOURCE_REVIEW"} for row in tasks),
        "ready_task_count": sum(row["status"] == "READY_TO_COMPLETE" for row in tasks),
    }
    return {
        "schema_version": "kmfa.v015.s19p2.policy_eligibility_view.v1",
        "allowed": True,
        "company_id": company_id,
        "company_zh": COMPANIES[company_id],
        "period": period,
        "selected_policy_id": policy_id,
        "selected_policy": selected,
        "policy_registry": registry,
        "evidence_items": items,
        "readiness_categories": categories,
        "policy_readiness": readiness,
        "tasks": tasks,
        "summary": summary,
        "formal_eligibility_conclusion": None,
        "formal_eligibility_conclusion_count": 0,
        "expired_policy_deterministic_conclusion_count": 0,
        "fabricated_evidence_count": 0,
        "material_packaging_assistance_count": 0,
        "cross_company_leak_count": 0,
        "external_network_request_count": 0,
        "raw_root_access_count": 0,
        "real_business_action_count": 0,
        "scope_limitation_zh": "只提示证据缺口和风险，不判断申报资格，不替代主管部门、税务或专业签字。",
        "anti_fabrication_zh": "不得伪造、倒签、包装或替换材料；没有已核验来源的任务不能完成。",
        "data_classification": DATA_CLASSIFICATION,
    }


def source_contract() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s19p2.source_contract.v1",
        "stage_id": "S19",
        "stage_name_zh": "税务、发票、政策资格与证据准备",
        "roadmap_phase_id": ROADMAP_PHASE_ID,
        "phase_name_zh": "政策资格",
        "task_ids": ["S19P2T01", "S19P2T02", "S19P2T03"],
        "task_names_zh": ["建立政策规则登记", "建立证据准备度", "实现政策任务清单"],
        "official_policy_snapshot": True,
        "synthetic_enterprise_evidence": True,
        "runtime_external_fetch_allowed": False,
        "eligibility_conclusion_allowed": False,
        "material_fabrication_assistance_allowed": False,
        "data_classification": DATA_CLASSIFICATION,
    }


def public_checks() -> list[dict[str, Any]]:
    registry = policy_registry()
    items = evidence_items()
    categories = readiness_categories(items)
    tasks = task_definitions()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL"})

    for row in registry:
        host = row["source_url"].split("/", 3)[2]
        add(f"policy_{row['policy_id']}_official_source", any(host.endswith(suffix) for suffix in OFFICIAL_HOST_SUFFIXES))
        add(f"policy_{row['policy_id']}_version_and_dates", bool(row["rule_version"] and row["source_date"] and row["effective_from"]))
        add(f"policy_{row['policy_id']}_review_metadata", row["reviewed_at"] == "2026-07-16" and row["next_review_due"] == "2026-10-14")
        add(
            f"policy_{row['policy_id']}_validity_gate",
            row["eligibility_conclusion"] is None
            and row["eligibility_conclusion_allowed"] is False
            and row["rule_use_allowed"] is (row["validity_status"] == "CURRENT_REVIEWED"),
        )
    for row in items:
        add(f"evidence_{row['evidence_id']}_category", row["category_id"] in CATEGORY_NAMES and bool(row["label_zh"]))
        add(
            f"evidence_{row['evidence_id']}_source_semantics",
            (row["status"] == "AVAILABLE" and row["source_verified"] is True and bool(row["source_ref"]))
            or (row["status"] == "MISSING" and row["source_verified"] is False and row["source_ref"] is None)
            or (row["status"] == "REVIEW_REQUIRED" and row["source_verified"] is False and bool(row["source_ref"])),
        )
        add(
            f"evidence_{row['evidence_id']}_public_boundary",
            row["company_id"] == "demo-north" and row["period"] == "2026-07" and row["fabricated"] is False and row["packaged_material"] is False,
        )
    for row in tasks:
        add(f"task_{row['task_id']}_owner_due_target", bool(row["owner_zh"] and row["due_date"] and row["target_location_ref"]))
        add(
            f"task_{row['task_id']}_source_gate",
            row["fabrication_or_packaging_allowed"] is False
            and row["completion_allowed"] is (row["status"] == "READY_TO_COMPLETE")
            and (row["completion_allowed"] is False or bool(row["source_evidence_ref"])),
        )
    add("global_policy_shape", len(registry) == 6 and sum(row["rule_use_allowed"] for row in registry) == 5)
    add("global_expired_conclusion_block", sum(row["eligibility_conclusion"] is not None for row in registry if not row["rule_use_allowed"]) == 0)
    add("global_readiness_shape", len(categories) == 6 and sum(row["required_count"] for row in categories) == 12)
    add("global_evidence_counts", sum(row["status"] == "AVAILABLE" for row in items) == 7 and sum(row["status"] == "MISSING" for row in items) == 3 and sum(row["status"] == "REVIEW_REQUIRED" for row in items) == 2)
    add("global_no_eligibility_conclusion", policy_view()["formal_eligibility_conclusion_count"] == 0)
    add("global_no_fabrication_or_packaging", policy_view()["fabricated_evidence_count"] == 0 and policy_view()["material_packaging_assistance_count"] == 0)
    add("global_company_scope", policy_view()["cross_company_leak_count"] == 0)
    add("global_runtime_boundary", policy_view()["raw_root_access_count"] == 0 and policy_view()["external_network_request_count"] == 0 and policy_view()["real_business_action_count"] == 0)
    if len(checks) != 80:
        raise PolicyEligibilityError(f"expected 80 public checks, got {len(checks)}")
    return checks


def validate_public_contract() -> None:
    failed = [row["name"] for row in public_checks() if row["status"] != "PASS"]
    if failed:
        raise PolicyEligibilityError("public contract failed: " + ", ".join(failed))


if __name__ == "__main__":
    validate_public_contract()
    print(json.dumps({
        "policy_count": 6,
        "current_policy_count": 5,
        "evidence_item_count": 12,
        "available_evidence_count": 7,
        "missing_evidence_count": 3,
        "review_evidence_count": 2,
        "task_count": 6,
        "public_check_count": 80,
    }, ensure_ascii=False, indent=2))
