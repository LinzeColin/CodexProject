# Project Governance Status

## Snapshot Metadata

- source_base_commit: `123f5a6f7e7af22c283e49e55c2ba581310238d5`
- source_tree_hash: `0676963ae9229b88d20debe0dd6d4c9468643d62`
- source_snapshot_hash: `PRECOMMIT_OVERLAY_PENDING_COMMIT`
- snapshot_event_time: `2026-07-16T09:50:30+10:00`
- generator_version: `4.0.1`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

## Current State

- Project: `PFI`
- Path: `PFI`
- Product version: `v0.2.5`
- Phase/Gate: `Stage 12 exact final acceptance, release freeze and final CLI App reinstall pass; 156/156 tasks; waiting only for the single main upload and post-push parity / ACC-PFI-V025-FINAL-DELIVERY-PARITY`
- Models/Formulas/Parameters total: `10 / 20 / 92`
- Active formulas/parameters: `20 / 92`
- Machine checked formulas/parameters: `0 / 0`

## Assurance

| Dimension | Status | Evidence |
|---|---|---|
| structural_completeness | `VERIFIED` | `scripts/validate_project_governance.py` |
| implementation_congruence | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv, PFI/docs/governance/formula_registry.yaml` |
| parameter_source_quality | `PARTIAL` | `PFI/docs/governance/parameter_registry.csv` |
| methodological_rationale | `VERIFIED` | `PFI/docs/governance/MODEL_SPEC.md` |
| empirical_validation | `UNVERIFIED` | `PFI/docs/governance/delivery_tasks.yaml` |
| operational_validation | `UNVERIFIED` | `PFI/docs/governance/development_events.jsonl` |
| delivery_evidence | `FAILED` | `PFI/docs/governance/delivery_tasks.yaml` |
| evidence_freshness | `PARTIAL` | `PFI/docs/governance/development_events.jsonl` |

## Delivery

- Readiness: `FAILED`
- Release gate: `ACC-PFI-V025-STAGE12-WHOLE-REVIEW`
- Next executable task: `PFI-V025-SINGLE-MAIN-UPLOAD-AND-POST-PUSH-PARITY`（只执行一次 main 上传；App 最终重装已完成）
- Pending/stale events: `56`
- Tree-bound events: `0`
- Commit-bound events: `15`
- Legacy unbound events: `51`
- Unresolved fact IDs: `2`

## v0.2.5 Stage 12 Exact Final Acceptance Current Overlay

- Owner 已精确接受 build/App、Stage 0–12、A/B/C、evidence-index、请求时间与五项 P2；TaskPack schema 与 release gate 通过。
- `S12-P3-T4=completed`；release freeze=true；Stage 12=`12/12`，v0.2.5=`156/156 (100%)`。
- 当前 delivery 真值：push=false、final reinstall=true、production parity=false；Finder/`open`/LaunchServices/AppleScript/GUI 计数为 0。
- 下一任务：`PFI-V025-SINGLE-MAIN-UPLOAD-AND-POST-PUSH-PARITY`。

## v0.2.5 Stage 12 Whole-stage Independent Rereview Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S12-WHOLE-REVIEW-REREVIEW` / `PFI-V025-STAGE12-WHOLE-REVIEW-REREVIEW` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW`。
- Commit model：runtime source=`78375ec98f...`；product/remediation anchor A=`c8ce63aac7...`；reviewed closure B=`559cf190cc...`；B 与当前非 runtime overlay 的 runtime drift=0。
- 独立重算：exact binding、Phase 12.3/remediation artifact manifests、CLI entry census 与 fresh real E2E 均通过；artifact/entry mismatch=0，canonical DB changed=false。
- Findings：初审三项 P1 均 `closed_verified`；复审新增 `0 P0 / 0 P1 / 0 minor`。五项 P2 residual 继续保留。
- 验证：fresh E2E 17/17、focused 61/61、adjacent 115/115、Node 8/8、dual-plane、Lean、complete-overlay、privacy 与 artifact manifest 通过。
- 边界：local deterministic rereview 不声称外部人工/subagent reviewer；final acceptance=false，未 freeze/push/final reinstall，Finder/`open`/LaunchServices/AppleScript/GUI 计数为 0。
- 下一任务：`S12-P3-T4`，必须对 exact release 与五项 P2 作明确 owner acceptance。

## v0.2.5 Stage 12 Whole-stage Initial-review Remediation Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S12-WHOLE-REVIEW-REMEDIATION` / `PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION`。
- Identity：runtime source=`78375ec98fc1265abd03ef10087cc05beccab8b4`；candidate=`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`；index SHA-256=`ebd03b8a...`；runtime drift=0，exact binding 全部通过。
- Entry：旧 Downloads v0.2.3 App 已 CLI 原子移动至私有隔离区，未删除；canonical App 未修改，Desktop symlink 正确，entry mismatch=0。
- Findings：初审 `0 P0 / 3 P1 / 0 minor`；当前三项 P1 均 `closed_pending_independent_rereview`，整改后 open P0/P1=`0/0`。
- 验证：fresh real E2E、focused/adjacent Python、Node 8/8、release identity、dual-plane、renderer、complete-overlay、privacy 与 artifact hashes 通过。
- 边界：rereview=`not_started`，final acceptance=false；未 freeze、push、final reinstall 或 canonical DB mutation，Finder/`open`/LaunchServices/AppleScript/GUI 计数为 0。
- 下一任务：`STAGE12-WHOLE-REVIEW-REREVIEW`。

## v0.2.5 Stage 12 Phase 12.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S12-P123` / `PFI-V025-STAGE12-PHASE123-RELEASE-FREEZE-CANDIDATE` / `ACC-PFI-V025-S12-P123-RELEASE-FREEZE-CANDIDATE`。
- 当前 lifecycle：`S12-P3-T1..T3=candidate_complete`，`S12-P3-T4=waiting`；Stage 12=`11/12`，v0.2.5=`155/156 (99.36%)`；whole-stage review/user acceptance=`not_started`。
- Source migration：上游已删除顶层 `MetaDatabase`；四个真实 blobs 由可达 immutable commit lock 验证 OID/bytes/SHA-256，不恢复旧 tree。
- Evidence/request：one-way final index + detached hash 已生成；历史 SELF binding 已由当前 exact candidate/index/request/state/evidence 取代，真正 `human_acceptance.json` 不存在。
- 边界：当前 exact binding 已关闭初审相关 P1 待独立复审；未 push、final reinstall、release freeze、production/final acceptance 或 canonical DB mutation，Finder/`open`/LaunchServices/GUI 计数为 0。

