from __future__ import annotations

from typing import Mapping


def authority_badge(source: Mapping[str, object]) -> str:
    tier = source.get("effective_tier") or "?"
    score = source.get("effective_score")
    name = source.get("name") or "Unknown source"
    sponsor = source.get("sponsor_unit") or source.get("supervisor_unit") or "unverified sponsor"
    score_text = "NA" if score is None else str(score)
    return f"{tier} / {score_text} / {name} / {sponsor}"
