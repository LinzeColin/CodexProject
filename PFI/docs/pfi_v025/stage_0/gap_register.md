# PFI v0.2.5 Stage 0 Gap Register

本文件把 Phase 0.3 冻结的 38 个 findings 聚合为可执行 gaps。它只记录当前差距、Roadmap 解析路径和验收边界，不宣称业务 gap 已修复，也不构成 Stage 0 整阶段验收或 production acceptance。

executable_p2_count: 0

GAP-P0-01 = FND-001;FND-002;FND-027;FND-035
GAP-P0-02 = FND-003;FND-004;FND-005;FND-006;FND-007
GAP-P0-03 = FND-008
GAP-P0-04 = FND-009;FND-010
GAP-P0-05 = FND-012;FND-014
GAP-P0-06 = FND-016;FND-017;FND-018;FND-019
GAP-P0-07 = FND-020
GAP-P0-08 = FND-023;FND-024
GAP-P0-09 = FND-029
GAP-P1-01 = FND-011;FND-013;FND-031
GAP-P1-02 = FND-022
GAP-P1-03 = FND-025
NON_GAP = FND-015;FND-021;FND-026;FND-028;FND-030;FND-032;FND-033;FND-034;FND-036;FND-037;FND-038
## Non-gap dispositions

| finding_id | status | priority | disposition | rationale_marker |
|---|---|---|---|---|
| FND-015 | Fixed | P0 | non_gap | scope_limit=static_source_scope |
| FND-021 | Fixed | P0 | non_gap | scope_limit=static_structure_scope |
| FND-026 | Fixed | P0 | non_gap | scope_limit=stage0_evidence_scope |
| FND-028 | Fixed | P1 | non_gap | scope_limit=scope_contract |
| FND-030 | N/A | P1 | non_gap | non_gap_reason=non_designated_legacy_home_path; formal_home_source=PFI/web/app/pages/home.js |
| FND-032 | Fixed | P1 | non_gap | scope_limit=syntax_scope |
| FND-033 | Fixed | P1 | non_gap | scope_limit=phase02_scope |
| FND-034 | N/A | P0 | non_gap | non_gap_reason=tracked_precommit_and_external_final_are_intentional_lifecycle_layers |
| FND-036 | N/A | P2 | non_gap | non_gap_reason=v024_live_verifier_replay_is_not_required_by_current_v025_contract |
| FND-037 | N/A | P2 | non_gap | non_gap_reason=repository_fallback_is_the_current_equivalent_yaml_gate |
| FND-038 | Fixed | P1 | non_gap | scope_limit=phase02_remote_scope |

### GAP-P0-01

- gap_id: GAP-P0-01
- priority: P0
- linked_finding_ids: FND-001;FND-002;FND-027;FND-035
- current_state: 旧 closeout、owner views、bare acceptance source 与 parameter-owner diagnostic 仍呈现不一致的 v0.2.5 状态真相。
- target_state: canonical owner surfaces、governance lifecycle 与参数 owner evidence 对同一版本和 acceptance 状态给出一致且可追溯的事实。
- roadmap_resolution_tasks: S0-P3-T1;S12-P3-T1;S12-P3-T3;S12-P3-T4
- dependencies: S0-P3-T1 先建立 Stage 0 truth baseline；S12-P3-T1、S12-P3-T3、S12-P3-T4 在最终交付时统一 owner truth 与 acceptance evidence。
- required_acceptance_evidence: owner collections、governance records、parameter-owner gate 与最终交付 attestation 对版本、状态和 evidence source 的一致性证明。
- stop_condition: 任一 owner surface 仍宣称未经 Stage review 或 production gate 证明的完成状态，或 parameter-owner consistency 仍失败。
- status: open

### GAP-P0-02

- gap_id: GAP-P0-02
- priority: P0
- linked_finding_ids: FND-003;FND-004;FND-005;FND-006;FND-007
- current_state: release identity 混合，canonical App 与用户入口不一致，repository App strict codesign 失败，且两个 canonical listeners 同时运行。
- target_state: VERSION、page、launcher、canonical App、用户入口与单一 healthy runtime listener 形成可验证的同一 release identity。
- roadmap_resolution_tasks: S1-P1-T1;S1-P1-T2;S1-P1-T3;S1-P1-T4;S1-P2-T1;S1-P2-T2;S1-P2-T3;S1-P2-T4;S1-P3-T2;S12-P2-T1;S12-P2-T2;S12-P3-T1
- dependencies: Stage 1 先完成 release identity 与 App 构建安装，再验证单 listener runtime；Stage 12 重装、runtime 与 owner delivery gates 最终闭环。
- required_acceptance_evidence: 四方版本 identity、repository/user App full-file hash、strict codesign、canonical reinstall 和单 listener runtime proof。
- stop_condition: 任一版本标识或 executable hash 不一致、codesign 未通过、canonical reinstall 缺失或 listener count 不为一。
- status: open

### GAP-P0-03

