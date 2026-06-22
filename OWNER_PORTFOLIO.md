# OWNER_PORTFOLIO

## 1. 当前结论

Review8-A 后，本仓库的 Owner 视图必须把结构完整、实现一致、方法依据、实证、运行和交付分开；当前 Portfolio 不是生产可用声明。

## 2. 本次运行改变了什么

- 状态桶现在覆盖 `FAILED`、`PARTIAL`、`UNVERIFIED`、`VERIFIED`、`NOT_APPLICABLE`，总数必须等于登记项目数。
- Owner 决策改为项目特定的人类责任角色、资源、收益、风险、证据和不决策后果。
- 陈旧的“创建首个治理基线”任务不得在事实已满足时继续作为下一任务。

## 3. 为什么重要

没有这些约束，仓库可能在 CI 绿色时仍输出错误汇总、陈旧任务或无责任人的资金/上线决策。

## 4. 需要人类决定什么

优先决定 P0/P1 项目是否投入真实数据、专家/法务/隐私/风险 owner 时间和验收证据；Codex 只能执行治理和验证，不能替代人类批准。

## 5. 默认建议

- 下一唯一任务：`TASK-ALPHA-B-001` - Resolve production validation and execution-policy UNKNOWN items before release readiness.
- 默认策略：先关闭 P0 证据和人类责任 blocker，再进入项目 C0-C7 实证闭环。

## 6. 不决策后果

没有 owner 决策和证据投入的项目保持 `FAILED`、`PARTIAL` 或 `UNVERIFIED`，不得提升为交付就绪。

## 7. 下一行动、责任角色和验收证据

- human_owner_role: `model_owner + risk_owner`
- acceptance_ids: `ACC-ALPHA-B-001`
- unblock_condition: Without explicit owner decision and validation evidence Alpha must not be called release-ready for live execution.

## 8. 九层 Assurance 状态

- project_total: `10`
- bucket_total: `10`
- failed: `6`
- partial: `0`
- unverified: `4`
- verified: `0`
- not_applicable: `0`

| Bucket | Count | Projects |
|---|---:|---|
| `FAILED` | `6` | Alpha, EEI, EVA_OS, OpenAIDatabase, whkmSalary, arxiv-daily-push |
| `PARTIAL` | `0` | none |
| `UNVERIFIED` | `4` | FIFA, OpMe_System, PFI_BIG_DATA_SIMULATOR, Serenity-Alipay |
| `VERIFIED` | `0` | none |
| `NOT_APPLICABLE` | `0` | none |

## 9. 技术元数据

- source_base_commit: `738887de4034ad42d90347d0fa0db6c0f3ed966f`
- source_tree_hash: `6d67efb26a6ea61fd8b05706dbb3eb2f1d34ab9f`
- source_snapshot_hash: `sha256:7006d944f058f726a4c78af258bb85db10782cec0e25e6c807152ca37b4c5623`
- snapshot_event_time: `2026-06-23T07:30:00+10:00`
- generator_version: `4.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`
- branch_protection: `UNVERIFIED` unless authenticated setup doctor evidence is attached

## 10. Top 5 Blockers

- Alpha: production validation evidence
- Alpha: broker policy decision
- EEI: 24h operator soak evidence
- EEI: historical event binding backlog
- EVA_OS: parameter review backlog

## 11. Owner Decisions

### `DEC-Alpha-REVIEW8-001`

- human_owner_role: `model_owner + risk_owner`
- recommendation: A: fund historical-data validation before any stronger delivery claim
- estimated_effort: P1; model_owner + risk_owner review plus data preparation
- estimated_cost_or_resource: historical market data, cost/slippage assumptions, review time
- expected_benefit: 判断当前信号和风险门禁是否有样本外价值，而不把实现一致性误认为有效性。
- principal_risks: future leakage, overfitting, data/vendor limits, transaction-cost understatement
- evidence_required: versioned market snapshot, baseline metrics, OOS report, sensitivity table
- no_decision_consequence: Alpha remains FAILED for operational/delivery readiness and cannot support production claims.

### `DEC-EEI-REVIEW8-001`

- human_owner_role: `product_owner + data_owner + risk_owner`
- recommendation: A: complete 24h soak and gold-set validation before publishing stronger claims
- estimated_effort: P2; product/data/risk owners plus operator time
- estimated_cost_or_resource: official-source access, labeled gold set, soak runner time
- expected_benefit: 降低未经证实企业关系被发布为事实的风险。
- principal_risks: source license limits, stale relationships, false relation assertions
- evidence_required: gold-set labels, precision/recall, source coverage, soak manifest
- no_decision_consequence: EEI remains FAILED/PARTIAL and publication readiness stays blocked.

### `DEC-EVA_OS-REVIEW8-001`

- human_owner_role: `model_owner + research_owner`
- recommendation: A: fund parameter review and OOS evidence hardening
- estimated_effort: P1; research/model owner review
- estimated_cost_or_resource: historical data, experiment logs, report evidence manifest
- expected_benefit: 把实验实现与真实可复现证据分开，避免选择性报告。
- principal_risks: parameter instability, cost omissions, cherry-picked reports
- evidence_required: OOS protocol, rerun logs, claim ledger, sensitivity results
- no_decision_consequence: EVA_OS remains FAILED for operational and delivery readiness.

