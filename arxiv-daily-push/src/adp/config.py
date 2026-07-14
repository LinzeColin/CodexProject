"""thresholds_v0_3.yaml 加载器 —— 参数只能来自阈值注册表（工作合同硬约束 3）."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS_PATH = PROJECT_ROOT / "config" / "thresholds_v0_3.yaml"
OWNER_CONTROLS_PATH = PROJECT_ROOT / "config" / "owner_controls.yaml"
DATA_DIR = PROJECT_ROOT / "data"

TIMEZONE = "Australia/Sydney"

# 排序策略版本域单指针：特征抽取器内部塑形常数的版本标识（改动必须换号+CHANGELOG 落行）
FEATURE_EXTRACTOR_VER = "features-v03-2"

# 8 特征权重键（顺序即展示顺序）
FEATURE_KEYS = (
    "user_relevance",
    "knowledge_gap",
    "novelty_to_user",
    "transfer_potential",
    "forgetting_pressure",
    "urgency",
    "evidence_quality",
    "diversity",
)

GATE_KEYS = (
    "evidence_traceable",
    "official_https_source",
    "dedup_version_unique",
    "source_health_ok",
    "license_policy_ok",
)


@dataclass(frozen=True)
class Thresholds:
    registry_id: str
    registry_status: str
    gates: Mapping[str, bool]
    weights: Mapping[str, float]
    diversity_effective_cap_single_board: float
    attention_cost_penalty: float
    abstain_threshold: float
    daily_focus_count: int
    source_share_cap: float
    queue_max_active: int
    desired_retention: float
    max_daily_reviews: int
    personalize_after_reviews: int
    fsrs_implementation: str
    raw: Mapping[str, Any] = field(repr=False, default_factory=dict)

    @property
    def weight_total(self) -> float:
        return float(sum(self.weights.values()))

    def effective_weights(self, *, single_board: bool) -> dict[str, float]:
        """盲点二对策: 仅板块一在线时 diversity 生效上限受 cap 约束."""
        weights = dict(self.weights)
        if single_board:
            cap = self.diversity_effective_cap_single_board
            weights["diversity"] = min(weights["diversity"], cap)
        return weights


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml  # venv 依赖 (PyYAML)，见 requirements.txt

    with open(path, encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)
    if not isinstance(loaded, dict):
        raise ValueError(f"registry root must be a mapping: {path}")
    return loaded


def load_thresholds(path: Path | None = None) -> Thresholds:
    raw = _load_yaml(path or THRESHOLDS_PATH)
    registry = raw.get("registry") or {}
    gates = raw.get("eligibility_gates") or {}
    weights_raw = raw.get("value_weights") or {}
    selection = raw.get("selection") or {}
    review = raw.get("review") or {}

    missing_gates = [key for key in GATE_KEYS if key not in gates]
    missing_weights = [key for key in FEATURE_KEYS if key not in weights_raw]
    if missing_gates or missing_weights:
        raise ValueError(
            f"thresholds registry incomplete: missing gates {missing_gates}, weights {missing_weights}"
        )

    return Thresholds(
        registry_id=str(registry.get("id") or "thresholds-v0.3"),
        registry_status=str(registry.get("status") or "unknown"),
        gates={key: bool(gates[key]) for key in GATE_KEYS},
        weights={key: float(weights_raw[key]) for key in FEATURE_KEYS},
        diversity_effective_cap_single_board=float(raw.get("diversity_effective_cap_single_board", 10)),
        attention_cost_penalty=float(raw.get("attention_cost_penalty", 6)),
        abstain_threshold=float(selection.get("abstain_threshold", 55)),
        daily_focus_count=int(selection.get("daily_focus_count", 1)),
        source_share_cap=float(selection.get("source_share_cap", 0.40)),
        queue_max_active=int(selection.get("queue_max_active", 10000)),
        desired_retention=float(review.get("desired_retention", 0.90)),
        max_daily_reviews=int(review.get("max_daily_reviews", 12)),
        personalize_after_reviews=int(review.get("personalize_after_reviews", 100)),
        fsrs_implementation=str(review.get("implementation", "fsrs==6.3.1")),
        raw=raw,
    )


def load_legacy_research_weights(path: Path | None = None) -> dict[str, float]:
    """旧 V7 research 权重（owner_controls.yaml scoring.research）——回放对照专用，只读."""
    raw = _load_yaml(path or OWNER_CONTROLS_PATH)
    research = ((raw.get("scoring") or {}).get("research")) or {}
    return {key: float(value) for key, value in research.items()}


def data_dir() -> Path:
    override = os.environ.get("ADP_DATA_DIR")
    base = Path(override) if override else DATA_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def config_versions() -> dict[str, str]:
    """Run manifest 契约的 config_versions 字段（版本域指针）."""
    return {
        "阈值": "thresholds-v0.3",
        "数据": "adp-sqlite-v03-schema1",
        "合同": "ADP-PRD-V0.3 (legacy lock V7.2 frozen)",
        "模板": "lesson-v03-2",
        "排序策略": FEATURE_EXTRACTOR_VER,
    }
