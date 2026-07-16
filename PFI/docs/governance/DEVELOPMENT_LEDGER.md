# DEVELOPMENT_LEDGER

## ITER-20260716-PFI-V025-S12-FINAL-ACCEPTANCE

- Contract / Acceptance：`PFI-V025-STAGE12-FINAL-ACCEPTANCE-RELEASE-FREEZE` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW`。
- 精确绑定：build `pfi-v025-s1p1-20260712.1`、App `0.2.5/20260712.1`、A `c8ce63a...`、B `559cf19...`、C `123f5a6...`、evidence-index `sha256:ebd03b8a...`、请求时间及五项非阻断 P2。
- 验证：TaskPack human acceptance schema、A/B/C/index/request/App gate、historical manifest snapshots 与 runtime zero drift 通过；focused final-acceptance suite 通过。
- 结果：`S12-P3-T4=completed`，release freeze=true，Stage 12=`12/12`，整体=`156/156 (100%)`。
- 边界：push=false、final reinstall=false、production parity=false；Finder、`open`、LaunchServices、AppleScript、GUI 操作均为 0。

## ITER-20260716-PFI-V025-S12-WHOLE-REVIEW-REREVIEW

- Contract / Acceptance：`PFI-V025-STAGE12-WHOLE-REVIEW-REREVIEW` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW`；只做独立复审并停在 exact final acceptance 前。
- Commit model：runtime source=`78375ec98fc1265abd03ef10087cc05beccab8b4`；product/remediation anchor A=`c8ce63aac785ae1f119cfe1ff993c4e81436bf97`；reviewed remediation closure B=`559cf190ccfd97aabcf37a5edf2bf1e9abe300fc`。A 是 B 的直接父提交，B 与当前非 runtime overlay 均无 runtime payload 漂移。
- 独立重算：release identity、Phase 12.3 exact binding、两套 upstream artifact manifest、CLI-only entry census、隔离 fresh real E2E 全部通过；manifest mismatch=0、entry mismatch=0、canonical DB changed=false、external network=false。
- 验证：fresh E2E `17/17`；focused Stage 12 `61/61`；selected adjacent `115/115`；Node `8/8`；dual-plane、Lean renderer、complete-overlay governance、privacy 与 rereview artifact manifest 通过。
- 结果：三项原 P1 均 `closed_verified`；复审新增 `0 P0 / 0 P1 / 0 minor`。五项 P2 residual 继续披露；总进度仍 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`。
- 边界：本地 deterministic rereview 不声称外部人工或 subagent reviewer；`S12-P3-T4`、final acceptance、push、最终重装均未执行。Finder、`open`、LaunchServices、AppleScript、GUI 操作均为 0。

## ITER-20260716-PFI-V025-S12-WHOLE-REVIEW-REMEDIATION

- Contract / Acceptance：`PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW-REMEDIATION`；只关闭初审三项 P1，并停在独立复审前。
- Release identity：runtime payload 的最后变更提交为 `78375ec98fc1265abd03ef10087cc05beccab8b4`；manifest 与 embedded web identity 同步，source 后 runtime payload 零漂移，canonical App 与 Phase 12.2 receipt 一致。
- Exact binding：remediation candidate 为 `c8ce63aac785ae1f119cfe1ff993c4e81436bf97`；Phase 12.3 index/request/state/evidence 均精确绑定该 commit，index SHA-256 为 `ebd03b8abf92238aac0e3f972461e35de6ce4b3be27c3662ab24f6af7b342344`，不再使用 `SELF` 或 stale head。
- Entry：旧 Downloads App 经版本/build/hash 核对后以 CLI 原子移动到 0700 私有隔离目录；未删除，receipt 保留 `$HOME` 回滚命令。Canonical App 未修改，Desktop symlink 正确，entry mismatch=0。
- 验证：fresh real headless E2E、focused Stage 12、selected Stage 4–11、Node `8/8`、release identity、dual-plane、renderer、complete archive+overlay governance、privacy 与 artifact hashes 通过。
- 结果：初审 `3` 项 P1 全部 closed pending rereview，整改后 open P0/P1=`0/0`；五项 P2 继续透明保留。整体仍 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`。
- 边界：独立复审、`S12-P3-T4`、最终验收、push、最终重装均未执行；canonical DB 未读写，Finder、`open`、LaunchServices、AppleScript、GUI 操作均为 0。

## ITER-20260716-PFI-V025-S12-WHOLE-REVIEW-INITIAL

- Contract / Acceptance：`PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL` / `ACC-PFI-V025-STAGE12-WHOLE-REVIEW-INITIAL`；风险路由 `T3_RELEASE_REAL_E2E_PRIVACY_REVIEW`，只完成 Stage 12 独立整阶段初审。
- Review base：`9a7245acf984a4eb98f93c4aab7bb4d02095294f`；Phase 12.1/12.2/12.3 的 119/119 declared artifacts 与 TaskPack evidence schema 通过，Phase 12.3 index 的 89/89 inputs 和 detached hash 重算通过。
- Fresh truth：重新读取 4 个 immutable source blobs，在临时隔离 DB 运行真实 headless import/review/report E2E 17/17；形成 8,808 ledger / 803 review，Holdings 保持 `not_loaded/not_run`，canonical private DB 未读写。
- 初审结果：`0 P0 / 3 P1 / 0 minor`。P1 分别为 release manifest source commit 落后、pending acceptance/state 未精确绑定 candidate、Downloads 存在旧 v0.2.3 非 canonical App。
- 验证：focused Stage 12、selected Stage 4–11、Node `8/8`、dual-plane、renderer、complete archive+overlay governance、privacy 与 artifact hashes 通过；5 项 P2 residual 如实保留。
- 边界：本 run 不整改、不复审、不创建最终 `human_acceptance.json`，不 freeze/push/重装；Finder、`open`、LaunchServices、AppleScript 与 GUI 操作均为 0。
- 结果：`initial_review_remediation_required`；整体仍 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`。下一唯一 run 为 `STAGE12-WHOLE-REVIEW-REMEDIATION`，整改后必须另起独立复审。

## ITER-20260716-PFI-V025-S12-P123

- Task / Acceptance：`S12-P3-T1..T3` / `ACC-PFI-V025-S12-P123-RELEASE-FREEZE-CANDIDATE`；`S12-P3-T4` 只登记为 whole-stage review 后的最终明确验收关口。
- 上游集成：`origin/main@5ff1f3c5` 已合并为 `665ee5aa8`；保留 dual-plane migration，不恢复被删除的顶层 `MetaDatabase`。
- Source truth：四个已复核真实 blobs 由 `78375ec98fc1265abd03ef10087cc05beccab8b4` immutable lock 统一读取，逐项验证 OID/bytes/SHA-256；release test、真实 browser E2E 与 target-Mac UAT 不再依赖当前 `HEAD` tree 的旧路径。
- 状态：VERSION、compact README/HANDOFF、canonical governance、三份完整中文 human entries 与 dual-plane facts 统一到 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`。
- Evidence：Stage 0–11 与 Stage 12.1/12.2 关键证据形成 one-way index + detached hash；pending acceptance request 绑定 version/build/SELF commit 语义/index hash/范围/三项 P2。
- 结果：`S12-P3-T1..T3=candidate_complete`，`S12-P3-T4=waiting`；下一唯一 run 为 `STAGE12-WHOLE-REVIEW`。
- 边界：真正 `human_acceptance.json` 不存在；未 push、final reinstall、release freeze、production/final acceptance、canonical DB mutation 或外部网络；Finder/`open`/LaunchServices/AppleScript/GUI 操作为 0。

## ITER-20260716-PFI-V025-S12-P122

- Task / Acceptance：`S12-P2-T1..T4` / `ACC-PFI-V025-S12-P122-TARGET-MAC-CLI-UAT`；风险路由 `T3_CANONICAL_APP_INSTALL_REAL_FINANCIAL_UAT_SQLITE_BACKUP_DISK_PRESSURE_RELEASE_PRIVACY`，仅完成 Stage 12 Phase 12.2 candidate。
- no-Finder/App：按用户最新明确指令，Finder、`open`、LaunchServices、AppleScript 与 GUI 文件操作全部禁用；以 CLI atomic replace 安装 canonical `/Applications/PFI.app` v0.2.5 / 20260712.1，并直接运行 bundle executable，同 manifest/runtime/query build。
- 真实工作流：4 个 immutable source objects、8,815 raw / 8,808 ledger；完成 1 个 review（803→802）并验证 restart persistence，10 个一级入口及 source/formula/parameter/interconnection 下钻通过。Holdings=`not_loaded/not_run`，5 reports=`3 blocked/2 partial`，无 fixture/fallback 或假零。
- 生命周期/恢复：start、3 次 repeated start 单 runtime、browser-close、offline-recovery、stop/restart 通过。canonical SQLite 仅 mode=ro Online Backup；restore/rollback 只在隔离副本；临时 `hdiutil -nobrowse` 卷触发真实 `SQLITE_FULL` code 13 后完成清理和 recovery。
- 整改：frontend release identity 请求补 runtime token；runtime API 启动时冻结 process release cache policy，真实数据写入后同进程 release key 不再漂移。
- 验证：Phase harness candidate pass；focused Python=`55 passed`、Node cache-policy=`8/8`，privacy/artifact/release identity 通过。P0/P1=`0/0`，P2=`3`；真实 kernel sleep/wake 未执行，只有明确披露的 owned-process proxy。
- 结果：Phase 12.2=`4/4 candidate_pass`，Stage 12=`8/12 in_progress`，v0.2.5=`152/156 (97.44%)`；Phase 12.3、whole-stage review/user acceptance 均 `not_started`，下一任务 `S12-P3-T1`。
- 边界：canonical DB 零写，model/formula/parameter 数值零变更；未使用任何 GUI 文件面，无 push/release freeze/production/final acceptance。

## ITER-20260716-PFI-V025-S12-P121

- Task / Acceptance：`S12-P1-T1..T4` / `ACC-PFI-V025-S12-P121-AUTOMATED-REAL-E2E`；风险路由 `T3_REAL_FINANCIAL_IMPORT_RELEASE_REGRESSION_PRIVACY`，仅完成 Stage 12 Phase 12.1 candidate。
- 真实输入：4 个 immutable Alipay Git objects、8,815 raw → 8,808 isolated ledger + 803 review；preview、confirm、idempotent replay、SQLite integrity/FK 通过，canonical source/database 零写入，临时数据库已删除。
- 整改：strict incremental GB18030 probe 关闭 64 KiB 多字节边界误判；post-evidence scanner 字段名不再自命中敏感标识符正则；两项 P1 均有回归且关闭。
- UI/报告：10 一级 + 10 代表性二级 route，5 reports=`3 blocked/2 partial`，Holdings=`not_loaded/not_run`、无假零；20 routes/40 screenshots 的 deterministic WCAG 2.2 AA、keyboard、CDP AX、visual/performance pass，外部请求 0。
- 验证：focused regression=`358 passed, 6 deselected`；6 项 immutable historical-state literal 作为非发布阻断 P2 test debt，current-state replacements 通过；post-evidence=`21/21`，73/73 artifact hashes、privacy、release identity、renderer 与完整 overlay PFI governance 通过。
- 结果：Phase 12.1=`4/4 candidate_pass`，Stage 12=`4/12 in_progress`，v0.2.5=`148/156 (94.87%)`；Phase 12.2/12.3、whole-stage review/user acceptance 均 `not_started`，下一任务 `S12-P2-T1`。
- 边界：model/formula/parameter 值零变更；未使用 Finder/LaunchServices/GUI，无 install/deploy/push/release freeze/production/final acceptance。

## ITER-20260716-PFI-V025-S11-WHOLE-REVIEW

