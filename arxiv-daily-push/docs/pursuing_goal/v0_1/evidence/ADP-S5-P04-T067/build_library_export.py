#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + report for ADP-S5-P04-T067 (Library / notes / Provenance export)."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import library_export as LX

# Fully-provenanced saved items (source_url, version, fetched_at, claim_evidence, license).
ITEMS = [
    {"canonical_id": "arxiv:2401.00001", "title": "Deep Learning for Protein Folding",
     "source_url": "https://arxiv.org/abs/2401.00001", "version": "v2 (sha256:ab12cd)",
     "fetched_at": "2026-07-10T08:00:00+10:00",
     "claim_evidence": "abstract §1: 'accuracy 92% on the test set' [offset 128]",
     "license": "arXiv non-exclusive license 1.0 — cite the original"},
    {"canonical_id": "gov-cn::guobanfa-2026-1", "title": "关于推进政务数据共享的意见",
     "source_url": "https://www.gov.cn/zhengce/guobanfa-2026-1", "version": "v1 (sha256:ef34gh)",
     "fetched_at": "2026-07-11T09:30:00+10:00",
     "claim_evidence": "第一条『建立数据共享机制』[offset 0]",
     "license": "中国政府网 公开政策原文 — 注明来源"},
]

# An item whose values contain format-hostile characters (comma, double-quote, newline) so CSV/MD
# integrity can be attacked: these must still round-trip losslessly.
TRICKY_ITEM = {"canonical_id": "arxiv:2402.55555",
               "title": 'Study of "attention", scaling\nand cost',
               "source_url": "https://arxiv.org/abs/2402.55555",
               "version": "v3 (sha256:zz99)",
               "fetched_at": "2026-07-12T12:00:00+10:00",
               "claim_evidence": 'result: "3.2x, faster"\nsee Table 1 [offset 640]',
               "license": "arXiv non-exclusive; do not, redistribute"}

# A deliberately UNDER-provenanced item (missing license + claim_evidence) -> must be refused.
BAD_ITEM = {"canonical_id": "x:no-prov", "title": "No provenance",
            "source_url": "https://x/y", "version": "v1", "fetched_at": "2026-07-12"}


def build_library():
    lib = LX.new_library("my-research")
    LX.add_to_library(lib, ITEMS[0], note="key result", collection="protein")
    LX.add_to_library(lib, ITEMS[1], note="policy baseline", collection="china-policy")
    LX.add_to_library(lib, TRICKY_ITEM, note='has, "commas" and\nnewlines', collection="edge")
    return lib


def main():
    lib = build_library()
    report = {
        "n_entries": len(lib["entries"]),
        "formats": {
            "markdown": LX.export_markdown(lib),
            "csv": LX.export_csv(lib),
            "json": LX.export_json(lib),
        },
        "provenance_fields": list(LX.PROVENANCE_FIELDS),
    }
    (HERE / "library_export_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # also drop the three concrete export artifacts for inspection
    (HERE / "export_sample.md").write_text(report["formats"]["markdown"], encoding="utf-8")
    (HERE / "export_sample.csv").write_text(report["formats"]["csv"], encoding="utf-8")
    (HERE / "export_sample.json").write_text(report["formats"]["json"] + "\n", encoding="utf-8")
    print("n_entries:", len(lib["entries"]))
    print("formats:", list(report["formats"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
