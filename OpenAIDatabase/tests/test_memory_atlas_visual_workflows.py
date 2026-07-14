import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_memory_atlas_data.py"
P0_VISUAL_IDS = (
    "cluster_tree",
    "bubble_map",
    "topic_cluster_explorer",
    "task_treemap",
    "automation_vs_augmentation",
    "roi_scatter",
    "opportunity_radar",
    "agent_decision_sankey",
    "friction_heatmap",
    "latent_radar",
    "evidence_timeline",
    "formula_explorer",
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_memory_atlas_data_r6", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def visual_map_payload() -> dict:
    visuals = []
    for index, visual_id in enumerate(P0_VISUAL_IDS):
        visuals.append(
            {
                "id": visual_id,
                "family": "clio_like" if index < 3 else "economic_like" if index < 7 else "workflow_governance",
                "title": f"图表 {index + 1}",
                "insight_header_zh": f"第 {index + 1} 张图先给出结论",
                "human_question_zh": f"第 {index + 1} 张图回答什么问题？",
                "action_value_zh": f"第 {index + 1} 张图支持下一步行动。",
                "filter_dimensions": ["source", "time", "project", "task"],
                "visual_roi_gate_pass": True,
                "p0_included": True,
                "private_note": "must-not-export",
            }
        )
    return {
        "schema_version": "human_question_map.v1_2_s11_p4",
        "filter_dimensions": ["source", "time", "project", "task"],
        "visuals": visuals,
        "excluded_candidates": [
            {
                "id": "decorative_density_cloud",
                "title": "装饰性密度云",
                "reason_zh": "没有决策价值。",
                "visual_roi_gate_pass": False,
                "p0_included": False,
                "raw_payload": "must-not-export",
            }
        ],
    }


def event_payload() -> dict:
    return {
        "schema_version": "memory_atlas_behavior_events.v1_2_s05_review",
        "events": [
            {
                "event_id": "event_late",
                "occurred_at": "2026-07-01T05:50:04Z",
                "source_id": "codex",
                "project": "Memory Atlas",
                "task_type": "engineering",
                "topic": "R6 可视化验收",
                "intent": "implementation",
                "friction": ["scope_creep"],
                "value_signal": ["reusable_asset"],
                "evidence_refs": [
                    {
                        "ref_id": f"ref_{index}",
                        "ref_type": "manifest",
                        "source_id": "codex",
                        "evidence_level": "processed_manifest",
                        "path": "data/processed/codex/codex_session_manifest.jsonl",
                        "reason": "",
                    }
                    for index in range(5)
                ],
                "transcript_text": "PRIVATE TRANSCRIPT MUST NOT EXPORT",
                "access_token": "SECRET TOKEN MUST NOT EXPORT",
            },
            {
                "event_id": "event_old",
                "occurred_at": "2025-12-01T00:00:00Z",
                "source": "chatgpt",
                "project": None,
                "task_type": "unknown",
                "topic": "旧主题",
                "intent": "research",
                "friction": [],
                "value_signal": [],
                "evidence_refs": [
                    {
                        "ref_id": "old_ref",
                        "ref_type": "missing_reason",
                        "source_id": "chatgpt",
                        "evidence_level": "missing_reason",
                        "path": "",
                        "reason": "processed_manifest_without_public_raw_ref",
                    }
                ],
            },
            {
                "event_id": "event_no_date",
                "occurred_at": "",
                "source_id": "codex",
                "project": "Finance",
                "task_type": "data",
                "topic": "无日期事件",
                "intent": "analysis",
                "friction": ["evidence_gap"],
                "value_signal": ["decision_support"],
                "evidence_refs": [],
            },
        ],
    }


def formula_payload() -> dict:
    return {
        "schema_version": "memory_atlas_formula_what_if_preview.v1_2_s07_p3",
        "simulator_mode": "config_preview_only",
        "base_score": 74,
        "human_readable_summary_zh": "仅用于比较内部 proxy，不写入配置。",
        "parameters": {
            "score_floor": 0,
            "score_ceiling": 100,
            "neutral_rework_score": 50,
            "rework_penalty_scale": 0.35,
            "default_weights": {
                "time_saved_weight": 1.0,
                "reuse_value_weight": 1.0,
                "opportunity_value_weight": 1.0,
                "skill_compounding_weight": 1.0,
                "automation_alignment_weight": 1.0,
                "rework_cost_weight": 1.0,
                "low_value_loop_penalty_weight": 1.0,
            },
            "adjustable_weight_bounds": {
                key: {"min": 0.25, "max": 2.0, "step": 0.05, "explanation_zh": f"调整 {key}。"}
                for key in (
                    "time_saved_weight",
                    "reuse_value_weight",
                    "opportunity_value_weight",
                    "skill_compounding_weight",
                    "automation_alignment_weight",
                    "rework_cost_weight",
                    "low_value_loop_penalty_weight",
                )
            },
        },
        "formulas": [
            {
                "formula_id": "FORM-MA-V12-S07P3-001",
                "expression_zh": "What-if 分 = clamp(加权正向 proxy 分 - 返工惩罚, 0, 100)",
                "interpretation_zh": "不是精确收入预测，也不是财务建议。",
            }
        ],
        "scenarios": [
            {
                "scenario_id": "baseline",
                "name_zh": "基线权重",
                "weighted_proxy_score": 80,
                "adjustable_weights": {
                    "time_saved_weight": 1.0,
                    "reuse_value_weight": 1.0,
                    "opportunity_value_weight": 1.0,
                    "skill_compounding_weight": 1.0,
                    "automation_alignment_weight": 1.0,
                    "rework_cost_weight": 1.0,
                    "low_value_loop_penalty_weight": 1.0,
                },
                "score_components": {
                    "rework_score": 45.0,
                    "signals": {
                        "time_saved_proxy": {"score": 100.0},
                        "reuse_value_proxy": {"score": 88.0},
                        "opportunity_score_proxy": {"score": 86.0},
                        "skill_compounding_proxy": {"score": 100.0},
                        "automation_enhancement_ratio_proxy": {"score": 27.0},
                    },
                },
                "parameter_change_proposal": {
                    "active_config_write": False,
                    "proposal_required_before_apply": True,
                    "target_active_config": "机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json",
                },
            },
            {
                "scenario_id": "reuse_asset_first",
                "name_zh": "复用资产优先",
                "weighted_proxy_score": 82,
                "adjustable_weights": {"reuse_value_weight": 1.4},
            },
        ],
        "phase_boundary": {
            "does_not_modify_raw": True,
            "does_not_mutate_active_formula_config": True,
            "does_not_provide_financial_advice": True,
            "does_not_claim_precise_income_prediction": True,
            "requires_proposal_before_apply": True,
        },
        "private_prompt": "MUST NOT EXPORT",
    }


class MemoryAtlasVisualWorkflowDataTests(unittest.TestCase):
    def test_snapshot_exports_exact_redacted_visual_workflow_contract(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            write_jsonl(
                database_dir / "data/memory/active/active_memory.jsonl",
                [
                    {
                        "id": "memory_fixture",
                        "date": "2026-07-01",
                        "statement": "Memory Atlas R6 derived fixture",
                        "memory_tier": "核心画像",
                        "category": "workflow",
                        "importance": "高",
                        "validity": "长期",
                        "confidence": "high",
                    }
                ],
            )
            visual_map_path = database_dir / "机器治理/可视化配置/human_question_map.v1_2_s11_p4.json"
            events_path = database_dir / "data/derived/behavior_intelligence/events.json"
            formula_path = database_dir / "data/derived/economic_proxy/formula_what_if_preview.json"
            write_json(visual_map_path, visual_map_payload())
            write_json(events_path, event_payload())
            write_json(formula_path, formula_payload())
            source_hashes = {path: sha256(path) for path in (visual_map_path, events_path, formula_path)}

            atlas = module.build_memory_atlas(database_dir)

            self.assertEqual(source_hashes, {path: sha256(path) for path in source_hashes})

        registry = atlas["visual_workflows"]
        self.assertEqual(registry["schema_version"], "memory_atlas_visual_workflows.v1_2_r6")
        self.assertEqual(registry["p0_visual_count"], 12)
        self.assertEqual(tuple(item["id"] for item in registry["visuals"]), P0_VISUAL_IDS)
        self.assertEqual(registry["filter_dimensions"], ["source", "time", "project", "task"])
        self.assertTrue(all(item["human_question_zh"] and item["action_value_zh"] for item in registry["visuals"]))
        self.assertTrue(all(set(item) == {
            "id",
            "family",
            "title_zh",
            "insight_header_zh",
            "human_question_zh",
            "action_value_zh",
            "visual_roi_gate_pass",
            "p0_included",
        } for item in registry["visuals"]))
        self.assertEqual(registry["excluded_candidates"][0]["id"], "decorative_density_cloud")

        behavior = atlas["behavior_intelligence"]
        self.assertEqual(behavior["facet_event_count"], 3)
        self.assertEqual([item["event_id"] for item in behavior["facet_events"]], ["event_old", "event_late", "event_no_date"])
        self.assertEqual(behavior["facet_events"][0]["project"], "未标注")
        self.assertEqual(behavior["facet_events"][0]["task_type"], "未标注")
        self.assertEqual(len(behavior["facet_events"][1]["evidence_refs"]), 3)
        self.assertEqual(behavior["facet_filter_options"]["source"], ["chatgpt", "codex"])
        self.assertEqual(behavior["facet_filter_options"]["project"], ["Finance", "Memory Atlas", "未标注"])
        self.assertEqual(behavior["facet_filter_options"]["task"], ["data", "engineering", "未标注"])

        formula = atlas["formula_what_if"]
        self.assertEqual(formula["schema_version"], "memory_atlas_formula_what_if_display.v1_2_r6")
        self.assertEqual(formula["default_weights"]["time_saved_weight"], 1.0)
        self.assertEqual(formula["adjustable_weight_bounds"]["reuse_value_weight"]["max"], 2.0)
        self.assertEqual(formula["baseline_signals"]["time_saved_proxy"], 100.0)
        self.assertEqual(formula["rework_score"], 45.0)
        self.assertEqual(formula["score_floor"], 0)
        self.assertEqual(formula["score_ceiling"], 100)
        self.assertEqual(formula["neutral_rework_score"], 50)
        self.assertEqual(formula["rework_penalty_scale"], 0.35)
        self.assertEqual([item["scenario_id"] for item in formula["scenarios"]], ["baseline", "reuse_asset_first"])
        self.assertEqual(
            formula["safety"],
            {
                "active_config_write": False,
                "proposal_required_before_apply": True,
                "raw_mutation": False,
                "financial_advice": False,
                "precise_income_prediction": False,
            },
        )

        serialized = json.dumps(
            {
                "visual_workflows": registry,
                "facet_events": behavior["facet_events"],
                "formula_what_if": formula,
            },
            ensure_ascii=False,
        )
        for forbidden in (
            "PRIVATE TRANSCRIPT MUST NOT EXPORT",
            "SECRET TOKEN MUST NOT EXPORT",
            "MUST NOT EXPORT",
            "private_note",
            "raw_payload",
            "transcript_text",
            "access_token",
            "private_prompt",
            "target_active_config",
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