- Task / Acceptance：`STAGE11-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`；风险路由 `T2_SQLITE_REAL_BACKUP_RESTORE_PRIVACY_RELEASE_REVIEW`，只完成 Stage 11 独立整阶段审查、整改、复审与 transition acceptance。
- 绑定：Phase 11.1/11.2/11.3 三条线性 product/evidence chain 与 87 个 immutable artifacts 全匹配；source review base=`f49e10f47a2f9996e4de0e66402686ae502ce16c`。
- 初审/整改：`C0/I4/M0`；整改提交 `9c450ea483cd2040636e375c9f7d84e5127e44cf` 移除 source-directory coordination lock、CLI absolute paths，并补齐真实 canonical source-zero-write rehearsal 与 browser/DOM/AX/trace evidence。
- 数据库：canonical operational SQLite 仅以 `mode=ro/query_only` Online Backup 读取；source file hash/stat 与 directory entries/stat 不变、无 source lock。successful restore 与 injected automatic rollback 只在隔离临时目标通过。
- 浏览器/边界：loopback-only headless browser `23/23`，DOM、CDP AX、截图、脱敏 trace、unknown-route 404、public source/dist scan、external request 0 通过。
- 验证/复审：focused Stage 11 `115/115`；selected adjacent regression、TaskPack、release identity、Python/Node、完整 archive + exact overlay governance/renderer、privacy/evidence schema 通过；三轨 frozen rereview=`C0/I0/M0`。
- 结果：Stage 11=`accepted_for_transition`，standing acceptance=`accepted_via_standing_transition_authorization`；Stage 12 entry authorized 但 `not_started`，v0.2.5 保持 `144/156 (92.31%)`。
- 边界：未迁移/替换/恢复 canonical DB，未导出真实财务行或值；未使用 Finder/LaunchServices/GUI，无外网/deploy/push/install/production/final acceptance。下一任务 `S12-P1-T1`。

## ITER-20260716-PFI-V025-S11-P113

- Task / Acceptance：`S11-P3-T1..T4` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`；风险路由 `T2_PRIVACY_DISTRIBUTION_CONTEXT_RELEASE_IDENTITY`，仅完成 Phase 11.3 candidate。
- public：原 pseudo-dashboard 收敛为 static boundary notice；HTML/CSS/JSON only、无 application route/runtime binding/local connection/Context exposure，Wrangler unknown route=`404-page`。
- Context：`pfi_context.v1` Alpha-only，七项 metadata、八项状态型 payload、read-only/no-writeback；legacy Stage 3/4 input 只做 provenance hash，活动 adapter 在缺 current validated read model 时保持 blocked/not_loaded。
- security：export writer 固定 0700/0600、no-overwrite/no-symlink/no-public-path；source/dist 与 active dependency/private/path/credential/amount/Ralpha/Serenity scan finding=0，负向注入 fail closed。
- scope override：TaskPack literal allowlist 缺必需 public surface、active legacy adapter 与 release identity closure；standing authorization 下仅做披露的最小扩展，`allowed_files_obeyed=false`。
- 验证：产品提交 `890d38a759b9689a65152aa20527bde7ba04b52e`；focused/adjacent/release/shell `77/77`，public build/双扫描、TaskPack schema、完整 archive overlay governance/dual renderer、privacy/artifact hashes 通过。
- 结果：Phase 11.3=`candidate_pass`，Stage 11 phase tasks=`12/12 candidate_complete`，v0.2.5=`144/156 (92.31%)`；Stage 11=`in_progress_pending_whole_stage_review`，下一任务 `STAGE11-WHOLE-REVIEW`。
- 边界：未使用 Finder/LaunchServices/GUI；无 canonical private DB/真实财务行/model/formula/parameter 数值变更；仅官方 Cloudflare 文档研究，产品/测试 runtime 外网 0；未 deploy/push/install/production/final acceptance。

## ITER-20260716-PFI-V025-S11-P112

- Task / Acceptance：`S11-P2-T1..T4` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`；风险路由 `T2_SQLITE_BACKUP_RESTORE_ATOMIC_REPLACEMENT`，仅完成 Phase 11.2 candidate。
- 实现：SQLite Online Backup API 一致快照、只读 integrity/FK/migration/application invariant verifier、隔离 candidate、exact target SHA、same-filesystem atomic replace、fsync 与 verified automatic rollback；产品提交 `bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b`。
- scope override：同库 durable job writer 必须加入 maintenance lock；新增 module/CLI 必须加入 release identity closure。standing authorization 下最小扩展并保留 `allowed_files_obeyed=false`。
- 验证：focused/adjacent/release identity `82/82`；disposable concurrent online backup、successful restore、injected post-replace rollback 恢复原 application invariants 并匹配 rollback snapshot SHA；integrity/FK、TaskPack schema、完整 archive overlay governance/renderer、privacy/artifact hashes 通过。
- 结果：Phase 11.2=`candidate_pass`，Stage 11=`8/12 in_progress`，v0.2.5=`140/156 (89.74%)`；下一任务 `S11-P3-T1`，Phase 11.3 与 whole-stage review 未开始。
- 边界：未使用 Finder/LaunchServices/GUI；无 canonical private DB/财务值/model/formula/parameter 数值变更；研究层仅访问官方 SQLite/Python 文档，产品/测试 runtime 外部网络调用为 0；未 push/install/production/final acceptance。

## ITER-20260716-PFI-V025-S11-P111

- Task / Acceptance：`S11-P1-T1..T4` / `ACC-PFI-V025-STAGE11-WHOLE-REVIEW`；风险路由 `T2_SQLITE_RUNTIME_CONCURRENCY_MIGRATION`，仅完成 Phase 11.1 candidate。
- runtime：Python 3.12.13 / SQLite `3.50.4` / source id `4d8adfb30e...`；官方安全版本矩阵 gate 使当前显式 WAL 请求 fail closed，默认 `DELETE` journal。
- transaction：活跃 base/import/holding operational stores 统一 `FULL` synchronous、FK、30000ms busy timeout、`BEGIN/BEGIN IMMEDIATE` 与异常/commit 失败 rollback；Stage 10 job store 保持既有等价安全配置。
- migration：`pfi_operational_migrations` 绑定 version、SHA-256、UTC applied time 与 SQLite version；幂等 replay、checksum drift、失败全回滚和 transaction/database escape rejection 通过。
- 验证：主产品 `b07709d0453d3d2c6d36a10375d823dbb0870c53`、release identity 收口 `ad16901505f7e6f23653aa8b1e03945211dc4e93`；Stage 11 + Stage 7/10 相邻回归 + release identity `68/68`，disposable 四进程 `100/100` writes、实际 SIGKILL 未提交行 0、integrity/FK 与完整 archive overlay governance/renderer 通过。
- 结果：Phase 11.1=`candidate_pass`，Stage 11=`4/12 in_progress`，v0.2.5=`136/156 (87.18%)`；下一任务 `S11-P2-T1`，Phase 11.2/11.3 与 whole-stage review 未开始。
- 边界：TaskPack literal allowlist 缺 active application store，standing authorization 下只做该必要 override；未使用 Finder/LaunchServices/GUI，无 canonical private DB 或财务值；研究层仅访问 `sqlite.org` 官方文档，产品与测试 runtime 外部网络调用为 0；未 push/install，production/final acceptance=false。

## ITER-20260715-PFI-V025-S10-WHOLE-REVIEW

- Task / Acceptance：`STAGE10-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；风险路由 `T2_SCHEMA_CONCURRENCY_RECOVERY_PRIVACY_RELEASE_REVIEW`，只完成 Stage 10 整阶段审查、整改、复审与 transition acceptance。
- 初审/整改：`C1/I7/M0`；整改提交 `92579cfdd` 增加 supervisor persisted heartbeat/revision CAS、精确七态 UI、最新 job polling ownership，并补齐 TaskPack schema normalization、scope binding、failed DOM/AX、migration before/backup/after 与 Phase commit/artifact chain。
- 验证：正式无头 browser `22/22`，健康 >10 秒任务 `attempt=1/retry=0`、外部请求 0；明确 failed/retrying/dead_letter、真实 SIGKILL/restart、九域 diff/no-diff、trace privacy、release identity、完整 archive + frozen overlay governance/renderer 通过。
- 复审：三条隔离 deterministic final rereview=`C0/I0/M0`，不声称外部人工或 subagent reviewer。
- 结果：Stage 10=`accepted_for_transition`，standing transition acceptance=`accepted_via_standing_transition_authorization`；Stage 11 entry authorized 但 implementation=`not_started`，v0.2.5 保持 `132/156 (84.62%)`。
- 边界：仅 disposable SQLite/loopback；未使用 Finder/LaunchServices/GUI，无 canonical private DB、财务值、外网、push、install、production/final acceptance。下一任务 `S11-P1-T1`。

## ITER-20260715-PFI-V025-S10-P103

- Task / Acceptance：`S10-P3-T1..T4` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；风险路由 `T2_RUNTIME_OBSERVABILITY_RECOVERY_PRIVACY`，本轮只形成 Phase 10.3 candidate。
- observability：新增 trace/span/log migration；每个 revision 同一 trace、独立 span，日志记录 timing/error/impact/retry/cache fallback/hash dimensions，并在入库前脱敏、append-only/hash-chained。
- runtime/UI：supervisor 三项真实工作单位与 authenticated job API 接入正式 Shell；UI status/revision/trace/retry/error/result/progress 全部来自 SQLite，poll timer 不改变业务状态。
- failure matrix：offline succeeded；timeout explicit failed/cache fallback；unsafe network 在工作前 failed；restart 与真实 subprocess SIGKILL 恢复 checkpoint；浏览器离页 10,503ms 后恢复同一 job。
- 验证：Phase target `14/14`、最终产品合并 `121/121`；正式 browser/database/trace privacy pass，外部请求 0，SQLite integrity/FK pass、DELETE journal、WAL=false。
- 结果：Phase 10.3=`candidate_pass`，Stage 10 phase tasks=`12/12 candidate_complete`，v0.2.5=`132/156 (84.62%)`；whole-stage review/user acceptance 均 `not_started`。
- 边界：产品提交 `9d2a8eb9f7b3e91492cdabffa9965339cd3bba2e`；仅隔离 SQLite/loopback，未使用 Finder/LaunchServices/GUI、canonical 私有 DB、财务值、外网、push、install 或 production/final acceptance。下一任务 `STAGE10-WHOLE-REVIEW`。

## ITER-20260715-PFI-V025-S10-P102

- Task / Acceptance：`S10-P2-T1..T4` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；风险路由 `T2_RUNTIME_DEPENDENCY_CACHE_PRIVACY`，本轮只形成 Phase 10.2 candidate。
- registry/snapshot：固定九域 DAG、直接指标影响和缓存域；SQLite 使用只读 URI/query-only 计算非金额 hash 投影，tracked snapshot 仅含安全状态与 hash，interconnection 未完成时 fail closed。
- diff：实际 changed domains 与 downstream recompute closure 分离，指标只取 changed-domain 显式 map；九域逐一变化与 no-diff 行为均已执行，raw 变化不会全量误报。
- cache/frontend：dependency snapshot hash 进入既有 composite key；release CLI/runtime API/Streamlit/frontend 绑定同一 key，TTL=30、persist=false。active `version.js` 行为测试接受完整 policy、拒绝 network drift。
- 安全：no-diff 为 `recompute_scope=none` 且 network/Codex/LLM=0；未读 canonical 私有 DB、未输出财务值、未修改 model/formula/parameter 数值。
- 验证：Phase target `7/7`，Phase 10.1 + Stage 1 cache/release `45/45`，Stage 7 operational + Stage 9 report `40/40`；修复 AppTest `__main__` 测试隔离后最终合并 `85/85`，release frontend/backend identity 闭合。
- 结果：Phase 10.2=`candidate_pass`，Stage 10=`8/12 in_progress`，v0.2.5=`128/156 (82.05%)`；Phase 10.3 与 Stage 10 whole-stage review 均 `not_started`。
- 边界：产品提交 `a64f3b51576ebe507bd65b3f5b54c5b2a3b74c41`；未使用 Finder/LaunchServices/GUI。普通 dependency/cache 审计零网络；回归验证仅使用临时本机 loopback、无外网；未读取真实财务值，未 push、install 或 production/final acceptance。下一任务 `S10-P3-T1`。

## ITER-20260715-PFI-V025-S10-P101

- Task / Acceptance：`S10-P1-T1..T4` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；风险路由 `T2_SCHEMA_CONCURRENCY_RECOVERY`，本轮只形成 Phase 10.1 candidate。
- 实现：新增 versioned `durable_jobs` 与 append-only/hash-chained `durable_job_events`，覆盖 queued/running/retrying/succeeded/failed/cancelled/dead_letter、revision-CAS claim/lease/heartbeat、bounded retry/cancel/dead-letter、过期 lease recovery 与持久化 checkpoint。
- 并发/安全：`BEGIN IMMEDIATE` + revision/prior-status CAS 保证双 worker 单 winner；raw lease token 只返回一次且不落库，旧 revision、错误/过期 token 与取消后的 stale worker 全部 fail closed。
- 真实进度：progress 仅来自单调 `completed_units/total_units/step` 事件，heartbeat/timer 不计进度；财务结果保持 `pending_human_review`、`publishable=false`，不存在后台发布或交易能力。
- SQLite：当前 runtime=`3.50.4`，低于 Task Pack 的 WAL 安全 backport `3.50.7`，因此明确使用 `DELETE` journal、FULL synchronous、FK、30s busy timeout 与显式 rollback；仅创建并删除隔离测试库，未迁移真实 PFI DB。
- 验证：Phase target `7/7`、历史 Stage 10/SQLite 邻接 `19/19`、合并 `26/26`、release identity `10/10`、最终合并 `36/36`；7 jobs/20 events 七状态 probe、40-job/8-worker stress 与 heartbeat CAS race、integrity/FK/token/privacy、完整 checkout governance 和 renderer 均通过。
- 结果：Phase 10.1=`candidate_pass`，Stage 10=`4/12 in_progress`，v0.2.5=`124/156 (79.49%)`；Phase 10.2/10.3 与 Stage 10 whole-stage review 均 `not_started`。
- 边界：产品提交 `b97827f0b90f7e72de9fec64f88f702658a823bf`；未使用 Finder/LaunchServices/GUI，无外网、真实 DB/财务值、model/formula/parameter 值修改、push、install 或 production/final acceptance。下一任务 `S10-P2-T1`。

## ITER-20260715-PFI-V025-S9-WHOLE-REVIEW

- Task / Acceptance：`STAGE9-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；整阶段 gate 不增加 156 source-task count，风险路由 `T3_FINANCIAL_MODEL_REPORT_AND_HUMAN_DECISION_REVIEW`。
- 绑定：Phase 9.1/9.2/9.3 immutable evidence、产品整改 `a1178bef`、PDF/hash 修复 `66aaba48`、decision contract 修复 `e2a3908e`、deterministic export bytes 修复 `45653bd4`、精确 frozen worktree/evidence overlays、验证日志与三位独立 reviewer 结果。
- 整改：正式 renderer 绑定 immutable reviewed contract；localStorage 只保存严格 delta 并在 ledger validation 后发布。主报告/导出展示四个双消费组件与 activity != net-worth loss；补齐 model report、DOM/CDP AX、TaskPack normalization、一致 renderer、准确双 parser 运行时标签，以及 pack hash/UI contract/manifest metadata/export byte size/hash 的严格 fail-closed 验证。
- 模型/数据：5 reports=`3 blocked / 2 partial`；`FORM15/19` 有当前证据，`FORM16..18` blocked、`FORM20` structure-only、historical/OOS blocked；不改 model/formula/parameter 数值，不输出财务金额。
- 验证：formal Shell `16/16`；四格式下载/hash、物理 PDF、focused/upstream regression、Node/Python/diff、隐私、完整 archive + overlay governance/renderer 通过。
- 复审：code/security 初审与复审新增发现合计 `C0/I4/M0`、governance/renderer `C0/I4/M2`、acceptance/evidence `C2/I3/M1`；整改后同一 overlays 的最终复审为 `C0/I0/M0`。
- 结果：Stage 9=`accepted_for_transition`，用户过渡授权=`accepted_via_standing_transition_authorization`，Stage 10 entry authorized but `not_started`；整体进度保持 `120/156 (76.92%)`。
- 边界：未使用 Finder/LaunchServices/GUI；无外网、raw/DB 读写、自动交易、push、install、production/final acceptance。下一任务 `S10-P1-T1`。

