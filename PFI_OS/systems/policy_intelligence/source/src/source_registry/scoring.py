from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

SCORING_VERSION = "authority-v1"

A_TIER_MIN = 90
B_TIER_MIN = 75
C_TIER_MIN = 60
D_TIER_MIN = 40

GOVERNMENT_SOURCE_TYPES = {
    "government_portal",
    "ministry",
    "subordinate_site",
    "information_disclosure",
    "official_directory",
    "provincial_portal",
    "provincial_department",
}


@dataclass(frozen=True)
class ScoreBreakdown:
    identity_evidence_score: int
    institution_level_score: int
    original_publisher_score: int
    traceability_score: int
    stability_score: int
    details: dict[str, object]

    @property
    def total(self) -> int:
        return min(
            100,
            self.identity_evidence_score
            + self.institution_level_score
            + self.original_publisher_score
            + self.traceability_score
            + self.stability_score,
        )


def tier_for_score(score: int | None) -> str | None:
    if score is None:
        return None
    if score >= A_TIER_MIN:
        return "A"
    if score >= B_TIER_MIN:
        return "B"
    if score >= C_TIER_MIN:
        return "C"
    if score >= D_TIER_MIN:
        return "D"
    return "E"


def score_source(
    source: Mapping[str, object],
    evidence: Iterable[Mapping[str, object]],
    alias_count: int = 0,
) -> ScoreBreakdown:
    evidence_types = {
        str(row.get("evidence_type", "")).strip()
        for row in evidence
        if row.get("evidence_type")
    }
    source_type = str(source.get("source_type") or "other")
    level = str(source.get("administrative_level") or "unknown")
    domain = str(source.get("canonical_domain") or "")
    status = str(source.get("status") or "candidate")
    crawl_failure_count = int(source.get("crawl_failure_count") or 0)
    publishes_original = bool(source.get("publishes_original_documents", 1))

    identity = _identity_score(evidence_types, source_type, domain)
    institution = _institution_score(source_type, level)
    original = _original_publisher_score(source_type, publishes_original)
    traceability = _traceability_score(source, evidence_types, alias_count)
    stability = _stability_score(status, domain, evidence_types, crawl_failure_count)

    return ScoreBreakdown(
        identity_evidence_score=identity,
        institution_level_score=institution,
        original_publisher_score=original,
        traceability_score=traceability,
        stability_score=stability,
        details={
            "scoring_version": SCORING_VERSION,
            "identity_evidence_max": 30,
            "institution_level_max": 25,
            "original_publisher_max": 20,
            "traceability_max": 15,
            "stability_max": 10,
            "source_type": source_type,
            "administrative_level": level,
            "evidence_types": sorted(evidence_types),
            "alias_count": alias_count,
        },
    )


def _identity_score(evidence_types: set[str], source_type: str, domain: str) -> int:
    score = 0
    if "official_directory" in evidence_types:
        score += 12
    if "organization_page" in evidence_types:
        score += 8
    if "government_site_id" in evidence_types:
        score += 6
    if source_type in GOVERNMENT_SOURCE_TYPES or domain.endswith(".gov.cn"):
        score += 6
    if "sponsor_unit" in evidence_types:
        score += 3
    if "supervisor_unit" in evidence_types:
        score += 3
    if "icp_registration" in evidence_types:
        score += 2
    if "police_registration" in evidence_types:
        score += 2
    return min(30, score)


def _institution_score(source_type: str, level: str) -> int:
    if level == "national" and source_type in {
        "government_portal",
        "ministry",
        "information_disclosure",
        "official_directory",
    }:
        return 25
    if level == "national" and source_type in {"subordinate_site", "think_tank"}:
        return 21
    if level == "provincial" and source_type in {
        "government_portal",
        "provincial_portal",
    }:
        return 22
    if level == "provincial" and source_type in {
        "provincial_department",
        "subordinate_site",
    }:
        return 18
    if source_type in {"official_media", "think_tank", "blue_book"}:
        return 16
    if source_type == "association":
        return 10
    return 5


def _original_publisher_score(source_type: str, publishes_original: bool) -> int:
    if not publishes_original:
        if source_type in {"official_media", "think_tank", "blue_book"}:
            return 10
        return 4
    if source_type in {
        "government_portal",
        "ministry",
        "information_disclosure",
        "official_directory",
    }:
        return 20
    if source_type in {
        "subordinate_site",
        "provincial_portal",
        "provincial_department",
    }:
        return 18
    if source_type in {"think_tank", "blue_book"}:
        return 13
    if source_type == "official_media":
        return 10
    if source_type == "association":
        return 7
    return 3


def _traceability_score(
    source: Mapping[str, object], evidence_types: set[str], alias_count: int
) -> int:
    score = 0
    if source.get("official_url") and source.get("canonical_domain"):
        score += 4
    if "official_directory" in evidence_types:
        score += 4
    if "organization_page" in evidence_types or "about_page" in evidence_types:
        score += 3
    if any(
        item in evidence_types
        for item in {"government_site_id", "sponsor_unit", "supervisor_unit"}
    ):
        score += 3
    if alias_count:
        score += 1
    return min(15, score)


def _stability_score(
    status: str, domain: str, evidence_types: set[str], crawl_failure_count: int
) -> int:
    score = 0
    if status == "active":
        score += 4
    if domain:
        score += 2
    if "official_directory" in evidence_types:
        score += 2
    if crawl_failure_count == 0:
        score += 2
    elif crawl_failure_count <= 3:
        score += 1
    return min(10, score)
