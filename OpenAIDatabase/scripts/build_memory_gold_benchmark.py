#!/usr/bin/env python3
"""Deterministically curate the PAM1.0013 synthetic 160-case Gold dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


DATABASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path("config/evaluation/memory_gold_benchmark_v1.json")
OLD_FROM = "2026-01-01T00:00:00Z"
CUTOVER = "2026-06-01T00:00:00Z"
HISTORICAL_AS_OF = "2026-05-15T12:00:00Z"
CURRENT_AS_OF = "2026-07-16T12:00:00Z"
RECORDED_AS_OF = "2026-07-16T12:05:00Z"

TOPICS = (
    ("output_language", "输出语言", "language mode", "locale-policy", "中文优先并保留 technical English", "English only", "法语优先"),
    ("time_zone", "业务时区", "business timezone", "time-zone", "Asia/Shanghai", "UTC", "Europe/Paris"),
    ("default_branch", "默认分支", "default branch", "branch-head", "main", "master", "release"),
    ("runtime_entry", "运行入口", "runtime entry", "launch-command", "atlasctl", "legacy runner", "manual shell"),
    ("report_cadence", "报告节奏", "report cadence", "report-cycle", "每周一生成", "每周五生成", "每日生成"),
    ("deployment_boundary", "部署边界", "deployment boundary", "publish-scope", "仅 derived public view", "包含 raw archive", "仅本地截图"),
    ("verification_tier", "验证层级", "verification tier", "quality-gate", "security tier", "smoke only", "integration only"),
    ("storage_format", "存储格式", "storage format", "record-format", "canonical JSONL", "SQLite only", "free-form Markdown"),
    ("owner_role", "批准角色", "approval owner", "owner-gate", "privacy owner", "automation bot", "anonymous reviewer"),
    ("source_priority", "来源优先级", "source priority", "evidence-order", "explicit user before inference", "model inference first", "latest timestamp only"),
    ("branch_policy", "分支策略", "branch policy", "change-route", "short-lived candidate branch", "direct main", "persistent feature branch"),
    ("retention_window", "保留窗口", "retention window", "retention-policy", "30 days", "365 days", "no expiry"),
    ("query_limit", "查询上限", "query limit", "result-cap", "20 records", "200 records", "unbounded"),
    ("export_format", "导出格式", "export format", "artifact-type", "redacted Markdown", "raw transcript", "binary dump"),
    ("audit_mode", "审计模式", "audit mode", "inspection-mode", "read-only", "automatic mutation", "best effort"),
    ("sensitivity_class", "敏感度等级", "sensitivity class", "data-class", "public synthetic", "private raw", "credential material"),
    ("release_channel", "发布通道", "release channel", "delivery-route", "trusted settlement", "manual upload", "preview only"),
    ("notification_mode", "通知方式", "notification mode", "alert-route", "owner summary", "broadcast all", "silent"),
    ("build_command", "构建命令", "build command", "build-entry", "reproducible build", "ad-hoc build", "skip build"),
    ("incident_action", "事故首要动作", "incident first action", "incident-route", "stop and escalate", "continue processing", "ignore warning"),
)

NOISE = (
    "背景噪声：unrelated trace marker alpha。",
    "旁注：旧 dashboard 颜色为 blue，与答案无关。",
    "无关日志：cache hit=true；不要把它当作 memory state。",
    "上下文噪声：ticket label=triage-only。",
    "技术旁注：latency sample=12ms，不参与事实选择。",
)

SOURCE_REFS = {
    "extraction": ["longmemeval"],
    "cross_session": ["longmemeval", "locomo"],
    "temporal": ["longmemeval", "locomo"],
    "update": ["longmemeval", "fama"],
    "abstention": ["longmemeval"],
    "forgetting": ["fama"],
    "conflict": ["longmemeval", "fama"],
    "cross_agent": ["locomo", "longmemeval"],
}


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_config_key")
        value[key] = item
    return value


def load_config(database_dir: Path, relative: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    path = relative if relative.is_absolute() else database_dir / relative
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object)


def _variant(seed: str, category: str, index: int) -> int:
    digest = hashlib.sha256(f"{seed}:{category}:{index}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _record(
    category: str,
    index: int,
    role: str,
    topic: tuple[str, str, str, str, str, str, str],
    value: str,
    *,
    status: str,
    scope: str,
    session: str,
    agent: str,
    source_type: str = "repository_evidence",
    verification: str = "verified",
    authorization: str = "allowed",
    valid_from: str = OLD_FROM,
    valid_to: str | None = None,
    statement: str | None = None,
) -> dict[str, Any]:
    key, label, alias, technical_alias, *_ = topic
    return {
        "id": f"gold_mem_{category}_{index:03d}_{role}",
        "memory_key": f"gold.{category}.{index:03d}.{key}",
        "statement": statement or f"在合成项目 {scope} 中，{label}记录为“{value}”。",
        "status": status,
        "session_id": f"synthetic_session_{category}_{index:03d}_{session}",
        "agent_id": f"synthetic_agent_{agent}",
        "scope": scope,
        "source_type": source_type,
        "source_ref": f"synthetic:{category}:{index:03d}:{role}",
        "verification_state": verification,
        "authorization": authorization,
        "valid_time": {"from": valid_from, "to": valid_to},
        "recorded_at": valid_from,
        "aliases": [alias, technical_alias],
        "tags": [category, key],
    }


def _is_forbidden_stale(state: list[dict[str, Any]], forbidden: list[str], as_of: str) -> bool:
    for record in state:
        if record["id"] not in forbidden:
            continue
        valid_to = record["valid_time"]["to"]
        if record["status"] == "retired" or (valid_to is not None and valid_to <= as_of):
            return True
    return False


def _case(
    config: dict[str, Any],
    category: str,
    index: int,
    *,
    state: list[dict[str, Any]],
    query_text: str,
    query_aliases: list[str],
    noise: str,
    as_of: str,
    expected: list[str],
    forbidden: list[str],
    hard_negatives: list[str],
    should_abstain: bool,
    answer_traits: list[str],
    abstain_conditions: list[str],
) -> dict[str, Any]:
    roles = config["roles"]
    return {
        "schema_version": config["dataset_schema_version"],
        "case_id": f"gold_{category}_{index:03d}",
        "category": category,
        "language": "zh-CN+technical-en",
        "fixed_seed": config["fixed_seed"],
        "state": state,
        "query": {"text": query_text, "aliases": query_aliases, "noise": noise},
        "as_of": {"valid_time": as_of, "recorded_time": RECORDED_AS_OF},
        "expected_ids": expected,
        "answer_traits": answer_traits,
        "forbidden_ids": forbidden,
        "abstain_conditions": abstain_conditions,
        "should_abstain": should_abstain,
        "stale_or_retired_trap": _is_forbidden_stale(state, forbidden, as_of),
        "hard_negative_ids": hard_negatives,
        "source_definition_refs": SOURCE_REFS[category],
        "gold_provenance": {
            "author_role": roles["generator"],
            "approval_role": roles["approver"],
            "tested_algorithm_role": roles["tested_algorithm"],
            "approval_mechanism": roles["approval_mechanism"],
            "algorithm_dependency_count": 0,
            "human_approval_claimed": roles["human_approval_claimed"],
        },
    }


def _build_category(config: dict[str, Any], category: str, index: int) -> dict[str, Any]:
    topic = TOPICS[index - 1]
    key, label, alias, technical_alias, current, old, distractor = topic
    scope = f"SyntheticLab-{index:02d}"
    archive_scope = f"{scope}:archive"
    noise = NOISE[_variant(config["fixed_seed"], category, index) % len(NOISE)]
    conditions = ["若 as_of 时点没有 verified、authorized 且有效的记录，必须返回 UNKNOWN。"]

    if category == "extraction":
        target = _record(category, index, "target", topic, current, status="active", scope=scope, session="primary", agent="curator")
        negative = _record(category, index, "hard_negative", topic, distractor, status="active", scope=archive_scope, session="archive", agent="curator")
        return _case(
            config,
            category,
            index,
            state=[target, negative],
            query_text=f"请提取 {scope} 的{label}（alias: {alias}），只采用匹配 scope 的 current record。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[target["id"]],
            forbidden=[negative["id"]],
            hard_negatives=[negative["id"]],
            should_abstain=False,
            answer_traits=["使用显式 state", "限定目标 scope", "返回 provenance ID"],
            abstain_conditions=conditions,
        )

    if category == "cross_session":
        target = _record(category, index, "target", topic, current, status="active", scope=scope, session="alpha", agent="research")
        bridge = _record(
            category,
            index,
            "alias_bridge",
            topic,
            current,
            status="active",
            scope=scope,
            session="beta",
            agent="curator",
            statement=f"在后续合成会话中，简称“{technical_alias}”继续指向 {scope} 的{label}记录。",
        )
        negative = _record(category, index, "hard_negative", topic, distractor, status="active", scope=archive_scope, session="gamma", agent="research")
        return _case(
            config,
            category,
            index,
            state=[target, bridge, negative],
            query_text=f"跨 session 追溯 {scope} 的“{technical_alias}”，给出事实记录及 alias bridge 的 provenance。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[target["id"], bridge["id"]],
            forbidden=[negative["id"]],
            hard_negatives=[negative["id"]],
            should_abstain=False,
            answer_traits=["连接两个 synthetic sessions", "保持 scope 一致", "同时引用事实与 bridge"],
            abstain_conditions=conditions,
        )

    if category == "temporal":
        old_record = _record(category, index, "old", topic, old, status="retired", scope=scope, session="before", agent="curator", valid_to=CUTOVER)
        current_record = _record(category, index, "current", topic, current, status="active", scope=scope, session="after", agent="curator", valid_from=CUTOVER)
        historical = index % 2 == 1
        as_of = HISTORICAL_AS_OF if historical else CURRENT_AS_OF
        expected = [old_record["id"]] if historical else [current_record["id"]]
        forbidden = [current_record["id"]] if historical else [old_record["id"]]
        return _case(
            config,
            category,
            index,
            state=[old_record, current_record],
            query_text=f"按 valid_time 回答 {scope} 在 {as_of} 的{label}，不要用 recorded order 替代 as_of。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=as_of,
            expected=expected,
            forbidden=forbidden,
            hard_negatives=forbidden,
            should_abstain=False,
            answer_traits=["遵守 half-open valid interval", "区分 valid_time 与 recorded_time", "只引用 as_of 有效记录"],
            abstain_conditions=conditions,
        )

    if category == "update":
        old_record = _record(category, index, "old", topic, old, status="retired", scope=scope, session="before", agent="curator", valid_to=CUTOVER)
        current_record = _record(category, index, "current", topic, current, status="active", scope=scope, session="after", agent="curator", valid_from=CUTOVER)
        candidate = _record(category, index, "hard_negative", topic, distractor, status="candidate", scope=scope, session="candidate", agent="model", source_type="model_inference", verification="unverified")
        return _case(
            config,
            category,
            index,
            state=[old_record, current_record, candidate],
            query_text=f"{scope} 的{label}发生 update 后，当前应采用哪条 record？",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[current_record["id"]],
            forbidden=[old_record["id"], candidate["id"]],
            hard_negatives=[old_record["id"], candidate["id"]],
            should_abstain=False,
            answer_traits=["只使用 active replacement", "排除 retired 与 unverified candidate", "保留更新 provenance"],
            abstain_conditions=conditions,
        )

    if category == "abstention":
        candidate = _record(category, index, "candidate", topic, current, status="candidate", scope=scope, session="candidate", agent="model", source_type="model_inference", verification="unverified")
        disputed = _record(category, index, "disputed", topic, old, status="disputed", scope=scope, session="dispute", agent="research", verification="disputed")
        denied = _record(category, index, "hard_negative", topic, distractor, status="active", scope=scope, session="guest", agent="guest", source_type="agent_report", authorization="denied")
        return _case(
            config,
            category,
            index,
            state=[candidate, disputed, denied],
            query_text=f"现在能否确定 {scope} 的{label}（{alias}）？证据不足时明确 abstain。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[],
            forbidden=[candidate["id"], disputed["id"], denied["id"]],
            hard_negatives=[candidate["id"], disputed["id"], denied["id"]],
            should_abstain=True,
            answer_traits=["返回 UNKNOWN", "不得猜测 candidate 或 disputed 值", "指出缺少 verified authorized evidence"],
            abstain_conditions=["只有 candidate、disputed 或 denied evidence，必须返回 UNKNOWN。"],
        )

    if category == "forgetting":
        retired = _record(category, index, "retired", topic, old, status="retired", scope=scope, session="before", agent="curator", valid_to=CUTOVER)
        active = _record(category, index, "active_boundary", topic, current, status="active", scope=scope, session="after", agent="curator", valid_from=CUTOVER)
        return _case(
            config,
            category,
            index,
            state=[retired, active],
            query_text=f"回答 {scope} 当前{label}；retired memory 只能审计，不能污染 current answer。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[active["id"]],
            forbidden=[retired["id"]],
            hard_negatives=[retired["id"]],
            should_abstain=False,
            answer_traits=["排除 obsolete memory", "采用当前有效边界", "不声称删除 Git history"],
            abstain_conditions=conditions,
        )

    if category == "conflict":
        unresolved = index <= 8
        if unresolved:
            left = _record(category, index, "conflict_left", topic, current, status="disputed", scope=scope, session="left", agent="research", verification="disputed")
            right = _record(category, index, "conflict_right", topic, old, status="disputed", scope=scope, session="right", agent="curator", verification="disputed")
            return _case(
                config,
                category,
                index,
                state=[left, right],
                query_text=f"{scope} 的{label}存在 unresolved conflict；没有 resolution 时应如何回答？",
                query_aliases=[alias, technical_alias],
                noise=noise,
                as_of=CURRENT_AS_OF,
                expected=[],
                forbidden=[left["id"], right["id"]],
                hard_negatives=[left["id"], right["id"]],
                should_abstain=True,
                answer_traits=["返回 UNKNOWN", "显式报告 unresolved conflict", "不得任意选边"],
                abstain_conditions=["同 scope/key 的证据仍 disputed 且无 resolution，必须返回 UNKNOWN。"],
            )
        loser = _record(category, index, "resolved_loser", topic, old, status="retired", scope=scope, session="left", agent="research", valid_to=CUTOVER)
        winner = _record(category, index, "resolved_winner", topic, current, status="active", scope=scope, session="right", agent="curator", valid_from=CUTOVER)
        return _case(
            config,
            category,
            index,
            state=[loser, winner],
            query_text=f"{scope} 的{label} conflict 已 resolved；只返回 surviving record。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[winner["id"]],
            forbidden=[loser["id"]],
            hard_negatives=[loser["id"]],
            should_abstain=False,
            answer_traits=["采用 resolved winner", "排除 retired loser", "保留 resolution provenance"],
            abstain_conditions=conditions,
        )

    if category == "cross_agent":
        fact = _record(category, index, "authorized_fact", topic, current, status="active", scope=scope, session="research", agent="research", source_type="agent_report")
        handoff = _record(
            category,
            index,
            "authorized_handoff",
            topic,
            current,
            status="active",
            scope=scope,
            session="curator",
            agent="curator",
            source_type="agent_report",
            statement=f"合成 curator 已授权 research agent 的 {scope}/{key} handoff 供跨 Agent 读取。",
        )
        denied = _record(category, index, "hard_negative", topic, distractor, status="active", scope=scope, session="guest", agent="guest", source_type="agent_report", authorization="denied")
        return _case(
            config,
            category,
            index,
            state=[fact, handoff, denied],
            query_text=f"跨 Agent 读取 {scope} 的{label}（{technical_alias}），仅接受有授权 handoff 的 provenance chain。",
            query_aliases=[alias, technical_alias],
            noise=noise,
            as_of=CURRENT_AS_OF,
            expected=[fact["id"], handoff["id"]],
            forbidden=[denied["id"]],
            hard_negatives=[denied["id"]],
            should_abstain=False,
            answer_traits=["连接 research 与 curator provenance", "拒绝 denied guest record", "保持 agent authorization boundary"],
            abstain_conditions=conditions,
        )

    raise ValueError(f"unsupported_category:{category}")


def build_cases(config: dict[str, Any]) -> list[dict[str, Any]]:
    categories = config["categories"]
    if len(TOPICS) != config["cases_per_category"]:
        raise ValueError("topic_count_mismatch")
    if categories != list(SOURCE_REFS):
        raise ValueError("category_order_or_definition_mismatch")
    cases = [
        _build_category(config, category, index)
        for category in categories
        for index in range(1, config["cases_per_category"] + 1)
    ]
    if len(cases) != config["case_count"]:
        raise ValueError("case_count_mismatch")
    return cases


def render_cases(cases: list[dict[str, Any]]) -> bytes:
    return (
        "".join(
            json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
            for case in cases
        )
    ).encode("utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=DATABASE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    config = load_config(database_dir, args.config)
    rendered = render_cases(build_cases(config))
    output = database_dir / config["paths"]["dataset"]
    digest = hashlib.sha256(rendered).hexdigest()
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_bytes(rendered)
        os.replace(temporary, output)
        status = "PASS"
        reason = "dataset_written"
    else:
        matches = output.is_file() and output.read_bytes() == rendered
        status = "PASS" if matches else "FAIL"
        reason = "dataset_matches_deterministic_build" if matches else "dataset_drift_or_missing"
    result = {
        "status": status,
        "task_id": config["task_id"],
        "acceptance_id": config["acceptance_id"],
        "case_count": config["case_count"],
        "fixed_seed": config["fixed_seed"],
        "dataset_sha256": digest,
        "writes_files": bool(args.write),
        "reason": reason,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