## v0.2.5 Stage 12 Phase 12.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S12-P122` / `PFI-V025-STAGE12-PHASE122-TARGET-MAC-CLI-UAT` / `ACC-PFI-V025-S12-P122-TARGET-MAC-CLI-UAT`。
- 当前 lifecycle：Phase 12.2=`4/4 candidate_pass`，Stage 12=`8/12 in_progress`，v0.2.5=`152/156 (97.44%)`；Phase 12.3、whole-stage review/user acceptance=`not_started`。
- no-Finder/App：用户明确禁止 Finder/`open`/LaunchServices/AppleScript/GUI；CLI 原子安装 `/Applications/PFI.app` v0.2.5 / 20260712.1，同 manifest/runtime/query build，以上 GUI surface 计数均 0。
- 真实流程/恢复：4 个 immutable objects、8,815 raw / 8,808 ledger、review 803→802 且 restart 后持久；start/repeated-start/browser-close/offline-recovery/stop-restart、canonical read-only backup、isolated restore/rollback、temporary-volume real SQLITE_FULL/recovery 通过。
- 真值/缺陷：Holdings=`not_loaded/not_run`，5 reports=`3 blocked/2 partial`；P0/P1=`0/0`，P2=`3`。真实 kernel sleep/wake 未执行，只有明确披露的 owned-process suspend/resume proxy。
- 验证/边界：focused Python=`55 passed`、Node cache-policy=`8/8`，privacy/artifact/release identity pass；canonical DB 零写，未 push/release freeze/production/final acceptance。下一任务 `S12-P3-T1`。

## v0.2.5 Stage 12 Phase 12.1 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S12-P121` / `PFI-V025-STAGE12-PHASE121-AUTOMATED-REAL-E2E` / `ACC-PFI-V025-S12-P121-AUTOMATED-REAL-E2E`。
- 当前 lifecycle：Phase 12.1=`4/4 candidate_pass`，Stage 12=`4/12 in_progress`，v0.2.5=`148/156 (94.87%)`；Phase 12.2/12.3、whole-stage review/user acceptance=`not_started`。
- 真实数据：4 个 immutable Git objects、8,815 raw → 8,808 isolated ledger + 803 review；preview/confirm/idempotent replay、integrity/FK 通过，canonical source/database 零写入且临时 DB 已删除。
- UI/报告：10 一级 + 10 代表性二级 route；Holdings=`not_loaded/not_run`，5 reports=`3 blocked/2 partial`、无假零；20 routes/40 screenshots 的 deterministic WCAG 2.2 AA、keyboard、CDP AX、visual/performance pass。
- 验证/整改：GB18030 probe boundary 与 evidence scanner self-match 两项 P1 均关闭；focused=`358 passed, 6 deselected`、post-evidence=`21/21`、73/73 hashes、privacy/release identity/renderer/PFI governance pass；P0/P1=`0/0`。
- 边界：6 项 historical-state P2 test debt 已披露；未使用 Finder/LaunchServices/GUI，无 install/deploy/push/release freeze/production/final acceptance。下一任务 `S12-P2-T1`。

## v0.2.5 Stage 11 Whole-stage Review Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S11-WHOLE-REVIEW` / `PFI-V025-STAGE11-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`。
- 当前 lifecycle：Stage 11=`12/12 tasks + whole-stage review pass, accepted_for_transition`，v0.2.5=`144/156 (92.31%)`；Stage 12 entry authorized 但 implementation=`not_started`。
- 独立审查：初审 `C0/I4/M0`；source-directory lock、absolute-path receipts、真实 source 演练和浏览器证据整改后，三条 frozen deterministic rereview=`C0/I0/M0`。
- SQLite 真值：canonical operational DB 仅以 SQLite `mode=ro/query_only` 执行 Online Backup；源 file hash/stat 与 directory entries/stat 不变、无 source lock；success restore 与 injected rollback 只在隔离临时目标通过。
- 公共边界：loopback-only headless browser `23/23`，DOM/CDP AX/截图/脱敏 trace/404 与 public source/dist 扫描通过，外部请求 0；三 Phase chain 与 87 artifacts、TaskPack、release identity、privacy/governance 通过。
- 边界：真实数据库只读、未导出财务行或值；未使用 Finder/LaunchServices/GUI，未外网/deploy/push/install，production/final acceptance=false。下一任务 `S12-P1-T1`，须在新 run 开始。

## v0.2.5 Stage 11 Phase 11.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S11-P113` / `PFI-V025-STAGE11-PHASE113-DISTRIBUTION-BOUNDARY` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`。
- 当前 lifecycle：Phase 11.1/11.2/11.3=`candidate_pass`；Stage 11=`12/12 candidate_complete, in_progress_pending_whole_stage_review`，v0.2.5=`144/156 (92.31%)`；whole-stage review/user acceptance=`not_started`。
- public boundary：static notice only；HTML/CSS/JSON，无 active UI/application route/runtime binding/local connection/Context exposure，unknown route=`404-page`，source/dist scan finding=0。
- Context boundary：`pfi_context.v1` 仅 Alpha、七项 metadata、八项状态型 payload、read-only/no-writeback；旧 read model 只贡献 provenance hash并保持 blocked/not_loaded；0700/0600/no-overwrite/no-public-path。
- 验证：focused/adjacent/release/shell `77/77`，public build/双扫描、负向注入、release identity、TaskPack schema、完整 archive overlay governance/dual renderer、privacy/artifact hashes 通过。
- 边界：必要 public/active-adapter/release scope overrides 已披露；未使用 Finder/LaunchServices/GUI，无 canonical private DB/真实财务行；研究层仅访问 `developers.cloudflare.com`，产品/测试 runtime 外网 0；未 deploy/push/install，production/final acceptance=false。下一任务 `STAGE11-WHOLE-REVIEW`。

## v0.2.5 Stage 11 Phase 11.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S11-P112` / `PFI-V025-STAGE11-PHASE112-BACKUP-RESTORE` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`。
- 当前 lifecycle：Phase 11.1/11.2=`candidate_pass`；Stage 11=`8/12 in_progress`，v0.2.5=`140/156 (89.74%)`；Phase 11.3 与 whole-stage review=`not_started`。
- backup/verify：SQLite Online Backup API、无 online file copy/overwrite、0600/fsync；integrity/FK/migration registry/schema/application invariants 全部 fail closed。
- restore/rollback：backup 与 isolated candidate 在 target 前验证；exact target hash、sidecar absence、same-filesystem、exclusive lock、verified rollback snapshot、atomic replace 与 post-replace automatic rollback 通过；恢复结果匹配 rollback snapshot SHA 与原 application invariants。
- 验证：focused/adjacent/release identity `82/82`，disposable online/restore/rollback、TaskPack schema、完整 archive overlay governance/renderer、privacy/artifact hashes 通过。
- 边界：必要 scope overrides 已披露；未使用 Finder/LaunchServices/GUI，无 canonical private DB；研究层仅访问 `sqlite.org`/`docs.python.org` 官方文档，产品与测试 runtime 外部网络调用为 0；未 push/install，production/final acceptance=false。下一任务 `S11-P3-T1`。