### `DEC-FIFA-REVIEW8-001`

- human_owner_role: `research_owner + risk_owner`
- recommendation: A: validate historical odds snapshots under zero-stake boundary
- estimated_effort: P1; research and risk review
- estimated_cost_or_resource: authorized odds snapshots, match results, report audit samples
- expected_benefit: 判断概率和报告是否比市场/简单基线更有用，同时避免下注风险。
- principal_risks: post-event leakage, unauthorized data, betting misuse
- evidence_required: timestamped odds data, calibration report, zero-stake gate evidence
- no_decision_consequence: FIFA remains UNVERIFIED and cannot support value/recommendation claims.

### `DEC-OpMe_System-REVIEW8-001`

- human_owner_role: `engineering_owner + safety_owner + operations_owner`
- recommendation: A: fund expert-labeled safety validation before operational use
- estimated_effort: P0; engineering, safety, operations owners required
- estimated_cost_or_resource: de-identified industrial cases, expert adjudication, safety review time
- expected_benefit: 降低危险故障漏报和无依据操作建议风险。
- principal_risks: unsafe advice, missing expert labels, provider outage,现场适用性不足
- evidence_required: expert labels, severity-weighted errors, dangerous false-negative rate, fallback logs
- no_decision_consequence: OpMe_System remains UNVERIFIED and must not be treated as production safety tooling.

### `DEC-OpenAIDatabase-REVIEW8-001`

- human_owner_role: `privacy_owner + product_owner`
- recommendation: A: fund privacy-first gold-set validation before persistent memory write claims
- estimated_effort: P0; privacy and product owner review
- estimated_cost_or_resource: consented/de-identified exports, adversarial secret set, evaluator time
- expected_benefit: 验证系统有用且不会把私密内容错误持久化或泄漏。
- principal_risks: PII/secret leakage, stale memory, false user facts
- evidence_required: gold labels, leakage-rate report, retrieval metrics, human write approval logs
- no_decision_consequence: OpenAIDatabase remains FAILED for delivery readiness and cannot claim safe memory operation.

### `DEC-PFI_BIG_DATA_SIMULATOR-REVIEW8-001`

- human_owner_role: `model_owner + risk_owner + research_owner`
- recommendation: A: validate OOS and multiple-testing controls before ranking strategy claims
- estimated_effort: P1; model/risk/research owner review
- estimated_cost_or_resource: multi-market snapshots, compute time, multiple-testing protocol
- expected_benefit: 区分真实稳健表现与大规模搜索偏差。
- principal_risks: data mining, survivor bias, underestimated costs, resource blowups
- evidence_required: pre-registration, OOS metrics, corrected significance, sensitivity results
- no_decision_consequence: PFI remains UNVERIFIED and cannot support strategy approval.

### `DEC-Serenity-Alipay-REVIEW8-001`

- human_owner_role: `model_owner + risk_owner`
- recommendation: A: fund empirical calibration and OOS validation; implementation is already machine-verified
- estimated_effort: P1; model/risk owner plus data preparation
- estimated_cost_or_resource: historical fund snapshots, benchmark series, calibration protocol
- expected_benefit: 判断当前权重/阈值/门禁是否有风险控制和排序价值。
- principal_risks: survivorship bias, overfitting, stale fund availability, investment misuse
- evidence_required: versioned snapshots, OOS metrics, ablation, sensitivity and gate-value report
- no_decision_consequence: Serenity remains UNVERIFIED for empirical/delivery readiness despite machine-verified implementation.

### `DEC-whkmSalary-REVIEW8-001`

- human_owner_role: `payroll_owner + legal_or_policy_owner + product_owner`
- recommendation: A: fund policy and payroll reconciliation evidence before any production payroll use
- estimated_effort: P0; payroll + legal/policy + product owner sign-off
- estimated_cost_or_resource: authoritative policy docs, approved payroll examples, reviewer time
- expected_benefit: 避免把未经授权或过期规则用于工资、税费和绩效结算。
- principal_risks: legal error, payroll under/overpayment, PII leakage, unfair impact
- evidence_required: policy refs, jurisdiction/effective-date matrix, reconciliation results, approval memo
- no_decision_consequence: whkmSalary remains FAILED and must not be used for production payroll.

### `DEC-arxiv-daily-push-V5-S1-006`

- human_owner_role: `content_owner + engineering_owner + operations_owner`
- recommendation: A: run S1-12 controlled live B1 email days before production acceptance
- estimated_effort: P1; controlled target-runner live delivery evidence
- estimated_cost_or_resource: GitHub/cloud runner, Gmail SMTP secret names, live arXiv metadata access, durable evidence refs
- expected_benefit: 证明 Stage 1 B1/arXiv 每日邮件在真实运行边界能稳定送达，而不是只在离线历史预览中通过。
- principal_risks: SMTP secret readiness, live arXiv availability, target runner drift, accidental scheduler enablement, local Mac fallback
- evidence_required: two natural-day B1 email delivery refs, target-runner refs, B1 report/email artifacts, no-secret delivery audits, no production scheduler
- no_decision_consequence: arxiv-daily-push remains at S1-11 and cannot reach ARXIV_PRODUCTION_ACCEPTED.


