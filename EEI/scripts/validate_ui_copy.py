from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = ROOT / "data" / "ui_copy_lexicon.csv"
UI_ROOT = ROOT / "apps" / "web" / "src" / "app"

VISIBLE_ATTRIBUTE_RE = re.compile(r'\b(?:aria-label|title|placeholder)="([^"]+)"')
JSX_TEXT_RE = re.compile(r">([^<>{}][^<>]*)<")
RENDERED_PROPERTY_RE = re.compile(
    r'\b(?:label|name|heading|subtitle|summary|description|change|overlay|role|stage|fixtureNotice|notes|state|path)\s*:\s*"([^"]+)"'
)


def load_forbidden_terms() -> list[str]:
    with LEXICON_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = csv.DictReader(handle)
        terms = [
            row["internal_term"].strip()
            for row in rows
            if row.get("context", "").strip().lower() == "forbidden"
        ]
    return sorted(set([*terms, "graph database", "neo4j", "cypher"]))


def visible_copy_candidates(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    candidates: list[str] = []
    candidates.extend(match.group(1) for match in JSX_TEXT_RE.finditer(source))
    candidates.extend(match.group(1) for match in VISIBLE_ATTRIBUTE_RE.finditer(source))
    candidates.extend(match.group(1) for match in RENDERED_PROPERTY_RE.finditer(source))
    return [" ".join(candidate.split()) for candidate in candidates if candidate.strip()]


def term_pattern(term: str) -> re.Pattern[str]:
    if " " in term:
        return re.compile(re.escape(term), re.IGNORECASE)
    return re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)


def main() -> int:
    forbidden_terms = load_forbidden_terms()
    patterns = [(term, term_pattern(term)) for term in forbidden_terms]
    violations: list[str] = []

    for path in sorted(UI_ROOT.rglob("*.tsx")):
        relative = path.relative_to(ROOT)
        for candidate in visible_copy_candidates(path):
            for term, pattern in patterns:
                if pattern.search(candidate):
                    violations.append(
                        f"{relative}: forbidden '{term}' in visible copy: {candidate}"
                    )

    if violations:
        print("UI copy validation: FAIL")
        for violation in violations:
            print(f"  - {violation}")
        return 1

    print("UI copy validation: PASS")
    print(f"  forbidden_terms={','.join(forbidden_terms)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