## v0.2.5 Stage 11 Phase 11.1 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260716-PFI-V025-S11-P111` / `PFI-V025-STAGE11-PHASE111-SQLITE-SAFETY` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`。
- 当前 lifecycle：Phase 11.1=`candidate_pass`；Stage 11=`4/12 in_progress`，v0.2.5=`136/156 (87.18%)`；Phase 11.2/11.3 与 whole-stage review=`not_started`。
- SQLite truth：Python 3.12.13 / SQLite `3.50.4` 明确 WAL-unsafe；显式 WAL fail closed，活跃 operational stores 固定 `DELETE/FULL/FK/30000ms` 与显式 rollback。
- migration/recovery：checksum registry、幂等 replay、drift/escape/failure rollback 通过；`68/68` 测试与 release identity，disposable 四进程 `100/100` writes、实际 SIGKILL 未提交行 0、integrity/FK pass。
- 边界：`application/operational_store.py` 为 standing-authorized minimal scope override；未使用 Finder/LaunchServices/GUI，无 canonical private DB；研究层仅访问 `sqlite.org` 官方文档，产品与测试 runtime 外部网络调用为 0；未 push/install，production/final acceptance=false。下一任务 `S11-P2-T1`。

## v0.2.5 Stage 10 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S10-WHOLE-REVIEW` / `PFI-V025-STAGE10-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 10=`12/12 candidate_complete`、whole review=`pass`、用户过渡授权=`accepted_via_standing_transition_authorization`；v0.2.5=`132/156 (84.62%)`。
- 初审/整改：`C1/I7/M0`；`92579cfdd` 增加 persisted heartbeat、精确七态与最新 job 投影，并补齐 commit/artifact、TaskPack normalization、migration before/backup/after 和 DOM/CDP AX。
- 验证：正式 browser `22/22`，健康 >10 秒任务 `attempt=1/retry=0`；明确 failed/retrying/dead_letter、SIGKILL、九域 diff/no-diff、trace privacy、release identity、完整 frozen overlay governance/renderer 通过。
- 复审/边界：三条隔离 deterministic rereview=`C0/I0/M0`。Stage 11 entry authorized 但 implementation=`not_started`；未使用 Finder/LaunchServices/GUI，无 canonical private DB、外网、push、install、production/final acceptance。下一任务 `S11-P1-T1`。

## v0.2.5 Stage 10 Phase 10.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S10-P103` / `PFI-V025-STAGE10-PHASE103-OBSERVABILITY-RECOVERY` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Stage 10 phase tasks=`12/12 candidate_complete`，v0.2.5=`132/156 (84.62%)`；whole-stage review/user acceptance=`not_started`，Stage 11 未进入。
- observability：同一 trace 跨 job revisions、每 revision 独立 span；结构化日志在入库前脱敏，并记录 timing/error/impact/retry/cache fallback/hash dimensions，append-only/hash-chained。
- runtime/UI：正式 Shell 只投影 SQLite API 的 status/revision/trace/retry/error/result/units，timer 不推进状态。offline、timeout、unsafe network、restart 与实际 SIGKILL 均有明确持久结果。
- 验证：Phase `14/14`、最终产品合并 `121/121`；正式浏览器离页 10,503ms 后恢复同一 job，browser/database/trace privacy pass，外部请求 0，integrity/FK pass、WAL=false。
- 边界：产品提交 `9d2a8eb9f`；仅使用隔离 SQLite 与临时 loopback，未使用 Finder/LaunchServices/GUI、canonical 私有 DB、财务值、外网、push、install 或 production/final acceptance。下一任务 `STAGE10-WHOLE-REVIEW`。

## v0.2.5 Stage 10 Phase 10.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S10-P102` / `PFI-V025-STAGE10-PHASE102-RUNTIME-DIFF-CACHE` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Stage 10 tasks=`8/12 in_progress`，v0.2.5=`128/156 (82.05%)`；Phase 10.3 与 whole-stage review=`not_started`。
- dependency truth：九域 registry/DAG 绑定 raw/source/ledger/interconnection/parameter/formula/fx/read-model/report；snapshot 只含 hash/status/aggregate count/fixed provenance。
- diff/cache：九域逐一变化可解释，raw 不误报全指标；no-diff 为零重算/零 cache invalidation/零 network/Codex/LLM。Streamlit/前端/process key 同一，TTL=30、persist=false。
- 验证：Phase target `7/7`、Phase 10.1 + Stage 1 cache/release `45/45`、Stage 7 operational + Stage 9 report `40/40`，最终合并 `85/85`；active Node frontend validator 与 release identity 闭合。
- 边界：产品提交 `a64f3b515`；未读 canonical 私有 PFI DB、未输出财务值、未改 model/formula/parameter 值；未使用 Finder/LaunchServices/GUI。普通 dependency/cache 审计零网络；回归验证仅使用临时本机 loopback、无外网；未 push、install 或 production/final acceptance。下一任务 `S10-P3-T1`。

## v0.2.5 Stage 10 Phase 10.1 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S10-P101` / `PFI-V025-STAGE10-PHASE101-DURABLE-JOB-LIFECYCLE` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Stage 10 tasks=`4/12 in_progress`，v0.2.5=`124/156 (79.49%)`；Phase 10.2/10.3 与 whole-stage review=`not_started`。
- durable lifecycle：versioned `durable_jobs`/append-only hash-chained events 覆盖七状态、revision-CAS lease/heartbeat、bounded retry/cancel/dead-letter、expired-lease recovery 与真实单位进度。
- 并发/SQLite：双 worker 单 claim winner，raw lease token 不落库；runtime `3.50.4` 下 WAL 明确关闭并使用 `DELETE` journal。隔离 probe 7 jobs/20 events，40-job/8-worker stress 与 heartbeat CAS race 通过。
- 验证：Phase `7/7`、邻接 `19/19`、release identity `10/10`、最终合并 `36/36`；integrity/FK/token/privacy、完整 checkout governance 与 renderer 通过。
- 边界：正式 UI、真实 PFI DB 迁移、后台发布和交易均不存在；未使用 Finder/LaunchServices/GUI，无外网、财务值、model/formula/parameter 值修改、push、install 或 production/final acceptance。下一任务 `S10-P2-T1`。

## v0.2.5 Stage 9 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S9-WHOLE-REVIEW` / `PFI-V025-STAGE9-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 9 tasks=`12/12`、whole-stage review=`pass`、用户过渡授权=`accepted_via_standing_transition_authorization`；v0.2.5 进度保持 `120/156 (76.92%)`。
- 产品整改：正式 Shell 绑定 immutable reviewed snapshot；localStorage 仅保存严格 review delta。总流出、生活消费、投资资金流出、投资域配置四个组件进入主报告/导出，且明确 activity 不等于 net-worth loss。
- 报告/模型：5 份报告为 `3 blocked / 2 partial`；`FORM-PFI-015/019` 有当前证据，`016..018` blocked、`020` structure-only、historical/OOS blocked，不声明预测准确率或生产有效性。
- 验证：current-content browser `16/16`、四格式同源导出与物理 PDF、DOM/CDP AX、完整 changed-scope governance/renderer 通过；最终三方复审 `C0/I0/M0`。
- 边界：Stage 10 entry 已授权但 implementation=`not_started`；未使用 Finder/LaunchServices/GUI，无外网、raw/DB 读写、model/formula/parameter 值修改、push、install、production/final acceptance。下一任务 `S10-P1-T1`。

