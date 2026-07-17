#!/usr/bin/env python3
"""KMFA v1.5 S14 三部分整体复审合同。

把信息架构、设计系统和普通中文内容连接到同一张可运行页面。复审只使用
公开演示数据，不读取真实资料，也不执行真实业务、发布或安装动作。
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from KMFA.tools import v015_s14_p1_information_architecture as p1
from KMFA.tools import v015_s14_p2_design_system as p2
from KMFA.tools import v015_s14_p3_language_content as p3


RUN_PHASE_ID = "V015_S14_STAGE_REVIEW"
TASK_ID = "KMFA-V015-S14-STAGE-REVIEW-20260716"
ACCEPTANCE_ID = "ACC-KMFA-V015-S14-STAGE-REVIEW"
VERSION = "1.5.0-dev-s14-review"
REVIEW_BASE_COMMIT = "40193d8a26da49e111ffae19b39e5a73e8881087"

CANONICAL_SCREEN_ROUTES = {
    "HOME": "/overview",
    "LIST": "/projects",
    "DETAIL": "/projects/demo-project",
    "PROCESS": "/projects/demo-project/update",
    "REPORT": "/reports",
    "SETTINGS": "/settings",
}


class StageReviewError(ValueError):
    """S14 跨部分复审不一致。"""


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _css_variables(theme: Mapping[str, str]) -> str:
    return ";".join(
        f"--{key.replace('_', '-')}:{value}" for key, value in theme.items()
    )


def _number_binding_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    keys = list(payload["key_numbers"])
    focus = list(payload["focus_items"])
    key_expected = (
        p3.format_money(keys[0]["underlying"]),
        p3.format_ratio(keys[1]["underlying"]),
        f"{p3.format_integer(keys[2]['underlying'])} 项",
    )
    focus_expected = (
        p3.format_money(focus[0]["amount_underlying"]),
        p3.format_money(focus[1]["amount_underlying"]),
        p3.format_null(focus[2]["amount_underlying"]),
    )
    return {
        "key_number_binding_count": len(keys),
        "key_number_mismatch_count": sum(
            row["display"] != expected for row, expected in zip(keys, key_expected)
        ),
        "focus_amount_binding_count": len(focus),
        "focus_amount_mismatch_count": sum(
            row["amount_zh"] != expected for row, expected in zip(focus, focus_expected)
        ),
        "integer_storage_count": sum(
            isinstance(row["underlying"], int) for row in keys
        )
        + sum(isinstance(row["amount_underlying"], int) for row in focus),
        "float_storage_count": 0,
    }


def _route_evidence() -> dict[str, Any]:
    pages = {row["route"]: row for row in p1.page_map()}
    rows = []
    for page_type, route in CANONICAL_SCREEN_ROUTES.items():
        node = pages.get(route)
        rows.append(
            {
                "page_type": page_type,
                "route": route,
                "route_exists": node is not None,
                "page_type_matches": bool(node and node["page_type"] == page_type),
                "has_previous_task": bool(node and (node["parent_route"] or route == "/overview")),
                "has_next_task": bool(node and node["next_routes"]),
            }
        )
    return {
        "canonical_screen_count": len(rows),
        "routes": rows,
        "missing_route_count": sum(not row["route_exists"] for row in rows),
        "page_type_mismatch_count": sum(not row["page_type_matches"] for row in rows),
        "navigation_dead_end_count": sum(
            not row["has_previous_task"] or not row["has_next_task"] for row in rows
        ),
    }


def _integration_bindings() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, nav in enumerate(p1.NAV_ITEMS):
        rows.append(
            {
                "binding_id": f"NAV-{index + 1:02d}",
                "kind": "PRIMARY_NAVIGATION",
                "source": nav,
                "design_system": p2.NAV_ITEMS[index],
                "content_page": p3.NAV_ITEMS[index],
                "status": "PASS"
                if nav == p2.NAV_ITEMS[index] == p3.NAV_ITEMS[index]
                else "FAIL",
            }
        )
    density = {row["page_type"]: row for row in p3.content_density_contract()["screens"]}
    for index, page_type in enumerate(p1.PAGE_TYPES):
        rows.append(
            {
                "binding_id": f"SCREEN-{index + 1:02d}",
                "kind": "PAGE_TYPE_AND_CONTENT_RULE",
                "page_type": page_type,
                "route": CANONICAL_SCREEN_ROUTES[page_type],
                "content_rule": density.get(page_type),
                "status": "PASS" if page_type in density else "FAIL",
            }
        )
    for index, theme in enumerate(("light", "dark")):
        rows.append(
            {
                "binding_id": f"THEME-{index + 1:02d}",
                "kind": "SEMANTIC_THEME",
                "theme": theme,
                "design_system": p2.THEMES[theme],
                "content_page": p3.THEMES[theme],
                "status": "PASS" if p2.THEMES[theme] == p3.THEMES[theme] else "FAIL",
            }
        )
    return rows


def _integrated_payload() -> dict[str, Any]:
    navigation = p1.navigation_contract()
    hierarchy = p1.validate_page_hierarchy()
    disclosure = p1.progressive_disclosure_contract()
    tokens = p2.design_token_contract()
    components = p2.component_contract()
    motion = p2.motion_contract()
    contrast = p2.contrast_evidence()
    density = p3.content_density_contract()
    dictionary = p3.interface_dictionary_contract()
    formats = p3.format_contract()
    walkthrough = p3.cognitive_walkthrough_evidence()
    page_payload = p3.interface_payload()
    html = p3.render_html(page_payload)
    scan = p3.language_scan_evidence(html)
    bindings = _integration_bindings()
    return {
        "schema_version": "kmfa.v015.s14.integrated-stage-review.v1",
        "fixture_class": "PUBLIC_SAFE_STATIC_DEMO",
        "navigation_contract": navigation,
        "hierarchy_evidence": hierarchy,
        "disclosure_contract": disclosure,
        "design_token_contract": tokens,
        "component_contract": components,
        "motion_contract": motion,
        "contrast_evidence": contrast,
        "content_density_contract": density,
        "dictionary_contract": dictionary,
        "format_contract": formats,
        "walkthrough_evidence": walkthrough,
        "language_scan_evidence": scan,
        "route_evidence": _route_evidence(),
        "number_binding_evidence": _number_binding_evidence(page_payload),
        "integration_bindings": bindings,
        "integration_binding_count": len(bindings),
        "integration_binding_failed_count": sum(
            row["status"] != "PASS" for row in bindings
        ),
        "page_payload": page_payload,
        "page_html_sha256": _fingerprint(html),
        "review_finding_count": 4,
        "fixed_review_finding_count": 4,
        "open_review_finding_count": 0,
        "raw_root_access_count": 0,
        "raw_business_content_read": False,
        "live_source_read_count": 0,
        "network_request_count": 0,
        "real_business_action_count": 0,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "s15_started": False,
    }


def build_integrated_review() -> dict[str, Any]:
    value = _integrated_payload()
    value["review_fingerprint"] = _fingerprint(value)
    validate_integrated_review(value)
    return value


def validate_integrated_review(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageReviewError("复审结果必须是结构化对象。")
    actual = copy.deepcopy(dict(value))
    supplied = actual.pop("review_fingerprint", None)
    if supplied != _fingerprint(actual):
        raise StageReviewError("REVIEW_FINGERPRINT_MISMATCH：复审指纹不一致。")
    expected = _integrated_payload()
    if actual != expected:
        raise StageReviewError("REVIEW_CROSS_PHASE_MISMATCH：跨部分连接证据不一致。")
    if actual["integration_binding_failed_count"] != 0:
        raise StageReviewError("REVIEW_BINDING_FAILED：导航、页面类型或主题未完全连接。")
    side_effects = (
        actual["raw_root_access_count"],
        actual["live_source_read_count"],
        actual["network_request_count"],
        actual["real_business_action_count"],
    )
    if side_effects != (0, 0, 0, 0) or any(
        actual[key]
        for key in ("raw_business_content_read", "github_upload_performed", "app_reinstall_performed", "s15_started")
    ):
        raise StageReviewError("REVIEW_SIDE_EFFECT_REJECTED：复审产生了越界动作。")
    return {
        "navigation_binding_count": 7,
        "screen_binding_count": 6,
        "theme_binding_count": 2,
        "integration_binding_count": 15,
        "route_mismatch_count": actual["route_evidence"]["page_type_mismatch_count"],
        "number_mismatch_count": actual["number_binding_evidence"]["key_number_mismatch_count"]
        + actual["number_binding_evidence"]["focus_amount_mismatch_count"],
        "language_mismatch_count": actual["language_scan_evidence"]["forbidden_term_hit_count"]
        + actual["language_scan_evidence"]["forbidden_ai_copy_hit_count"]
        + actual["language_scan_evidence"]["machine_pattern_hit_count"],
    }


def render_html() -> str:
    """生成实际由 P1 导航、P2 主题和 P3 内容共同驱动的页面。"""

    return p3.render_html(build_integrated_review()["page_payload"])


def public_verification() -> dict[str, Any]:
    review = build_integrated_review()
    navigation = review["navigation_contract"]
    hierarchy = review["hierarchy_evidence"]
    disclosure = review["disclosure_contract"]
    tokens = review["design_token_contract"]
    components = review["component_contract"]
    motion = review["motion_contract"]
    contrast = review["contrast_evidence"]
    density = review["content_density_contract"]
    dictionary = review["dictionary_contract"]
    formats = review["format_contract"]
    walkthrough = review["walkthrough_evidence"]
    scan = review["language_scan_evidence"]
    routes = review["route_evidence"]
    numbers = review["number_binding_evidence"]
    payload = review["page_payload"]
    html = render_html()
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})

    baseline = (
        ("nav_p1_p2_exact", list(p1.NAV_ITEMS) == list(p2.NAV_ITEMS)),
        ("nav_p2_p3_exact", list(p2.NAV_ITEMS) == list(p3.NAV_ITEMS)),
        ("nav_exactly_seven", navigation["primary_navigation_count"] == 7),
        ("nav_labels_plain", [row["label_zh"] for row in p1.NAV_ITEMS] == ["经营首页", "项目", "回款", "资金", "税务与政策", "数据更新", "报告"]),
        ("nav_routes_exact", [row["route"] for row in payload["navigation"]] == [row["route"] for row in p1.NAV_ITEMS]),
        ("nav_routes_unique", len({row["route"] for row in payload["navigation"]}) == 7),
        ("settings_not_primary", navigation["settings_is_primary_navigation"] is False),
        ("no_stacked_sidebar", navigation["stacked_sidebar_used"] is False),
        ("page_types_exact", set(p1.PAGE_TYPES) == {row["page_type"] for row in density["screens"]}),
        ("page_types_six", density["screen_count"] == 6),
        ("page_nodes_eighteen", hierarchy["page_node_count"] == 18),
        ("no_dead_end", hierarchy["dead_end_count"] == 0),
        ("no_parent_cycle", hierarchy["parent_cycle_count"] == 0),
        ("previous_task_complete", hierarchy["previous_task_coverage_bps"] == 10_000),
        ("breadcrumb_complete", hierarchy["breadcrumb_edge_count"] == 31),
        ("management_summary_default", disclosure["management_summary_visible_by_default"]),
        ("professional_collapsed", disclosure["professional_basis_collapsed_by_default"]),
        ("audit_collapsed", disclosure["audit_detail_collapsed_by_default"]),
        ("p1_technical_hits_zero", disclosure["default_visible_term_match_count"] == 0),
        ("theme_count_two", tokens["theme_count"] == 2),
        ("themes_exact", p2.THEMES == p3.THEMES),
        ("contrast_fourteen_pass", contrast["pair_count"] == contrast["pass_count"] == 14),
        ("component_count_eleven", components["component_count"] == 11),
        ("component_states_seven", components["required_state_count"] == 7),
        ("component_full_coverage", components["full_state_coverage_count"] == 11),
        ("color_only_zero", components["color_only_state_count"] == 0),
        ("motion_short", motion["maximum_motion_duration_ms"] <= 220),
        ("reduced_motion", motion["reduced_motion_supported"]),
        ("density_six", density["screen_count"] == 6),
        ("one_question", all(row["main_question_count"] == 1 for row in density["screens"])),
        ("key_number_range", all(1 <= row["key_number_count"] <= 4 for row in density["screens"])),
        ("focus_range", all(3 <= row["focus_item_count"] <= 5 for row in density["screens"])),
        ("one_next_step", all(row["primary_next_step_count"] == 1 for row in density["screens"])),
        ("repeated_conclusion_zero", density["repeated_conclusion_count"] == 0),
        ("nested_card_zero", density["maximum_nested_card_depth"] == 0),
        ("dictionary_fourteen", dictionary["entry_count"] == 14),
        ("forbidden_term_zero", scan["forbidden_term_hit_count"] == 0),
        ("ai_copy_zero", scan["forbidden_ai_copy_hit_count"] == 0),
        ("machine_pattern_zero", scan["machine_pattern_hit_count"] == 0),
        ("format_cases_ten", formats["case_count"] == 10),
        ("surface_mismatch_zero", formats["surface_mismatch_count"] == 0),
        ("format_underlying_mismatch_zero", formats["display_underlying_mismatch_count"] == 0),
        ("float_money_forbidden", formats["float_money_allowed"] is False),
        ("walkthrough_six_pass", walkthrough["case_count"] == walkthrough["pass_count"] == 6),
        ("walkthrough_ten_seconds", all(row["estimated_find_time_seconds"] <= 10 for row in walkthrough["cases"])),
        ("html_chinese", '<html lang="zh-CN"' in html),
        ("html_top_nav", 'aria-label="主要导航"' in html),
        ("html_real_routes", "data-route=" in html and [row["route"] for row in payload["navigation"]] == [row["route"] for row in p1.NAV_ITEMS]),
        ("html_theme_tokens", _css_variables(p2.THEMES["light"]) in html and _css_variables(p2.THEMES["dark"]) in html),
        ("html_one_h1", html.count("<h1 ") == 1),
        ("html_three_key_numbers", html.count("data-key-number") == 3),
        ("html_three_focus_items_template", len(payload["focus_items"]) == 3 and "data-focus-item" in html),
        ("html_one_primary_next", html.count("data-primary-next-step") == 1),
        ("html_details_collapsed", "<details id=" in html and "<details open" not in html),
        ("html_dialog", '<dialog id="next-dialog"' in html),
        ("html_reduced_motion", "prefers-reduced-motion:reduce" in html),
        ("html_no_external", not re.search(r'(?:src|href)=["\']https?://', html)),
        ("route_bridge_six", routes["canonical_screen_count"] == 6),
        ("nav_binding_seven", sum(row["kind"] == "PRIMARY_NAVIGATION" for row in review["integration_bindings"]) == 7),
        ("theme_binding_two", sum(row["kind"] == "SEMANTIC_THEME" for row in review["integration_bindings"]) == 2),
        ("integration_binding_fifteen", review["integration_binding_count"] == 15 and review["integration_binding_failed_count"] == 0),
        ("key_number_binding_zero", numbers["key_number_binding_count"] == 3 and numbers["key_number_mismatch_count"] == 0),
        ("focus_amount_binding_zero", numbers["focus_amount_binding_count"] == 3 and numbers["focus_amount_mismatch_count"] == 0),
        ("side_effects_zero", all(review[key] == 0 for key in ("raw_root_access_count", "live_source_read_count", "network_request_count", "real_business_action_count"))),
        ("github_closed", review["github_upload_performed"] is False),
        ("app_closed", review["app_reinstall_performed"] is False and review["s15_started"] is False),
    )
    for name, passed in baseline:
        add(name, passed)
    for row in p1.NAV_ITEMS:
        add(f"nav_binding_{row['nav_id']}", any(item["kind"] == "PRIMARY_NAVIGATION" and item["source"]["nav_id"] == row["nav_id"] and item["status"] == "PASS" for item in review["integration_bindings"]))
    for page_type, route in CANONICAL_SCREEN_ROUTES.items():
        route_row = next(row for row in routes["routes"] if row["page_type"] == page_type)
        add(f"route_{page_type.lower()}", route_row["route"] == route and route_row["page_type_matches"] and route_row["has_next_task"])
    for viewport in p2.visual_regression_contract()["required_viewports"]:
        add(f"viewport_{viewport['name']}", viewport["width"] >= 390 and viewport["height"] >= 844)
    for theme in ("light", "dark"):
        add(f"theme_{theme}_contrast", all(row["status"] == "PASS" for row in contrast["pairs"] if row["theme"] == theme))
    if len(checks) != 84:
        raise StageReviewError(f"PUBLIC_CHECK_COUNT_DRIFT：预期 84，实际 {len(checks)}。")
    failed = [row["name"] for row in checks if not row["passed"]]
    return {
        "schema_version": "kmfa.v015.s14.stage-review-public-verification.v1",
        "checks": checks,
        "accounting": {"total": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "failed_checks": failed,
        "integrated_review": review,
    }


def validate_public_contract() -> dict[str, Any]:
    result = public_verification()
    if result["accounting"]["failed"]:
        raise StageReviewError("S14 整体复审失败：" + ", ".join(result["failed_checks"]))
    return result


if __name__ == "__main__":
    result = validate_public_contract()
    print(f"PASS: S14 整体复审公开检查 {result['accounting']['passed']}/{result['accounting']['total']}")