- gap_id: GAP-P0-03
- priority: P0
- linked_finding_ids: FND-008
- current_state: PFI_DATA_HOME 未设置，候选 roots 与 repository data surface 尚未收敛为单一 data-root truth。
- target_state: canonical data root、root selection、repository surface 与 query-only inventory 有单一可复现来源和 provenance。
- roadmap_resolution_tasks: S2-P1-T1;S2-P1-T2;S2-P1-T3
- dependencies: S2-P1-T1 确立 canonical root，S2-P1-T2 规范 root routing，S2-P1-T3 完成 query-only database inventory。
- required_acceptance_evidence: canonical root configuration、候选 root inventory、source evidence bindings 与无数据突变的 read-only proof。
- stop_condition: canonical root 仍未定义、root precedence 含歧义，或 inventory 无法绑定当前 evidence。
- status: open

### GAP-P0-04

- gap_id: GAP-P0-04
- priority: P0
- linked_finding_ids: FND-009;FND-010
- current_state: transaction rows 不能证明 account、holding、net-worth inputs，且 no-false-zero 尚无 fresh production gate。
- target_state: immutable raw inputs、account/holding read model、核心财务指标和 no-false-zero gate 具备端到端 provenance 与 production evidence。
- roadmap_resolution_tasks: S2-P1-T4;S4-P1-T1;S4-P1-T2;S4-P1-T3;S4-P1-T4;S4-P2-T1;S4-P2-T2;S4-P2-T3;S4-P2-T4;S4-P3-T1;S12-P1-T4
- dependencies: S2-P1-T4 先固定 raw provenance；Stage 4 构建 inputs、metrics 和验证；S12-P1-T4 执行 production no-false-zero regression gate。
- required_acceptance_evidence: account/holding/net-worth inputs、raw-to-read-model lineage、公式输出与 no-false-zero production test evidence。
- stop_condition: 任何核心输入缺失却被表示为零，或 metric 无法追溯到 immutable raw provenance。
- status: open

### GAP-P0-05

- gap_id: GAP-P0-05
- priority: P0
- linked_finding_ids: FND-012;FND-014
- current_state: frontend 仍含旧 FX snapshot/rate，dual-consumption gross activity 与 lineage 尚未 fresh 验证。
- target_state: FX、time-aware conversions、dual-consumption ledger 和 gross activity 由注册公式及同源 lineage 驱动。
- roadmap_resolution_tasks: S2-P2-T2;S2-P2-T3;S3-P2-T2;S3-P2-T3;S5-P1-T3;S5-P2-T1
- dependencies: Stage 2 先建立时间与 FX truth；Stage 3 完成 ledger lineage；Stage 5 将注册公式接入消费与展示。
- required_acceptance_evidence: fresh FX source/as-of、dual-consumption ledger fixtures、gross activity calculation 与 frontend lineage consistency proof。
- stop_condition: 旧 FX 常量仍驱动 UI，或任一消费路径无法回溯到同一 ledger/formula evidence。
- status: open

### GAP-P0-06

- gap_id: GAP-P0-06
- priority: P0
- linked_finding_ids: FND-016;FND-017;FND-018;FND-019
- current_state: rendered DOM/a11y/no-JS 尚无证明，route targets 与旧 markers 冲突，导航历史行为未验，且 mechanical template text 仍存在。
- target_state: 真实 routes、差异化 pages、可访问 rendered DOM、no-JS boundary 与 click/deep-link/history/back-forward 行为全部通过 fresh runtime evidence。
- roadmap_resolution_tasks: S1-P1-T1;S6-P1-T1;S6-P1-T2;S6-P1-T3;S6-P1-T4;S6-P2-T1;S6-P2-T2;S6-P2-T4;S6-P3-T1;S6-P3-T2;S6-P3-T3;S8-P1-T2;S12-P1-T1;S12-P1-T4;S12-P3-T1
- dependencies: S1-P1-T1 固定 release route identity；Stage 6 完成 routes、pages、a11y 和 history behavior；Stage 8 清理 mechanical content；Stage 12 执行 regression 与 delivery truth gates。
- required_acceptance_evidence: route manifest、rendered DOM/a11y/no-JS capture、browser navigation matrix、差异化 page proof 与禁止模板文本扫描。
- stop_condition: stale route marker、不可达 target、no-16-stack/rendered DOM 证据缺失、history behavior 失败或 mechanical shell text 仍存在。
- status: open

### GAP-P0-07

- gap_id: GAP-P0-07
- priority: P0
- linked_finding_ids: FND-020
- current_state: localStorage/toast 路径仍可能把浏览器瞬时状态呈现为 durable persistence。
- target_state: workflow 状态由真实持久化写入、读取、失败与恢复语义驱动，UI 明确区分 transient feedback 和 durable result。
- roadmap_resolution_tasks: S7-P2-T1;S7-P2-T2;S7-P2-T3;S7-P2-T4
- dependencies: Stage 7 persistence contract、write/read path、failure behavior 与 user-visible state 必须按顺序完成。
- required_acceptance_evidence: durable write/read round-trip、重载后状态、失败注入、恢复证据以及 toast/localStorage 非持久化边界测试。
- stop_condition: UI 成功提示无法绑定 durable write，或刷新后状态与持久层不一致。
- status: open