## 12. Executable Tasks

- `Alpha`: `TASK-ALPHA-B-001` - Resolve production validation and execution-policy UNKNOWN items before release readiness.
- `EEI`: `TASK-T1301` - Implement real data ingestion, entity resolution and evidence chain for the Golden Vertical
- `EVA_OS`: `TASK-EVA-B-001` - Resolve calibration evidence for built-in strategy defaults and enhanced Alipay multipliers.
- `FIFA`: `TASK-FIFA-C-001` - Recover authorized raw data path without violating TAB access-policy boundaries.
- `OpMe_System`: `TASK-OPME-B-001` - Resolve engineering calibration, prompt version, provider policy, and signoff evidence gaps.
- `OpenAIDatabase`: `TASK-OAI-B-001` - Resolve UNKNOWN calibration evidence for heuristic weights and thresholds.
- `PFI_BIG_DATA_SIMULATOR`: `TASK-PFI-B-001` - Resolve calibration evidence for strategy catalog rule constants and indicator thresholds.
- `Serenity-Alipay`: `NONE` - No ready or in_progress task has completed dependencies, Acceptance IDs, and test commands.
- `whkmSalary`: `TASK-WHKM-B-001` - Resolve salary policy source, jurisdiction, effective date, tax basis, boundary behavior, and rounding policy evidence.
- `arxiv-daily-push`: `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001` - Collect controlled live B1/arXiv email delivery evidence across two real natural days before ARXIV_PRODUCTION_ACCEPTED can be claimed.

## 13. Next Unique Governance Task

- `TASK-ALPHA-B-001` - Resolve production validation and execution-policy UNKNOWN items before release readiness.

## 14. Assurance Dimensions

| Project | Structural | Impl | Param Source | Methodology | Empirical | Operational | Delivery | Freshness | Readiness | Owner action |
|---|---|---|---|---|---|---|---|---|---|---|
| `Alpha` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `FAILED` | `PARTIAL` | `FAILED` | 是否投入资源用真实历史行情、交易成本和样本外窗口验证 Alpha 动量筛选、风险评分和交易前门禁是否优于简单基线，同时保持零实盘执行。 |
| `EEI` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `PARTIAL` | `PARTIAL` | `FAILED` | `PARTIAL` | `FAILED` | 是否继续投入 24 小时 operator soak 和人工黄金集，验证 EEI 实体解析、关系抽取、证据覆盖与撤回能力。 |
| `EVA_OS` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `FAILED` | `PARTIAL` | `FAILED` | 是否投入参数来源、样本外、成本和报告 claim-to-evidence 验证，证明 EVA_OS 研究结论可复现且不夸大。 |
| `FIFA` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `UNVERIFIED` | `PARTIAL` | `UNVERIFIED` | 是否补齐授权赛前赔率快照、概率校准和报告事实复核，且继续保证 stake/executable amount 为 0。 |
| `OpMe_System` | `VERIFIED` | `VERIFIED` | `VERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `UNVERIFIED` | `PARTIAL` | `UNVERIFIED` | 是否由工程/安全/运营责任人投入专家裁决案例，验证 OpMe 诊断、严重度、LLM 路由和危险漏报失效安全。 |
| `OpenAIDatabase` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `FAILED` | `PARTIAL` | `FAILED` | 是否投入去标识黄金集和隐私攻击测试，验证记忆提取、脱敏、冲突/去重、检索和建议效用不会泄漏高风险秘密。 |
| `PFI_BIG_DATA_SIMULATOR` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `UNVERIFIED` | `PARTIAL` | `UNVERIFIED` | 是否投入多市场、OOS、成本和多重检验控制，验证 PFI 策略族不是数据挖掘赢家。 |
| `Serenity-Alipay` | `VERIFIED` | `VERIFIED` | `VERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `PARTIAL` | `UNVERIFIED` | `PARTIAL` | `UNVERIFIED` | 是否投入历史基金快照、基准、OOS、消融和敏感性，验证评分权重、等级阈值、硬门禁和 Top5 衰减是否有稳定区分力。 |
| `whkmSalary` | `VERIFIED` | `PARTIAL` | `PARTIAL` | `UNVERIFIED` | `UNVERIFIED` | `FAILED` | `FAILED` | `PARTIAL` | `FAILED` | 是否由工资、法务/政策和产品责任人提供权威政策、法域、生效日期、税务和舍入证据，验证 whkmSalary 可用于真实算薪。 |
| `arxiv-daily-push` | `VERIFIED` | `VERIFIED` | `VERIFIED` | `UNVERIFIED` | `PARTIAL` | `PARTIAL` | `FAILED` | `PARTIAL` | `FAILED` | 是否继续执行 S1-12，在目标 runner 上收集两个真实自然日的受控 B1/arXiv 邮件发送证据。 |