## v0.2.5 Stage 9 Phase 9.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S9-P93` / `PFI-V025-STAGE9-PHASE93-DECISION-REVIEW-EXPORT` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Stage 9 phase tasks=`12/12 candidate_complete`，v0.2.5=`120/156 (76.92%)`；whole-stage review/user acceptance=`not_started`。
- 正式报告页显示 2 个只读 decision objects、四种人工复核结果、反证/失效条件和 HTML/PDF/CSV/Markdown 四格式同源导出；浏览器 `16/16`。
- accepted 只追加 SHA-256 review event，不触发交易；automatic trading/order execution 均不可用。四格式 snapshot/manifest hash 可重建，物理 PDF 栅格目视通过。
- 产品提交 `16866630`；Phase 9.2 analysis pack 与 model/formula/parameter 值未改，公开财务值 0。只使用临时 loopback，无外网；未读写数据库/真实财务行。
- 未使用 Finder/LaunchServices/GUI，无 push、install 或 production/final acceptance；本轮未进入 Stage 10。下一唯一任务 `STAGE9-WHOLE-REVIEW`。

## v0.2.5 Stage 8 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S8-WHOLE-REVIEW` / `PFI-V025-STAGE8-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 8 tasks=`12/12`、whole-stage review=`pass`、用户过渡授权=`accepted_via_standing_transition_authorization`；v0.2.5 进度保持 `108/156 (69.23%)`。
- 产品整改关闭 archetype 自证/页面克隆、timer 假成功、持仓删除缺确认、24px link、timeline 任意标签持久化以及旧截图/重复二级路由。当前内容覆盖 10 核心 + 10 不同二级路由、desktop/mobile 40 PNG。
- deterministic WCAG 2.2 AA 覆盖 20 唯一路由/3646 文本样本，blocking/contrast/target/name/duplicate/structure failures=`0/0/0/0/0/0`；键盘、Chrome CDP AX、44px target、错误预防和 reduced-motion 均通过。
- axe-core 本地不可用，`axe_results.json` 保持 `not_run` 且不声明 axe pass；绑定 zero-blocking WCAG/CDP AX substitute。Release frontend=`0e3da07efc9b569b00e4182d445da1d12cd2cee0e505fd7f913fb74016dd01ca`、backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`。
- 初审 `C4/I14/M2`；整改后同一 frozen overlay 的三方复审目标/结果为 `C0/I0/M0`。Stage 9 entry 已授权但本轮仍 `not_started`，下一任务 `S9-P1-T1`。
- 本整阶段复审未使用 Finder、LaunchServices 或 GUI 文件操作；历史 Phase 8.3 的一次意外 `lsregister -dump` 已如实披露并当时立即中止。无财务数据/数据库/模型/公式/参数变更，无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 8 Phase 8.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S8-P82` / `PFI-V025-STAGE8-PHASE82-MOTION-FEEDBACK` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Phase 8.1/8.2 tasks=`8/8`，Stage 8=`8/12 in_progress`，v0.2.5=`104/156 (66.67%)`。
- 正式 Shell 使用 100/300/1000/10000ms 反馈预算、220ms 动效上限、reduced-motion 0ms、显式 haptics/sound opt-in 与跨路由 durable job timeline；无真实单位时不显示百分比。
- 实际浏览器 `17/17`；official candidate canonical sources=`19/19`；release/Stage 7 compatibility=`56/56`；console/page/HTTP/external errors=`0/0/0/0`。
- Release frontend=`33ef94e054dfc45bda699a5c44dee209868816eb27e107c3b73a3dae80e7be98`、backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`。
- Phase 8.3 和 whole-stage review 未开始；未使用 Finder/LaunchServices/GUI 文件操作，无财务数据/数据库/模型/公式/参数变更，无外网、push、install 或 production/final acceptance。下一唯一任务 `S8-P3-T1`。

## v0.2.5 Stage 8 Phase 8.1 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S8-P81` / `PFI-V025-STAGE8-PHASE81-DESIGN-SYSTEM` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Phase 8.1 tasks=`4/4`，Stage 8=`4/12 in_progress`，v0.2.5=`100/156 (64.10%)`。
- 正式 Shell 默认亮色，10 类 token family、10 个 semantic archetype、empty/error/stale/ready 图表状态和 desktop/mobile 正式布局均已绑定。
- 强制 OS dark 下实际浏览器 10 routes × 2 viewports=`20/20`；console/page/HTTP/external-request errors=`0/0/0/0`，20 PNG decode pass，black-pixel files=0。
- Release frontend=`50e715a6b2e5c5162b32592c15d1661cba430ead3c2ed7a0a36d4634e38333f4`、backend=`83dbc65036a8921b4d45048eb736af4a526afb39a4d3fd6b7cb8d222165f8467`。
- Phase 8.2/8.3 和 whole-stage review 未开始；未使用 Finder/LaunchServices/GUI 文件操作，无财务数据/数据库/模型/公式/参数变更，无外网、push、install 或 production/final acceptance。下一唯一任务 `S8-P2-T1`。

## v0.2.5 Stage 7 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S7-WHOLE-REVIEW` / `PFI-V025-STAGE7-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE7-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 7 tasks=`12/12`、whole-stage review=`pass`、user acceptance=`accepted`；Stage 8 entry authorized but `not_started`。
- 当前 worktree 三条正式 Shell 工作流由 68 项 browser checks、frozen overlay、真实 verification logs 与三个 reviewer text/hash 绑定；最终结果只由 fail-closed builder 生成。
- 缺 economic-event adapter 时 operational lineage 与 11 metrics 全部 blocked/null；Phase 7.3 的 6,879/1,936 是 immutable historical candidate evidence，不是当前运行时金融事实。
- 初始 `C0/I14/M4` 经 auth/input/concurrency/migration/raw/canonical-read-model/trace/evidence/governance 整改后复审 `C0/I0/M0`。
- Release frontend=`584ff69880dcacf84da0a94b0fd7f4f42c3e2c28b50a920467a77cdf362a11de`、backend=`83dbc65036a8921b4d45048eb736af4a526afb39a4d3fd6b7cb8d222165f8467`。
- 未使用 Finder/LaunchServices/GUI 文件操作；无外网、push、install 或 production/final acceptance。下一唯一任务 `S8-P1-T1`。

## v0.2.5 Stage 7 Phase 7.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S7-P73` / `PFI-V025-STAGE7-PHASE73-METRIC-DRILLDOWN` / `ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN`。
- 当前 lifecycle：`candidate_pass`；Stage 7 phase tasks=`12/12 candidate_complete`，whole-stage review=`not_started`，Stage 7 仍 `in_progress`。
- 正式 Shell 三条 canonical 二级路由展示 15 参数域/96 entries、20 formulas、7-node/6-edge Interconnection Map 与 11 metric drilldowns。
- 当前 lineage 为 8,815 source records、6,879 complete、1,936 review、0 missing/silent drop；not-ready 值保持 null，tracked evidence 不含财务值。
- current-HEAD focused/compatibility Python 44/44、Node 29/29、正式 Shell 21/21；trace privacy rescan pass。未使用 Finder、无外网、无 DB/源数据写入、未 push/install。当前进度 `96/156 = 61.54%`。
- 下一唯一任务为 `STAGE7-WHOLE-REVIEW`；不得直接进入 Stage 8。

