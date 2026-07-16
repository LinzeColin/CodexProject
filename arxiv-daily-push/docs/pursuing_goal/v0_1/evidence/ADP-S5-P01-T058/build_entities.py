#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S5-P01-T058 -- resolve cross-source entity mentions + emit schema/aliases/provenance/audit."""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import entity_resolver as ER

MENTIONS = [
    {"name": "国家统计局", "type": "agency", "source_id": "stats-gov", "aliases": ["统计局", "NBS"]},
    {"name": "NBS", "type": "agency", "source_id": "media-x"},
    {"name": "国务院办公厅", "type": "agency", "source_id": "gov-cn-policy", "aliases": ["国办"]},
    {"name": "国办", "type": "agency", "source_id": "media-y"},
    {"name": "江苏省人民政府", "type": "agency", "source_id": "jiangsu-gov", "aliases": ["苏政府"]},
    {"name": "国家发展和改革委员会", "type": "agency", "source_id": "ndrc-gov", "aliases": ["发改委", "NDRC"]},
    {"name": "发改委", "type": "agency", "source_id": "media-z"},
]

def main():
    ents = ER.resolve(MENTIONS)
    ids = list(ents)
    # demonstrate a reversible WRONG merge (two genuinely different agencies) with a full audit
    a, b = ids[0], ids[2]
    merged, audit = ER.merge(ents, a, b, evidence="operator error (same-day mention)", confidence=0.95)
    restored = ER.split(merged, audit)
    reversible = (restored[a] == ents[a] and restored[b] == ents[b] and len(restored) == len(ents))
    # a low-confidence merge is held for review, not applied
    _, weak_audit = ER.merge(ents, a, b, evidence="weak name overlap", confidence=0.5)

    report = {
        "task": "ADP-S5-P01-T058",
        "mentions_in": len(MENTIONS), "entities_out": len(ents),
        "entities": [{"entity_id": e["entity_id"], "type": e["type"], "canonical_name": e["canonical_name"],
                      "aliases": e["aliases"], "provenance": ER.provenance_of(e), "confidence": e["confidence"]}
                     for e in ents.values()],
        "merge_split_audit": {
            "wrong_merge_applied": audit["status"], "wrong_merge_reversible": reversible,
            "audit_id": audit["audit_id"], "kept": audit["kept"], "absorbed": audit["absorbed"],
            "low_confidence_merge_status": weak_audit["status"], "auto_merge_min": ER.AUTO_MERGE_MIN,
        },
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0, "r2_bytes": 0,
                 "r2_ops": 0, "model_calls": 0, "human_maintenance": "entity-resolver authoring"},
        "deployment": "NOT_DEPLOYED",
    }
    (HERE / "entity_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"mentions={len(MENTIONS)} entities={len(ents)} wrong_merge_reversible={reversible} "
          f"low_conf_status={weak_audit['status']}")

if __name__ == "__main__":
    main()
