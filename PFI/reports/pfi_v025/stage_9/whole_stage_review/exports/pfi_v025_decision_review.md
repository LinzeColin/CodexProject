# PFI v0.2.5 Decision Review Export

- Snapshot: `sha256:b12e2796b89d4c60947fd32f0bf5efd1e789f5a254205536d9252dbfb05a9760`
- Analysis pack: `sha256:9bd7c8a32fd25d47c7658d7cbf5ddbc132c1cebab187ab9a500c178a1882c6ae`
- Human review required: `true`
- Automatic trading: `forbidden`

## Report truth

| Report | Status | Range | Records |
|---|---|---|---:|
| 净资产报告 | blocked | 2022-06-06 to 2026-06-03 | 8815 |
| 现金报告 | blocked | 2022-06-06 to 2026-06-03 | 8815 |
| 投资报告 | blocked | 2022-06-06 to 2026-06-03 | 8815 |
| 消费报告 | partial | 2022-06-06 to 2026-06-03 | 8815 |
| 现金流报告 | partial | 2022-06-06 to 2026-06-03 | 8815 |

## Consumption and investment activity components

| Component | Status | Formula | Scope |
|---|---|---|---|
| 消费总流出 | 本机真实快照已验证 | FORM-PFI-015 | gross activity 口径，不等于净资产损失。 |
| 生活消费 | 本机真实快照已验证 | FORM-PFI-015 | 独立活动组件；与其他组件分开展示和复核。 |
| 投资资金流出 | 本机真实快照已验证 | FORM-PFI-015 | 独立活动组件；与其他组件分开展示和复核。 |
| 投资域内配置 | 本机真实快照已验证 | FORM-PFI-015 | 独立活动组件；与其他组件分开展示和复核。 |

Investment activity is not net-worth loss. Private financial values are not persisted in this export.

## 人工复核待复核交易分类

- Decision ID: `DEC-PFI-V025-REVIEW-QUEUE`
- Status: `awaiting_human_review`
- Horizon: `next_human_review_session`
- Thesis: 当前有 1,936 条记录仍在待复核队列；先人工核对分类与退款/转账边界，再解释消费结构。
- Portfolio effect: 该动作只影响分类复核与报告覆盖，不生成组合交易或金额影响。
- Counter evidence:
  - 队列数量不能证明分类准确性，且未标注 ground truth 时不能声明模型有效率。
  - 新导入、退款识别或人工重分类会改变当前队列与覆盖结论。
- Invalidation conditions:
  - `review_queue_record_count_equals_zero` (not_met)
  - `source_analysis_pack_hash_changes` (not_met)
- Risks:
  - 待复核记录可能包含转账、退款或投资活动，不能直接解释为生活消费。
  - 缺少分类 labels 与样本外 ground truth，不能声明分类准确率。

## 补齐并复核关键财务来源

- Decision ID: `DEC-PFI-V025-SOURCE-COMPLETENESS`
- Status: `awaiting_human_review`
- Horizon: `next_human_review_session`
- Thesis: 账户余额、负债、持仓、价格、FX 与 Economic Event lineage 未全部 ready；先补齐来源，再解释净资产、现金或投资结果。
- Portfolio effect: 缺少余额、持仓、价格与 FX，组合影响保持不可计算且不生成交易动作。
- Counter evidence:
  - 交易来源已有真实覆盖，因此消费与现金流仍可保留 partial 的覆盖结论。
  - 来源状态可能在新快照中改变，当前建议不得跨 snapshot 延用。
- Invalidation conditions:
  - `all_required_sources_and_lineage_ready` (not_met)
  - `source_analysis_pack_hash_changes` (not_met)
- Risks:
  - 来源未 ready 时强行解释净资产、现金或投资会制造假结论。
  - 持仓、价格与 FX 时间不一致会破坏估值和收益解释。

## Canonical snapshot JSON