## v0.2.5 Stage 6 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S6-WHOLE-REVIEW` / `PFI-V025-STAGE6-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE6-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 6 tasks=`12/12`、whole-stage review=`pass`、user acceptance=`accepted`，Stage 7 entry authorized but not_started。
- 三笔 Phase commits/evidence 线性绑定；初审 `C0/I4/M1` 已整改为复审 `C0/I0/M0`。三份 Phase evidence 当前副本符合 Task Pack schema。
- 当前 HEAD 正式 Shell 14/14 browser checks：10 主入口、10 workspace 代表二级页、7 aliases、History/Reload/Invalid/keyboard/AX/no-JS 均通过，console/page/http/external-network errors=0。
- 未修改 model/formula/parameter 值，未读取财务数据或数据库；未使用 Finder、无外部网络、未 push/install。进度保持 `84/156 = 53.85%`。
- 下一唯一任务为 Stage 7 Phase 7.1 `S7-P1-T1..T4`；本次 run 未进入 Stage 7。

## v0.2.5 Stage 5 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S5-WHOLE-REVIEW` / `PFI-V025-STAGE5-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；12/12 tasks，初审 `C1/I4/M1` 整改后复审 `C0/I0/M0`，Pass Gate=`pass_with_explicit_blocked_models`。
- 四项真实财务指标已通过同一私有 read-model payload 绑定 homepage、consumption_page、report；三页 headless formal shell release identity ready，金额在写 evidence 前脱敏。
- `FORM-PFI-016/017/018/020` 的缺来源、chain、ground truth 或 OOS 残余继续 blocked；接受不等于生产模型全部有效。
- Stage 6 entry authorized 但 `not_started`；未使用 Finder，未访问外部网络，未 push/install，production/final acceptance=false。进度保持 `72/156 = 46.15%`。

## v0.2.5 Stage 5 Phase 5.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S5-P53` / `PFI-V025-STAGE5-PHASE53-MODEL-VALIDATION` / `ACC-PFI-V025-S5-P53-MODEL-VALIDATION`。
- 当前 lifecycle：`candidate_pass`；Stage 5 phase tasks=`12/12 candidate_complete`，whole-stage review=`not_started`。
- immutable Git blob 只读重放结果为 `8,815 = 6,879 published + 1,936 review + 0 silent drop`；源对象前后 identity 不变，数据库未读取或修改。
- `FORM-PFI-015/019` 真实 invariant、metamorphic 和 boundary sensitivity 通过；`FORM-PFI-016/017/018` 因真实依赖缺失 fail closed，`FORM-PFI-020` 为 structure-only，classification accuracy/OOS blocked。
- homepage、consumption_page、report 三个 consumer contract 表面 payload hash 一致；真实 UI/report renderer source 未修改，两个 actual render binding 均为 false/open，必须在 Stage 5 whole-stage review 解决或明确裁决。
- 未修改 model/formula/parameter 值，公开 evidence 不含财务金额或私有行；未使用 Finder、network、push 或 App install。当前进度 `72/156 = 46.15%`。
- 下一唯一任务为 `S5-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`；不得进入 Stage 6。

## v0.2.5 Stage 5 Phase 5.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S5-P52` / `PFI-V025-STAGE5-PHASE52-FINANCIAL-MODELS` / `ACC-PFI-V025-S5-P52-FINANCIAL-MODELS`。
- 当前 lifecycle：`candidate_pass`；Stage 5=`8/12 in_progress`，Phase 5.3 与 whole-stage review=`not_started`。
- 四个双口径分量按 source/economic event 去重且差异为 0；投资入金与投资申购是活动口径，不是净资产损失；未链接或超额退款 fail closed。
- 核心净资产/现金/余额 invariant 精确无容差；投资收益/成本/XIRR/fee/tax/FX/idle-cash drag 对零分母、多根、不可括根和不收敛 fail closed。
- 现金流窗口固定为 `7/21/30/60/90/180/360`；taxonomy/tag 约束为 L1<=12、单 L1 下 L2<=5、L2 总数<=50、恰好一个 primary category、default/custom/history/all-any view。
- 新增 `MOD-PFI-010`、`FORM-PFI-015..020`、`PARAM-PFI-081..092`；当前总数 `10/20/92`，五载体一致性纳入验证。
- 未读取/修改真实财务行或数据库，未改 Web/UI/报告源，未使用 Finder、network、push 或 App install；真实数据模型验证与真实绑定均为 Phase 5.3 scope，不声明 Stage 5/production/final acceptance。当前进度 `68/156 = 43.59%`。
- 下一唯一任务为 `S5-P3-T1..T4`；不得进入 Stage 5 whole-stage review。

## v0.2.5 Stage 5 Phase 5.1 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260715-PFI-V025-S5-P51` / `PFI-V025-STAGE5-PHASE51-FORMULA-PARAMETER-GOVERNANCE` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`。
- 当前 lifecycle：`candidate_pass`；Stage 5=`4/12 in_progress`，Phase 5.2/5.3 与 whole-stage review=`not_started`。
- 14 个现行公式均有完整 machine-readable version/hash/lifecycle；五载体参数零冲突；CNY/AUD 方向和单位固定，4.81 仅示例、production default=null。
- 六类可信度独立；记录分类权重/阈值保留，source/reconciliation/valuation/model/report 不得被 overall score 替代。
- 新增 `MOD-PFI-009`、`FORM-PFI-014`、`PARAM-PFI-073..080`；当前总数 `9/14/80`。
- 未读取/修改真实财务行或数据库，未使用 Finder、network、push 或 App install；不声明 Stage 5/production/final acceptance。当前进度 `64/156 = 41.03%`。
- 下一唯一任务为 `S5-P2-T1..T4`；不得进入 Phase 5.3。

## v0.2.5 Stage 4 Whole-stage Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S4-WHOLE-REVIEW` / `PFI-V025-STAGE4-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE4-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；12/12 tasks、6/6 Acceptance、4/4 safety stops，初审 `C0/I5/M1` 整改后复审 `C0/I0/M0`。
- 七个核心指标全部 `not_loaded/null`，五个表面同 hash，Chrome headless false-zero=0；这不表示生产余额/持仓/估值已就绪。
- 用户阶段授权已绑定精确残余；Stage 5 entry authorized 但 Stage 5=`not_started`，下一 gate 为 `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`。
- 未使用 Finder，未读取/修改真实财务行或数据库，未 network、push、install，不声明 production/final acceptance。进度保持 `60/156 = 38.46%`。

## v0.2.5 Stage 4 Phase 4.3 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S4-P43` / `PFI-V025-STAGE4-PHASE43-METRIC-CONSISTENCY` / `ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY`。
- 当前 lifecycle：`candidate_pass`；Stage 4 三个 Phase 共 `12/12 candidate tasks`，Stage 4=`in_progress`，whole-stage review=`not_started`。
- 七个核心指标全部 `not_loaded/null`，financial values emitted=0；13 状态 strict contract 禁止非 ready 数值、ready 零和无完整证据的 confirmed_zero。
- Stage 2/3/4 aggregate 与 formula/parameter contract 生成一个 page-independent hash；homepage/accounts/investment/consumption/report 五表面 hash 与 metric fingerprints 零差异。
- 新增 `MOD-PFI-008`、`FORM-PFI-011..013`、`PARAM-PFI-068..072`；当前总数 `8/13/72`。
- 未读取或修改真实财务行/数据库，未使用 Finder、network、push 或 App install；不声明 Stage 4/production/final acceptance。当前进度 `60/156 = 38.46%`。
- 下一唯一任务为 `S4-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE4-WHOLE-REVIEW`；不得进入 Stage 5。

