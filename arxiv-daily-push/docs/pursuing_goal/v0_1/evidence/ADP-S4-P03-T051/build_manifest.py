#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ADP-S4-P03-T051 -- build the key-city A1 cohort manifest (deterministic; reachability from recon).

Emits city_cohort_manifest.json: the value-ranked admitted cohort (each with official identity + a
2016 cursor), the value-tiered onboarding waves, and the rejected low-value / non-official sources.
`reachability` is the real server-side observation captured during recon (honest metadata; NOT the
admission gate). No production side effects.
"""
import sys, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import city_cohort as C

# server-side reachability observed during T051 recon (stdlib fetch from a server env)
REACHABILITY = {
    "suzhou-gov": "reachable_news_only", "shenzhen-gov": "js_rendered", "guangzhou-gov": "js_rendered",
    "wuhan-gov": "js_rendered", "shanghai-gov": "js_rendered", "chongqing-gov": "js_rendered",
    "tianjin-gov": "tls_blocked", "qingdao-gov": "tls_blocked", "ningbo-gov": "tls_blocked",
    "xiamen-gov": "tls_blocked", "dalian-gov": "unknown", "hangzhou-gov": "tls_blocked",
    "nanjing-gov": "tls_blocked", "chengdu-gov": "tls_blocked", "xian-gov": "unknown",
    "dongguan-gov": "unknown", "foshan-gov": "tls_blocked", "wuxi-gov": "tls_blocked",
}

def main():
    res = C.select_cohort(reachability=REACHABILITY)
    waves = C.plan_waves(res["admitted"])
    manifest = {
        "task": "ADP-S4-P03-T051",
        "cohort_id": "A1-CITY-WAVE",
        "selection_principle": "value-tiered, not volume: admit only value >= stop AND a verified A1 official original publisher",
        "stop_threshold": res["stop_threshold"],
        "candidates": res["candidates"],
        "admitted_count": len(res["admitted"]),
        "rejected_count": len(res["rejected"]),
        "waves": waves,
        "admitted": res["admitted"],
        "rejected": res["rejected"],
        "note_original_fetch": ("City portals are largely JS-rendered / TLS-hardened server-side; original "
                                "fetch is a later batch (T050 mechanism) once a headless fetcher reaches them. "
                                "The municipality tier is proven fetchable by Beijing (T049/T050 province cohort)."),
        "cost": {"production_new_requests": 0, "d1_rows_read": 0, "d1_rows_written": 0,
                 "r2_bytes": 0, "r2_ops": 0, "model_calls": 0,
                 "human_maintenance": "value model + curated city candidates + recon"},
        "deployment": "SHADOW (cohort manifest + identity + cursors; production worker/cron untouched)",
    }
    (HERE / "city_cohort_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"admitted={len(res['admitted'])} rejected={len(res['rejected'])} waves={ {k: len(v) for k, v in waves.items()} }")
    for a in res["admitted"][:5]:
        print(f"  {a['value']:.3f} {a['tier']:20} {a['city']} cursor={a['cursor_2016']['start_month']} fetch={a['original_fetch_status']}")
    for r in res["rejected"]:
        print(f"  REJECT {r['source_id']}: {r['reason']}")

if __name__ == "__main__":
    main()