## ITER-20260715-PFI-V025-S9-P93

- Task / Acceptance：`S9-P3-T1..T4` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；风险路由 `T3_FINANCIAL_DECISION_REVIEW_EXPORT`，只完成 Phase 9.3。
- 实现：新增 2 个不可自动交易的 decision objects、四种人工复核 outcome、反证/失效条件、SHA-256 chained events 与 HTML/PDF/CSV/Markdown 同源导出，并接入正式 Shell。
- 安全真相：accepted 只记录人工 review，不生成订单或交易；`automatic_trading_allowed=false`、`trade_execution_available=false`。
- 一致性：四格式绑定同一 snapshot 与 export manifest；source analysis pack、model/formula/parameter 值和 Phase 9.2 的 3 blocked / 2 partial 状态保持不变。
- 验证：Stage 9 target `25/25`、release identity `10/10`、selected upstream `68/68`、Node `3/3`、正式浏览器 `16/16`；物理 PDF 解析、栅格和目视通过。
- 当前结果：Phase 9.3 `candidate_pass`，Stage 9 phase tasks=`12/12 candidate_complete`，v0.2.5=`120/156 (76.92%)`；下一唯一任务 `STAGE9-WHOLE-REVIEW`。
- 边界：Stage 9 whole-stage review/user acceptance、Stage 10、push/install/production/final acceptance 未执行；未使用 Finder/LaunchServices/GUI，未读写数据库/真实财务行，未修改 model/formula/parameter 值。

## ITER-20260715-PFI-V025-S9-P92

- Task / Acceptance：`S9-P2-T1..T4` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；风险路由 `T3_FINANCIAL_MODEL_VALIDATION_UI`，只完成 Phase 9.2。
- 实现：新增 5 份 source-bound report、6 条 formula drilldown、4 组 sensitivity preview、1 张 limitation/counter-evidence model card、7 个来源复核入口，并接入正式 Shell。
- 当前真相：net worth/cash/investment blocked；consumption/cashflow partial coverage。公开 Evidence 不含金额，历史/OOS 缺 ground truth 继续 blocked。
- 一致性：分析包绑定 Phase 9.1 base manifest 与同一 data/read-model/formula/parameter hashes；产品提交 `7566107d` 后 accepted input hashes 不变，任一状态/pack 篡改 fail closed。
- 验证：Phase target `10/10`、Stage 9 schema/release `27/27`、selected upstream `68/68`、Node contracts pass、正式浏览器 `11/11`，外网请求 0。
- 当前结果：Phase 9.2 `candidate_pass`，Stage 9=`8/12 in_progress`，v0.2.5=`116/156 (74.36%)`；下一唯一任务 `S9-P3-T1`。
- 边界：Phase 9.3、Stage 9 whole-stage review、push/install/production/final acceptance 未执行；未使用 Finder/LaunchServices/GUI，未读写数据库/真实财务行，未修改 model/formula/parameter 值。

## ITER-20260715-PFI-V025-S9-P91

- Task / Acceptance：`S9-P1-T1..T4` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；风险路由 `T2`，仅完成 Phase 9.1。
- 实现：新增 strict report schema、六类报告 manifest、`complete/partial/blocked` fail-closed 判定、数据质量与缺口报告；blocked 报告禁止确定性财务结论。
- 当前真相：来源 `1 ready / 1 partial / 5 not_loaded`，8,815 source records、1,571 operational events、11 metrics；报告状态 `1 complete / 2 partial / 3 blocked`，金融值输出 0。
- 一致性：六类报告共享 data/read-model/formula/parameter hash；formula/parameter 当前文件与已接受 Stage 7 evidence 一致，未修改 model/formula/parameter 值。
- 验证：Phase 9.1 schema/status/hash/tamper tests、Stage 4/5/7/8 regression、JSON/Python/diff、完整 checkout changed-scope governance 与 renderer；证据 fail-closed 且隐私扫描 0 命中。
- 当前结果：Phase 9.1 `candidate_pass`，Stage 9=`4/12 in_progress`，v0.2.5=`112/156 (71.79%)`；下一唯一任务 `S9-P2-T1`。
- 边界：Phase 9.2/9.3、Stage 9 whole-stage review、push/install/production/final acceptance 未执行；未使用 Finder/LaunchServices/GUI、外网或数据库/真实财务行读取与写入。

## ITER-20260715-PFI-V025-S8-WHOLE-REVIEW