## v0.2.5 Stage 4 Phase 4.2 Historical Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S4-P42` / `PFI-V025-STAGE4-PHASE42-HOLDINGS-VALUATION` / `ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION`。
- 当前 lifecycle：`candidate_pass`；Stage 4=`in_progress`，Phase 4.1/4.2=`8/12 candidate_pass`，Phase 4.3 与 whole-stage review=`not_started`。
- holdings/prices/FX 三个 required sources 均 `not_loaded`；投资市值、成本基础、未实现损益 3/3 metrics 为非 ready/null，financial values emitted=0。
- 持仓数量不按交易推断；cost-basis method 与 fees 必须显式；价格/FX 不得晚于 valuation time；legacy FX reference 未使用。
- 新增 `MOD-PFI-007`、`FORM-PFI-009..010`、`PARAM-PFI-061..067`；当前总数 `7/10/67`。
- 未读取/修改真实财务行或数据库，未使用 Finder、network、push 或 App install；不声明 Stage 4/production/final acceptance。当前进度 `56/156 = 35.90%`。
- 下一唯一任务为 `S4-P3-T1..T4` / `ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY`；不得进入 Stage 4 whole-stage review。

## v0.2.5 Stage 4 Phase 4.1 Current Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S4-P41` / `PFI-V025-STAGE4-PHASE41-ACCOUNT-BALANCE` / `ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT`。
- 当前 lifecycle：`candidate_pass`；Stage 4=`in_progress`，Phase 4.1=`4/4 candidate_pass`，Phase 4.2/4.3 与 whole-stage review=`not_started`。
- 两个 required sources 均 `not_loaded`；账户资产、现金、负债 3/3 metrics 为非 ready/null，financial values emitted=0；交易数据未用于推断余额。
- 完整 snapshot lineage 才可按 Decimal 精确执行现金公式；差异 fail closed，tolerance=0，confirmed-zero 必须完整证据。
- homepage/accounts 共享同一 read_model_hash；五页面整体一致性未在本 Phase 声明。
- 新增 `MOD-PFI-006`、`FORM-PFI-008`、`PARAM-PFI-058..060`；当前总数 `6/8/60`。
- 未读取/修改真实财务行或数据库，未使用 Finder、network、push 或 App install；不声明 Stage 4/production/final acceptance。当前进度 `52/156 = 33.33%`。
- 下一唯一任务为 `S4-P2-T1..T4` / `ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION`；不得进入 Phase 4.3。

## v0.2.5 Stage 3 Whole-Stage Current Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S3-WHOLE-REVIEW` / `PFI-V025-STAGE3-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE3-WHOLE-REVIEW`。
- 当前 lifecycle：`accepted_for_transition`；Stage 3 tasks=`12/12`、Acceptance=`6/6`、Stop Conditions=`4/4`，初审 `C0/I3/M1` 整改后复审 `C0/I0/M0`。
- 真实只读输入仍精确为 8,815=6,879 published+1,936 review+0 silent drop；第二次导入发布 0、collision 0、lineage 6,879/6,879 完整、五页面共用一个 read_model_hash。
- 残余不升级：1,250 条 transfer 与 249 条 refund 未确认，只 fail-closed 到 review queue；Stage Pass 精确结果为 `pass_with_review_queue`。
- 本 Gate `model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `5/7/57`。
- 用户中间授权已绑定 Stage 3 exact scope；Stage 4 entry authorized 但 Stage 4=`not_started`，下一 gate 为 `ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT`。
- 未修改真实源或数据库，未使用 Finder，未执行 network、push 或 App install；不声明 production/final acceptance。当前 v0.2.5 进度保持 `48/156 = 30.77%`。

## v0.2.5 Stage 3 Phase 3.2 Current Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S3-P32` / `PFI-V025-STAGE3-PHASE32-NORMALIZED-EVENT` / `ACC-PFI-V025-S3-P32-NORMALIZED-EVENT`。
- 当前 lifecycle：`candidate_pass`；Stage 3=`in_progress`，Phase 3.1/3.2=`8/12 candidate_pass`，Phase 3.3=`not_started`，下一 gate 为 `ACC-PFI-V025-S3-P33-RECONCILIATION`。
- NormalizedTransaction 强制金额/币种/方向与四类时间；Interconnection 只允许显式 link reference 或 singleton，不按金额、时间或来源名称猜测。
- 10 类 event policy 明确 transfer/repayment/refund/investment chains 的 flags；未知 event type 禁止发布。Ledger Event 保存逐笔 posting、完整 lineage 与 deterministic idempotency key。
- 新增 `MOD-PFI-004`、`FORM-PFI-004..005`、`PARAM-PFI-036..047`；当前总数 `model/formula/parameter=4/5/47`。
- 本 Phase 只使用 typed contract values，不读取真实财务数据、不执行真实 duplicate import/reconciliation、DB migration、Finder、network、push 或 App install，也不声明 production financial acceptance。
- 当前 v0.2.5 进度：`44/156 = 28.21%`；Stage 3：`8/12 = 66.67%`。

## v0.2.5 Stage 3 Phase 3.1 Current Overlay

- Iteration / Contract / Acceptance：`ITER-20260714-PFI-V025-S3-P31` / `PFI-V025-STAGE3-PHASE31-SOURCE-ACCOUNT` / `ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT`。
- 当前 lifecycle：`candidate_pass`；Stage 3=`in_progress`，Phase 3.1=`4/4 candidate_pass`，Phase 3.2/3.3=`not_started`，下一 gate 为 `ACC-PFI-V025-S3-P32-NORMALIZED-EVENT`。
- Source Profile 的 source type/capability 为开放 namespaced token；账户支持多角色与重叠生效期；parser provenance 强制绑定 parser id/version/source hash；unknown role 进入 review queue 且 `publish_allowed=false`。
- 新增 `MOD-PFI-003`、`FORM-PFI-003`、`PARAM-PFI-028..035`；当前总数 `model/formula/parameter=3/3/35`。
- 本 Phase 未读取或修改真实财务数据/数据库，未使用来源名称分类、Finder、network、push 或 App install；Stage 3 whole review、production 与 final human acceptance 均为 false。
- 当前 v0.2.5 进度：`40/156 = 25.64%`；Stage 3：`4/12 = 33.33%`。

## v0.2.5 Stage 0 Phase 0.2 Candidate Overlay

