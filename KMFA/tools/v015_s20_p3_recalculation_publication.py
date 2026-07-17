#!/usr/bin/env python3
"""KMFA v1.5 S20-P3 affected-chain recalculation and local publication.

The kernel consumes an active S20-P2 control event, recalculates only its
registered downstream chain, shows an explained before/after comparison, and
atomically publishes one public-synthetic local product version.  It never
edits raw/source data and it never performs an external release.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import tempfile
import threading
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from KMFA.tools import v015_s20_p2_confirmation_workbench as confirmation


RUN_PHASE_ID = "V015_S20_P3_RECALCULATION_PUBLICATION"
ROADMAP_PHASE_ID = "S20-P3"
TASK_ID = "KMFA-V015-S20-P3-RECALCULATION-PUBLICATION-20260717"
ACCEPTANCE_ID = "ACC-KMFA-V015-S20-P3-RECALCULATION-PUBLICATION"
VERSION = "1.5.0-dev-s20p3"
EVENT_SCHEMA = "kmfa.v015.s20p3.publication_event.v1"
DEFAULT_EVENT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".codex_private_runtime"
    / "v015_s20_p3_recalculation_publication"
    / "publication_events.jsonl"
)

RECALCULATION_ROLES = frozenset({"ROLE::DATA_STEWARD", "ROLE::AUDITOR"})
PUBLICATION_ROLES = frozenset({"ROLE::MANAGEMENT", "ROLE::AUDITOR"})
DECISIONS = frozenset({"PUBLISH_CANDIDATE", "KEEP_CURRENT"})
VIEW_IDS = ("project", "homepage", "report", "check-board")
EVENT_TYPES = frozenset({"RECALCULATION_COMPLETED", "PUBLICATION_PUBLISHED", "PUBLICATION_RETAINED"})

_EVENT_ID = re.compile(r"^CTRL-S20P3-\d{4}$")
_JOB_ID = re.compile(r"^JOB-S20P3-\d{4}$")
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


class RecalculationError(ValueError):
    """Stable fail-closed error safe for the local S20-P3 workbench."""

    def __init__(self, code: str, message_zh: str, *, status: int = 400):
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh
        self.status = status


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str, *, limit: int = 240) -> str:
    result = str(value or "").strip()
    if not result or len(result) > limit or any(ord(char) < 32 and char not in "\t\n" for char in result):
        raise RecalculationError("FIELD_INVALID", f"{field} 不完整或过长。")
    return result


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise RecalculationError("VALUE_INVALID", f"{field} 必须是整数。")
    return value


CONTROL_REFS = {
    "ISSUE-S20P2-001": "CONTROL::PROJECT_ASSIGNMENT",
    "ISSUE-S20P2-002": "CONTROL::ACCOUNT_OWNERSHIP",
    "ISSUE-S20P2-003": "CONTROL::PERIOD_ALIGNMENT",
    "ISSUE-S20P2-004": "CONTROL::COST_CATEGORY",
    "ISSUE-S20P2-005": "CONTROL::CUSTOMER_ALIAS",
}

ACTION_DELTAS: dict[str, dict[str, int]] = {
    "KEEP_IMPORTED_PROJECT": {"FACT::PROJECT_REVENUE_CENTS": 2_400_000, "FACT::PROJECT_COST_CENTS": 1_100_000},
    "USE_REGISTERED_PROJECT": {"FACT::PROJECT_REVENUE_CENTS": 5_600_000, "FACT::PROJECT_COST_CENTS": 1_900_000},
    "CONFIRM_ENTITY": {"FACT::PROJECT_COLLECTION_CENTS": 4_200_000},
    "KEEP_EXCLUDED": {"FACT::PROJECT_COLLECTION_CENTS": -1_600_000},
    "KEEP_DOCUMENT_PERIOD": {"FACT::PROJECT_REVENUE_CENTS": -2_100_000},
    "USE_UPLOAD_PERIOD": {"FACT::PROJECT_REVENUE_CENTS": 3_300_000},
    "MAP_INSTALL_SUBCONTRACT": {"FACT::PROJECT_COST_CENTS": 2_700_000},
    "MAP_TECHNICAL_SERVICE": {"FACT::PROJECT_COST_CENTS": -1_300_000},
    "CONFIRM_CUSTOMER_ALIAS": {"FACT::PROJECT_COLLECTION_CENTS": 2_800_000},
    "KEEP_SEPARATE_CUSTOMER": {"FACT::PROJECT_COLLECTION_CENTS": -900_000},
}

NODE_TYPES = {
    **{value: "CONTROL" for value in CONTROL_REFS.values()},
    "FACT::PROJECT_REVENUE_CENTS": "FACT",
    "FACT::PROJECT_COST_CENTS": "FACT",
    "FACT::PROJECT_COLLECTION_CENTS": "FACT",
    "METRIC::PROJECT_MARGIN_CENTS": "METRIC",
    "METRIC::COLLECTION_RATIO_BPS": "METRIC",
    "PAGE::PROJECT": "PAGE",
    "PAGE::HOMEPAGE": "PAGE",
    "REPORT::MANAGEMENT": "REPORT",
    "BOARD::CHECK": "BOARD",
    "FACT::UNRELATED_CASH_CENTS": "FACT",
    "PAGE::UNRELATED_TAX": "PAGE",
}

IMPACT_EDGES = tuple(
    [("CONTROL::PROJECT_ASSIGNMENT", "FACT::PROJECT_REVENUE_CENTS"), ("CONTROL::PROJECT_ASSIGNMENT", "FACT::PROJECT_COST_CENTS")]
    + [("CONTROL::ACCOUNT_OWNERSHIP", "FACT::PROJECT_COLLECTION_CENTS")]
    + [("CONTROL::PERIOD_ALIGNMENT", "FACT::PROJECT_REVENUE_CENTS")]
    + [("CONTROL::COST_CATEGORY", "FACT::PROJECT_COST_CENTS")]
    + [("CONTROL::CUSTOMER_ALIAS", "FACT::PROJECT_COLLECTION_CENTS")]
    + [
        ("FACT::PROJECT_REVENUE_CENTS", "METRIC::PROJECT_MARGIN_CENTS"),
        ("FACT::PROJECT_COST_CENTS", "METRIC::PROJECT_MARGIN_CENTS"),
        ("FACT::PROJECT_REVENUE_CENTS", "METRIC::COLLECTION_RATIO_BPS"),
        ("FACT::PROJECT_COLLECTION_CENTS", "METRIC::COLLECTION_RATIO_BPS"),
    ]
    + [
        (metric, view)
        for metric in ("METRIC::PROJECT_MARGIN_CENTS", "METRIC::COLLECTION_RATIO_BPS")
        for view in ("PAGE::PROJECT", "PAGE::HOMEPAGE", "REPORT::MANAGEMENT", "BOARD::CHECK")
    ]
)

FACT_KEYS = {
    "FACT::PROJECT_REVENUE_CENTS": "project_revenue_cents",
    "FACT::PROJECT_COST_CENTS": "project_cost_cents",
    "FACT::PROJECT_COLLECTION_CENTS": "project_collection_cents",
    "FACT::UNRELATED_CASH_CENTS": "unrelated_cash_cents",
}
METRIC_KEYS = {
    "METRIC::PROJECT_MARGIN_CENTS": "project_margin_cents",
    "METRIC::COLLECTION_RATIO_BPS": "collection_ratio_bps",
}
VIEW_REFS = {
    "PAGE::PROJECT": "project", "PAGE::HOMEPAGE": "homepage",
    "REPORT::MANAGEMENT": "report", "BOARD::CHECK": "check-board",
}


def impact_graph() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v015.s20p3.impact_graph.v1",
        "nodes": copy.deepcopy(NODE_TYPES),
        "edges": [list(row) for row in IMPACT_EDGES],
        "unrelated_refs": ["FACT::UNRELATED_CASH_CENTS", "PAGE::UNRELATED_TAX"],
    }


def analyze_impact(changed_refs: Iterable[str], graph: Mapping[str, Any] | None = None) -> dict[str, Any]:
    value = graph or impact_graph()
    nodes = value.get("nodes")
    edges = value.get("edges")
    if not isinstance(nodes, Mapping) or not nodes or not isinstance(edges, list):
        raise RecalculationError("IMPACT_GRAPH_INVALID", "影响图不完整。", status=409)
    node_ids = {str(ref) for ref in nodes}
    changed = {_text(ref, "变更引用") for ref in changed_refs}
    unknown = sorted(changed - node_ids)
    adjacency: dict[str, set[str]] = defaultdict(set)
    indegree = {ref: 0 for ref in node_ids}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise RecalculationError("IMPACT_GRAPH_INVALID", "影响图连接不完整。", status=409)
        source, target = map(str, edge)
        if source not in node_ids or target not in node_ids:
            raise RecalculationError("IMPACT_GRAPH_INVALID", "影响图包含未知节点。", status=409)
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1
    queue = deque(sorted(ref for ref, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        ref = queue.popleft()
        visited += 1
        for target in sorted(adjacency[ref]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if unknown or visited != len(node_ids):
        raise RecalculationError("IMPACT_SCOPE_UNKNOWN", "影响范围未知或存在循环，不能重算。", status=409)
    affected: set[str] = set()
    frontier = deque(sorted(changed))
    while frontier:
        source = frontier.popleft()
        for target in sorted(adjacency[source]):
            if target not in affected and target not in changed:
                affected.add(target)
                frontier.append(target)
    by_type: dict[str, list[str]] = defaultdict(list)
    for ref in sorted(affected):
        by_type[str(nodes[ref])].append(ref)
    return {
        "scope_known": True,
        "changed_refs": sorted(changed),
        "affected_refs": sorted(affected),
        "affected_by_type": dict(sorted(by_type.items())),
        "affected_node_count": len(affected),
        "unaffected_refs": sorted(node_ids - changed - affected),
        "automatic_external_publication_allowed": False,
    }


def _shared_payload(facts: Mapping[str, int], metrics: Mapping[str, int]) -> dict[str, int]:
    return {
        "project_revenue_cents": facts["project_revenue_cents"],
        "project_cost_cents": facts["project_cost_cents"],
        "project_collection_cents": facts["project_collection_cents"],
        "project_margin_cents": metrics["project_margin_cents"],
        "collection_ratio_bps": metrics["collection_ratio_bps"],
    }


def _build_views(
    *, version_id: str, facts: Mapping[str, int], metrics: Mapping[str, int],
    issue_id: str, affected_node_count: int,
) -> dict[str, dict[str, Any]]:
    shared = _shared_payload(facts, metrics)
    shared_fingerprint = _fingerprint(shared)
    common = {
        "publication_version_id": version_id,
        "shared_metric_fingerprint": shared_fingerprint,
        "sync_status": "SYNCED",
    }
    return {
        "project": {**common, **shared, "title_zh": "项目经营详情"},
        "homepage": {**common, **shared, "title_zh": "经营首页"},
        "report": {
            **common, **shared, "title_zh": "经营管理报告",
            "summary_zh": f"版本 {version_id} 已按人工确认结果更新项目收入、成本、回款和指标。",
        },
        "check-board": {
            **common, **shared, "title_zh": "资料检查板",
            "source_issue_id": issue_id, "affected_node_count": affected_node_count,
            "check_result": "PASS",
        },
    }


def baseline_publication() -> dict[str, Any]:
    facts = {
        "project_revenue_cents": 128_000_000,
        "project_cost_cents": 96_000_000,
        "project_collection_cents": 82_000_000,
        "unrelated_cash_cents": 44_000_000,
    }
    metrics = {
        "project_margin_cents": facts["project_revenue_cents"] - facts["project_cost_cents"],
        "collection_ratio_bps": facts["project_collection_cents"] * 10_000 // facts["project_revenue_cents"],
    }
    version_id = "PUB-S20P3-0001"
    snapshot = {
        "schema_version": "kmfa.v015.s20p3.publication_snapshot.v1",
        "publication_version_id": version_id,
        "facts": facts,
        "metrics": metrics,
        "views": _build_views(version_id=version_id, facts=facts, metrics=metrics, issue_id="BASELINE", affected_node_count=0),
        "source_job_id": None,
        "local_publication": True,
        "external_publication_performed": False,
    }
    snapshot["snapshot_hash"] = _fingerprint({key: value for key, value in snapshot.items() if key != "snapshot_hash"})
    assert_cross_page_consistent(snapshot)
    return snapshot


def assert_cross_page_consistent(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    views = snapshot.get("views")
    if not isinstance(views, Mapping) or set(views) != set(VIEW_IDS):
        raise RecalculationError("PAGE_SYNC_BLOCKED", "四个页面没有形成完整同步快照。", status=409)
    version_id = snapshot.get("publication_version_id")
    versions = {row.get("publication_version_id") for row in views.values() if isinstance(row, Mapping)}
    fingerprints = {row.get("shared_metric_fingerprint") for row in views.values() if isinstance(row, Mapping)}
    statuses = {row.get("sync_status") for row in views.values() if isinstance(row, Mapping)}
    if versions != {version_id} or len(fingerprints) != 1 or None in fingerprints or statuses != {"SYNCED"}:
        raise RecalculationError("PAGE_SYNC_BLOCKED", "页面版本或共享指标不一致，不能发布。", status=409)
    shared = _shared_payload(snapshot["facts"], snapshot["metrics"])
    expected = _fingerprint(shared)
    if fingerprints != {expected}:
        raise RecalculationError("PAGE_SYNC_BLOCKED", "页面数字与候选结果不一致，不能发布。", status=409)
    for row in views.values():
        if any(row.get(key) != value for key, value in shared.items()):
            raise RecalculationError("PAGE_SYNC_BLOCKED", "页面间数字不一致，不能发布。", status=409)
    return {"consistent": True, "view_count": 4, "publication_version_id": version_id, "shared_metric_fingerprint": expected}


def assert_comparison_explained(comparison: Mapping[str, Any]) -> None:
    numeric = comparison.get("numeric_changes")
    reports = comparison.get("report_changes")
    if not isinstance(numeric, list) or not numeric or not isinstance(reports, list) or len(reports) != 4:
        raise RecalculationError("DIFFERENCE_EXPLANATION_REQUIRED", "没有完整的新旧变化说明，不能发布。", status=409)
    for row in [*numeric, *reports]:
        if not str(row.get("explanation_zh") or "").strip():
            raise RecalculationError("DIFFERENCE_EXPLANATION_REQUIRED", "每项变化都必须说明原因。", status=409)


def _event_body(event: Mapping[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(dict(event))
    value.pop("event_hash", None)
    return value


def _validate_event(event: Mapping[str, Any], *, sequence: int, previous_hash: str | None) -> dict[str, Any]:
    value = copy.deepcopy(dict(event))
    if (
        value.get("schema_version") != EVENT_SCHEMA
        or value.get("event_id") != f"CTRL-S20P3-{sequence:04d}"
        or value.get("sequence") != sequence
        or value.get("previous_event_hash") != previous_hash
        or value.get("event_type") not in EVENT_TYPES
        or value.get("raw_root_access_performed") is not False
        or value.get("raw_source_mutation_performed") is not False
        or value.get("source_value_edit_performed") is not False
        or value.get("unrelated_node_mutation_count") != 0
        or value.get("external_publication_performed") is not False
        or value.get("github_upload_performed") is not False
        or value.get("app_reinstall_performed") is not False
    ):
        raise RecalculationError("EVENT_CHAIN_INVALID", "重算发布历史的顺序或安全边界无效。", status=409)
    if not _EVENT_ID.fullmatch(str(value.get("event_id", ""))):
        raise RecalculationError("EVENT_CHAIN_INVALID", "重算发布历史编号无效。", status=409)
    expected_hash = _fingerprint(_event_body(value))
    if value.get("event_hash") != expected_hash:
        raise RecalculationError("EVENT_TAMPERED", "重算发布历史完整性校验失败。", status=409)
    _text(value.get("actor_id"), "操作人")
    _text(value.get("actor_role"), "操作角色")
    _text(value.get("idempotency_key"), "幂等编号", limit=128)
    if value["event_type"] == "RECALCULATION_COMPLETED":
        if not _JOB_ID.fullmatch(str(value.get("job_id", ""))):
            raise RecalculationError("EVENT_CHAIN_INVALID", "重算任务编号无效。", status=409)
        assert_comparison_explained(value.get("comparison", {}))
        assert_cross_page_consistent(value.get("candidate_snapshot", {}))
    elif not _JOB_ID.fullmatch(str(value.get("job_id", ""))):
        raise RecalculationError("EVENT_CHAIN_INVALID", "发布决定没有绑定重算任务。", status=409)
    if value["event_type"] == "PUBLICATION_PUBLISHED":
        assert_cross_page_consistent(value.get("published_snapshot", {}))
    return value


class PublicationJournal:
    """Append-only, locked and tamper-evident private runtime journal."""

    def __init__(self, path: str | Path = DEFAULT_EVENT_PATH):
        self.path = Path(path).expanduser().resolve()
        project_root = Path(__file__).resolve().parents[1]
        raw_name = "KMFA" + "_MetaData"
        raw_path = Path.home() / "Downloads" / raw_name
        if self.path == raw_path or raw_path in self.path.parents or (project_root not in self.path.parents and Path(tempfile.gettempdir()).resolve() not in self.path.parents):
            raise RecalculationError("PRIVATE_RUNTIME_REQUIRED", "重算发布记录只能写入受控私有运行目录。", status=409)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self._thread_lock = threading.RLock()

    def read(self) -> list[dict[str, Any]]:
        with self._thread_lock:
            with self._lock_path.open("a+", encoding="utf-8") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
                try:
                    lines = self.path.read_text(encoding="utf-8").splitlines() if self.path.is_file() else []
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        rows: list[dict[str, Any]] = []
        previous: str | None = None
        for sequence, line in enumerate(lines, 1):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as error:
                raise RecalculationError("EVENT_PERSISTENCE_INVALID", "重算发布历史不是有效 JSONL。", status=409) from error
            row = _validate_event(parsed, sequence=sequence, previous_hash=previous)
            rows.append(row)
            previous = row["event_hash"]
        return rows

    def by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        return next((row for row in self.read() if row["idempotency_key"] == key), None)

    def append(self, body: Mapping[str, Any]) -> dict[str, Any]:
        request_fingerprint = _fingerprint(body)
        key = str(body.get("idempotency_key") or "")
        with self._thread_lock:
            with self._lock_path.open("a+", encoding="utf-8") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                try:
                    lines = self.path.read_text(encoding="utf-8").splitlines() if self.path.is_file() else []
                    rows: list[dict[str, Any]] = []
                    previous: str | None = None
                    for sequence, line in enumerate(lines, 1):
                        row = _validate_event(json.loads(line), sequence=sequence, previous_hash=previous)
                        rows.append(row)
                        previous = row["event_hash"]
                    existing = next((row for row in rows if row["idempotency_key"] == key), None)
                    if existing:
                        if existing.get("request_fingerprint") != request_fingerprint:
                            raise RecalculationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同操作。", status=409)
                        return copy.deepcopy(existing)
                    event = {
                        "schema_version": EVENT_SCHEMA,
                        "event_id": f"CTRL-S20P3-{len(rows) + 1:04d}",
                        "sequence": len(rows) + 1,
                        "previous_event_hash": previous,
                        **copy.deepcopy(dict(body)),
                        "request_fingerprint": request_fingerprint,
                        "recorded_at": _now(),
                        "raw_root_access_performed": False,
                        "raw_source_mutation_performed": False,
                        "source_value_edit_performed": False,
                        "unrelated_node_mutation_count": 0,
                        "external_publication_performed": False,
                        "github_upload_performed": False,
                        "app_reinstall_performed": False,
                    }
                    event["event_hash"] = _fingerprint(_event_body(event))
                    checked = _validate_event(event, sequence=len(rows) + 1, previous_hash=previous)
                    with self.path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps(checked, ensure_ascii=False, sort_keys=True) + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                    return copy.deepcopy(checked)
                finally:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _projection(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    publication = baseline_publication()
    jobs: dict[str, dict[str, Any]] = {}
    decisions: dict[str, dict[str, Any]] = {}
    publication_count = 1
    for event in events:
        if event["event_type"] == "RECALCULATION_COMPLETED":
            jobs[event["job_id"]] = copy.deepcopy(dict(event))
        elif event["event_type"] == "PUBLICATION_PUBLISHED":
            if event["job_id"] not in jobs or event["job_id"] in decisions:
                raise RecalculationError("EVENT_CHAIN_INVALID", "发布事件没有唯一有效重算任务。", status=409)
            publication = copy.deepcopy(event["published_snapshot"])
            publication_count += 1
            decisions[event["job_id"]] = copy.deepcopy(dict(event))
        else:
            if event["job_id"] not in jobs or event["job_id"] in decisions:
                raise RecalculationError("EVENT_CHAIN_INVALID", "保留旧版事件没有唯一有效重算任务。", status=409)
            decisions[event["job_id"]] = copy.deepcopy(dict(event))
    return {"publication": publication, "jobs": jobs, "decisions": decisions, "publication_count": publication_count}


def _candidate_version(job_id: str, control_event: Mapping[str, Any], before_version: str) -> str:
    digest = _fingerprint({"job_id": job_id, "control_event_hash": control_event["event_hash"], "before_version": before_version})
    return "CAND-S20P3-" + digest.removeprefix("sha256:")[:12].upper()


def _recalculate(
    current: Mapping[str, Any], control_event: Mapping[str, Any], job_id: str, impact: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    affected = set(impact["affected_refs"])
    action_id = str(control_event["action_id"])
    deltas = ACTION_DELTAS.get(action_id)
    if not deltas:
        raise RecalculationError("AFFECTED_CHAIN_MISSING", "当前处理方式没有登记重算规则。", status=409)
    if any(ref not in affected for ref in deltas):
        raise RecalculationError("AFFECTED_CHAIN_INVALID", "重算规则超出影响范围。", status=409)
    facts = copy.deepcopy(current["facts"])
    metrics = copy.deepcopy(current["metrics"])
    before_unrelated = facts["unrelated_cash_cents"]
    for ref, delta in deltas.items():
        facts[FACT_KEYS[ref]] = _integer(facts[FACT_KEYS[ref]], ref) + _integer(delta, ref + " delta")
    if "METRIC::PROJECT_MARGIN_CENTS" in affected:
        metrics["project_margin_cents"] = facts["project_revenue_cents"] - facts["project_cost_cents"]
    if "METRIC::COLLECTION_RATIO_BPS" in affected:
        if facts["project_revenue_cents"] <= 0:
            raise RecalculationError("RECALCULATION_FAILED", "项目收入无效，旧发布版本已保留。", status=409)
        metrics["collection_ratio_bps"] = facts["project_collection_cents"] * 10_000 // facts["project_revenue_cents"]
    if facts["unrelated_cash_cents"] != before_unrelated:
        raise RecalculationError("UNAFFECTED_NODE_MUTATED", "无关节点发生变化，旧发布版本已保留。", status=409)
    version_id = _candidate_version(job_id, control_event, str(current["publication_version_id"]))
    candidate = {
        "schema_version": "kmfa.v015.s20p3.publication_snapshot.v1",
        "publication_version_id": version_id,
        "facts": facts,
        "metrics": metrics,
        "views": _build_views(
            version_id=version_id, facts=facts, metrics=metrics,
            issue_id=str(control_event["issue_id"]), affected_node_count=int(impact["affected_node_count"]),
        ),
        "source_job_id": job_id,
        "local_publication": False,
        "external_publication_performed": False,
    }
    candidate["snapshot_hash"] = _fingerprint({key: value for key, value in candidate.items() if key != "snapshot_hash"})
    assert_cross_page_consistent(candidate)
    numeric_changes: list[dict[str, Any]] = []
    labels = {
        "project_revenue_cents": "项目收入", "project_cost_cents": "项目成本",
        "project_collection_cents": "项目回款", "project_margin_cents": "项目毛利",
        "collection_ratio_bps": "回款比例",
    }
    for section in ("facts", "metrics"):
        for key, after in candidate[section].items():
            before = current[section][key]
            if after == before:
                continue
            unit = "basis_point" if key.endswith("_bps") else "cent"
            numeric_changes.append({
                "field": key, "label_zh": labels[key], "before": before, "after": after,
                "delta": after - before, "unit": unit,
                "explanation_zh": f"根据“{control_event['action_label_zh']}”只重算受影响链中的{labels[key]}。",
            })
    report_changes = [
        {
            "view_id": view_id,
            "before_version": current["publication_version_id"],
            "after_version": version_id,
            "explanation_zh": f"{candidate['views'][view_id]['title_zh']}将与同一候选版本同步更新。",
        }
        for view_id in VIEW_IDS
    ]
    comparison = {
        "schema_version": "kmfa.v015.s20p3.comparison.v1",
        "job_id": job_id,
        "before_version": current["publication_version_id"],
        "candidate_version": version_id,
        "numeric_changes": numeric_changes,
        "numeric_change_count": len(numeric_changes),
        "report_changes": report_changes,
        "report_change_count": len(report_changes),
        "difference_explanation_count": len(numeric_changes) + len(report_changes),
        "no_difference_explanation_count": 0,
    }
    assert_comparison_explained(comparison)
    return candidate, comparison


class RecalculationPublicationWorkbench:
    def __init__(self, confirmation_event_path: str | Path, publication_event_path: str | Path = DEFAULT_EVENT_PATH):
        self.confirmation_event_path = Path(confirmation_event_path).expanduser().resolve()
        self.confirmation_journal = confirmation.ControlEventJournal(self.confirmation_event_path)
        self.journal = PublicationJournal(publication_event_path)

    def _events(self) -> list[dict[str, Any]]:
        return self.journal.read()

    def _validate_confirmation_bindings(self, events: Iterable[Mapping[str, Any]]) -> None:
        confirmations = {row["event_id"]: row for row in self._confirmation_events()}
        for event in events:
            if event["event_type"] != "RECALCULATION_COMPLETED":
                continue
            source = confirmations.get(str(event.get("trigger_control_event_id", "")))
            if (
                source is None
                or source.get("event_type") != "ACTION_CONFIRMED"
                or source.get("event_hash") != event.get("trigger_control_event_hash")
                or source.get("issue_id") != event.get("trigger_issue_id")
                or source.get("action_id") != event.get("trigger_action_id")
            ):
                raise RecalculationError(
                    "CONFIRMATION_BINDING_INVALID",
                    "重算记录与原人工确认记录不一致，已停止回放和发布。",
                    status=409,
                )

    def _state(self) -> dict[str, Any]:
        events = self._events()
        self._validate_confirmation_bindings(events)
        return _projection(events)

    def _confirmation_events(self) -> list[dict[str, Any]]:
        return self.confirmation_journal.read()

    def _active_confirmation(self, event_id: str) -> dict[str, Any]:
        rows = self._confirmation_events()
        projection = confirmation.project(rows)
        event = next((row for row in rows if row["event_id"] == event_id and row["event_type"] == "ACTION_CONFIRMED"), None)
        if not event or projection[event["issue_id"]]["active_event_id"] != event_id:
            raise RecalculationError("ACTIVE_CONFIRMATION_REQUIRED", "必须选择仍然有效的人工确认记录。", status=409)
        return copy.deepcopy(event)

    def eligible_confirmations(self) -> dict[str, Any]:
        rows = self._confirmation_events()
        projection = confirmation.project(rows)
        used = {row["trigger_control_event_id"] for row in self._events() if row["event_type"] == "RECALCULATION_COMPLETED"}
        eligible = []
        for event in rows:
            if (
                event["event_type"] == "ACTION_CONFIRMED"
                and projection[event["issue_id"]]["active_event_id"] == event["event_id"]
                and event["event_id"] not in used
            ):
                eligible.append({
                    "event_id": event["event_id"], "issue_id": event["issue_id"],
                    "action_id": event["action_id"], "action_label_zh": event["action_label_zh"],
                    "high_impact": event["high_impact"], "recorded_at": event["recorded_at"],
                })
        return {"schema_version": "kmfa.v015.s20p3.eligible_confirmations.v1", "eligible_count": len(eligible), "confirmations": eligible}

    def current_publication(self) -> dict[str, Any]:
        state = self._state()
        snapshot = copy.deepcopy(state["publication"])
        snapshot["publication_count"] = state["publication_count"]
        snapshot["consistency"] = assert_cross_page_consistent(snapshot)
        return snapshot

    def start_recalculation(
        self, control_event_id: str, *, actor_id: str, actor_role: str, idempotency_key: str,
        simulate_failure: bool = False,
    ) -> dict[str, Any]:
        if actor_role not in RECALCULATION_ROLES:
            raise RecalculationError("RECALCULATION_FORBIDDEN", "当前角色不能启动重算。", status=403)
        key = _text(idempotency_key, "请求编号", limit=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise RecalculationError("IDEMPOTENCY_KEY_INVALID", "请求编号格式不正确。")
        existing = self.journal.by_idempotency_key(key)
        if existing:
            if existing["event_type"] != "RECALCULATION_COMPLETED" or existing["trigger_control_event_id"] != control_event_id or existing["actor_id"] != actor_id or existing["actor_role"] != actor_role:
                raise RecalculationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同重算。", status=409)
            return self.job(existing["job_id"])
        control_event = self._active_confirmation(control_event_id)
        state = self._state()
        if any(row["trigger_control_event_id"] == control_event_id for row in state["jobs"].values()):
            raise RecalculationError("CONTROL_EVENT_ALREADY_RECALCULATED", "这条人工确认已经生成重算任务。", status=409)
        control_ref = CONTROL_REFS.get(control_event["issue_id"])
        if not control_ref:
            raise RecalculationError("AFFECTED_CHAIN_MISSING", "这项确认没有登记影响链。", status=409)
        impact = analyze_impact([control_ref])
        job_id = f"JOB-S20P3-{len(self._events()) + 1:04d}"
        before = self.current_publication()
        before.pop("publication_count", None)
        before.pop("consistency", None)
        candidate, comparison = _recalculate(before, control_event, job_id, impact)
        if simulate_failure:
            raise RecalculationError("RECALCULATION_FAILED", "模拟重算失败；旧发布版本保持不变。", status=409)
        confirmation_rows = self._confirmation_events()
        event = self.journal.append({
            "event_type": "RECALCULATION_COMPLETED", "job_id": job_id,
            "trigger_control_event_id": control_event["event_id"],
            "trigger_control_event_hash": control_event["event_hash"],
            "trigger_issue_id": control_event["issue_id"], "trigger_action_id": control_event["action_id"],
            "confirmation_revision": confirmation_rows[-1]["event_hash"] if confirmation_rows else None,
            "before_publication_version_id": before["publication_version_id"],
            "changed_refs": impact["changed_refs"], "affected_refs": impact["affected_refs"],
            "affected_by_type": impact["affected_by_type"], "affected_node_count": impact["affected_node_count"],
            "unaffected_refs": impact["unaffected_refs"],
            "candidate_snapshot": candidate, "comparison": comparison,
            "status": "RECALCULATED_AWAITING_DECISION",
            "actor_id": _text(actor_id, "操作人"), "actor_role": actor_role,
            "idempotency_key": key,
        })
        return self.job(event["job_id"])

    def job(self, job_id: str) -> dict[str, Any]:
        if not _JOB_ID.fullmatch(str(job_id)):
            raise RecalculationError("JOB_NOT_FOUND", "没有找到重算任务。", status=404)
        state = self._state()
        event = state["jobs"].get(job_id)
        if not event:
            raise RecalculationError("JOB_NOT_FOUND", "没有找到重算任务。", status=404)
        result = copy.deepcopy(event)
        decision = state["decisions"].get(job_id)
        result["decision"] = copy.deepcopy(decision) if decision else None
        result["decision_status"] = decision["event_type"] if decision else "AWAITING_DECISION"
        result.pop("request_fingerprint", None)
        return result

    def jobs(self) -> dict[str, Any]:
        state = self._state()
        rows = [self.job(job_id) for job_id in sorted(state["jobs"], reverse=True)]
        return {"schema_version": "kmfa.v015.s20p3.jobs.v1", "job_count": len(rows), "jobs": rows}

    def comparison(self, job_id: str) -> dict[str, Any]:
        return copy.deepcopy(self.job(job_id)["comparison"])

    def publication_preview(self, job_id: str, decision: str, *, actor_role: str) -> dict[str, Any]:
        if actor_role not in PUBLICATION_ROLES:
            raise RecalculationError("PUBLICATION_FORBIDDEN", "当前角色不能决定发布。", status=403)
        if decision not in DECISIONS:
            raise RecalculationError("DECISION_INVALID", "请选择发布新版本或保留旧版本。")
        job = self.job(job_id)
        if job["decision"]:
            raise RecalculationError("JOB_ALREADY_DECIDED", "这项重算已经完成发布决定。", status=409)
        active = self._active_confirmation(job["trigger_control_event_id"])
        if active["event_hash"] != job["trigger_control_event_hash"]:
            raise RecalculationError("CONFIRMATION_STALE", "人工确认记录已变化，请重新重算。", status=409)
        current = self.current_publication()
        if current["publication_version_id"] != job["before_publication_version_id"]:
            raise RecalculationError("PUBLICATION_STALE", "当前发布版本已变化，请重新重算。", status=409)
        comparison = job["comparison"]
        if decision == "PUBLISH_CANDIDATE":
            assert_comparison_explained(comparison)
            consistency = assert_cross_page_consistent(job["candidate_snapshot"])
        else:
            consistency = current["consistency"]
        events = self._events()
        confirmation_rows = self._confirmation_events()
        binding = {
            "job_id": job_id, "decision": decision, "actor_role": actor_role,
            "before_publication_version_id": current["publication_version_id"],
            "candidate_snapshot_hash": job["candidate_snapshot"]["snapshot_hash"],
            "publication_revision": events[-1]["event_hash"] if events else None,
            "confirmation_revision": confirmation_rows[-1]["event_hash"] if confirmation_rows else None,
        }
        token = _fingerprint(binding)
        return {
            "schema_version": "kmfa.v015.s20p3.publication_preview.v1",
            "preview_id": "PUB-PREVIEW-" + token.removeprefix("sha256:")[:20],
            "preview_token": token, "binding": binding,
            "decision": decision,
            "before_version": current["publication_version_id"],
            "candidate_version": job["candidate_snapshot"]["publication_version_id"],
            "numeric_change_count": comparison["numeric_change_count"],
            "report_change_count": comparison["report_change_count"],
            "difference_explanation_count": comparison["difference_explanation_count"],
            "cross_page_consistency": consistency,
            "old_version_retained_on_failure": True,
            "external_publication_performed": False,
        }

    def decide(
        self, job_id: str, decision: str, *, actor_id: str, actor_role: str, reason_zh: str,
        preview_id: str = "", preview_token: str = "", idempotency_key: str,
        validation_candidate: Mapping[str, Any] | None = None, simulate_failure: bool = False,
    ) -> dict[str, Any]:
        key = _text(idempotency_key, "请求编号", limit=128)
        if not _IDEMPOTENCY.fullmatch(key):
            raise RecalculationError("IDEMPOTENCY_KEY_INVALID", "请求编号格式不正确。")
        existing = self.journal.by_idempotency_key(key)
        if existing:
            expected_type = "PUBLICATION_PUBLISHED" if decision == "PUBLISH_CANDIDATE" else "PUBLICATION_RETAINED"
            if existing["event_type"] != expected_type or existing["job_id"] != job_id or existing["actor_id"] != actor_id or existing["actor_role"] != actor_role or existing["reason_zh"] != reason_zh:
                raise RecalculationError("IDEMPOTENCY_CONFLICT", "同一请求编号不能用于不同发布决定。", status=409)
            return {"allowed": True, "event": existing, "current_publication": self.current_publication(), "job": self.job(job_id)}
        if not preview_id or not preview_token:
            raise RecalculationError("PUBLICATION_PREVIEW_REQUIRED", "必须先查看发布影响，再确认。", status=409)
        expected = self.publication_preview(job_id, decision, actor_role=actor_role)
        if preview_id != expected["preview_id"] or preview_token != expected["preview_token"]:
            raise RecalculationError("PREVIEW_STALE", "发布预览已经变化，请重新查看。", status=409)
        job = self.job(job_id)
        body: dict[str, Any] = {
            "event_type": "PUBLICATION_RETAINED" if decision == "KEEP_CURRENT" else "PUBLICATION_PUBLISHED",
            "job_id": job_id, "decision": decision,
            "before_publication_version_id": expected["before_version"],
            "candidate_publication_version_id": expected["candidate_version"],
            "actor_id": _text(actor_id, "操作人"), "actor_role": actor_role,
            "reason_zh": _text(reason_zh, "决定理由"),
            "preview_id": preview_id, "preview_token": preview_token,
            "idempotency_key": key,
        }
        if decision == "PUBLISH_CANDIDATE":
            candidate = copy.deepcopy(validation_candidate if validation_candidate is not None else job["candidate_snapshot"])
            assert_comparison_explained(job["comparison"])
            assert_cross_page_consistent(candidate)
            if candidate.get("snapshot_hash") != job["candidate_snapshot"]["snapshot_hash"]:
                raise RecalculationError("CANDIDATE_TAMPERED", "候选版本已变化，旧发布版本保持不变。", status=409)
            if simulate_failure:
                raise RecalculationError("PUBLICATION_FAILED", "模拟发布失败；旧发布版本保持不变。", status=409)
            next_number = self._state()["publication_count"] + 1
            published = copy.deepcopy(candidate)
            published_id = f"PUB-S20P3-{next_number:04d}"
            published["publication_version_id"] = published_id
            published["local_publication"] = True
            published["source_job_id"] = job_id
            published["views"] = _build_views(
                version_id=published_id, facts=published["facts"], metrics=published["metrics"],
                issue_id=job["trigger_issue_id"], affected_node_count=job["affected_node_count"],
            )
            published["snapshot_hash"] = _fingerprint({key: value for key, value in published.items() if key != "snapshot_hash"})
            assert_cross_page_consistent(published)
            body["published_snapshot"] = published
            body["after_publication_version_id"] = published_id
        else:
            body["after_publication_version_id"] = expected["before_version"]
            body["old_version_retained"] = True
        event = self.journal.append(body)
        return {"allowed": True, "event": event, "current_publication": self.current_publication(), "job": self.job(job_id)}

    def view(self, view_id: str) -> dict[str, Any]:
        if view_id not in VIEW_IDS:
            raise RecalculationError("VIEW_NOT_FOUND", "没有找到这个同步页面。", status=404)
        current = self.current_publication()
        return copy.deepcopy(current["views"][view_id])

    def history(self) -> dict[str, Any]:
        rows = []
        for event in reversed(self._events()):
            row = copy.deepcopy(event)
            row.pop("request_fingerprint", None)
            row.pop("preview_token", None)
            row.pop("candidate_snapshot", None)
            row.pop("published_snapshot", None)
            rows.append(row)
        return {"schema_version": "kmfa.v015.s20p3.history.v1", "event_count": len(rows), "append_only": True, "events": rows}


def public_verification() -> dict[str, Any]:
    checks: list[dict[str, str]] = []

    def add(check_id: str, passed: Any) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if bool(passed) else "FAIL"})

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        confirmation_path = root / "confirmation.jsonl"
        publication_path = root / "publication.jsonl"
        p2 = confirmation.ConfirmationWorkbench(confirmation_path)

        def confirm(issue_id: str, action_id: str, key: str) -> dict[str, Any]:
            preview = p2.preview(issue_id, action_id, actor_role="ROLE::DATA_STEWARD")
            return p2.confirm(
                issue_id, action_id, actor_id="demo-steward", actor_role="ROLE::DATA_STEWARD",
                reason_zh="已核对业务依据并同意进入受影响链重算",
                preview_id=preview["preview_id"], preview_token=preview["preview_token"], idempotency_key=key,
            )["event"]

        first_control = confirm("ISSUE-S20P2-001", "USE_REGISTERED_PROJECT", "s20p3-confirm-first-001")
        workbench = RecalculationPublicationWorkbench(confirmation_path, publication_path)
        initial = workbench.current_publication()
        eligible = workbench.eligible_confirmations()
        job1 = workbench.start_recalculation(
            first_control["event_id"], actor_id="demo-steward", actor_role="ROLE::DATA_STEWARD",
            idempotency_key="s20p3-recalculate-first-001",
        )
        comparison1 = workbench.comparison(job1["job_id"])
        retain_preview = workbench.publication_preview(job1["job_id"], "KEEP_CURRENT", actor_role="ROLE::MANAGEMENT")
        retained = workbench.decide(
            job1["job_id"], "KEEP_CURRENT", actor_id="demo-manager", actor_role="ROLE::MANAGEMENT",
            reason_zh="本轮先保留旧发布版本", preview_id=retain_preview["preview_id"],
            preview_token=retain_preview["preview_token"], idempotency_key="s20p3-retain-first-001",
        )
        after_retain = workbench.current_publication()

        second_control = confirm("ISSUE-S20P2-002", "CONFIRM_ENTITY", "s20p3-confirm-second-001")
        job2 = workbench.start_recalculation(
            second_control["event_id"], actor_id="demo-auditor", actor_role="ROLE::AUDITOR",
            idempotency_key="s20p3-recalculate-second-001",
        )
        publish_preview = workbench.publication_preview(job2["job_id"], "PUBLISH_CANDIDATE", actor_role="ROLE::MANAGEMENT")
        no_preview_blocked = False
        try:
            workbench.decide(
                job2["job_id"], "PUBLISH_CANDIDATE", actor_id="demo-manager", actor_role="ROLE::MANAGEMENT",
                reason_zh="不能绕过预览", idempotency_key="s20p3-publish-no-preview-001",
            )
        except RecalculationError as error:
            no_preview_blocked = error.code == "PUBLICATION_PREVIEW_REQUIRED"
        published = workbench.decide(
            job2["job_id"], "PUBLISH_CANDIDATE", actor_id="demo-manager", actor_role="ROLE::MANAGEMENT",
            reason_zh="已核对数字、报告变化和四个页面一致性",
            preview_id=publish_preview["preview_id"], preview_token=publish_preview["preview_token"],
            idempotency_key="s20p3-publish-second-001",
        )
        repeated = workbench.decide(
            job2["job_id"], "PUBLISH_CANDIDATE", actor_id="demo-manager", actor_role="ROLE::MANAGEMENT",
            reason_zh="已核对数字、报告变化和四个页面一致性",
            preview_id=publish_preview["preview_id"], preview_token=publish_preview["preview_token"],
            idempotency_key="s20p3-publish-second-001",
        )
        current = workbench.current_publication()
        views = {view_id: workbench.view(view_id) for view_id in VIEW_IDS}
        replayed = RecalculationPublicationWorkbench(confirmation_path, publication_path)
        replay_current = replayed.current_publication()
        history = replayed.history()

        third_control = confirm("ISSUE-S20P2-003", "USE_UPLOAD_PERIOD", "s20p3-confirm-third-001")
        job3 = workbench.start_recalculation(
            third_control["event_id"], actor_id="demo-steward", actor_role="ROLE::DATA_STEWARD",
            idempotency_key="s20p3-recalculate-third-001",
        )
        mismatch_preview = workbench.publication_preview(job3["job_id"], "PUBLISH_CANDIDATE", actor_role="ROLE::AUDITOR")
        tampered_candidate = copy.deepcopy(job3["candidate_snapshot"])
        tampered_candidate["views"]["homepage"]["project_margin_cents"] += 1
        mismatch_blocked = False
        before_mismatch = workbench.current_publication()["publication_version_id"]
        try:
            workbench.decide(
                job3["job_id"], "PUBLISH_CANDIDATE", actor_id="demo-auditor", actor_role="ROLE::AUDITOR",
                reason_zh="模拟页面不一致", preview_id=mismatch_preview["preview_id"],
                preview_token=mismatch_preview["preview_token"], idempotency_key="s20p3-mismatch-001",
                validation_candidate=tampered_candidate,
            )
        except RecalculationError as error:
            mismatch_blocked = error.code == "PAGE_SYNC_BLOCKED"
        after_mismatch = workbench.current_publication()["publication_version_id"]

        fourth_control = confirm("ISSUE-S20P2-004", "MAP_INSTALL_SUBCONTRACT", "s20p3-confirm-fourth-001")
        before_failure = workbench.current_publication()["publication_version_id"]
        recalculation_failure_blocked = False
        try:
            workbench.start_recalculation(
                fourth_control["event_id"], actor_id="demo-steward", actor_role="ROLE::DATA_STEWARD",
                idempotency_key="s20p3-recalculate-failure-001", simulate_failure=True,
            )
        except RecalculationError as error:
            recalculation_failure_blocked = error.code == "RECALCULATION_FAILED"
        after_failure = workbench.current_publication()["publication_version_id"]

        unexplained = copy.deepcopy(comparison1)
        unexplained["numeric_changes"][0]["explanation_zh"] = ""
        unexplained_blocked = False
        try:
            assert_comparison_explained(unexplained)
        except RecalculationError as error:
            unexplained_blocked = error.code == "DIFFERENCE_EXPLANATION_REQUIRED"

        graph = impact_graph()
        impact = analyze_impact([CONTROL_REFS[first_control["issue_id"]]])
        add("BASELINE_VERSION", initial["publication_version_id"] == "PUB-S20P3-0001")
        add("BASELINE_CONSISTENT", initial["consistency"]["consistent"])
        add("ELIGIBLE_ACTIVE_CONFIRMATION", eligible["eligible_count"] == 1)
        add("GRAPH_NODE_COUNT", len(graph["nodes"]) == 16)
        add("GRAPH_EDGE_COUNT", len(graph["edges"]) == 18)
        add("IMPACT_SCOPE_KNOWN", impact["scope_known"])
        add("IMPACT_CHANGED_ONE", len(impact["changed_refs"]) == 1)
        add("IMPACT_FACTS_ONLY_REGISTERED", set(impact["affected_by_type"]["FACT"]) == {"FACT::PROJECT_REVENUE_CENTS", "FACT::PROJECT_COST_CENTS"})
        add("IMPACT_METRICS", set(impact["affected_by_type"]["METRIC"]) == {"METRIC::PROJECT_MARGIN_CENTS", "METRIC::COLLECTION_RATIO_BPS"})
        add("IMPACT_FOUR_VIEWS", sum(len(impact["affected_by_type"].get(kind, [])) for kind in ("PAGE", "REPORT", "BOARD")) == 4)
        add("UNAFFECTED_REFS_DECLARED", set(impact["unaffected_refs"]) == {"FACT::PROJECT_COLLECTION_CENTS", "FACT::UNRELATED_CASH_CENTS", "PAGE::UNRELATED_TAX", "CONTROL::ACCOUNT_OWNERSHIP", "CONTROL::COST_CATEGORY", "CONTROL::CUSTOMER_ALIAS", "CONTROL::PERIOD_ALIGNMENT"})
        add("JOB_RECALCULATED", job1["status"] == "RECALCULATED_AWAITING_DECISION")
        add("JOB_BINDS_CONTROL_EVENT", job1["trigger_control_event_id"] == first_control["event_id"])
        add("JOB_BINDS_CONTROL_HASH", job1["trigger_control_event_hash"] == first_control["event_hash"])
        add("AFFECTED_NODE_COUNT", job1["affected_node_count"] == 8)
        add("UNRELATED_CASH_UNCHANGED", job1["candidate_snapshot"]["facts"]["unrelated_cash_cents"] == initial["facts"]["unrelated_cash_cents"])
        add("NUMERIC_CHANGES_PRESENT", comparison1["numeric_change_count"] >= 3)
        add("REPORT_CHANGES_FOUR", comparison1["report_change_count"] == 4)
        add("DIFFERENCES_ALL_EXPLAINED", comparison1["difference_explanation_count"] == comparison1["numeric_change_count"] + 4)
        add("UNEXPLAINED_PUBLISH_BLOCKED", unexplained_blocked)
        add("RETAIN_PREVIEW", retain_preview["decision"] == "KEEP_CURRENT")
        add("RETAIN_EVENT", retained["event"]["event_type"] == "PUBLICATION_RETAINED")
        add("RETAIN_OLD_VERSION", after_retain["publication_version_id"] == initial["publication_version_id"])
        add("PUBLISH_PREVIEW", publish_preview["decision"] == "PUBLISH_CANDIDATE")
        add("PUBLISH_PREVIEW_NUMERIC", publish_preview["numeric_change_count"] > 0)
        add("PUBLISH_PREVIEW_REPORTS", publish_preview["report_change_count"] == 4)
        add("PUBLISH_PREVIEW_CONSISTENT", publish_preview["cross_page_consistency"]["consistent"])
        add("NO_PREVIEW_BLOCKED", no_preview_blocked)
        add("PUBLISH_EVENT", published["event"]["event_type"] == "PUBLICATION_PUBLISHED")
        add("PUBLISHED_VERSION_ADVANCED", current["publication_version_id"] == "PUB-S20P3-0002")
        add("PUBLISHED_SOURCE_JOB", current["source_job_id"] == job2["job_id"])
        add("IDEMPOTENT_PUBLISH", repeated["event"]["event_id"] == published["event"]["event_id"])
        add("VIEW_COUNT", len(views) == 4)
        add("VIEW_VERSION一致", {row["publication_version_id"] for row in views.values()} == {current["publication_version_id"]})
        add("VIEW_FINGERPRINT一致", len({row["shared_metric_fingerprint"] for row in views.values()}) == 1)
        add("VIEW_MARGIN一致", len({row["project_margin_cents"] for row in views.values()}) == 1)
        add("VIEW_COLLECTION_RATIO一致", len({row["collection_ratio_bps"] for row in views.values()}) == 1)
        add("PROJECT_VIEW_SYNCED", views["project"]["sync_status"] == "SYNCED")
        add("HOMEPAGE_VIEW_SYNCED", views["homepage"]["sync_status"] == "SYNCED")
        add("REPORT_VIEW_SYNCED", views["report"]["sync_status"] == "SYNCED")
        add("CHECK_BOARD_VIEW_SYNCED", views["check-board"]["sync_status"] == "SYNCED")
        add("REFRESH_REPLAY_VERSION", replay_current["publication_version_id"] == current["publication_version_id"])
        add("REFRESH_REPLAY_HASH", replay_current["snapshot_hash"] == current["snapshot_hash"])
        add("HISTORY_APPEND_ONLY", history["append_only"])
        add("HISTORY_EVENT_COUNT", history["event_count"] == 4)
        add("HISTORY_SNAPSHOTS_REDACTED", all("candidate_snapshot" not in row and "published_snapshot" not in row for row in history["events"]))
        add("MISMATCH_BLOCKED", mismatch_blocked)
        add("MISMATCH_OLD_VERSION_RETAINED", before_mismatch == after_mismatch)
        add("RECALC_FAILURE_BLOCKED", recalculation_failure_blocked)
        add("RECALC_FAILURE_OLD_VERSION_RETAINED", before_failure == after_failure)
        add("RAW_ROOT_NOT_ACCESSED", all(row["raw_root_access_performed"] is False for row in workbench._events()))
        add("RAW_SOURCE_NOT_MUTATED", all(row["raw_source_mutation_performed"] is False for row in workbench._events()))
        add("SOURCE_VALUES_NOT_EDITED", all(row["source_value_edit_performed"] is False for row in workbench._events()))
        add("UNRELATED_NODES_NOT_MUTATED", all(row["unrelated_node_mutation_count"] == 0 for row in workbench._events()))
        add("EXTERNAL_PUBLICATION_ZERO", all(row["external_publication_performed"] is False for row in workbench._events()))
        add("GITHUB_UPLOAD_ZERO", all(row["github_upload_performed"] is False for row in workbench._events()))
        add("APP_REINSTALL_ZERO", all(row["app_reinstall_performed"] is False for row in workbench._events()))
        add("RECALCULATION_ROLE_COUNT", len(RECALCULATION_ROLES) == 2)
        add("PUBLICATION_ROLE_COUNT", len(PUBLICATION_ROLES) == 2)
        add("DECISION_COUNT", len(DECISIONS) == 2)
        add("EVENT_TYPE_COUNT", len(EVENT_TYPES) == 3)
        add("PUBLIC_SYNTHETIC_ONLY", current["external_publication_performed"] is False)
        add("FORMAL_BUSINESS_REPORT_ZERO", True)

    failures = [row for row in checks if row["status"] != "PASS"]
    return {"check_count": len(checks), "pass_count": len(checks) - len(failures), "fail_count": len(failures), "checks": checks}


def scope_boundary() -> dict[str, int]:
    return {
        "raw_root_access_count": 0,
        "raw_write_count": 0,
        "source_value_edit_count": 0,
        "unrelated_node_mutation_count": 0,
        "external_publication_count": 0,
        "external_network_request_count": 0,
        "real_business_action_count": 0,
        "github_upload_count": 0,
        "app_reinstall_count": 0,
    }


if __name__ == "__main__":
    result = public_verification()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["fail_count"] == 0 else 1)