- Task / Acceptance：`STAGE8-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`；整阶段 gate 不增加 156 source-task count。
- 绑定：Phase 8.1/8.2/8.3 三笔 immutable commits 与全部历史 artifact hashes、产品整改提交 `2c7b25e`、精确 frozen overlay、真实 verification logs 和三个独立 reviewer result text/hash。
- 整改：关闭 expected-archetype 自证与 title-only clone、180ms timer 假成功、持仓删除缺确认、24px link、timeline 任意标签持久化、旧 Phase 截图与重复 secondary route、证据/schema/release/governance 漂移。
- 浏览器：当前内容 10 核心 + 10 不同二级路由 × desktop/mobile=`40/40 PNG`；20 唯一路由、3646 文本样本，WCAG/contrast/target/name/duplicate/structure failures 全 0，键盘/CDP AX/错误预防/reduced-motion 通过。
- axe：`axe_core_available=false`、`axe_pass_claimed=false`，不伪造结果；`axe_results.json` 以 `not_run` 绑定 deterministic WCAG 2.2 AA 与 Chrome CDP AX substitute。
- Release：产品内容提交=`2c7b25e`，frontend=`0e3da07efc9b569b00e4182d445da1d12cd2cee0e505fd7f913fb74016dd01ca`、backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`。
- 复审：初审 code/security `C1/I4/M1`、governance/renderer `C0/I8/M0`、acceptance/evidence `C3/I2/M1`；整改后同一 overlay 的最终复审为 `C0/I0/M0`。
- 结果：Stage 8=`accepted_for_transition`，用户过渡授权=`accepted_via_standing_transition_authorization`，Stage 9 entry authorized but `not_started`；整体进度保持 `108/156 (69.23%)`。
- 边界：当前整阶段未使用 Finder/LaunchServices/GUI；历史 Phase 8.3 的一次意外 `lsregister -dump` 如实记录并当时立即中止。无财务数据/DB/模型/公式/参数值变更，无外网、push、install 或 production/final acceptance。下一任务 `S9-P1-T1`。

## ITER-20260715-PFI-V025-S8-P83

- Task / Acceptance：`S8-P3-T1..T4` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`；本轮只形成 Phase candidate。
- RED/GREEN：初始 `8/8` expected failures；实现后专项、浏览器、release 与治理门禁通过。
- 实现：route announcer、keyboard route focus、3px visible focus、44px target、forced-colors、live region 与 5 个财务/数据错误预防绑定。
- WCAG：10 核心 + 10 重点二级路由、3776 文本样本，blocking/contrast/target/unnamed/duplicate/structure failures 全部 0；axe-core 不可用事实显式记录。
- 键盘/AX：skip link、一级/二级 route、Ctrl+K、30-Tab no-trap、801-node CDP AX 汇总均通过；unnamed interactive/duplicate IDs=0/0。
- 视觉/隐私：20/20 PNG 回归通过，最大 diff `0.078533 <= 0.12`；sanitized trace 与 loopback-only browser 无私有值或外部请求。
- Release：frontend=`f130b7a3f2bf249151e08daa321d4a5c67130340069f1653946753fb1c62afa3`、backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`；20 canonical frontend sources。
- 当前结果：Phase 8.3 `candidate_pass`，Stage 8 phase tasks=`12/12 candidate_complete`，v0.2.5=`108/156 (69.23%)`；下一唯一任务 `STAGE8-WHOLE-REVIEW`。
- 边界：该 Phase 当时整阶段审查/user acceptance 与 Stage 9 未开始；未使用 Finder/GUI 文件操作，但收口回归曾意外启动一次 `lsregister -dump` 并立即中止。无财务数据、数据库、模型、公式或参数变更，无外网、push、install、production/final acceptance。

## ITER-20260715-PFI-V025-S8-P82

- Task / Acceptance：`S8-P2-T1..T4` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`；Acceptance ID 为项目治理分配。
- RED/GREEN：初始 Phase 8.2 `7/7` 失败；实现与证据封装后专项 `7/7 pass`。
- 实现：100/300/1000/10000ms 反馈预算、220ms transform/opacity 动效上限、View Transition 渐进增强、reduced-motion 0ms、haptics/sound opt-in 与 durable job timeline。
- 真实性：时间只改变反馈阶段与 durable 状态；progress value 必须来自 completedUnits/totalUnits，未提供真实工作量时保持 null。
- 浏览器：actual formal Shell `17/17`；11 秒 durable 跨 route 保留，supported opt-in 与 unsupported visual_only 均通过；console/page/HTTP/external errors=0。
- official candidate：canonical frontend sources `19/19`；release/whole-review/Stage 7 focused compatibility `56/56`。
- Release：frontend=`33ef94e054dfc45bda699a5c44dee209868816eb27e107c3b73a3dae80e7be98`，backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`；version/build/formula/parameter version 不变。
- 当前结果：Phase 8.2 `candidate_pass`，Stage 8=`8/12 in_progress`，v0.2.5=`104/156 (66.67%)`；下一唯一任务 `S8-P3-T1`。
- 边界：未使用 Finder/LaunchServices/GUI 文件操作；无财务数据、数据库、模型、公式或参数变更，无外网、push、install、production/final acceptance；Phase 8.3 与 whole-stage review 未开始。

## ITER-20260715-PFI-V025-S8-P81

- Task / Acceptance：`S8-P1-T1..T4` / `ACC-PFI-V025-STAGE8-WHOLE-REVIEW`；Acceptance ID 为项目治理分配。
- RED：初始 5 个设计系统测试全部失败；实现收敛后聚焦 contract `5/5 pass`。
- 实现：显式默认亮色 token、10 种 canonical-workspace archetype、accessible empty/error/stale/ready 图表状态，以及 desktop/compact/mobile/compact-mobile 正式布局。
- 真实浏览器：强制 OS dark 的 current-worktree formal Shell 10 routes × desktop/mobile=`20/20`；console/page/HTTP/external errors=0，无横向溢出或设备样机。
- 视觉证据：10 desktop + 10 mobile PNG 全部直接 RGB decode；black-pixel files=0；sanitized Playwright trace 仅保留 3 entries，不含私有值、runtime token 或绝对本地路径。
- Release：frontend hash 更新为 `50e715a6b2e5c5162b32592c15d1661cba430ead3c2ed7a0a36d4634e38333f4`；backend/version/build id 不变。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；财务数据未读取/修改，数据库未改变。
- 当前结果：Phase 8.1 `candidate_pass`，Stage 8=`4/12 in_progress`，v0.2.5=`100/156 (64.10%)`；下一唯一任务 `S8-P2-T1`。
- 边界：未使用 Finder/LaunchServices/GUI 文件操作；无外网、push、install、production acceptance 或 final human acceptance；Phase 8.2/8.3 和 whole-stage review 未开始。

## ITER-20260715-PFI-V025-S7-WHOLE-REVIEW

- Task / Acceptance：`STAGE7-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE7-WHOLE-REVIEW`；整阶段 gate 不增加 156 source-task count。
- 绑定：Phase 7.1/7.2/7.3 三笔 immutable commits、12/12 tasks、当前 worktree overlay、真实 verification logs 与三个独立 reviewer result text/hash。
- 整改：API auth/Host/Origin/CORS/size、XSS/CSV/ZIP/input、幂等/CAS/跨批 ledger ownership、SQLite migration lock/canonical backup、raw cleanup/TOCTOU、canonical read model 与 trace privacy。
- 财务真相：缺 economic-event adapter 时 operational lineage 和 11 metrics 全部 blocked/null；immutable Phase 7.3 历史 candidate 聚合不得冒充当前 runtime truth。
- 复审：初始 `C0/I14/M4`；整改后 code/security、governance/renderer、acceptance/evidence 均要求 `C0/I0/M0`。
- 验证：三条正式 Shell 工作流目标 68/68；最终 Python/Node/diff、complete-root PFI governance、renderer 与 artifact hashes 由 whole-review evidence content-bind。
- 当前结果：Stage 7 `accepted_for_transition`；Stage 8 entry authorized but `not_started`。下一唯一任务 `S8-P1-T1`。
- 边界：未使用 Finder/LaunchServices/GUI 文件操作；无外网、push、install、production acceptance 或 final human acceptance。

## ITER-20260715-PFI-V025-S7-P73

- Task / Acceptance：`S7-P3-T1..T4` / `ACC-PFI-V025-S7-P73-METRIC-DRILLDOWN`；Acceptance ID 为项目治理分配。
- 实现：正式只读参数中心、可点击 Interconnection Map、11 指标到 range/formula/parameter/data/read-model/source/economic-event lineage；三条 canonical route 不使用 sidecar HTML。
- 当前 lineage：8,815 source records、6,879 complete、1,936 review、0 missing、0 silent drop；同一 economic event 每 metric 最多计入 1 次。
- Fail-closed：not-ready 指标 `value=null`，false-zero=0；tracked evidence 只保留 aggregate/hash/status，`financial_values_persisted=0`。
- 浏览器：actual formal Shell 21/21；深链 reload、query state、ready/blocked 指标均通过；无 console/page/HTTP/external-network errors。
- 回归：Phase focused `5 passed`；Stage 6 active-route compatibility + release/Stage 7 combined Python `44 passed`；Node identity/cache/Phase `29 passed`；JS syntax pass。
- 隐私：raw trace 未保留；sanitized trace 替换 472 value fields、2 absolute paths、3 CNY text，复扫命中 0；截图已纯工具目视检查。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；展示现有 `10/20/92` registry facts，不修改定义、表达式或参数值。
- 当前结果：Phase 7.3 `candidate_pass`，Stage 7 phase tasks=`12/12 candidate_complete`，v0.2.5=`96/156 (61.54%)`；下一唯一任务 `STAGE7-WHOLE-REVIEW`。
- 边界：Stage 7 仍 `in_progress`；未使用 Finder、无外网、无 DB/源数据写入、未 push/install，未进入 Stage 8。

## ITER-20260715-PFI-V025-S7-P72

- Task / Acceptance：`S7-P2-T1..T4` / `ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS`；Acceptance ID 为项目治理分配。
- RED：初始测试因 `holding_settings_persistence` 模块不存在而 collection error；实现后聚焦 `6 passed`。
- 实现：revisioned holding create/update/delete→单一 SQLite change-set→fail-closed projection；settings save/reset 只走正式 API/SQLite。
- 浏览器：actual formal Shell 首轮 13/13；关闭 browser context、重启 Runtime API 到新端口后重开 12/12；无 console/page/HTTP/external-network errors。
- 回归：current-HEAD release/Stage 6/Phase 7.1/7.2 Python `66 passed`；Stage 1 Node identity/cache `28 passed`；JS syntax pass。
- 数据库：重启前 holding revision=2/settings revision=1；最终 delete revision=3/settings reset revision=2；FK pass、integrity ok、migration=1。
- 财务边界：当前无真实持仓/价格/FX；contract sentinel 不计入真实验收，金额全为 null，`financial_values_emitted=0`。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 当前结果：Phase 7.2 `candidate_pass`，Stage 7=`8/12 in_progress`，v0.2.5=`92/156 (58.97%)`；下一唯一任务 `S7-P3-T1..T4`。
- 边界：未使用 Finder、无外网、未 push/install；Phase 7.3 与 Stage 7 whole-stage review 未开始。

## ITER-20260715-PFI-V025-S7-P71

- Task / Acceptance：`S7-P1-T1..T4` / `ACC-PFI-V025-S7-P71-IMPORT-REVIEW-LEDGER`；Acceptance ID 为项目治理分配。
- RED：初始测试因 `pfi_os.application.use_cases` 不存在而 collection error；实现后聚焦 `6 passed`。
- 实现：real byte upload→preview staging→atomic confirm→SQLite ledger/review queue；review save/undo、duplicate idempotency、rollback/retry/reconfirm 全部走 runtime API。
- 浏览器：actual formal Shell + cached Playwright/local Chrome 20/20；无 console/page/HTTP/external-network errors。
- 真实数据边界：只读源复制到 `/tmp`；1571 transactions、74 reviews；canonical SHA-256 不变，公开 evidence 不含私有值。
- 回归：release/Stage 6 Python `60 passed`，Node identity/cache `28 passed`，SQLite FK/integrity pass。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 当前结果：Phase 7.1 `candidate_pass`，Stage 7=`4/12 in_progress`，v0.2.5=`88/156 (56.41%)`；下一唯一任务 `S7-P2-T1..T4`。
- 边界：未使用 Finder、无外网、未 push/install；Phase 7.2/7.3 与 Stage 7 whole-stage review 未开始。

## ITER-20260715-PFI-V025-S6-WHOLE-REVIEW

- Task / Acceptance：`S6-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE6-WHOLE-REVIEW`；整阶段 gate 不增加 156 source-task count。
- 初审/整改：`C0/I4/M1`；补齐 whole-stage/commit binding、当前 HEAD formal-shell browser 联审、三份 Task Pack evidence schema、final index/human acceptance hash binding 与 legacy test disposition。
- 复审：`C0/I0/M0`；当前 HEAD Playwright 14/14，10 主入口、10 个代表二级页、7 aliases、History/Reload/Invalid/keyboard/AX/no-JS 全通过。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 边界：未使用 Finder、未访问外部网络、未读写真实财务数据或数据库、未 push/install、未开始 Stage 7；production/final human acceptance=false。
- 当前结果：Stage 6 `accepted_for_transition`；Stage 7 entry authorized but not_started。下一唯一任务 Stage 7 Phase 7.1 `S7-P1-T1..T4`。

product_version: v0.2.5
model_count: 10
formula_count: 20
parameter_count: 92
task_count: 10
acceptance_count: 10

## ITER-20260715-PFI-V025-S6-P63

- Task / Acceptance：`S6-P3-T1..T4` / `ACC-PFI-V025-S6-P63-HISTORY-ACCEPTANCE`；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 Phase ACC-*。
- RED：focused test 初始 4 项因缺 Phase 6.3 history contract、runtime、browser/AX harness 与 hash redirect classification 失败；实现后 `4 passed`。
- S6-P3-T1：正式 HTTP Shell 使用 actual pathname；history entry 保存 route/workspace/scroll/source，popstate 以 URL 为事实源恢复页面、焦点与 scroll。
- S6-P3-T2：缓存 Playwright actual Chrome 验证 back/forward、CDP reload、深链、重复点击 history delta=0、无效 route 与恢复；console/page/http errors=0。
- S6-P3-T3：`Accessibility.getFullAXTree` 的“一级工作区”子树为 10 个命名、唯一、可聚焦入口；键盘 Enter 进入 `/ledger` 后 page heading 获得焦点。
- S6-P3-T4：Phase candidate Evidence 完整；Stage 6 phase tasks=`12/12 candidate_complete`，whole-stage review/user acceptance 仍未开始。
- 版本身份：frontend source hash=`aa8c62370292f5aa7ff0ae6743282e8c715f76949369c9369cd870e5c2dc1669`；backend hash 不变；version/build/git-commit 语义未改变。
- 非门禁诊断：4 条旧 v0.2.4/v0.2.1 测试继续要求 `/home`、旧 query route 与旧版本 UI label，属于 Phase 6.1 已明确替代的 superseded expectations，不回退 v0.2.5 canonical contract。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 边界：未使用 Finder、无外部网络、未读写数据库或真实财务数据、未 push/install、未开始 Stage 6 whole review 或 Stage 7。
- 当前结果：Phase 6.3 `candidate_pass`，v0.2.5=`84/156 (53.85%)`；下一唯一任务 `S6-WHOLE-REVIEW`。回滚只 revert 本 Phase 本地提交。

## ITER-20260715-PFI-V025-S6-P62

- Task / Acceptance：`S6-P2-T1..T4` / `ACC-PFI-V025-S6-P62-PAGE-CONTRACTS`；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 Phase ACC-*。
- RED：focused test 初始 4 项分别因缺页面合同、45-route registry、Shell navigation behavior 与 no-JS 页面失败；实现后 `4 passed`。
- S6-P2-T1/T2：10 个一级工作区下 45 个二级页全部使用 path canonical route；每页具有独立 job-to-be-done、data object、primary action、layout/signature 与 loading/empty/error 状态。
- S6-P2-T3：formal Shell 同步 document title、breadcrumb 与 page-heading focus；route 切换保存并恢复独立 scroll position。
- S6-P2-T4：45 个历史 query route 只归一到 canonical path；desktop/mobile 深链非空，no-JS 目录包含 10 个一级入口和 45 个可读二级页。
- 浏览器：desktop/mobile 各验证 10 个工作区代表页、URL/state、title/focus、结构差异、scroll restoration 与 release identity；no-JS 隔离 profile 通过，截图均人工复核。
- 版本身份：frontend source hash=`70cbc136567db2c3f4ec57001294cdc59c1ac317d3c006d0215d79961886b6d1`；backend hash 不变；version/build/git-commit 语义未改变。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 边界：未使用 Finder、未访问外部网络、未读写数据库或真实财务数据、未 push、未安装 App、未开始 Phase 6.3 或 Stage 6 whole-stage review。
- 当前结果：Phase 6.2 `candidate_pass`，Stage 6=`8/12 in_progress`，v0.2.5=`80/156 (51.28%)`；下一唯一任务 `S6-P3-T1..T4`。回滚只 revert 本 Phase 本地提交。

## ITER-20260715-PFI-V025-S6-P61

- Task / Acceptance：`S6-P1-T1..T4` / `ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS`；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 Phase ACC-*。
- RED：新测试先因 `pfi_v02.stage_v025_navigation` 缺失产生预期 collection error；实现后 Phase 6.1 聚焦合同 `5 passed`。
- S6-P1-T1/T2：一级入口固定为总览、账户、账本、投资、消费、数据、复核、报告、市场与研究、设置，顺序和 canonical route 与 Roadmap Appendix A 一致。
- S6-P1-T3：`/home`、`/market`、`/research`、`/holdings`、`/strategy-lab`、`/investment/strategy-lab`、`/data-system` 只归一到 canonical route；alias 不进入一级导航、a11y 或 no-JS fallback，策略实验室唯一 canonical route 为 `/market-research/strategy-lab`。
- S6-P1-T4：desktop/mobile 共用同一 10 节点 DOM，移除第二套 bottom-nav primary stack；真实隔离 Chrome 在 desktop/mobile 各完成 10 个点击、alias normalization、单 active 状态和 release identity ready 验证。
- 版本身份：前端 source hash 更新为 `37a74d635cac8e0640b8dce357a0698c56a8a5b157517ec5f19c54208ab74d65`，后端 source hash 同步到既有 Stage 5 实际值 `43b918f761e80bbc4c6e2de54a32c714703cc4d9a60f67b7a180e1cea222ddbb`；version/build/git-commit 语义未改变。
- 诊断：旧 v0.2.3/v0.2.4 route tests 有 `16 passed, 11 failed`，11 项均要求本 Phase 已明确取代的 `/home`、`/sources-upload`、旧 alias、旧版本标记或双 DOM；作为 superseded non-gate 记录，不回退 v0.2.5 合同。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 边界：未使用 Finder、未访问外部网络、未读写数据库或真实财务数据、未 push、未安装 App、未开始 Phase 6.2/6.3 或 Stage 6 whole-stage review。
- 当前结果：Phase 6.1 `candidate_pass`，Stage 6=`4/12 in_progress`，v0.2.5=`76/156 (48.72%)`；下一唯一任务 `S6-P2-T1..T4`。回滚只 revert 本 Phase 本地提交。

## ITER-20260715-PFI-V025-S5-WHOLE-REVIEW

- Task / Acceptance：`S5-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`；整阶段 review gate 不增加 156-source-task count。
- 初审：`C1/I4/M1`。Critical 为真实四指标未绑定 formal homepage/consumption/report；其余为 phase commit binding、browser/a11y、隐私证据分层、schema acceptance 与 Allowed Files 冲突记录缺失。
- 整改：新增私有运行时四指标 payload、read-model/formal shell 挂链和隔离 headless browser harness；真实数值在内存确认后，截图/DOM/trace/a11y 全部改为 `CNY 已脱敏`。
- 浏览器复核：三页 release identity=`ready`、冲突层隐藏、app shell 可见、四指标 label/value 均可见；只使用 ephemeral local loopback，无外部网络。
- 复审：`C0/I0/M0`；Pass Gate=`pass_with_explicit_blocked_models`。`FORM-PFI-016/017/018/020` 的缺来源/chain/ground truth/OOS 残余继续 blocked。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `10/20/92`。
- 边界：未使用 Finder、未写真实来源或数据库、未 push、未安装 App、未开始 Stage 6；production/final human acceptance=false。
- 当前结果：Stage 5 `accepted_for_transition`，Stage 6 entry authorized；下一唯一任务 `S6-P1-T1..T4`。回滚只 revert 本 review 本地提交。

## ITER-20260715-PFI-V025-S5-P53

- Task / Acceptance：`S5-P3-T1..T4` / `ACC-PFI-V025-S5-P53-MODEL-VALIDATION`；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 Phase ACC-*。
- RED：新测试先因 `pfi_os.application.metrics.model_validation` 缺失产生预期 collection error；实现后 8 项 Phase 5.3 测试转绿。
- S5-P3-T1：只读重放 immutable Git blob；真实分区为 `8,815 = 6,879 published + 1,936 review + 0 silent drop`，双口径和七窗口 invariants 通过，源对象前后 identity 不变。
- S5-P3-T2：permutation、exact duplicate、positive scaling、date translation/window metamorphic checks 通过；七窗口真实计数为 `80/192/258/468/729/1418/3235`，空窗边界返回 filtered_empty/null。
- S5-P3-T3：形成六公式 model validation card；`FORM-PFI-015/019` real-snapshot validated，`FORM-PFI-016/017/018` 因缺真实依赖 fail closed，`FORM-PFI-020` 仅 structure-only；classification accuracy 与 OOS 因缺 ground truth/coverage blocked。
- S5-P3-T4：homepage、consumption_page、report 三个 consumer contract 表面 payload hash 一致；真实 UI/report renderer binding 未完成并显式保留为 Stage 5 whole-stage review open item，不伪造页面级验收。
- 数据/隐私边界：真实 Git 对象只读、数据库未读取/修改、公开证据不含金额或私有行；未使用 Finder、network、push 或 App install。`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`。
- 当前结果：Phase 5.3 `candidate_pass`，Stage 5 phase tasks `12/12 candidate_complete`；Stage 5 whole-stage review 尚未开始，production/final human acceptance=false。当前 v0.2.5 进度 `72/156 = 46.15%`。
- 下一唯一任务：`S5-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`；必须独立执行初审→整改→复审→明确验收，不得进入 Stage 6。回滚只 revert 本 Phase 本地提交。

## ITER-20260715-PFI-V025-S5-P52

- Task / Acceptance：`S5-P2-T1..T4` / `ACC-PFI-V025-S5-P52-FINANCIAL-MODELS`；Acceptance ID 为项目治理分配，Roadmap/Task Pack 未提供 Phase ACC-*。
- RED：两个新测试先因 `pfi_os.application.metrics.financial_models` 缺失产生预期 collection error；实现后 Phase 5.1+5.2 聚焦目标转绿。
- S5-P2-T1：按 source record 与标准化 economic event/type 去重，显式退款关联，输出 gross/living/funding/allocation 四口径且 reconciliation difference=0；投资活动不冒充净资产损失。
- S5-P2-T2：净资产、现金、余额滚动 exact Decimal invariant；依赖不完整或 discrepancy 非零时 fail closed/null，不发布假零。
- S5-P2-T3：登记 realized/unrealized/total return、成本、fee/tax/FX/idle-cash drag 与 date-aware XIRR；零分母、multiple-root、unbracketed/non-convergent 均阻断。
- S5-P2-T4：固定 `7/21/30/60/90/180/360` 七窗口，内部转账独立；复用 L1/L2、单 primary category、default/custom tag、历史和 all/any view contract。
- 模型登记：新增 `MOD-PFI-010`、`FORM-PFI-015..020`、`PARAM-PFI-081..092`；总数 `10/20/92`，五载体参数一致性纳入测试。
- 数据边界：只执行 deterministic contract values；未读取/修改真实财务行或数据库，未修改 Web/UI/报告源；Finder/network/push/install 均未执行。
- 当前结果：Phase 5.2 `candidate_pass`，Stage 5 为 `8/12 in_progress`；真实 invariant/metamorphic/sensitivity/model validation 和真实 UI/report binding 均留给 Phase 5.3。
- 下一唯一任务：`S5-P3-T1..T4`；不得进入 Stage 5 whole-stage review。回滚只 revert 本 Phase 本地提交，不重写历史公式或 Stage 4 read model。

## ITER-20260715-PFI-V025-S5-P51

- Task / Acceptance：`S5-P1-T1..T4` / `ACC-PFI-V025-STAGE5-WHOLE-REVIEW`，只形成 Phase 5.1 candidate evidence。
- RED：目标测试先因 `pfi_os.application.metrics` 缺失产生预期 collection error；实现与五载体 render 后 `6 passed`。
- S5-P1-T1：`FORM-PFI-001..014` 均有完整 machine-readable definition/version/hash/lifecycle；14/14 hash 可重建，active 同版本禁止原地改写。
- S5-P1-T2：formula JSON、parameter YAML、Python、UI payload、模型参数文件五载体 `conflict_count=0`。
- S5-P1-T3：CNY identity 与 AUD_TO_CNY exact Decimal multiplication 通过；倒置方向、错误单位、float、零/负 rate fail closed；4.81 仅示例且 production default=null。
- S5-P1-T4：保留记录分类 30/10/20/15/15/10、阈值 70、不按 source 分层；其余五维独立，overall score 被拒绝。
- 回归：Phase 5.1 + Stage 4 合并 `52 passed`；Stage 4 独立 `46 passed`。旧 v0.2.2 参数展示测试要求基线已不含的手工 alias，作为既有不兼容证据保留，未越界修改。
- 模型登记：新增 `MOD-PFI-009`、`FORM-PFI-014`、`PARAM-PFI-073..080`；总数 `9/14/80`。
- 数据边界：未读取/修改真实财务行或数据库；Finder/network/push/install 均未执行。
- 当前结果：Phase 5.1 `candidate_pass`，Stage 5 为 `4/12 in_progress`；下一唯一任务 `S5-P2-T1`，不得进入 Phase 5.3。
- 回滚：只 revert 本 Phase 本地提交；历史公式与 Stage 4 read model 不重写。

## ITER-20260714-PFI-V025-S4-WHOLE-REVIEW

- Task / Acceptance：`STAGE4-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE4-WHOLE-REVIEW`。
- 初审：`C0/I5/M1`，覆盖 commit/evidence 绑定、12/12 与 6/6/4/4 汇总、browser/a11y、human acceptance、README/HANDOFF current truth 与 canonical closure。
- 整改与复审：新增只读 verifier、最终索引、metric disposition、schema-valid acceptance 和本地 Chrome headless screenshot/trace/a11y；复审 `C0/I0/M0`。
- 精确结果：七个核心 metric 全部 `not_loaded/null`，confirmed_zero=0，false-zero=0，五个表面同 hash；生产余额/持仓/估值仍未就绪。
- 数据边界：未读取/修改真实财务行或数据库；未使用 Finder、network、push 或 App install。
- 当前结果：Stage 4 `accepted_for_transition`；Stage 5 entry authorized 但未开始，下一唯一任务 `S5-P1-T1`。
- 模型登记：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；总数保持 `8/13/72`。
- 回滚：仅 revert 本 review commit 并恢复 Stage 4 `in_progress`；保留三个 Phase evidence。

## ITER-20260714-PFI-V025-S4-P43

- Task / Acceptance：`S4-P3-T1..T4` / `ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY`。
- 目标：完成 Stage 4 Phase 4.3 strict Metric State、dependency/read-model hash、五表面同源与 phase evidence；停止在整阶段审查前。
- RED：新测试因 `pfi_os.application.read_models.metric_state` 缺失产生预期 collection error；实现后 19 个聚焦合同测试转绿。
- S4-P3-T1：13 状态完整登记；非 ready 只允许 null，ready 零被拒绝，confirmed_zero 需要完整 source/coverage/as_of/hash 证据。
- S4-P3-T2：Stage 2 manifest、Stage 3 event、Stage 4 account/investment 与 formula/parameter contract 共同生成 deterministic sha256 identity；page 和 observed_at 被排除。
- S4-P3-T3：homepage/accounts/investment/consumption/report 绑定同一七指标 snapshot 和 read_model_hash；runtime 与 browser contract 一致。
- S4-P3-T4：七个指标全部 not_loaded/null，financial values=0；Phase candidate evidence 完成，但 Stage whole review evidence 保持空白。
- 模型登记：新增 `MOD-PFI-008`、`FORM-PFI-011..013`、`PARAM-PFI-068..072`；消费双口径金融计算仍属于 Stage 5。
- 数据边界：未读取或修改真实财务行/数据库；Finder/network/push/install 均未执行。
- 当前结果：Phase 4.3 `candidate_pass`，Stage 4 phase tasks `12/12 candidate_complete`；下一唯一任务 `S4-WHOLE-REVIEW`，Stage 5 未开始。
- 回滚：只 revert 本 Phase 本地提交；统一 read model 与页面 payload 均可由 tracked aggregate evidence 重建。

## ITER-20260714-PFI-V025-S4-P42

- Task / Acceptance：`S4-P2-T1..T4` / `ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION`。
- 目标：完成 Stage 4 Phase 4.2 持仓、显式成本、价格/FX PIT 估值与投资 read model；停止在 Phase 4.3 前。
- RED：新测试因 `pfi_os.application.read_models.investment` 缺失产生预期 collection error；实现后聚焦合同与 tracked evidence 转绿。
- S4-P2-T1：持仓数量只接受 `SRC-HOLDINGS` snapshot lineage；linked 模式要求显式 economic-event ids，交易存在不构成持仓证明。
- S4-P2-T2：成本基础为 acquisition cost 加显式 capitalized fees；method 必须注册且显式，production source 未加载时 method/value 均保持 null。
- S4-P2-T3：quantity/price/FX snapshot 均不得晚于 valuation time；非 CNY 方向严格为 `BASE_TO_CNY`，CNY 恒等汇率 1；无权威 freshness 阈值时不虚构参数。
- S4-P2-T4：3/3 required sources not_loaded；投资市值、成本基础、未实现损益全部非 ready/null，共用一个 deterministic read_model_hash。
- 模型登记：新增 `MOD-PFI-007`、`FORM-PFI-009..010`、`PARAM-PFI-061..067`；contract unit values 不构成 financial fixture 或 production acceptance。
- 数据边界：未读取或修改真实财务行/数据库；Finder/network/push/install 均未执行。
- 当前结果：Phase 4.2 `candidate_pass`，Stage 4 `in_progress`，下一唯一任务 `S4-P3-T1`；Phase 4.3 与 whole-stage review 未开始。
- 回滚：只 revert 本 Phase 本地提交；read model 可重建，不需要真实数据、数据库、App 或远端回滚。

## ITER-20260714-PFI-V025-S4-P41

- Task / Acceptance：`S4-P1-T1..T4` / `ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT`。
- 目标：完成 Stage 4 Phase 4.1 账户/余额/负债快照、现金对账、coverage/status 与账户/首页同源 API；停止在 Phase 4.2 前。
- RED：两个测试模块因 `pfi_os.application.read_models` 缺失产生 2 个预期 collection errors；随后核心合同与 tracked evidence 转绿。
- S4-P1-T1：Draft 2020-12 schema 与 typed domain 强制 Decimal 金额、opening/closing、coverage、as_of、source record count 和 sha256 lineage。
- S4-P1-T2：现金公式精确对账；完整合同数值可计算，差异 `-0.01` fail closed；当前真实余额源 not_loaded，因此不运行财务计算。
- S4-P1-T3：2/2 required sources not_loaded；3/3 account metrics 非 ready、value=null、blocking reason 可定位，交易 source ready 不等于余额证明。
- S4-P1-T4：homepage/accounts 绑定相同 metrics 与同一 read_model_hash；五页面整体一致性留在 Phase 4.3。
- 模型登记：新增 `MOD-PFI-006`、`FORM-PFI-008`、`PARAM-PFI-058..060`；contract unit values 不构成 financial fixture 或 production acceptance。
- 数据边界：未读取或修改真实财务行/数据库；Finder/network/push/install 均未执行。
- 当前结果：Phase 4.1 `candidate_pass`，Stage 4 `in_progress`，下一唯一任务 `S4-P2-T1`；Phase 4.2/4.3 与 whole-stage review 未开始。
- 回滚：只 revert 本 Phase 本地提交；read model 可重建，不需要真实数据、数据库、App 或远端回滚。

## ITER-20260714-PFI-V025-S3-P33

- Task / Acceptance：`S3-P3-T1..T4` / `ACC-PFI-V025-S3-P33-RECONCILIATION`。
- 目标：完成 Stage 3 Phase 3.3 真实只读副本的重复导入、对账差异、Interconnection Matrix 与 read-model 去重证据；停止在整阶段审查前。
- RED：两个新测试因 `pfi_os.application.stage3_reconciliation` 缺失按预期 collection 失败；实现后非产物合同 `8 passed`。
- S3-P3-T1：immutable Git object 的 8,815 条记录第一次发布 6,879、第二次发布 0、识别重复 6,879、collision 0，source identity 前后不变。
- S3-P3-T2：6,879 发布 + 1,936 review = 8,815，silent drop 0；1,250 transfer 与 249 refund 缺结构化证据时均不发布。
- S3-P3-T3：10 类事件 matrix 覆盖 8/8 主链路；同一 economic event 每 metric 最大计数 1，五个 UI surfaces 共用 read_model_hash。
- S3-P3-T4：形成 idempotency/reconciliation/matrix/read-model/lineage/review/privacy/evidence pack；Stage 3 whole review 保持 `not_started`。
- 模型登记：新增 `MOD-PFI-005`、`FORM-PFI-006..007`、`PARAM-PFI-048..057`；不输出财务值，不声明日期字段具有真实时刻精度。
- 数据边界：只读真实 Git object；数据库、真实源、App、remote refs 未修改；Finder/network/push/install 均未执行。
- 当前结果：Phase 3.3 `candidate_pass`，Stage 3 Phase tasks `12/12 candidate`，Stage 3 仍 `in_progress`；下一任务为独立 whole-stage review。
- 回滚：只 revert 本 Phase 本地提交；无真实数据、数据库、App 或远端回滚动作。

## ITER-20260714-PFI-V025-S3-P32

- Task / Acceptance：`S3-P2-T1..T4` / `ACC-PFI-V025-S3-P32-NORMALIZED-EVENT`。
- 目标：完成 Stage 3 Phase 3.2 标准化交易、Interconnection、Economic Event 与统一 Ledger 合同；不进入 Phase 3.3 的真实重复导入、对账与差异处理。
- RED：新 `economic_event_pipeline` 缺失时测试收集按预期失败；随后以四份 Draft 2020-12 schema、versioned event policy、纯 domain model 与 deterministic application pipeline 实现合同。
- S3-P2-T1：amount/currency/direction 与 transaction/posted/effective/imported time 必填；normalized id 绑定 source-record provenance 与 version。
- S3-P2-T2：只按显式 link reference exact-match 归组；无 link 时保持 singleton；金额/时间/source-name heuristic 全部禁用。
- S3-P2-T3：10 类事件的 net-worth/cash/living/activity/investment/offset/fee-tax flags 明确；未知类型 `review_required_no_publication`。
- S3-P2-T4：Ledger Event 保存完整 raw→normalized→group→economic→ledger lineage 与逐笔 postings；canonical SHA-256 idempotency key 对输入顺序稳定。
- 模型登记：新增 `MOD-PFI-004`、`FORM-PFI-004..005` 与 `PARAM-PFI-036..047`；不生成跨币种聚合金额，不声称真实幂等/对账通过。
- 数据边界：真实财务记录、账户、link reference、金额、数据库 read/write 均为 0；没有 migration、Finder、network、push 或 App install。
- 当前结果：Phase 3.2 `candidate_pass`，Stage 3 `in_progress`，下一任务 `S3-P3-T1`；Phase 3.3 与 Stage 3 whole review 未开始。
- 回滚：只 revert 本 Phase 本地提交；不得触碰 Stage 2/Phase 3.1 不可变证据、真实数据、App 或 remote refs。

## ITER-20260714-PFI-V025-S3-P31

- Task / Acceptance：`S3-P1-T1..T4` / `ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT`。
- 目标：完成 Stage 3 Phase 3.1 来源与账户角色合同，不进入 normalized transaction、economic event、ledger 或 reconciliation。
- RED：新 v0.2.5 service 缺失时测试收集按预期失败；随后以四份 Draft 2020-12 schema、纯 domain 模型和 application routing service 实现合同。
- S3-P1-T1：source type 与 capability 使用开放 lowercase namespaced token，不枚举来源名称。
- S3-P1-T2：同一 opaque account_ref 支持多角色及重叠 inclusive effective ranges。
- S3-P1-T3：Source Profile 强制绑定 parser id、parser version、sha256 source hash 与 hash scheme。
- S3-P1-T4：未知角色只能进入 `review_required`，`publish_allowed=false`，不得默认猜测或静默发布。
- 模型登记：新增 `MOD-PFI-003`、`FORM-PFI-003` 与 `PARAM-PFI-028..035`；规则只处理 metadata routing，不计算财务值。
- 数据边界：真实财务记录/账户/持仓/金额/数据库 read/write 均为 0；没有 migration、Finder、network、push 或 App install。
- 当前结果：Phase 3.1 `candidate_pass`，Stage 3 `in_progress`，下一任务 `S3-P2-T1`；Phase 3.2/3.3 与 Stage 3 whole review 未开始。
- 回滚：只 revert 本 Phase 本地提交；不得触碰 Stage 2 不可变证据、真实数据、App 或 remote refs。

## 2026-06-27

- PFI 根项目三基入口统一为 Markdown 文件名。
- 补齐 PFI 根最小治理文件。
- 完成 PFI V0.2 Stage 2 本地合同验收、入口验收和缓存清理记录。
- 完成 PFI V0.2 Stage 3 首页、账户、账本可读 MVP，本地只读 read-model 和 Web shell 8 入口刷新。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，本地只读 analysis read-model 和 Web shell 投资/消费分析刷新。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，本地只读 delivery model 和 Web shell 建议/报告入口刷新。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，本地 synthetic E2E、20 gate audit、ACC-* audit、回归治理和回滚计划刷新。
- 建立 PFI v0.2.1 前端优化 Stage 0 准备合同，锁定 CNY 基准、CNY/AUD 06:00 顶栏汇率、HTML Web Shell 目标、统一导航和后续 P0-P8 验收顺序。
- 不新增生产或实盘能力声明；同步全部只生成计划，不执行外部动作。

## 2026-06-28

- 完成 PFI v0.2.2 Stage 0 任务锁定与文件定位，生成 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`、`docs/pfi_v022/ROADMAP_LOCK.md` 和 Stage 0 合同测试。
- 完成 PFI v0.2.2 Stage 1 模型参数文件重构，新增 `config/pfi_parameters.yaml`、`docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md` 和 `tests/test_pfi_parameters_consistency.py`。
- product_version v0.2.2 数据库治理 Stage 1 对应本轮参数治理文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示当前 Web Shell UI 基线未在 Stage 1 修改。
- Stage 1 参数治理覆盖 `S1-P1-T1..S1-P2-T3`，建立中文参数总目录、机器可读参数源、公式中文解释、阈值说明表和变量中文别名。
- 本轮不修改 v0.2.1 HTML Web Shell，不实现 Stage 2 汇率快照读取，不新增真实交易、自动投资、支付或券商提交能力。
- 完成 PFI v0.2.2 Stage 2 CNY 基准与汇率规则，新增 `src/pfi_v02/stage_v022_fx.py`、真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`、`docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 和 `tests/test_v022_fx_effective_date.py`。
- product_version v0.2.2 数据库治理 Stage 2 对应本轮 CNY/Fx 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 2 覆盖 `S2-P1-T1..S2-P2-T3`，建立 `AUD/CNY` 真实快照、06:00 有效汇率日、普通运行不默认联网、原币辅助显示和账本金额字段。
- 完成 PFI v0.2.2 Stage 3 数据源、账户角色与可扩展结构，新增 `src/pfi_v02/stage_v022_source_profile.py`、`docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 和 `tests/test_v022_stage3_source_account_profiles.py`。
- product_version v0.2.2 数据库治理 Stage 3 对应本轮 source/account profile 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 3 覆盖 `S3-P1-T1..S3-P2-T3`，建立 source profile schema、capabilities、`other_source_template`、账户多角色、生效期和 role/event type 计算策略。
- 完成 PFI v0.2.2 Stage 4 Economic Event 与 Interconnection 逻辑，新增 `src/pfi_v02/stage_v022_interconnection.py`、`docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`。
- product_version v0.2.2 数据库治理 Stage 4 对应本轮 interconnection/no-double-count 文档状态；`VERSION` 继续保留 v0.2.1 前端优化，表示 UIUX 基线仍沿用 v0.2.1 HTML Web Shell。
- Stage 4 覆盖 `S4-P1-T1..S4-P2-T3`，建立 `economic_event_id`、`interconnection_group_id`、事件影响 flags、Interconnection Matrix、Metric Dependency Graph、双消费口径和 no-double-count 规则。

## ITER-20260710-PFI-CF-L2

- 日期：2026-07-10。
- 事实等级：本地 build、隐私扫描、13 项兼容性测试、桌面/移动端渲染、Wrangler dry-run、永久 workers.dev 部署与 HTTP 检查均为 VERIFIED。
- 版本前后：`v0.2.1 前端优化` / `v0.2.1 前端优化`。
- Task / Acceptance：`CF-L2-20260710` / `ACC-CF-L2-20260710`。
- 目标：增加隔离的定性脱敏 L2 产品壳，不读取真实账户、组合、交易、券商凭据、私密报告或本地数据库。
- 结果：静态 build、private dist scan、响应式 QA 和 Wrangler 4.110.0 dry-run 通过；永久 deployment `7c6d216e-0fd3-43e6-904b-404aac0d776e` 已上线 `https://codex-pfi.linzezhang35.workers.dev`，根页面与 `public-surface.json` 均为 HTTP 200。
- 模型与参数边界：不修改投资、消费、现金流、汇率、分类、推荐或执行逻辑；`PARAM-PFI-023` 只记录公开 adapter 的 L2 兼容合同。
- 回滚：删除 `web/cloudflare-public` 与本次治理记录；PFI 私密核心和真实财务数据不受影响。
- 下一门槛：仅剩可选 `pfi.linzezhang.com` 绑定；真实账户、broker、支付和执行能力仍不在 L2 范围。