- Iteration / Contract / Acceptance：`ITER-20260711-PFI-V025-S0-P02` / `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` / `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT`。
- 最新用户决策批准 exact 20-file override：8 个 Phase core/evidence artifacts + 12 个具名 governance companions；不授权第 21 条路径。
- Active Requirements、history disposition、scope boundary 与 run contract 已组成 pre-commit candidate；开放的 owner/release/App/runtime/route conflicts 继续保持 blocked，不能被统一授权改写成 resolved。
- 当前 gate：`candidate_pending_postcommit_attestation`。Task 5 evidence 与 pre-commit validation 已完成；单一原子提交和 external post-commit attestation 完成前，不声明 Phase acceptance。
- 本 overlay 不改变上方历史 snapshot/assurance facts，不代表 release、Stage pass、v0.2.5 完成或生产就绪。
- 本轮没有 runtime、模型/公式/参数运行值、真实/私有 data、DB、App、migration、安装或 GitHub push 变更。

## v0.2.5 Stage 0 Phase 0.3 Validation Overlay

- Iteration / Contract / Acceptance：`ITER-20260711-PFI-V025-S0-P03` / `PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE` / `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`。
- Phase 0.2 external attestation 已将上一 Phase scope conflict 解析为 `resolved_by_approved_override`，绑定 content commit `7433be0d70bdae42959c1b71753d93f8737db60d`；本 overlay 不改写其历史 tracked lifecycle。
- 当前 lifecycle：`candidate_pass_pending_postcommit_attestation / approved_pending_postcommit_attestation`。second-remediation corrected provisional 与 canonical exact-25 final-tree gates 已通过，仅待 atomic commit 与 external postcommit attestation。
- 上方 product version、VERSION、runtime、owner、assurance 与 delivery truth 均未改变；模型/公式/参数运行值保持不变，canonical delivery tasks 仍为 10。
- Stage 0 whole-stage review 与 Stage 1 均为 `not_started`；没有 release、安装、GitHub push 或生产验收声明。

## v0.2.5 Stage 0 Phase 0.3 FND-030 Compensation Overlay

- Correction / Iteration / Acceptance：`PFI-V025-S0-P03-COMP-FND030` / `ITER-20260711-PFI-V025-S0-P03` / `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`；上方原 P03 lifecycle 是补偿前历史快照。
- FND-030 已修正为 `N/A/non-gap`，`GAP-P1-04` 已删除；正式首页源为 `PFI/web/app/pages/home.js`，而未被指定的 legacy path 缺失不构成 product gap。
- 当前分类计数为 `StillPresent=23 / Fixed=7 / Regressed=0 / N/A=4 / New=4`；开放生产阻断为 `27 (P0=22 / P1=5)`；primary gaps 为 `12`；non-gap findings 为 `11`。
- 原 Phase commit `31368570082c34eca50c72c7d7b2ef46b0e6854d` 与原 attestation SHA-256 `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` 保持不可变；当前 gate 为 `classification_compensation_pending_postcommit_attestation`，补偿 commit 和 external compensation attestation 尚未完成。
- 本补偿不改变上方 product/version/runtime/owner/assurance/delivery truth，不新增 model/formula/parameter/task/Acceptance，不安装、不 push。Stage 0 whole-stage review 与 Stage 1 均为 `not_started`。

## v0.2.5 Stage 0 Whole-Stage Review Overlay

- Review / Acceptance：`PFI-V025-S0-WHOLE-REVIEW` / `ACC-PFI-V025-S0-WHOLE-REVIEW`；base `a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2`。
- external compensation attestation `2161efc16fdd178dba81ff5da5b97633656d433da8a26c1f71896625b1905b13` 已解析上方历史 compensation-pending layer；whole-stage tracked index 持久绑定 P01/P02/P03/compensation commit 与 hash chain。
- 六项 Stage 0 Acceptance 与 Stop Conditions 通过；durable index、executable verifier/typed result records、review-commit attestation lifecycle、FND-030 unique-selector overlay 已整改，post-remediation review counts 为 `0/0/0`。
- 当前 lifecycle 为 `codex_candidate_pass_pending_review_commit_attestation_and_explicit_user_acceptance`；27 个 P0/P1 production blockers 仍开放，不能声明 v0.2.5、release、App/runtime/data 或 production acceptance。
- `human_acceptance.json` 不存在，Stage 1 未开始；本轮不安装、不 push、不改产品/runtime/data/DB。

## v0.2.5 Stage 1 Phase 1.1 Release Identity Overlay

- Iteration / Acceptance：`ITER-20260712-PFI-V025-S1-P11` / `ACC-PFI-V025-S1-P11-RELEASE-IDENTITY`；tasks `S1-P1-T1..T4`。
- `VERSION=v0.2.5`；App plist、launcher、runtime API、frontend embedded manifest 绑定同一 build/content commit/frontend/backend hash。
- mismatch、partial query、invalid JSON 与 backend unavailable 均 fail closed；隔离 Chrome screenshot 证明中文“版本冲突”页可见且旧 shell 隐藏。
- final post-review content commit `a9592b8c...` supersede 初始及中间 pairs；除 raw manifest SHA、runtime-config 与路径脱敏外，新增 Streamlit iframe launcher-source 门禁、static embedded validation 与 Finder 中文恢复 dialog。focused GREEN 为 Python `10`、Node `15`；中间 review `C1/I2/M0` 尚待 fresh re-review 清零。
- 生命周期：`candidate_pass_pending_identity_binding_commit_attestation_and_independent_review`；Stage 1 `in_progress`，Stage 2 `not_started`。
- 用户持续过渡授权为 active，但不等于 final release acceptance；production/final human acceptance 仍为 false。
- 本 Phase 没有 push、App install、live 8501/8502、财务数据、SQLite、model/formula/parameter behavior 变更。

## v0.2.5 Stage 1 Phase 1.2 Cache Governance Overlay

- Iteration / Acceptance：`ITER-20260712-PFI-V025-S1-P12` / `ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE`；tasks `S1-P2-T1..T4`。
- HTTP：HTML private revalidation + validators/304；只对真实 content-hash Streamlit assets immutable；PFI-owned assets 是 `srcdoc` inline，不制造 hashed-URL 声明。
- Browser/runtime：历史 Service Worker/CacheStorage 显式清理；surviving controller fail closed；`pageshow.persisted` 重验 manifest/cache policy；old epoch 不可覆盖 newer mismatch。
- Streamlit：actual 1.35.0，30 秒 memory-only `st.cache_data` adapter；composite key 覆盖 Roadmap/Task Pack 全部必需 dimensions，并将 runtime/lock drift 纳入 invalidation。
- Evidence：初始 pair 独立复核 `C0/I4/M0` 后已 superseded；remediation RED `4 failed / 8 passed`，最终 Python `22 passed`、Node `23 passed`、HTTP `4/4`、Chromium `10/10`、trace ZIP 22 members integrity/privacy PASS、console/page error `0/0`；real back/forward 为 `persisted=false`，未伪报真实 bfcache hit。
- 生命周期：`remediation_candidate_pass_pending_final_binding_attestation_and_fresh_independent_review`；content commit `b3885f15...`。Stage 1 仍 `in_progress`，Phase 1.3/Stage 2 未开始。
- 未执行 push、App install/Finder/new profile、live 8501/8502、财务数据/DB、model/formula/parameter semantics 或 final human acceptance。

