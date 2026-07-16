#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic fixtures + report generator for ADP-S5-P02-T062 (version / as-of / diff API).

Builds:
  * a single canonical document with a v1 render, a SUBSTANTIVE v2 render (one add + one delete +
    one modify), and a NOISE-ONLY re-render (same substance + template chrome);
  * a small multi-document corpus of dated versions for the as-of no-future-leakage battery.
No network, no clock, no randomness. Fixtures are literals so the verifier can re-derive.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent.parent
sys.path.insert(0, str(V01 / "tools"))
import version_asof_api as API
import coverage_asof as CA

CID = "gov-cn::guobanfa-2026-17"

# ---- v1 substantive body (4 lines) -------------------------------------------------------------
V1_BODY = "\n".join([
    "国务院办公厅关于推进政务数据共享的指导意见",
    "第一条 各地区各部门应当建立数据共享机制。",
    "第二条 数据共享应当遵循安全可控原则。",
    "第三条 本意见自发布之日起施行。",
])
# ---- v2 substantive: modify line 2, delete line 3, add a new article -----------------------------
V2_BODY = "\n".join([
    "国务院办公厅关于推进政务数据共享的指导意见",
    "第一条 各地区各部门应当建立健全数据共享机制。",   # modify (健全 added)
    # (第二条 deleted)
    "第三条 本意见自发布之日起施行。",
    "第四条 建立数据共享考核评价制度。",                 # add
])
# ---- noise-only re-render: SAME substance as v1 + pure template chrome ---------------------------
NOISE_LINES = [
    "版权所有 © 2026 国务院办公厅",
    "责任编辑：张三",
    "分享到微信",
    "阅读 12,345",
    "发布于 3 分钟前",
    "京ICP备12345号",
]
V1_NOISE_BODY = V1_BODY + "\n" + "\n".join(NOISE_LINES)

R_V1 = {"canonical_id": CID, "body": V1_BODY, "status": "published", "observed_at": "2026-03-01"}
R_V2 = {"canonical_id": CID, "body": V2_BODY, "status": "published", "observed_at": "2026-06-01"}
R_V1_NOISE = {"canonical_id": CID, "body": V1_NOISE_BODY, "status": "published", "observed_at": "2026-04-01"}


def build_asof_corpus():
    """Multi-document dated versions for the as-of no-future-leakage battery (>=100 samples)."""
    docs = []
    for n in range(1, 9):
        cid = f"gov-cn::doc-{n:02d}"
        docs.append({"canonical_id": cid, "body": f"文件{n} 第一版正文内容第一条。",
                     "status": "published", "observed_at": f"2026-0{ (n % 6) + 1 }-05"})
        docs.append({"canonical_id": cid, "body": f"文件{n} 修订版正文内容第一条与第二条。",
                     "status": "amended", "observed_at": f"2026-0{ (n % 6) + 1 }-20"})
    grouped = {}
    for d in docs:
        grouped.setdefault(d["canonical_id"], []).append(d)
    return grouped


def main():
    timeline_subst = API.version_timeline([R_V1, R_V2])
    timeline_noise = API.version_timeline([R_V1, R_V1_NOISE])
    dp_subst = API.diff_payload(R_V1, R_V2)
    dp_noise = API.diff_payload(R_V1, R_V1_NOISE)

    report = {
        "canonical_id": CID,
        "timeline_substantive": timeline_subst,
        "timeline_noise_versions": len(timeline_noise),
        "diff_substantive": dp_subst,
        "diff_noise_only": dp_noise,
        "as_of_examples": {
            "2026-02-01": API.as_of(timeline_subst, "2026-02-01"),
            "2026-04-15": (API.as_of(timeline_subst, "2026-04-15") or {}).get("version_no"),
            "2026-07-01": (API.as_of(timeline_subst, "2026-07-01") or {}).get("version_no"),
        },
        "replay_v1": API.replay_version(timeline_subst, 1),
        "replay_v1_idempotent": API.replay_is_idempotent(timeline_subst, 1),
    }
    (HERE / "version_asof_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("timeline_substantive versions:", len(timeline_subst))
    print("timeline_noise versions:", len(timeline_noise))
    print("diff_substantive counts:", dp_subst["counts"], "changed:", dp_subst["changed"])
    print("diff_noise_only changed:", dp_noise["changed"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