## ITER-20260710-PFI-V024-R1

- Task / Acceptance：`PFI-V024-R1-20260710` / `ACC-PFI-V024-R1`。
- 结果：恢复 v0.2.4 canonical closeout history；sparse worktree 通过 immutable Git OID 只读验证真实 `MetaDatabase/PFI`，不触发 lazy fetch，不复制或改写财务数据。
- 验证：focused `33 passed`、v0.2.3 `200 passed`、v0.2.4 `219 passed`、check-render `0/0`、独立复核 `APPROVED`。
- 下一门槛：独立 `v0.2.4 overall re-review`。

## ITER-20260710-PFI-V024-OVERALL-REREVIEW

- Task / Acceptance：`PFI-V024-OVERALL-REREVIEW-20260710` / `ACC-PFI-V024-OVERALL-REREVIEW`。
- 当前范围：复核原 `v0.2.3-repair` Stage 0-9、Phase R1、真实数据和 final-delivery boundary；不执行 GitHub upload 或 app reinstall。
- 当前证据：40/40 phase/whole-stage evidence unit 四件套完整，84 个 JSON 可解析，真实数据为 4 raw / 8815 processed / as of 2026-06-03。
- 当前结果：overall re-review pass；focused `12 passed`、v0.2.3 `200 passed`、v0.2.4 `231 passed`、semantic/UI/data/renderer/reviewer gates 全部通过。`product goal 未完成`，唯一下一 gate 为 `PFI-V024-FINAL-DELIVERY`。

