#!/usr/bin/env python3
"""ADP V0.1 Source Registry compiler (ADP-S1-P02-T014).

From ONE source (source_registry.json) deterministically compiles:
  - runtime.json   : sources the worker reads (id/board/method/feed/enabled/authority)
  - ui_labels.json : display labels + official/discovery badge
  - seed.sql       : deterministic D1 cn_sources INSERT statements
  - registry_hash  : sha256 over the canonical registry (written into each output)

Determinism: outputs are sorted by source_id with sorted keys and carry NO
timestamps, so two consecutive compiles are byte-identical. The compiler FAILS
(exit 1) on: duplicate source_id, a non-boolean `enabled`, or an unknown
`authority_kind`. It also runs the T012 schema/hard-rule validator.

Usage: python3 compile_registry.py [--registry PATH] [--out-dir DIR]
"""
import argparse, hashlib, json, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
DEFAULT_REG = V01 / "source_registry.json"
DEFAULT_OUT = V01 / "compiled"
AUTHORITY_KINDS = {"china_official", "intl_official", "journal", "preprint", "media", "search", "aggregator"}
NON_OFFICIAL = {"media", "search", "aggregator"}


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hard_checks(reg):
    problems = []
    seen = {}
    for s in reg.get("sources", []):
        sid = s.get("source_id", "<missing>")
        seen[sid] = seen.get(sid, 0) + 1
        if not isinstance(s.get("enabled"), bool):
            problems.append(f"{sid}: enabled must be boolean, got {s.get('enabled')!r}")
        if s.get("authority_kind") not in AUTHORITY_KINDS:
            problems.append(f"{sid}: unknown authority_kind {s.get('authority_kind')!r}")
    dupes = sorted(k for k, n in seen.items() if n > 1)
    if dupes:
        problems.append(f"duplicate source_id(s): {dupes}")
    return problems


def sql_escape(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    return "'" + str(v).replace("'", "''") + "'"


def compile_reg(reg):
    reg_hash = "sha256:" + hashlib.sha256(canonical(reg).encode("utf-8")).hexdigest()
    srcs = sorted(reg.get("sources", []), key=lambda s: s["source_id"])
    runtime = {"registry_hash": reg_hash, "sources": [
        {"source_id": s["source_id"], "board": s["board"], "method": s.get("method"),
         "feed_url": s.get("feed_url", ""), "enabled": s["enabled"],
         "authority_kind": s["authority_kind"], "official_evidence": s["official_evidence"]}
        for s in srcs]}
    ui = {"registry_hash": reg_hash, "labels": [
        {"source_id": s["source_id"], "name": s.get("name", s["source_id"]), "board": s["board"],
         "badge": ("official" if s["official_evidence"] else "discovery"),
         "authority": (s.get("authority_level") or s["authority_kind"])}
        for s in srcs]}
    lines = [f"-- ADP cn_sources seed (compiled; registry_hash {reg_hash})",
             "-- deterministic order by source_id; regenerate via tools/compile_registry.py"]
    for s in srcs:
        cols = "source_id, name, board, method, feed_url, enabled, authority_kind, official_evidence"
        vals = ", ".join([sql_escape(s["source_id"]), sql_escape(s.get("name", "")),
                          sql_escape(s["board"]), sql_escape(s.get("method")),
                          sql_escape(s.get("feed_url", "")), sql_escape(s["enabled"]),
                          sql_escape(s["authority_kind"]), sql_escape(s["official_evidence"])])
        lines.append(f"INSERT INTO cn_sources ({cols}) VALUES ({vals});")
    seed_sql = "\n".join(lines) + "\n"
    return reg_hash, runtime, ui, seed_sql


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=str(DEFAULT_REG))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    reg = json.loads(pathlib.Path(args.registry).read_text(encoding="utf-8"))

    # T012 schema/hard-rule validation first
    sys.path.insert(0, str(HERE))
    import validate_source_registry as vsr
    vproblems, _ = vsr.validate(reg)
    problems = vproblems + hard_checks(reg)
    if problems:
        print("COMPILE: FAIL")
        for p in problems:
            print("  - " + p)
        sys.exit(1)

    reg_hash, runtime, ui, seed_sql = compile_reg(reg)
    out = pathlib.Path(args.out_dir)
    out.mkdir(exist_ok=True)
    (out / "runtime.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "ui_labels.json").write_text(json.dumps(ui, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "seed.sql").write_text(seed_sql, encoding="utf-8")
    (out / "registry_hash.txt").write_text(reg_hash + "\n", encoding="utf-8")
    print("COMPILE: OK")
    print(f"  registry_hash: {reg_hash}")
    print(f"  sources: {len(runtime['sources'])}")
    print(f"  outputs: runtime.json, ui_labels.json, seed.sql, registry_hash.txt -> {out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
