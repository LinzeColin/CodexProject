#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T059 -- build the bounded, evidence-backed cross-board relation graph + query examples."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import evidence_relation as R

ASSERTIONS = [
    ("苏政办函〔2026〕39号", "policy", "implements", "国办函〔2025〕X号", "policy",
     {"doc_id": "ttl:jiangsu-39", "fragment": "根据《国办函〔2025〕X号》...结合本省实际制定", "source_id": "jiangsu-gov"}),
    ("苏采〔2026〕7号", "procurement", "procurement_under", "苏政办函〔2026〕39号", "policy",
     {"doc_id": "ttl:proc-7", "fragment": "为落实苏政办函〔2026〕39号...开展采购", "source_id": "jiangsu-gov"}),
    ("鲁科字〔2023〕143号", "policy", "references_standard", "GB/T 12345", "standard",
     {"doc_id": "ttl:shandong-143", "fragment": "按GB/T 12345执行验收", "source_id": "shandong-gov"}),
    ("某试点", "pilot", "pilot_under", "苏政办函〔2026〕39号", "policy",
     {"doc_id": "ttl:pilot-1", "fragment": "本试点依据苏政办函〔2026〕39号开展", "source_id": "jiangsu-gov"}),
    # evidence-free inference -> must be marked, NOT saved
    ("苏政办函〔2026〕39号", "policy", "supported_by_stat", "2026年江苏GDP", "statistic", None),
    # off-vocabulary -> refused
    ("some-paper", "paper", "implements", "苏政办函〔2026〕39号", "policy", {"doc_id": "x", "fragment": "y"}),
    # unknown board kind -> refused
    ("x", "tweet", "cites", "苏政办函〔2026〕39号", "policy", {"doc_id": "x", "fragment": "y"}),
]

def main():
    g = R.build_graph(ASSERTIONS)
    report = {
        "task": "ADP-S5-P01-T059",
        "relation_types": g["relation_types"],
        "assertions_in": g["assertions_in"], "saved": g["saved"], "refused": g["refused"],
        "inferred_unsaved": g["inferred_unsaved"], "every_saved_has_evidence": g["every_saved_has_evidence"],
        "audit": g["audit"],
        "query_examples": {
            "procurement_under_苏政办函39": [r["subject"] for r in R.query(g["graph"], predicate="procurement_under")],
            "implements_from_苏政办函39": [r["object"] for r in R.query(g["graph"], subject="苏政办函〔2026〕39号", predicate="implements")],
        },
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "relation-layer authoring"},
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "relation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"assertions={g['assertions_in']} saved={g['saved']} refused={g['refused']} "
          f"inferred_unsaved={g['inferred_unsaved']} every_saved_has_evidence={g['every_saved_has_evidence']}")

if __name__ == "__main__":
    main()