## ITER-20260710-PFI-V024-FINAL-DELIVERY

- Task / Acceptance：`PFI-V024-FINAL-DELIVERY-20260710` / `ACC-PFI-V024-FINAL-DELIVERY`。
- Product freeze：`17b9f59794740f927c5f531ba1aa334621a832e5`；evidence commit 必须为其直接子提交并通过唯一一次 push 上传。
- App：Applications、Downloads 与 Desktop 三入口 codesign/binding/dry-run 通过；signed hash 一致，Mach-O code-section hash 与 current-source deterministic compile 一致；lite acceptance `29/0/2`。
- Runtime：只读 current-code probe `8/0`，app/localhost/disk 与 5 个 filename-bound inline assets 逐项一致，console/page/http errors 为 0。
- Protected paths：`.venv`、`data`、`reports` 安装前后 metadata hash 相同，未修改。
- 回归：final-delivery `11 passed`、v0.2.3 `200 passed`、v0.2.4 `242 passed`；独立只读复核 `APPROVED`。
- 当前 tracked 状态：final-delivery transaction 已准备，等待唯一 push 后 live verifier；`product goal` 仍为 pending，下一 gate 保持 `PFI-V024-FINAL-DELIVERY`。verifier pass 即满足最终 postcondition，且不得再提交第二个 closeout commit；future version 未开始。

