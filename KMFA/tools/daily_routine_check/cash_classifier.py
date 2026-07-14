from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    matched_features: list[str]
    conflicts: list[str]
    needs_review: bool


def classify_text(text: str, feature_profiles: dict[str, Any]) -> ClassificationResult:
    """Config-driven document classifier.

    This intentionally avoids hard-coded Chinese business keywords. Profiles are
    supplied by YAML metadata.
    """
    text = text or ""
    best_type = "unknown"
    best_score = 0.0
    best_features: list[str] = []
    conflicts: list[str] = []

    for profile_name, profile in feature_profiles.items():
        positives = profile.get("strong_positive_features", []) or []
        negatives = profile.get("strong_negative_features", []) or []
        score = 0.0
        matched = []
        for k in positives:
            if k and k in text:
                score += 1.0
                matched.append(k)
        for k in negatives:
            if k and k in text:
                score -= 0.75
                conflicts.append(f"{profile_name}:{k}")
        if score > best_score:
            best_type = profile_name
            best_score = score
            best_features = matched

    confidence = min(1.0, best_score / 5.0) if best_score > 0 else 0.0
    return ClassificationResult(
        document_type=best_type,
        confidence=confidence,
        matched_features=best_features,
        conflicts=conflicts,
        needs_review=confidence < 0.80 or bool(conflicts),
    )