```json
{
  "automatic_trading_allowed": false,
  "contains_private_values": false,
  "data_quality_report_hash": "sha256:122e21e70fcc08cbb9d52b3aba62c62baba02169c34c64475e42ec9cf755a9da",
  "data_quality_status": "complete",
  "decision_count": 2,
  "decisions": [
    {
      "action": "review_pending_transaction_classification",
      "action_label_zh": "人工复核待复核交易分类",
      "allowed_review_outcomes": [
        "accepted",
        "rejected",
        "deferred",
        "invalidated"
      ],
      "automatic_trading_allowed": false,
      "catalysts": [
        {
          "catalyst_id": "CAT-QUEUE-REVIEW",
          "review_route": "/ledger?tab=review",
          "statement_zh": "待复核记录减少且无静默丢弃时，可扩大消费报告的已验证覆盖。"
        }
      ],
      "confidence_dimensions": [
        {
          "basis_refs": [
            "pfi-v025-consumption",
            "REVIEW-SRC-TRANSACTIONS-ALIPAY"
          ],
          "dimension": "evidence_coverage",
          "status": "partial"
        },
        {
          "basis_refs": [
            "FORM-PFI-015",
            "FORM-PFI-020",
            "MOD-PFI-010"
          ],
          "dimension": "model_validity",
          "status": "structure_validated_ground_truth_missing"
        },
        {
          "basis_refs": [
            "V025-S9-P9.3"
          ],
          "dimension": "execution_safety",
          "status": "review_only_no_trade_capability"
        }
      ],
      "contains_private_values": false,
      "counter_evidence": [
        {
          "counter_evidence_id": "COUNTER-QUEUE-CONTEXT",
          "effect": "blocks_accuracy_claim",
          "review_route": "/reports/metric-drilldown?formula=FORM-PFI-020",
          "statement_zh": "队列数量不能证明分类准确性，且未标注 ground truth 时不能声明模型有效率。"
        },
        {
          "counter_evidence_id": "COUNTER-QUEUE-STALE",
          "effect": "requires_snapshot_refresh",
          "review_route": "/data/sources",
          "statement_zh": "新导入、退款识别或人工重分类会改变当前队列与覆盖结论。"
        }
      ],
      "decision_id": "DEC-PFI-V025-REVIEW-QUEUE",
      "evidence": [
        {
          "evidence_id": "EVID-QUEUE-PARTITION",
          "kind": "real_source_partition",
          "source_refs": [
            "pfi-v025-consumption",
            "SRC-TRANSACTIONS-ALIPAY"
          ],
          "statement_zh": "真实来源分区中待复核记录为 1,936 条，当前财务金额未进入公开决策对象。"
        }
      ],
      "financial_values_emitted": 0,
      "horizon": "next_human_review_session",
      "human_review_required": true,
      "invalidation_conditions": [
        {
          "condition_id": "INVALIDATE-QUEUE-EMPTY",
          "current_state": "not_met",
          "predicate": "review_queue_record_count_equals_zero",
          "review_route": "/ledger?tab=review"
        },
        {
          "condition_id": "INVALIDATE-ANALYSIS-HASH-DRIFT",
          "current_state": "not_met",
          "predicate": "source_analysis_pack_hash_changes",
          "review_route": "/reports"
        }
      ],
      "model_versions": [
        {
          "model_id": "MOD-PFI-010",
          "status": "partial_validated_with_blocked_components",
          "version": "v0.2.5"
        },
        {
          "model_id": "FORM-PFI-015",
          "status": "validated_real_snapshot",
          "version": "1.0.0"
        },
        {
          "model_id": "FORM-PFI-020",
          "status": "validated_structure_only",
          "version": "1.0.0"
        }
      ],
      "portfolio_effect": {
        "statement_zh": "该动作只影响分类复核与报告覆盖，不生成组合交易或金额影响。",
        "status": "not_calculable"
      },
      "review_history": [
        {
          "actor_ref": "phase_9_3_builder",
          "actor_role": "system",
          "event_hash": "sha256:9e35449e4b0c68a05686c339e3ae2571e75db10e31844f8d94f1e1294f0c2271",
          "event_id": "DEC-PFI-V025-REVIEW-QUEUE-EVT-0001",
          "event_type": "created",
          "from_status": null,
          "observed_at": "2026-07-15T17:30:00+10:00",
          "outcome": null,
          "prior_event_hash": null,
          "reason_zh": "由同一 Phase 9.2 分析快照生成，等待人工复核。",
          "to_status": "awaiting_human_review"
        }
      ],
      "review_route": "/ledger?tab=review",
      "risks": [
        "待复核记录可能包含转账、退款或投资活动，不能直接解释为生活消费。",
        "缺少分类 labels 与样本外 ground truth，不能声明分类准确率。"
      ],
      "source_analysis_pack_hash": "sha256:9bd7c8a32fd25d47c7658d7cbf5ddbc132c1cebab187ab9a500c178a1882c6ae",
      "source_ids": [
        "SRC-TRANSACTIONS-ALIPAY"
      ],
      "status": "awaiting_human_review",
      "thesis": {
        "evidence_refs": [
          "pfi-v025-consumption",
          "FORM-PFI-015",
          "FORM-PFI-020"
        ],
        "scope": "operational_review_only",
        "statement_zh": "当前有 1,936 条记录仍在待复核队列；先人工核对分类与退款/转账边界，再解释消费结构。"
      },
      "trade_execution_available": false,
      "version": "1.0.0"
    },
    {
      "action": "complete_missing_financial_source_review",
      "action_label_zh": "补齐并复核关键财务来源",
      "allowed_review_outcomes": [
        "accepted",
        "rejected",
        "deferred",
        "invalidated"
      ],
      "automatic_trading_allowed": false,
      "catalysts": [
        {
          "catalyst_id": "CAT-SOURCES-READY",
          "review_route": "/data/sources",
          "statement_zh": "所有关键来源与 lineage 达到 ready 后，可重建完整度并重新评估报告状态。"
        }
      ],
      "confidence_dimensions": [
        {
          "basis_refs": [
            "REVIEW-ECONOMIC-EVENT-ADAPTER",
            "REVIEW-SRC-ACCOUNT-BALANCES",
            "REVIEW-SRC-FX-SNAPSHOT",
            "REVIEW-SRC-HOLDINGS",
            "REVIEW-SRC-LIABILITIES",
            "REVIEW-SRC-MARKET-PRICES"
          ],
          "dimension": "evidence_coverage",
          "status": "blocked_missing_required_sources"
        },
        {
          "basis_refs": [
            "FORM-PFI-016",
            "FORM-PFI-017",
            "FORM-PFI-018"
          ],
          "dimension": "model_validity",
          "status": "blocked_for_full_financial_conclusion"
        },
        {
          "basis_refs": [
            "V025-S9-P9.3"
          ],
          "dimension": "execution_safety",
          "status": "review_only_no_trade_capability"
        }
      ],
      "contains_private_values": false,
      "counter_evidence": [
        {
          "counter_evidence_id": "COUNTER-TRANSACTIONS-READY",
          "effect": "prevents_all_reports_blocked_claim",
          "review_route": "/data/sources",
          "statement_zh": "交易来源已有真实覆盖，因此消费与现金流仍可保留 partial 的覆盖结论。"
        },
        {
          "counter_evidence_id": "COUNTER-SOURCE-STATE-DRIFT",
          "effect": "requires_snapshot_refresh",
          "review_route": "/reports",
          "statement_zh": "来源状态可能在新快照中改变，当前建议不得跨 snapshot 延用。"
        }
      ],
      "decision_id": "DEC-PFI-V025-SOURCE-COMPLETENESS",
      "evidence": [
        {
          "evidence_id": "EVID-MISSING-SOURCE-SET",
          "kind": "source_dependency_state",
          "source_refs": [
            "SRC-ACCOUNT-BALANCES",
            "SRC-FX-SNAPSHOT",
            "SRC-HOLDINGS",
            "SRC-LIABILITIES",
            "SRC-MARKET-PRICES",
            "economic_event_adapter"
          ],
          "statement_zh": "当前有 6 个关键来源或 lineage 依赖未 ready。"
        }
      ],
      "financial_values_emitted": 0,
      "horizon": "next_human_review_session",
      "human_review_required": true,
      "invalidation_conditions": [
        {
          "condition_id": "INVALIDATE-SOURCES-READY",
          "current_state": "not_met",
          "predicate": "all_required_sources_and_lineage_ready",
          "review_route": "/data/sources"
        },
        {
          "condition_id": "INVALIDATE-ANALYSIS-HASH-DRIFT",
          "current_state": "not_met",
          "predicate": "source_analysis_pack_hash_changes",
          "review_route": "/reports"
        }
      ],
      "model_versions": [
        {
          "model_id": "MOD-PFI-010",
          "status": "partial_validated_with_blocked_components",
          "version": "v0.2.5"
        },
        {
          "model_id": "FORM-PFI-016",
          "status": "blocked_missing_required_sources",
          "version": "1.0.0"
        },
        {
          "model_id": "FORM-PFI-017",
          "status": "blocked_missing_required_sources",
          "version": "1.0.0"
        },
        {
          "model_id": "FORM-PFI-018",
          "status": "blocked_insufficient_chain",
          "version": "1.0.0"
        }
      ],
      "portfolio_effect": {
        "statement_zh": "缺少余额、持仓、价格与 FX，组合影响保持不可计算且不生成交易动作。",
        "status": "not_calculable"
      },
      "review_history": [
        {
          "actor_ref": "phase_9_3_builder",
          "actor_role": "system",
          "event_hash": "sha256:7c4167131a25cedf0ca33d302d33309ce5b1199c0bd846cbb0313847a6102b07",
          "event_id": "DEC-PFI-V025-SOURCE-COMPLETENESS-EVT-0001",
          "event_type": "created",
          "from_status": null,
          "observed_at": "2026-07-15T17:30:00+10:00",
          "outcome": null,
          "prior_event_hash": null,
          "reason_zh": "由同一 Phase 9.2 分析快照生成，等待人工复核。",
          "to_status": "awaiting_human_review"
        }
      ],
      "review_route": "/data/sources",
      "risks": [
        "来源未 ready 时强行解释净资产、现金或投资会制造假结论。",
        "持仓、价格与 FX 时间不一致会破坏估值和收益解释。"
      ],
      "source_analysis_pack_hash": "sha256:9bd7c8a32fd25d47c7658d7cbf5ddbc132c1cebab187ab9a500c178a1882c6ae",
      "source_ids": [
        "SRC-ACCOUNT-BALANCES",
        "SRC-FX-SNAPSHOT",
        "SRC-HOLDINGS",
        "SRC-LIABILITIES",
        "SRC-MARKET-PRICES",
        "economic_event_adapter"
      ],
      "status": "awaiting_human_review",
      "thesis": {
        "evidence_refs": [
          "pfi-v025-net-worth",
          "pfi-v025-cash",
          "pfi-v025-investment",
          "REVIEW-ECONOMIC-EVENT-ADAPTER",
          "REVIEW-SRC-ACCOUNT-BALANCES",
          "REVIEW-SRC-FX-SNAPSHOT",
          "REVIEW-SRC-HOLDINGS",
          "REVIEW-SRC-LIABILITIES",
          "REVIEW-SRC-MARKET-PRICES"
        ],
        "scope": "data_completeness_review_only",
        "statement_zh": "账户余额、负债、持仓、价格、FX 与 Economic Event lineage 未全部 ready；先补齐来源，再解释净资产、现金或投资结果。"
      },
      "trade_execution_available": false,
      "version": "1.0.0"
    }
  ],
  "financial_values_emitted": 0,
  "hashes": {
    "base_report_manifest_hash": "sha256:ad0208b30a895e902c86b226a1186840a5a8c1f2747062f406f4debea48dabf4",
    "data_manifest_hash": "sha256:f960dc36a23ce8e283eef7e76a8098164718410415ed54374bf18bf34309f658",
    "formula_registry_hash": "sha256:65098b8f10602070639c3e42a128c0fed8bcabddb3b9400cf1436c0f2f85d8cd",
    "parameter_hash": "sha256:d6aacff83da3e7c4945b1376d62da72f7f1edd88999972645eba9488f90db433",
    "read_model_hash": "sha256:f1962e376536611ab43f60a95c9789510b52ee11f627de7037046dc71b73e4b6"
  },
  "human_review_required": true,
  "observed_at": "2026-07-15T17:30:00+10:00",
  "phase_id": "V025-S9-P9.3",
  "report_count": 5,
  "report_statuses": {
    "cash": "blocked",
    "cashflow": "partial",
    "consumption": "partial",
    "investment": "blocked",
    "net_worth": "blocked"
  },
  "reports": [
    {
      "component_cards": [],
      "data_range": {
        "end": "2026-06-03",
        "start": "2022-06-06"
      },
      "formula_ids": [
        "FORM-PFI-016"
      ],
      "parameter_ids": [
        "PARAM-PFI-081"
      ],
      "report_id": "pfi-v025-net-worth",
      "report_type": "net_worth",
      "review_entry_ids": [
        "REVIEW-SRC-ACCOUNT-BALANCES",
        "REVIEW-SRC-LIABILITIES",
        "REVIEW-SRC-HOLDINGS",
        "REVIEW-SRC-MARKET-PRICES",
        "REVIEW-SRC-FX-SNAPSHOT",
        "REVIEW-ECONOMIC-EVENT-ADAPTER"
      ],
      "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
      "snapshot_hash": "sha256:3b7c826b2f6443eb780cbe5767a01201164eb1389e920a9d33e7acead0770015",
      "status": "blocked",
      "title_zh": "净资产报告",
      "transaction_record_count": 8815
    },
    {
      "component_cards": [],
      "data_range": {
        "end": "2026-06-03",
        "start": "2022-06-06"
      },
      "formula_ids": [
        "FORM-PFI-016",
        "FORM-PFI-019"
      ],
      "parameter_ids": [
        "PARAM-PFI-081",
        "PARAM-PFI-086"
      ],
      "report_id": "pfi-v025-cash",
      "report_type": "cash",
      "review_entry_ids": [
        "REVIEW-SRC-ACCOUNT-BALANCES",
        "REVIEW-SRC-LIABILITIES",
        "REVIEW-ECONOMIC-EVENT-ADAPTER"
      ],
      "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
      "snapshot_hash": "sha256:390f4ed9600e5259de130cbb2280ced0ddf77699c4b685d04c557259aef0f93c",
      "status": "blocked",
      "title_zh": "现金报告",
      "transaction_record_count": 8815
    },
    {
      "component_cards": [],
      "data_range": {
        "end": "2026-06-03",
        "start": "2022-06-06"
      },
      "formula_ids": [
        "FORM-PFI-017",
        "FORM-PFI-018"
      ],
      "parameter_ids": [
        "PARAM-PFI-081",
        "PARAM-PFI-089",
        "PARAM-PFI-090",
        "PARAM-PFI-091",
        "PARAM-PFI-092"
      ],
      "report_id": "pfi-v025-investment",
      "report_type": "investment",
      "review_entry_ids": [
        "REVIEW-SRC-HOLDINGS",
        "REVIEW-SRC-MARKET-PRICES",
        "REVIEW-SRC-FX-SNAPSHOT",
        "REVIEW-ECONOMIC-EVENT-ADAPTER"
      ],
      "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
      "snapshot_hash": "sha256:9066b892f7824e239ee7d688d389786f6179ecaa6c53b4b6e2befaea63398df4",
      "status": "blocked",
      "title_zh": "投资报告",
      "transaction_record_count": 8815
    },
    {
      "component_cards": [
        {
          "contains_private_values": false,
          "financial_values_emitted": 0,
          "formula_id": "FORM-PFI-015",
          "label_zh": "消费总流出",
          "metric_id": "total_consumption_outflow_cny",
          "review_route": "/reports?tab=consumption-components",
          "scope_zh": "gross activity 口径，不等于净资产损失。",
          "status": "ready",
          "status_zh": "本机真实快照已验证",
          "value_visibility": "private_runtime_only_not_persisted"
        },
        {
          "contains_private_values": false,
          "financial_values_emitted": 0,
          "formula_id": "FORM-PFI-015",
          "label_zh": "生活消费",
          "metric_id": "living_consumption_cny",
          "review_route": "/reports?tab=consumption-components",
          "scope_zh": "独立活动组件；与其他组件分开展示和复核。",
          "status": "ready",
          "status_zh": "本机真实快照已验证",
          "value_visibility": "private_runtime_only_not_persisted"
        },
        {
          "contains_private_values": false,
          "financial_values_emitted": 0,
          "formula_id": "FORM-PFI-015",
          "label_zh": "投资资金流出",
          "metric_id": "investment_funding_outflow_cny",
          "review_route": "/reports?tab=consumption-components",
          "scope_zh": "独立活动组件；与其他组件分开展示和复核。",
          "status": "ready",
          "status_zh": "本机真实快照已验证",
          "value_visibility": "private_runtime_only_not_persisted"
        },
        {
          "contains_private_values": false,
          "financial_values_emitted": 0,
          "formula_id": "FORM-PFI-015",
          "label_zh": "投资域内配置",
          "metric_id": "investment_allocation_amount_cny",
          "review_route": "/reports?tab=consumption-components",
          "scope_zh": "独立活动组件；与其他组件分开展示和复核。",
          "status": "ready",
          "status_zh": "本机真实快照已验证",
          "value_visibility": "private_runtime_only_not_persisted"
        }
      ],
      "data_range": {
        "end": "2026-06-03",
        "start": "2022-06-06"
      },
      "formula_ids": [
        "FORM-PFI-015",
        "FORM-PFI-020"
      ],
      "parameter_ids": [
        "PARAM-PFI-081",
        "PARAM-PFI-082",
        "PARAM-PFI-083",
        "PARAM-PFI-084",
        "PARAM-PFI-085",
        "PARAM-PFI-087",
        "PARAM-PFI-088"
      ],
      "report_id": "pfi-v025-consumption",
      "report_type": "consumption",
      "review_entry_ids": [
        "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "REVIEW-ECONOMIC-EVENT-ADAPTER"
      ],
      "scope_explanation_zh": "消费总流出是用户定义的 gross activity 口径；生活消费、投资资金流出与投资域内配置必须拆分展示，投资活动不等于净资产损失。",
      "snapshot_hash": "sha256:d4faaf1663ead4cb92774e48791027e75378c342ee13241f0e219e292a58b676",
      "status": "partial",
      "title_zh": "消费报告",
      "transaction_record_count": 8815
    },
    {
      "component_cards": [],
      "data_range": {
        "end": "2026-06-03",
        "start": "2022-06-06"
      },
      "formula_ids": [
        "FORM-PFI-019",
        "FORM-PFI-015"
      ],
      "parameter_ids": [
        "PARAM-PFI-081",
        "PARAM-PFI-082",
        "PARAM-PFI-083",
        "PARAM-PFI-084",
        "PARAM-PFI-085",
        "PARAM-PFI-086"
      ],
      "report_id": "pfi-v025-cashflow",
      "report_type": "cashflow",
      "review_entry_ids": [
        "REVIEW-SRC-TRANSACTIONS-ALIPAY",
        "REVIEW-ECONOMIC-EVENT-ADAPTER"
      ],
      "scope_explanation_zh": "当前报告只使用已验证的真实来源覆盖，不把缺失输入解释为零。",
      "snapshot_hash": "sha256:883ca42c133033b2e7546df6c556f7ad91fe7e6ec61edb35ddcd55e211ef0292",
      "status": "partial",
      "title_zh": "现金流报告",
      "transaction_record_count": 8815
    }
  ],
  "schema": "PFIV025Stage9Phase93ExportSnapshotV1",
  "snapshot_hash": "sha256:b12e2796b89d4c60947fd32f0bf5efd1e789f5a254205536d9252dbfb05a9760",
  "source_analysis_pack_hash": "sha256:9bd7c8a32fd25d47c7658d7cbf5ddbc132c1cebab187ab9a500c178a1882c6ae",
  "source_analysis_snapshot_hash": "sha256:2e37ee5aedc4b0b8d74b38195d4b1f48a255ea14741d2804ce8e8e4cf671ee96",
  "trade_execution_available": false,
  "version": "v0.2.5"
}
```
