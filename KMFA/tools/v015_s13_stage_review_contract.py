#!/usr/bin/env python3
"""KMFA v1.5 S13 跨部分整体复审合同。

把 P1 指标登记、P2 六维健康判断和 P3 行动优先级连接成一条公开安全、
可重复验证的证据链。任何来源漂移、硬门禁失效、过期资料或建议越权都会
失败关闭；本模块不会读取真实资料或执行真实业务动作。
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from typing import Any

from KMFA.tools import v015_s13_p1_indicator_registry as p1
from KMFA.tools import v015_s13_p2_business_health_model as p2
from KMFA.tools import v015_s13_p3_action_priority as p3


RUN_PHASE_ID = "V015_S13_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S13-STAGE-REVIEW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S13-STAGE-REVIEW"
VERSION = "1.5.0-dev-s13-review"
REVIEW_BASE_COMMIT = "1b3cda853132428619598829ea6c6efb2a402905"

DIMENSION_ACTION = {
    "HEALTH-CASH-SAFETY": ("FUNDS", "复核现金安全信号", "资金负责人"),
    "HEALTH-PROJECT-PROFIT": ("PROJECT", "复核项目利润与成本信号", "项目负责人"),
    "HEALTH-COLLECTION-QUALITY": ("COLLECTION", "复核回款质量信号", "回款负责人"),
    "HEALTH-TAX-POLICY": ("TAX", "复核税务政策信号", "税务负责人"),
    "HEALTH-CONTRACT-PERFORMANCE": ("PROJECT", "复核合同履约信号", "合同负责人"),
    "HEALTH-DATA-COMPLETENESS": ("DATA", "补齐影响判断的数据", "数据负责人"),
}


class StageReviewError(ValueError):
    """复审输入或跨部分证据不一致。"""

    def __init__(self, code: str, message_zh: str) -> None:
        super().__init__(f"{code}: {message_zh}")
        self.code = code
        self.message_zh = message_zh


def _fingerprint(value: Any) -> str:
    return p2.fingerprint(value)


def _health_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(dict(value))
    supplied = payload.pop("result_fingerprint", None)
    if supplied != _fingerprint(payload):
        raise StageReviewError("HEALTH_FINGERPRINT_MISMATCH", "健康结果指纹与内容不一致。")
    return payload


def _dimension_specs() -> dict[str, dict[str, Any]]:
    specs = p2.health_dimensions()
    p2.validate_health_dimensions(specs)
    return {str(row["dimension_id"]): row for row in specs}


def _source_binding_payload(health_result: Mapping[str, Any], dimension: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "health_result_fingerprint": health_result["result_fingerprint"],
        "dimension_id": dimension["dimension_id"],
        "source_indicator_ids": copy.deepcopy(dimension["source_indicator_ids"]),
        "score_bps": dimension["score_bps"],
        "hard_gate_passed": dimension["hard_gate_passed"],
        "freshness_state": dimension["freshness_state"],
    }


def _candidate_factors(dimension: Mapping[str, Any], index: int) -> dict[str, int]:
    score = dimension.get("score_bps")
    impact = 7000 if score is None else min(9500, max(3500, 10_000 - int(score) + 3500))
    confidence = 8200 if dimension.get("freshness_state") == "FRESH" else 6500
    return {
        "IMPACT": impact,
        "CONFIDENCE": confidence,
        "URGENCY": 8800 - index * 350,
        "EFFORT": 2400 + index * 300,
        "CASH_COST": 900 + index * 250,
        "EXECUTION_RISK": 1500 + index * 300,
    }


def build_health_action_candidates(health_result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """把 P2 的六维结果逐项绑定到 P1 来源和 P3 候选。"""

    if not isinstance(health_result, Mapping):
        raise StageReviewError("HEALTH_RESULT_REQUIRED", "必须提供结构化健康结果。")
    _health_payload(health_result)
    specs = _dimension_specs()
    results = health_result.get("dimension_results")
    if isinstance(results, (str, bytes)) or not isinstance(results, Sequence):
        raise StageReviewError("HEALTH_DIMENSIONS_REQUIRED", "健康结果必须包含六个维度。")
    rows = [copy.deepcopy(dict(row)) for row in results if isinstance(row, Mapping)]
    if len(rows) != 6 or {row.get("dimension_id") for row in rows} != set(specs):
        raise StageReviewError("HEALTH_DIMENSION_SET_MISMATCH", "健康结果必须完整包含登记的六个维度。")

    known = {row["indicator_id"] for row in p1.indicator_registry()}
    candidates: list[dict[str, Any]] = []
    for index, dimension_id in enumerate(DIMENSION_ACTION):
        row = next(item for item in rows if item.get("dimension_id") == dimension_id)
        expected_sources = specs[dimension_id]["source_indicator_ids"]
        if row.get("source_indicator_ids") != expected_sources or not set(expected_sources) <= known:
            raise StageReviewError("INDICATOR_BINDING_MISMATCH", "健康维度与指标登记不一致。")
        domain, title, owner = DIMENSION_ACTION[dimension_id]
        candidates.append(
            {
                "candidate_id": f"ACT-S13-REVIEW-{index + 1:02d}",
                "domain": domain,
                "title_zh": title,
                "source_refs": [f"S13-P2:{dimension_id}"]
                + [f"S13-P1:{source_id}" for source_id in expected_sources],
                "source_fingerprint": _fingerprint(_source_binding_payload(health_result, row)),
                "freshness": row["freshness_state"],
                "hard_gate_passed": row["hard_gate_passed"],
                "owner_role": owner,
                "next_human_step": "由负责人核对来源和解释后决定是否采纳，不自动执行。",
                "factors": _candidate_factors(row, index),
            }
        )
    return candidates


def _recommendation_reviews(focus: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        p3.build_recommendation_review(
            recommendation_id=f"REC-S13-REVIEW-{index:02d}",
            candidate_id=item["candidate_id"],
            recommendation_text_zh=f"请{item['owner_role']}核对依据后决定是否处理：{item['title_zh']}。",
            calibration_note_zh="尚无真实结果，只保留待复盘记录。",
        )
        for index, item in enumerate(focus["focus_items"], start=1)
    ]


def _link_explanations(health_result: Mapping[str, Any], ranked: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    health_by_id = {row["dimension_id"]: row for row in health_result["dimension_results"]}
    ranked_by_id = {row["candidate_id"]: row for row in ranked}
    rows = []
    for index, dimension_id in enumerate(DIMENSION_ACTION, start=1):
        health = health_by_id[dimension_id]
        action = ranked_by_id[f"ACT-S13-REVIEW-{index:02d}"]
        rows.append(
            {
                "dimension_id": dimension_id,
                "candidate_id": action["candidate_id"],
                "health_state": health_result["health_state"],
                "dimension_score_bps": health["score_bps"],
                "action_state": action["state"],
                "source_refs": copy.deepcopy(action["source_refs"]),
                "source_fingerprint": action["source_fingerprint"],
                "reason_zh": "行动候选只继承该健康维度及其已登记指标来源；是否执行仍由人工决定。",
                "automatic_execution_allowed": False,
            }
        )
    return rows


def build_integrated_review(observations: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    source = p2.synthetic_observations(factor_shift_bps=300) if observations is None else copy.deepcopy(list(observations))
    health = p2.evaluate_health(source)
    candidates = build_health_action_candidates(health)
    ranked = p3.rank_actions(candidates)
    focus = p3.select_focus_items(candidates)
    reviews = _recommendation_reviews(focus)
    calibration = p3.build_calibration_proposal(reviews)
    integrated = {
        "schema_version": "kmfa.v015.s13.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SAFE_SYNTHETIC",
        "indicator_registry_fingerprint": p1.validate_indicator_registry(p1.indicator_registry())["registry_fingerprint"],
        "health_result": health,
        "health_action_candidates": candidates,
        "ranked_actions": ranked,
        "focus_selection": focus,
        "recommendation_reviews": reviews,
        "calibration_proposal": calibration,
        "link_explanations": _link_explanations(health, ranked),
        "source_binding_count": sum(len(row["source_indicator_ids"]) for row in health["dimension_results"]),
        "automatic_execution_count": 0,
        "recommendation_fact_write_count": 0,
        "automatic_parameter_change_count": 0,
        "raw_root_access_count": 0,
        "live_source_read_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
    }
    integrated["review_fingerprint"] = _fingerprint(integrated)
    validate_integrated_review(integrated)
    return integrated


def validate_integrated_review(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("REVIEW_RECORD_REQUIRED", "复审结果必须是结构化对象。")
    actual = copy.deepcopy(dict(value))
    supplied = actual.pop("review_fingerprint", None)
    if supplied != _fingerprint(actual):
        raise StageReviewError("REVIEW_FINGERPRINT_MISMATCH", "复审结果指纹与内容不一致。")
    health = actual.get("health_result")
    expected_candidates = build_health_action_candidates(health)
    expected_ranked = p3.rank_actions(expected_candidates)
    expected_focus = p3.select_focus_items(expected_candidates)
    expected_reviews = _recommendation_reviews(expected_focus)
    expected_calibration = p3.build_calibration_proposal(expected_reviews)
    expected_explanations = _link_explanations(health, expected_ranked)
    bindings = sum(len(row["source_indicator_ids"]) for row in health["dimension_results"])
    comparisons = (
        actual.get("health_action_candidates") == expected_candidates,
        actual.get("ranked_actions") == expected_ranked,
        actual.get("focus_selection") == expected_focus,
        actual.get("recommendation_reviews") == expected_reviews,
        actual.get("calibration_proposal") == expected_calibration,
        actual.get("link_explanations") == expected_explanations,
        actual.get("source_binding_count") == bindings == 7,
    )
    if not all(comparisons):
        raise StageReviewError("REVIEW_CROSS_PHASE_MISMATCH", "跨部分来源、排序、重点事项或复盘记录不一致。")
    if (
        actual.get("automatic_execution_count") != 0
        or actual.get("recommendation_fact_write_count") != 0
        or actual.get("automatic_parameter_change_count") != 0
        or actual.get("raw_root_access_count") != 0
        or actual.get("live_source_read_count") != 0
        or actual.get("real_business_action_count") != 0
        or actual.get("github_upload_performed") is not False
        or actual.get("app_reinstall_performed") is not False
    ):
        raise StageReviewError("REVIEW_SIDE_EFFECT_REJECTED", "复审不得产生真实动作、事实写入或发布副作用。")
    return {
        "dimension_count": 6,
        "candidate_count": len(expected_candidates),
        "focus_item_count": expected_focus["focus_item_count"],
        "source_binding_count": bindings,
        "explanation_count": len(expected_explanations),
        "explanation_mismatch_count": 0,
    }


def _rejected(callable_value: Any, exception: type[BaseException], token: str | None = None) -> bool:
    try:
        callable_value()
    except exception as error:
        return token is None or token in str(error)
    return False


def public_verification() -> dict[str, Any]:
    """执行恰好 72 项跨部分和反例检查。"""

    review = build_integrated_review()
    health = review["health_result"]
    candidates = review["health_action_candidates"]
    ranked = review["ranked_actions"]
    focus = review["focus_selection"]
    known = {row["indicator_id"] for row in p1.indicator_registry()}
    specs = _dimension_specs()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    registry = p1.validate_indicator_registry(p1.indicator_registry())
    health_contract = p2.validate_health_dimensions(p2.health_dimensions())
    baseline = (
        ("indicator_count", registry["indicator_count"] == 8),
        ("indicator_domain_count", registry["domain_count"] == 8),
        ("indicator_registry_deterministic", registry == p1.validate_indicator_registry(p1.indicator_registry())),
        ("health_dimension_count", health_contract["dimension_count"] == 6),
        ("health_weight_total", health_contract["weight_total_bps"] == 10_000),
        ("health_score_displayed", health["score_displayable"] is True),
        ("health_state_explained", health["health_state"] in {"HEALTHY", "WATCH", "AT_RISK"}),
        ("health_explanations_complete", health["explanation_complete"] is True),
        ("health_freshness_visible", health["data_freshness_visible"] is True),
        ("source_binding_count", review["source_binding_count"] == 7),
        ("all_health_sources_registered", all(source in known for row in health["dimension_results"] for source in row["source_indicator_ids"])),
        ("candidate_count", len(candidates) == 6),
        ("health_fingerprint_exact", _health_payload(health) == {key: copy.deepcopy(value) for key, value in health.items() if key != "result_fingerprint"}),
        ("ranked_count", len(ranked) == 6),
        ("ranking_deterministic", ranked == p3.rank_actions(candidates)),
        ("focus_ready", focus["selection_status"] == "READY"),
        ("focus_count_five", focus["focus_item_count"] == 5),
        ("focus_bounds", 3 <= focus["focus_item_count"] <= 5),
        ("focus_domain_cap", all(sum(item["domain"] == domain for item in focus["focus_items"]) <= 2 for domain in p3.ACTION_DOMAINS)),
        ("candidates_bind_p2", all(row["source_refs"][0].startswith("S13-P2:HEALTH-") for row in candidates)),
        ("candidates_bind_p1", all(any(ref.startswith("S13-P1:IND-") for ref in row["source_refs"]) for row in candidates)),
        ("candidate_fingerprints_exact", all(row["source_fingerprint"] == _fingerprint(_source_binding_payload(health, health["dimension_results"][index])) for index, row in enumerate(candidates))),
        ("ranked_sources_preserved", all(row["source_refs"] == next(item for item in candidates if item["candidate_id"] == row["candidate_id"])["source_refs"] for row in ranked)),
        ("review_count", len(review["recommendation_reviews"]) == 5),
        ("review_unknown_explicit", all(row["outcome_state"] == "UNKNOWN" for row in review["recommendation_reviews"])),
        ("recommendation_not_fact", all(not row["recommendation_written_as_fact"] and row["fact_layer_write_count"] == 0 for row in review["recommendation_reviews"])),
        ("calibration_insufficient", review["calibration_proposal"]["status"] == "INSUFFICIENT_DATA"),
        ("no_auto_parameter_change", review["calibration_proposal"]["automatic_parameter_change_allowed"] is False),
        ("no_auto_execution", focus["automatic_execution_count"] == review["automatic_execution_count"] == 0),
        ("public_boundary", all(review[key] == 0 for key in ("raw_root_access_count", "live_source_read_count", "real_business_action_count")) and not review["github_upload_performed"] and not review["app_reinstall_performed"]),
    )
    for name, passed in baseline:
        add(name, passed)

    for index, dimension_id in enumerate(DIMENSION_ACTION):
        health_row = health["dimension_results"][index]
        candidate = candidates[index]
        ranked_row = next(row for row in ranked if row["candidate_id"] == candidate["candidate_id"])
        expected_domain = DIMENSION_ACTION[dimension_id][0]
        add(f"{dimension_id}_domain", candidate["domain"] == expected_domain)
        add(f"{dimension_id}_refs", candidate["source_refs"] == [f"S13-P2:{dimension_id}"] + [f"S13-P1:{source}" for source in specs[dimension_id]["source_indicator_ids"]])
        add(f"{dimension_id}_fingerprint", candidate["source_fingerprint"] == _fingerprint(_source_binding_payload(health, health_row)))
        add(f"{dimension_id}_ranked_source", ranked_row["source_fingerprint"] == candidate["source_fingerprint"])
        add(f"{dimension_id}_eligible", ranked_row["state"] == "ELIGIBLE" and ranked_row["focus_eligible"] is True)

    unknown = p2.health_dimensions()
    unknown[0]["source_indicator_ids"] = ["IND-UNKNOWN"]
    wrong = p2.synthetic_observations()
    wrong[0]["source_indicator_ids"] = ["IND-REVENUE-RECOGNIZED-CENTS"]
    assumption = p2.synthetic_observations()
    assumption[0]["factors"][0]["record_kind"] = "ASSUMPTION"
    tampered_health = copy.deepcopy(health)
    tampered_health["overall_score_bps"] += 1
    tampered_review = copy.deepcopy(review)
    tampered_review["health_action_candidates"][0]["source_refs"][0] = "S13-P2:HEALTH-TAMPERED"
    tampered_review["review_fingerprint"] = _fingerprint({key: copy.deepcopy(value) for key, value in tampered_review.items() if key != "review_fingerprint"})

    hard_observations = p2.synthetic_observations()
    hard_observations[5]["hard_gate_passed"] = False
    hard_observations[5]["hard_gate_reason_zh"] = "公开反例触发数据完整度硬门禁。"
    hard_health = p2.evaluate_health(hard_observations)
    hard_candidates = build_health_action_candidates(hard_health)
    hard_ranked = p3.rank_actions(hard_candidates)
    hard_focus = p3.select_focus_items(hard_candidates)
    hard_row = hard_ranked[5]

    stale_observations = p2.synthetic_observations()
    stale_observations[0]["freshness_age_days"] = 30
    stale_health = p2.evaluate_health(stale_observations)
    stale_candidates = build_health_action_candidates(stale_health)
    stale_ranked = p3.rank_actions(stale_candidates)
    stale_focus = p3.select_focus_items(stale_candidates)
    stale_row = next(row for row in stale_ranked if row["candidate_id"] == "ACT-S13-REVIEW-01")

    flood = []
    for index in range(6):
        row = copy.deepcopy(candidates[0])
        row["candidate_id"] = f"ACT-FLOOD-{index:02d}"
        row["source_fingerprint"] = _fingerprint({"flood": index})
        flood.append(row)
    flood_focus = p3.select_focus_items(flood)
    adversarial = (
        ("unknown_indicator_rejected", _rejected(lambda: p2.validate_health_dimensions(unknown), p2.HealthModelError, "SOURCE_UNKNOWN")),
        ("wrong_observation_binding_rejected", _rejected(lambda: p2.evaluate_health(wrong), p2.HealthModelError, "SOURCE_BINDING_MISMATCH")),
        ("assumption_actual_score_rejected", _rejected(lambda: p2.evaluate_health(assumption), p2.HealthModelError, "ASSUMPTION_IN_ACTUAL_SCORE")),
        ("tampered_health_fingerprint_rejected", _rejected(lambda: build_health_action_candidates(tampered_health), StageReviewError, "HEALTH_FINGERPRINT_MISMATCH")),
        ("tampered_candidate_binding_rejected", _rejected(lambda: validate_integrated_review(tampered_review), StageReviewError, "REVIEW_CROSS_PHASE_MISMATCH")),
        ("hard_gate_hides_health_score", hard_health["overall_score_bps"] is None and not hard_health["score_displayable"]),
        ("hard_gate_blocks_candidate", hard_row["state"] == "BLOCKED_BY_HARD_GATE" and hard_row["priority_score_bps"] is None),
        ("hard_gate_not_focus", hard_row["candidate_id"] not in {row["candidate_id"] for row in hard_focus["focus_items"]}),
        ("stale_hides_health_score", stale_health["overall_score_bps"] is None and not stale_health["score_displayable"]),
        ("stale_candidate_insufficient", stale_row["state"] == "INSUFFICIENT_DATA" and stale_row["priority_score_bps"] is None),
        ("stale_not_focus", stale_row["candidate_id"] not in {row["candidate_id"] for row in stale_focus["focus_items"]}),
        ("domain_flooding_rejected", flood_focus["focus_item_count"] == 2 and flood_focus["selection_status"] == "INSUFFICIENT_ELIGIBLE_ITEMS"),
    )
    for name, passed in adversarial:
        add(name, passed)

    if len(checks) != 72:
        raise StageReviewError("CHECK_ACCOUNTING_DRIFT", f"复审检查数量应为 72，实际为 {len(checks)}。")
    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s13.stage-review-verification.v1",
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "checks": checks,
        "integrated_review": review,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(public_verification(), ensure_ascii=False, indent=2, sort_keys=True))