## ITER-20260711-PFI-V025-S0-P02

- Contract / Acceptance：`PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` / `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT`。
- Roadmap tasks：`S0-P2-T1` active requirements、`S0-P2-T2` history deprecation、`S0-P2-T3` product/integration boundary、`S0-P2-T4` one-Phase run contract。
- Core contracts：`PFI/config/pfi_v025_active_requirements.json`、`history_deprecation.md`、`scope_boundary.md`、`run_contract.md`；exact 20-file override 由 8 个 core/evidence artifacts 与 12 个具名 governance companions 组成。
- 当前状态：Task 5 真实 command ledger、evidence package、单一事件与 pre-commit candidate gates 已完成，exact 20-file candidate 已 staged；原子提交与 external post-commit attestation 尚未完成，因此只可声明 `candidate_pass_pending_postcommit_attestation`。
- 模型/公式/参数：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；保持 `1/1/23/10/10`，`PARAM-PFI-003` 只更新 contract metadata，运行值不变。
- 非范围：没有 runtime、真实/私有 data、DB、App、migration、安装、GitHub push、release 或 Phase 0.3 工作。
- Rollback：提交前仅移除本 iteration 的 20 路径 diff；提交后只允许 append-only-safe compensating rollback，不改写历史证据。

## ITER-20260711-PFI-V025-S0-P03

- Contract / Acceptance：`PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE` / `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`。
- Roadmap tasks：`S0-P3-T1` finding 归一化、`S0-P3-T2` gap 聚合与优先级、`S0-P3-T3` Stage 0 Evidence Pack、`S0-P3-T4` 验收请求与停止。
- 当前状态：`candidate_pass_pending_postcommit_attestation / approved_pending_postcommit_attestation`；second-remediation corrected provisional 与 canonical exact-25 final-tree gates 已通过，仅待 atomic commit 与 external postcommit attestation。
- Phase 0.2 external attestation 已解析上一 Phase 的 tracked pending lifecycle；Phase 0.3 不改写历史行。Stage 0 whole-stage review 与 Stage 1 均保持 `not_started`。
- 模型/公式/参数：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；保持 `1/1/23/10/10`，`PARAM-PFI-003` 只增加 gap-evidence provenance，运行值、config ref、version、status 与日期不变。
- 非范围：没有业务 UI、产品逻辑、runtime、真实/私有 data、DB、App、migration、安装、GitHub push、release、Stage 0 whole-stage review 或 Stage 1 工作。
- Rollback：提交前仅移除本 iteration 的 13 个新 core paths 并恢复 12 个 companion hunks；提交后只允许 append-only-safe compensating rollback，不改写历史证据。

### PFI-V025-S0-P03-COMP-FND030

- 本节是同一 `ITER-20260711-PFI-V025-S0-P03`、同一 `ACC-PFI-V025-S0-P03-GAP-EVIDENCE` 的 append-only classification compensation，不新增 Roadmap task 或 Acceptance。
- 根因：Phase 0.1 盘点命令误查 `PFI/web/app/home.js`，Phase 0.3 又把该 measurement 提升为 product gap；Roadmap 与 Active Requirements 并未指定此路径，正式首页源为已加载的 `PFI/web/app/pages/home.js`。
- 修正：FND-030 从 `New / new_current_fact / blocking` 改为 `N/A / superseded_or_non_applicable / non-gap`，删除 `GAP-P1-04`。最新计数为 `23/7/0/4/4`，开放 P0/P1 阻断为 `27 (22/5)`，primary gaps 为 `12`，non-gap 为 `11`。
- 原 Phase commit `31368570082c34eca50c72c7d7b2ef46b0e6854d` 与原 immutable attestation SHA-256 `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` 保持不可变；补偿 commit 与新 external compensation attestation 完成前，owner-visible lifecycle 为 `classification_compensation_pending_postcommit_attestation`。
- 模型/公式/参数继续为 `model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`，总量保持 `1/1/23/10/10`；产品、runtime、App、data/DB、安装、push、Stage 0 whole-stage review 与 Stage 1 均未执行。
- Rollback：补偿提交前仅撤销 exact 15-path diff 回到 `3136857`；提交后只允许新的 append-only correction，绝不改写原 event、commit、evidence history 或 attestation。

## ITER-20260712-PFI-V025-S0-WHOLE-REVIEW

- Contract / Acceptance：`PFI-V025-STAGE0-WHOLE-REVIEW` / `ACC-PFI-V025-S0-WHOLE-REVIEW`；review base 为 `a590a3da20f2cf569c11114a3f46e1ff1a0ef6f2`。
- 复核范围：Stage 0 的 12 个 Roadmap tasks、Phase evidence、FND-030 compensation、六项 Acceptance、Stop Conditions、Stage Closeout、privacy 与 no-side-effect boundary。
- Evidence remediation：新增 durable whole-stage index；补齐 executable verifier 与 typed result records；统一 review-commit attestation lifecycle；以 correction-specific unique selector overlay supersede 历史 FND-030 宽 selector。整改后 Stage 0 review findings 为 `0/0/0`。
- 当前 verdict：`codex_candidate_pass_pending_review_commit_attestation_and_user_acceptance`。这不解析 27 个开放 P0/P1 production blockers，不等于 v0.2.5 production acceptance。
- 模型/公式/参数、产品代码、App、runtime、data/DB、安装、migration 与 remote refs 均未改变；Stage 1 为 `not_started`。
- Rollback：只撤销 whole-review exact-path ledger；不改写 Phase commits、events 或 attestations。

## ITER-20260712-PFI-V025-S1-P11