### GAP-P0-08

- gap_id: GAP-P0-08
- priority: P0
- linked_finding_ids: FND-023;FND-024
- current_state: SQLite version/WAL/holding production gate 未完成，backup/restore/atomic rollback 也无 fresh proof。
- target_state: SQLite schema/version/WAL/holding truth 与 backup、restore、atomic rollback 形成可恢复且可审计的 production contract。
- roadmap_resolution_tasks: S11-P1-T1;S11-P1-T2;S11-P2-T1;S11-P2-T2;S11-P2-T3;S11-P2-T4;S12-P2-T3
- dependencies: Stage 11 先验证 database contract，再完成 backup/restore/rollback；Stage 12 执行最终恢复 delivery gate。
- required_acceptance_evidence: schema/version/WAL/holding probes、backup manifest、restore equality、failure-atomicity 与 rollback rehearsal evidence。
- stop_condition: database truth 不完整、backup 不可恢复、restore 不等价或失败路径留下部分写入。
- status: open

### GAP-P0-09

- gap_id: GAP-P0-09
- priority: P0
- linked_finding_ids: FND-029
- current_state: full tests、browser regression 与 human UAT 尚未按 v0.2.5 production contract 运行。
- target_state: focused、full、browser、UAT 和 delivery regression gates 均由 fresh evidence 证明，并与同一 candidate identity 绑定。
- roadmap_resolution_tasks: S12-P1-T1;S12-P1-T2;S12-P1-T3;S12-P1-T4;S12-P2-T4
- dependencies: Stage 1 至 Stage 11 的实现与局部 acceptance 完成后，Stage 12 才能运行完整 regression、browser 和 UAT gates。
- required_acceptance_evidence: full test report、browser matrix、UAT sign-off、failure evidence 与 candidate-bound delivery verification。
- stop_condition: 任一 required suite 未运行、失败未解决、UAT 未完成或证据未绑定同一 candidate。
- status: open

### GAP-P1-01

- gap_id: GAP-P1-01
- priority: P1
- linked_finding_ids: FND-011;FND-013;FND-031
- current_state: temporal/timezone truth 未闭环，单一 confidence 混合质量维度，且 read_model_hash 含 generated_at 导致跨调用不稳。
- target_state: timezone-aware temporal semantics、分维度 quality/confidence 和排除非决定性时间字段的稳定 read-model identity 均有注册定义与测试。
- roadmap_resolution_tasks: S2-P2-T1;S2-P2-T2;S2-P2-T3;S4-P3-T2;S5-P1-T4
- dependencies: Stage 2 建立 temporal/FX contract；Stage 4 修复 read-model determinism；Stage 5 分离 quality dimensions 与 confidence semantics。
- required_acceptance_evidence: timezone fixtures、as-of propagation、重复调用 hash equality、quality dimension schema 与 formula/model registry traceability。
- stop_condition: 时间解释含歧义、相同 inputs 产生不同 read_model_hash，或单一 confidence 继续隐藏不同质量维度。
- status: open

### GAP-P1-02

- gap_id: GAP-P1-02
- priority: P1
- linked_finding_ids: FND-022
- current_state: timer-driven fake progress path 仍存在，workflow progress 不能证明真实后台工作或 durable job 状态。
- target_state: progress 只由真实 job lifecycle、durable state 和 failure/retry transitions 驱动。
- roadmap_resolution_tasks: S8-P2-T2;S8-P2-T4;S10-P1-T4
- dependencies: Stage 8 移除 timer simulation 并绑定真实 workflow；Stage 10 补齐 durable job reliability gate。
- required_acceptance_evidence: job state transition log、progress source binding、failure/retry test 与无 timer-simulated success 的 static/runtime proof。
- stop_condition: progress 可在无真实 job state 变化时推进，或失败/retry 后 UI 与 durable state 不一致。
- status: open

### GAP-P1-03

- gap_id: GAP-P1-03
- priority: P1
- linked_finding_ids: FND-025
- current_state: public shell/PFI OS 非第二 UI 的 boundary 尚未通过 fresh runtime 验证。
- target_state: public shell 只暴露批准的单一 UI/runtime surface，并以可验证 boundary 防止第二 UI 或私有 runtime 泄露。
- roadmap_resolution_tasks: S11-P3-T1;S11-P3-T3
- dependencies: Stage 11 先固定 public shell surface，再验证 single-UI/runtime 与 privacy boundary。
- required_acceptance_evidence: public route inventory、runtime surface capture、single-UI assertion 与 private path/value exclusion scan。
- stop_condition: 存在第二 UI root、未批准 runtime surface 或 public evidence 含私有路径/值。
- status: open