## v0.2.5 Stage 1 Phase 1.3 Isolated App Acceptance Overlay

- Iteration / Acceptance：`ITER-20260712-PFI-V025-S1-P13` / `ACC-PFI-V025-S1-P13-ISOLATED-APP-ACCEPTANCE`；tasks `S1-P3-T1..T4`。
- Finder/runtime：一次性候选真实双击；三成员 PGID、两个候选端口与 fresh Chromium identity/hash chain 全部验证通过。
- Browser：25 项 checks 全部为 true，6 次 pageshow / 6 次 websocket，console/page/request/HTTP/unexpected-host errors 均为 0；`persisted=false` 是真实记录。
- Cleanup：canonical entries、protected metadata 与 Git 状态不变；进程组、端口、LaunchServices 与临时根全部清理。
- 生命周期：`candidate_pass_pending_direct_binding_attestation_and_independent_review`；Stage 1 保持 `in_progress`，Stage 2 `not_started`。
- 未执行 canonical install、canonical Finder UAT、GitHub push、dependency install、财务数据/SQLite 或 model/formula/parameter 行为变更。

<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_BEGIN -->
Stage 1 Phase 1.3 Isolated App Acceptance Overlay
owner_view_conflict_id=PFI-V025-CONFLICT-OWNER-VIEWS
owner_view_conflict_status=blocked
owner_evidence_state=unified_owner_view_not_proven
owner_view_resolution_task=STAGE12-WHOLE-REVIEW-REREVIEW
owner_views_unified=false
v0.2.5_accepted=false
stage_1_status=in_progress
canonical_install_gate=S12-P2-T1
<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_END -->

## v0.2.5 Stage 1 Whole-Stage Review Overlay

> 历史 tracked snapshot；已由下方 matching external attestation activation 与 Stage 2 overlay 取代，不是当前状态。

- Iteration / Contract / Acceptance：`ITER-20260713-PFI-V025-S1-WHOLE-REVIEW` / `PFI-V025-STAGE1-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE1-WHOLE-REVIEW`。
- Final remediation content：`04390bcf17c18de107eb2f1b4ce051c83638f98c`；tracked lifecycle 为 `candidate_pass_pending_postcommit_attestation`。
- 12 个 Stage 1 tasks、6 个 Acceptance Criteria 与 4 个 Stop Conditions 已机器化；T1/T3 install/entry 语义由 `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE` 满足，canonical install 保留到 `S12-P2-T1`。
- matching external attestation 激活后 Stage 1 才解释为 `accepted_for_transition`；当前 Stage 2 entry 未激活，stage_2_status: `not_started`。
- 未 push、未安装 canonical App、未读取/修改财务数据或 SQLite；model/formula/parameter behavior 未改变，production/final human acceptance=false。

## v0.2.5 Stage 2 Phase 2.1 Data Root / Source Manifest Overlay

- Stage 1 matching external attestation SHA-256 a03651248d67f727f001b52c0a08961416155506b374fa08123247ebfa8f0d2a 已验证，Stage 1 解释为 accepted_for_transition，Stage 2 entry=true。
- Phase 2.1 tasks S2-P1-T1..T4 candidate pass；canonical private root alias=$PFI_DATA_HOME，当前由 ~/.pfi user-state default 显式解析；未搬迁数据。
- 交易 source=ready、record_count=8815、coverage=2022-06-06..2026-06-03；SQLite=partial metadata。余额/负债/持仓/价格/FX 因尚未绑定可验证 aggregate metadata 均为 not_loaded。
- 交易 source input available；分类、CNY 消费、现金、投资市值、净资产因 source/contract dependencies 未完成均 blocked/null，不声明 0。
- Root metadata 与 DB before-after 已在限定观察范围内保持一致；无绝对私有路径、row、金额、账户标识、credential、Finder、push 或 App install。
- 当前生命周期：stage_2_phase_2_1_candidate_pass；Stage 2=in_progress，Phase 2.2=not_started，production/final human acceptance=false。

## v0.2.5 Stage 2 Phase 2.2 Temporal / FX Truth Overlay

- Phase 2.2 tasks `S2-P2-T1..T4` candidate pass；八个时间字段与 timezone-aware RFC3339 contract 固定为 `Australia/Sydney`。
- FX effective business date 使用 Sydney local `06:00:00` cutoff；周末及显式 source-closed dates 仅向前回退到前一 open date，naive timestamp/无效 cutoff fail closed。
- `AUD/CNY` direction 固定为 `AUD_TO_CNY`，含义为 `1 AUD = rate CNY`；production source/snapshot/rate/hash 仍 `not_loaded/null`，旧 v0.2.2 snapshot 只作 reference。
- ordinary runtime network audit=`pass`，Phase 2.2 policy module 的 network import/call 均为 0；未执行 refresh、source mutation、Finder、push 或 App install。
- 当前生命周期：`stage_2_phase_2_2_candidate_pass`；Stage 2=`in_progress`，Phase 2.3=`not_started`，下一任务 `S2-P3-T1`，production/final human acceptance=false。

## v0.2.5 Stage 2 Phase 2.3 Safe Sandbox Overlay

- Phase 2.3 tasks `S2-P3-T1..T4` candidate pass；transaction source 以 commit-bound immutable Git object 读取，8815 条记录与 manifest count 一致，未输出财务行值。
- operational SQLite 只复制到 `0700` 临时目录中的 `0600` 文件，完成 `quick_check` 与已知表数量探测后清理；source identity/hash 前后相同，未输出私有路径、表名或 row。
- 三次真实性能观测为 `117.636/123.182/127.156 ms` 与 peak Python allocation `14491986/14491986/14492499 bytes`；该结果不是生产 SLA。
- no-fake/privacy gate 通过：source 缺失即 blocked，无 financial fixture fallback；固定十文件扫描的私密路径、财务值、账户标识、credential、表名、Finder、source mutation 计数均为 0。
- 当前生命周期：`stage_2_phase_2_3_candidate_pass_pending_whole_stage_review`；Stage 2 仍 `in_progress`，whole-stage review=`not_started`，用户接受 pending，Stage 3 未授权；未 push/install/Finder。

## v0.2.5 Stage 2 Whole-Stage Review Overlay

- `ITER-20260714-PFI-V025-S2-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE2-WHOLE-REVIEW`；Phase evidence commits `bce1b2182 -> 7875e006a -> 431ddb30c` 保持不可变。
- 初审 `C0/I3/M1` 的 verifier/Evidence、final index、human acceptance 与 current source disposition 缺口已全部整改；requirements/evidence、code-security/privacy、governance/renderer 三路复审 `C0/I0/M0`。
- Stage 2 `12/12 tasks`、`6/6 Acceptance`、`4/4 Stop Conditions` 与 Pass Gate 全部通过。
- 用户 blanket interim authorization 已具体绑定 canonical root、8815-record scope、五个 blocked/null 指标及 offline/no-fake 边界；Stage 2=`accepted_for_transition`。
- Stage 3 entry authorized，但 Stage 3=`not_started`；未使用 Finder，未 push/install，production/final human acceptance=false。
