# 模型与队列

本页解释排序模型和队列参数。owner 要看的已发送、未发送、排队状态在 GitHub 浅层用户中心：

- `arxiv-daily-push/用户中心/README.md`
- `arxiv-daily-push/用户中心/邮件发送与队列状态.md`

当前 2026-06-26 最新事实：

| 类别 | 当前值 |
|---|---|
| 最新补发 | `sent` |
| 最新模板 | `EMAIL_LEARNING_V1` |
| 最新未发送/阻断 | 0 |
| 当前排队候选 | 11 |
| 队列更新时间 | `2026-06-26T06:27:41Z` |

- generated_at: 2026-06-22T21:00:00+10:00
- generated_from: `config/owner_controls.yaml`
- model_id: `adp-owner-controls-v1`
- validation_status: `pass`
- rollback_config_version: `owner-controls-v1`

## 权重组

| Group | Total | Target | Tolerance | Status |
|---|---:|---:|---:|---|
| `owner_sources` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_boards` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_research` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_china_policy` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_us_official` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_cross_board` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_scoring_queue_priority` | 100.0 | 100.0 | 0.0001 | `pass` |
| `owner_us_attention_budget` | 100.0 | 100.0 | 0.0001 | `pass` |

## 评分卡

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

## Queue

- max_active_items: `10000`
- max_event_age_days: `365`
- source_share_cap_per_board: `0.4`
- replay_status: `S1_06_DETERMINISTIC_QUEUE_READY_NO_PRODUCTION_REPLAY_DATA`
