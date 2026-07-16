#!/usr/bin/env python3
"""ADP V0.1 Source Registry validator (ADP-S1-P02-T012).

Validates a source registry JSON against schemas/source_registry.schema.json and
enforces the two hard acceptance rules on top of the schema:
  1. a china_official source MUST carry an authority_level in {A0, A1, A2}
     (any other China official level -- A3+, B/C/D, or missing -- fails);
  2. a media/search/aggregator source MUST NOT be marked official_evidence: true.
Also checks source_id uniqueness across the whole registry.

Exit 0 => VALID; exit 1 => INVALID. Read-only.

Usage: python3 validate_source_registry.py <registry.json>
"""
import argparse, json, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
SCHEMA = HERE.parent / "schemas" / "source_registry.schema.json"
CHINA_LEVELS = {"A0", "A1", "A2"}
NON_OFFICIAL_KINDS = {"media", "search", "aggregator"}


def validate(reg):
    problems = []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        import jsonschema
        jsonschema.validate(reg, schema)
    except ImportError:
        problems.append("(jsonschema not installed -- ran hard-rule checks only)")
    except Exception as e:
        problems.append(f"schema violation: {getattr(e,'message',str(e))[:200]}")

    seen = {}
    for s in reg.get("sources", []):
        sid = s.get("source_id", "<missing>")
        seen[sid] = seen.get(sid, 0) + 1
        kind = s.get("authority_kind")
        if kind == "china_official":
            lvl = s.get("authority_level")
            if lvl not in CHINA_LEVELS:
                problems.append(f"{sid}: china_official authority_level {lvl!r} not in A0/A1/A2")
        if kind in NON_OFFICIAL_KINDS and s.get("official_evidence") is True:
            problems.append(f"{sid}: {kind} source must not be official_evidence=true")
    dupes = [k for k, n in seen.items() if n > 1]
    if dupes:
        problems.append(f"duplicate source_id(s): {dupes}")
    return [p for p in problems if not p.startswith("(")], [p for p in problems if p.startswith("(")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("registry")
    args = ap.parse_args()
    reg = json.loads(pathlib.Path(args.registry).read_text(encoding="utf-8"))
    problems, notes = validate(reg)
    print(f"registry: {args.registry} ({len(reg.get('sources', []))} sources)")
    for n in notes:
        print("  note: " + n)
    if problems:
        print("RESULT: INVALID")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("RESULT: VALID")
    sys.exit(0)


if __name__ == "__main__":
    main()