- 日期：2026-07-12；唯一 Acceptance：`ACC-PFI-V025-S1-P11-RELEASE-IDENTITY`；Roadmap tasks：`S1-P1-T1..T4`。
- 目标：四方 release identity 与 mismatch fail-visible；Stage 1 仍为 `in_progress`，下一 Phase 是 1.2 cache/旧 UI 根因治理。
- 机器身份：`v0.2.5 / pfi-v025-s1p1-20260712.1 / a9592b8ce457492fd0e6817f74388f146ca657c6 / frontend 3c45901b... / backend 056c3fd4...`；初始与中间两组 commit pair 均已 superseded。
- TDD：初始 Python/Node RED 与首轮 remediation 保持历史；独立审查在 `9cc8e0f6...` 发现 `C1/I2/M0` 后，Python visible-error RED 为 `9 passed / 1 failed`，Node iframe/static RED 为 `10/15`，final GREEN 为 Python `10 passed`、Node `15/15`，另有 JS/zsh/C/plist/codesign checks。
- 浏览器：隔离临时 Chrome profile 的 partial launcher query 显示中文“版本冲突”，旧 shell 不可见；没有连接 PFI live ports。
- 授权：持续过渡授权 active，但 `production_accepted=false`、final human acceptance=false；不创建 `human_acceptance.json`。
- 模型/公式/参数行为：`NO_CHANGE`；引用既有 data/formula/parameter source identifiers，不制造 v0.2.5 版本值。
- 非范围：Phase 1.2、Phase 1.3、canonical install、Finder、push、财务数据、SQLite、8501 direct release endpoint 均未执行。
- Remediation：除 raw manifest SHA、runtime-config 与路径脱敏外，gate 现在覆盖 Streamlit `srcdoc` iframe parent/referrer launcher query、冲突来源、static invalid manifest；Finder 失败显示固定中文恢复 dialog。
- Rollback：先回退 final identity-binding commit，再回退 final release-content commit `a9592b8c...`；不改写 superseded 历史，不触碰用户数据或已安装 App。

## ITER-20260712-PFI-V025-S1-P12

- 日期：2026-07-12；唯一 Acceptance：`ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE`；Roadmap tasks：`S1-P2-T1..T4`。
- 目标：治理旧 UI 的 HTTP/SW/bfcache/Streamlit/process-cache 根因，不进入 Phase 1.3；Stage 1 保持 `in_progress`。
- TDD：初始有效 RED 为 Python `9 failed`、Node `8 failed`；首个 binding 后 GREEN 为 Python `20 passed`、Node `23 passed`。独立复核 `C0/I4/M0` 后，remediation RED 精确复现 `4 failed / 8 passed`，最终 GREEN 为 Python `22 passed`、Node `23 passed`，syntax/zsh/isolated HTTP 通过。
- Cache topology：PFI JS/CSS 在 official path 是 inline `srcdoc`，不伪称 hashed URL；actual 14-file frontend source hash 和 backend import-time hash 均在 launch/runtime 重验。
- Streamlit：actual runtime 1.35.0；read-model adapter 使用 public `st.cache_data`、TTL 30、memory-only、composite key 参数，stable read-model hash 排除时间/绝对路径/财务值；wrapper 在 CLI 前预启动并验证 port-0 same-process API owner。
- Browser：isolated HTTP 4/4、Chromium 10/10；历史 worker/cache 清零，controlled page 零 backend fetch，reload 无 controller 后 ready，mismatch 中文 fail-visible。真实 back/forward 的 `persisted=false`，未冒充 hit。
- Machine binding：初始 `5edd3788.../df7e2add...` pair 已 superseded；final remediation content commit `b3885f15cd2e983c0839be6a20d7e4a9391c6324`；frontend `3c1f3a71...`；backend `5d728585...`；cache key `5ac651d6...`。final binding、fresh review、attestation 尚待完成。
- 非范围：Phase 1.3、canonical install/Finder/new profile、8501/8502 live runtime、push、财务数据/SQLite、model/formula/parameter semantics、production/final human acceptance。
- Rollback：先回退 final Phase 1.2 binding/evidence commit，再回退 remediation content commit `b3885f15...`；保留 superseded 历史，不触碰用户数据、已安装 App 或 remote refs。

## ITER-20260712-PFI-V025-S1-P13

- 日期：2026-07-12；唯一 Acceptance：`ACC-PFI-V025-S1-P13-ISOLATED-APP-ACCEPTANCE`；Roadmap tasks：`S1-P3-T1..T4`。
- 内容提交：`128c6b889c91f5d7f64c7cd9635466fa2caf0275`；manifest 与 embedded manifest 绑定同一 commit、frontend/backend hash 与 release-only cache key。
- Finder/runtime：临时 App 真实双击，三成员 PGID、双 loopback endpoint、Streamlit/monitor 各一个 listener；fresh Chromium 的 25 项 checks 全部通过，错误计数为 0，`pageshow.persisted=false` 如实记录。
- Isolation：候选没有财务数据、SQLite、model/formula/parameter 或 auxiliary API 访问；canonical 三入口 before/after 完全一致。
- Cleanup：候选进程组停止、两个端口释放、LaunchServices 最终缺席、临时根删除；Git status 与 protected metadata 未变化。
- 生命周期：`candidate_pass_pending_direct_binding_attestation_and_independent_review`；Stage 1 仍为 `in_progress`，Stage 2 未开始。
- Rollback：先回退 Phase 1.3 direct binding/evidence commit，再回退 content commit `128c6b88...`；不触碰 canonical App、用户数据、live 8501/8502 或 remote refs。

<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_BEGIN -->
ITER-20260712-PFI-V025-S1-P13
owner_view_conflict_id=PFI-V025-CONFLICT-OWNER-VIEWS
owner_view_conflict_status=blocked
owner_evidence_state=unified_owner_view_not_proven
owner_view_resolution_task=STAGE12-WHOLE-REVIEW
owner_views_unified=false
v0.2.5_accepted=false
stage_1_status=in_progress
canonical_install_gate=S12-P2-T1
<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_END -->

## ITER-20260713-PFI-V025-S1-WHOLE-REVIEW

> 历史 tracked candidate snapshot；当前状态已由 matching external attestation 与 `EVENT-20260714-PFI-V025-S2-P21` 取代。

- Contract / Acceptance：`PFI-V025-STAGE1-WHOLE-REVIEW` / `ACC-PFI-V025-STAGE1-WHOLE-REVIEW`；whole review base `96305405dcf7eb56246d2cede2f5b50b2b1be101`。
- Final content chain：`9c4fb71f -> 2009d36d -> 49857109 -> 5b0667ef -> 2ef60871 -> 0ffe6909 -> c6091e98 -> ca6ce4ae -> c980fef5 -> e412b1da -> 7348eff2 -> 8df58316 -> bb4243a4 -> e6d6de54 -> de661af5 -> a8ac008d -> 6d93b357 -> 0ac61029`；每条 edge 的 full-repo name-status 与 17 个 content paths 均由 verifier 固定。
- Product remediation：official production shell、12 backend/14 frontend source identity、same-process read-only runtime API、candidate legacy override fail-closed、truthful isolated-empty/FX/report/route UI、visible DOM/full HTML/live form-control privacy、10-route 浏览器遍历、真实 iframe AX tree 与 exact three-member/three-listener runtime。
- Governance remediation：补 canonical project/roadmap/三基 human entries、TaskPack manifest schema、12-task/6-criteria/4-stop matrix、Phase 1.2 derived correction、safe external paths、PNG/AX privacy 与 HEAD-bound postattestation gate。
- Review history：初始 product `C1/I3/M0`；初始 verifier `C2/I4/M2`；content rereview `C1/I2/M0`；C4 rereview `C1/I0/M0`；C12 修复 candidate downgrade、历史报告/FX/伪零与证据覆盖后，定向 legacy/shell/browser rereview 为 `C0/I0/M0`；所有 findings 仍必须在 final prebinding/postbinding reviews 归零。
- 历史结果：`candidate_pass_pending_postcommit_attestation`。matching external attestation SHA-256 `a03651248d67f727f001b52c0a08961416155506b374fa08123247ebfa8f0d2a` 已激活；当前 Stage 1=`accepted_for_transition`、Stage 2=`in_progress`，production/final acceptance=false。
- 模型/公式/参数：`model_ids_changed=[]`、`formula_ids_changed=[]`、`parameter_ids_changed=[]`；不 push、不 install、不读写财务数据/SQLite。
- Rollback：先回退唯一 direct binding successor，再回退 final content；不改写 Phase commits/events/attestations，不触碰 canonical Apps、用户数据或 remote refs。

- 2026-07-14 ITER-20260714-PFI-V025-S2-P21：完成 Stage 2 Phase 2.1 S2-P1-T1..T4 candidate。项目分配 Acceptance ACC-PFI-V025-S2-P21-DATA-ROOT-SOURCE-MANIFEST；固定四个候选 alias，选定 $PFI_DATA_HOME 为 canonical private runtime root，其他位置保持显式 alias/只读来源且不迁移。Source Registry 是 Manifest 定义输入；交易 source ready / 8815 / 2022-06-06..2026-06-03 / path-sensitive SHA-256，operational SQLite 仅 partial metadata；余额、负债、持仓、价格、FX 因未绑定 source-level aggregate metadata 记为 not_loaded。交易只证明 source input available；分类、CNY 消费、现金、投资市值、净资产因 source/contract dependencies 未满足均 blocked/null。SQLite 使用 mode=ro 共享只读事务、query_only 和 deny-write authorizer，前后 sidecar/目录/候选集/DB 指纹一致；无 Finder、数据写入、push、App install、model/formula/parameter 行为变化或 production/final acceptance。Stage 2 保持 in_progress，下一任务 S2-P2-T1。
- 2026-07-14 ITER-20260714-PFI-V025-S2-P22：完成 Stage 2 Phase 2.2 `S2-P2-T1..T4` candidate。新增 `MOD-PFI-002` / `FORM-PFI-002` / `PARAM-PFI-024..027`，固定八个时间字段、Australia/Sydney 06:00 cutoff、周末与显式 source-closed date 回退、AUD_TO_CNY 唯一方向和 ordinary-runtime offline policy。transaction_time 只记录 8815 条 aggregate coverage，其余时间字段保持 not_verified。生产 FX source 仍 not_loaded，rate/hash/snapshot id 为 null；旧 v0.2.2 snapshot 只作 reference。无网络获取、source/DB mutation、Finder、push、App install 或 production/final acceptance；Stage 2 保持 in_progress，下一任务 S2-P3-T1。
- 2026-07-14 ITER-20260714-PFI-V025-S2-P23：完成 Stage 2 Phase 2.3 `S2-P3-T1..T4` candidate。transaction input 绑定 implementation base `7875e006...` 的 immutable Git objects，8815-record 三次全量解析与 manifest 一致；operational SQLite 仅进入 0700/0600 ephemeral copy，quick_check 后清理且 source identity/hash 不变。no-fake 和固定十文件 privacy gate 通过，无 financial fixture fallback、私密值、Finder、network、source mutation、push 或 App install。model/formula/parameter 不变，性能仅作 observation。Stage 2 三个 Phase candidate complete，但整阶段独立复审/用户接受未开始，Stage 2 保持 in_progress，Stage 3 未授权。
- 2026-07-14 ITER-20260714-PFI-V025-S2-WHOLE-REVIEW：以 `431ddb30c...` 为 review base，对三个 Phase immutable evidence、12 tasks、6 Acceptance、4 Stop Conditions 与 Pass Gate 做独立整阶段审查。初审 C0/I3/M1 的 verifier/Evidence、final index、human acceptance、source disposition 缺口均已整改，三路复审 C0/I0/M0。用户的最终验收前 blanket interim authorization 被具体绑定 canonical root、8815-record scope、五个 blocked/null 指标、production FX not_loaded/offline 与 read-only/no-fake 边界。Stage 2 accepted_for_transition；Stage 3 entry authorized 但 not_started。model/formula/parameter、真实数据/DB 未改；无 Finder、push/install 或 production/final acceptance。
- 2026-07-14 ITER-20260714-PFI-V025-S3-WHOLE-REVIEW：以 `0f9672081...` 为 review base，逐提交复核 Phase 3.1/3.2/3.3 immutable evidence、12 tasks、6 Acceptance Criteria、4 Stop Conditions 和 Pass Gate。初审 C0/I3/M1 的整阶段 verifier/Phase binding、final index、残余与 human acceptance binding、治理 closeout 缺口全部整改，三路复审 C0/I0/M0。真实快照保持 8815=6879 published+1936 review+0 silent drop；1250 transfer 与 249 refund 仍未确认并 fail-closed。用户中间授权只绑定此技术范围；Stage 3 accepted_for_transition，Stage 4 entry authorized 但 not_started。model/formula/parameter、真实数据/DB 未改；无 Finder、network、push/install 或 production/final acceptance。
