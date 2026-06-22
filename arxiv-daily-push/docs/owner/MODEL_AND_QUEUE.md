# Model And Queue

- generated_at: 2026-06-22T16:30:00+10:00
- generated_from: `config/owner_controls.yaml`
- model_id: `adp-owner-controls-v1`
- validation_status: `pass`
- rollback_config_version: `owner-controls-v1`

## Weight Groups

| Group | Total | Target | Tolerance | Status |
|---|---:|---:|---:|---|
| `owner_sources` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_boards` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_research` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_china_policy` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_us_official` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_cross_board` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_queue_priority` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_legacy_arxiv_ranking` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_phase12_roi` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_us_attention_budget` | 100.0 | 100.0 | 0.0001 | `pass` |

## Scoring Cards

### research

| Component | Weight |
|---|---:|
| `relevance` | 22 |
| `novelty` | 16 |
| `evidence_quality` | 16 |
| `technical_breakthrough` | 16 |
| `conversion_economic_value` | 14 |
| `impact_scale` | 8 |
| `timeliness_version_change` | 5 |
| `diversity_coverage` | 3 |

### china_policy

| Component | Weight |
|---|---:|
| `authority_legal_effect` | 18 |
| `policy_delta` | 16 |
| `technology_industry_relevance` | 16 |
| `economic_impact` | 14 |
| `scope` | 10 |
| `urgency` | 10 |
| `regional_relevance` | 8 |
| `actionability` | 5 |
| `completeness_confidence` | 3 |

### us_official

| Component | Weight |
|---|---:|
| `innovation_breakthrough` | 20 |
| `regulatory_market_impact` | 18 |
| `authority_evidence` | 14 |
| `novelty_delta` | 14 |
| `entity_asset_scope` | 12 |
| `urgency` | 10 |
| `commercialization` | 8 |
| `actionability` | 4 |

### cross_board

| Component | Weight |
|---|---:|
| `normalized_quality` | 40 |
| `cross_board_linkage` | 20 |
| `decision_impact` | 15 |
| `urgency` | 10 |
| `confidence` | 10 |
| `diversity` | 5 |

### queue_priority

| Component | Weight |
|---|---:|
| `quality` | 55 |
| `event_delta` | 15 |
| `urgency` | 10 |
| `cross_board_linkage` | 10 |
| `waiting_credit` | 5 |
| `source_balance` | 5 |

### legacy_arxiv_ranking

| Component | Weight |
|---|---:|
| `frontier_signal` | 20 |
| `evidence_reliability` | 20 |
| `novelty` | 15 |
| `transfer_value` | 15 |
| `problem_importance` | 10 |
| `taxonomy_priority` | 10 |
| `waiting_time` | 5 |
| `diversity` | 5 |

### phase12_roi

| Component | Weight |
|---|---:|
| `relevance` | 20 |
| `learning_value` | 20 |
| `economic_conversion_rate` | 20 |
| `roi` | 20 |
| `interdisciplinary_value` | 10 |
| `explainability` | 10 |

## Queue

- max_active_items: `10000`
- max_event_age_days: `365`
- source_share_cap_per_board: `0.4`
- replay_status: `NOT_RUN_UNTIL_S1_06_REPLAY_DATA_EXISTS`
