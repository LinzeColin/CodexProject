# CHANGELOG

## v0.2.5 Remote Recovery and Local Retirement Handoff - 2026-07-16

- 记录 final delivery commit `d488b1f47d5ef8dd5f95fc7d6f9a5382d1486a8a` 已进入 GitHub `main`，当前远端仍保持已验收 PFI product tree `a6aae2ae9e89f601b9a1833a45947ed625aa100c`；最终 App 重装与 post-push parity 已闭合。
- 将原始 Roadmap `fc2f406e...` 与 TaskPack ZIP `591c8399...` exact bytes 归档到 `PFI/docs/source_packages/pfi_v025/`，补齐仅存在于本机 Downloads 的开发输入。
- 逐项证明四个 immutable raw source blobs 已在迁移后的 `LinzeColin/MetaDatabase@main` commit `8fad21d...` 保持相同 OID、bytes 与 SHA-256；未恢复已迁出目录，未把 `$HOME/.pfi` 或私有值写入公开 PFI。
- 本地 canonical SQLite 与三份备份在退休前均 `quick_check=ok` 且业务表 0 行；App/worktree/入口/Downloads 原包/runtime 均可从远端产品、schema/migrations 与迁移后 raw sources 重建。全程 Finder/`open`/LaunchServices/AppleScript/GUI 为 0，共享 Git object DB 不执行 GC。

## v0.2.5 Stage 12 Exact Final Acceptance and Release Freeze - 2026-07-16

- 唯一 CLI-only canonical App 最终重装已于 `2026-07-16T00:27:09Z` 实际执行：`install_performed_this_invocation=true`，version/build/codesign/project-binding 与 deterministic bundle/executable hashes 全部通过；Finder/LaunchServices/`open`/GUI 为 0。仅余唯一 main 上传与 post-push parity。
- Owner 精确最终接受 build `pfi-v025-s1p1-20260712.1`、App `0.2.5 / 20260712.1`、Stage 0–12、product candidate A `c8ce63a...`、reviewed closure B `559cf19...`、rereview evidence C `123f5a6...` 与 evidence-index `sha256:ebd03b8a...`。
- 验收请求时间 `2026-07-15T21:45:47Z` 与五项非阻断 P2 已原样绑定；TaskPack human acceptance schema、A/B/C/index/App gate 和 runtime zero-drift 验证通过。
- `S12-P3-T4=completed`，release freeze 已执行；v0.2.5=`156/156 (100%)`、Stage 12=`12/12 (100%)`。
- 仓库拆分移除顶层 `MetaDatabase` 后，历史 pytest 仅在测试层把默认 `git_ref` 路由到已锁定的 immutable source commit `78375ec...`；不恢复迁出目录、不修改 runtime。原始 Phase 12.1 矩阵复跑为 `358 passed, 6 deselected`。
- 本 freeze 尚未执行 GitHub main push 或 post-push production parity；唯一 canonical App 最终重装已闭合。Finder/`open`/LaunchServices/AppleScript/GUI 操作为 0。

## v0.2.5 Stage 12 Whole-stage Independent Rereview - 2026-07-16

- 在整改闭合 B `559cf190ccfd97aabcf37a5edf2bf1e9abe300fc` 上完成单独 deterministic local rereview；重新验证 runtime source `78375ec...` → product/remediation anchor A `c8ce63a...` → closure B 的精确 ancestry，B 后 runtime payload drift=0。
- 重新计算 release identity、Phase 12.3 exact binding、Phase 12.3/整改两套 artifact manifests、CLI-only entry census 与 fresh real headless E2E；所有 manifest mismatch 与 entry mismatch 均为 0，canonical DB 未变且无外网。
- 三项原 P1 均为 `closed_verified`；复审新增 `0 P0 / 0 P1 / 0 minor`。Focused Stage 12 `61/61`、adjacent `115/115`、Node `8/8`、dual-plane/Lean/complete-overlay/privacy 通过。
- 五项 P2 residual 原样保留；`S12-P3-T4`、final human acceptance、GitHub main push 与 canonical App 最终重装均未执行。Finder/`open`/LaunchServices/AppleScript/GUI 操作为 0。
- 总进度保持 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`；下一唯一任务为 exact final acceptance `S12-P3-T4`。

## v0.2.5 Stage 12 Whole-stage Initial-review Remediation - 2026-07-16

- 关闭初审三项 P1 待独立复审：runtime payload 精确锚定 `78375ec98fc1265abd03ef10087cc05beccab8b4`，manifest 与 embedded identity 一致；后续 runtime drift 为 0。
- 建立 remediation candidate `c8ce63aac785ae1f119cfe1ff993c4e81436bf97`；Phase 12.3 index、request、state 与 evidence 全部绑定该 40 位提交及 index SHA-256 `ebd03b8a...`，不再使用 `SELF` 或 precommit snapshot。
- 核对旧 Downloads App 为 v0.2.3/build 20260629.1 后，以 CLI 原子移动到私有隔离区；未删除，公开 receipt 保留 `$HOME` 回滚命令。Canonical App 与 Desktop symlink 保持 v0.2.5/build 20260712.1，入口 mismatch=0。
- Fresh real headless E2E、focused Stage 12、selected adjacent regression、Node `8/8`、release identity、dual-plane、renderer、complete overlay governance、privacy 与 artifact hashes 通过；整改后 open P0/P1=`0/0`，5 项 P2 residual 保留。
- 当前仍为 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`；独立复审、`S12-P3-T4`、最终 human acceptance、GitHub main push 与 canonical App 最终重装均未执行。Finder/`open`/LaunchServices/AppleScript/GUI 操作为 0。

## v0.2.5 Stage 12 Whole-stage Initial Review - 2026-07-16

- 在 exact candidate `9a7245acf984a4eb98f93c4aab7bb4d02095294f` 完成独立整阶段初审；Phase 12.1/12.2/12.3 的 119/119 declared artifacts、Phase 12.3 final-index 的 89/89 inputs 与 detached hash 全部重算通过。
- 重新运行 fresh real headless E2E 17/17：4 个 immutable source blobs、8,808 ledger / 803 review；Holdings 保持 `not_loaded/not_run`，canonical private DB 未读写。
- 初审登记 `0 P0 / 3 P1 / 0 minor`：release manifest source commit drift、pending acceptance/state 非 exact candidate binding、Downloads 旧 v0.2.3 noncanonical App。
- focused/adjacent Python、Node `8/8`、dual-plane、Lean renderer、complete archive+overlay governance、privacy 与 artifact hashes 通过；5 项 P2 residual 如实保留。
- 下一唯一 run 为 `STAGE12-WHOLE-REVIEW-REMEDIATION`；整改后必须另起独立复审。本 run 未整改、freeze、push、重装或最终验收，Finder/`open`/LaunchServices/AppleScript/GUI 操作均为 0。

## v0.2.5 Stage 12 Phase 12.3 Release-freeze Candidate - 2026-07-16

- 将 VERSION、compact README/HANDOFF、canonical governance、三份完整中文 human entries 与 dual-plane facts 统一到 `155/156 (99.36%)`、Stage 12 `11/12 (91.67%)`；下一唯一 run 为 `STAGE12-WHOLE-REVIEW`。
- 合并当前 `origin/main` dual-plane migration；不恢复已删除的顶层 `MetaDatabase`，改由单一 immutable source lock 从可达历史 commit 读取四个已复核 Git blobs，并验证 OID/bytes/SHA-256。
- Stage 12 release test、真实 browser E2E 与 target-Mac UAT 共用 source-lock loader，关闭当前 `HEAD` tree 不再包含旧路径的回归故障。
- 新增 one-way `final_evidence_index.json` + detached SHA-256、状态一致性证据、source migration attestation 与 release-bound pending `human_acceptance_request.json`。
- `S12-P3-T1..T3` candidate complete；`S12-P3-T4`、整阶段 review/remediation/rereview、最终 human acceptance、push 与 post-push canonical App reinstall 均未执行。
- Finder、`open`、LaunchServices、AppleScript、GUI 文件操作、canonical DB mutation、外部网络、production acceptance 与 v0.2.6 均为 0/false。

## v0.2.5 Stage 12 Phase 12.2 - 2026-07-16

- 遵守用户最新明确指令：全程不使用 Finder、`open`、LaunchServices、AppleScript 或 GUI 文件操作；source Roadmap 的 Finder surface 仅替换为 CLI 原子安装和 canonical bundle executable 直接启动，同 build、真实流程、生命周期、恢复和证据门未豁免。
- `/Applications/PFI.app` 已以 CLI 原子替换安装为 v0.2.5 / build `20260712.1`，与 release manifest、runtime identity 和 launcher query 同一 build；保留可回滚的旧 App archive。
- 真实目标 Mac 流程通过：4 个 immutable source objects、8,815 raw / 8,808 ledger，完成 1 个 review 并在 restart 后保持；10 个一级入口和 source/formula/parameter/interconnection 下钻通过。Holdings 仍 `not_loaded/not_run`，报告仍为 3 blocked / 2 partial，无 fixture/fallback 或假零。
- 生命周期通过 start、3 次 repeated start 单 runtime、browser close、offline/recovery、stop/restart/persistence；`SIGSTOP/SIGCONT` 仅作为 owned-process suspend/resume proxy，真实内核 sleep/wake 未执行且不作通过声明。
- canonical 私有 SQLite 仅以 `mode=ro/query_only` Online Backup 读取，源文件与目录零变化；successful restore 和 injected rollback 仅在隔离副本通过。临时 `hdiutil -nobrowse` 卷触发真实 `SQLITE_FULL` code 13，partial output 清理与 recovery backup 通过，未填满主机卷。
- 修复 canonical App UAT 暴露的两项 release/cache 缺陷：frontend release identity 请求现在携带 runtime token；runtime server 启动时冻结 process release cache policy，真实数据写入后不再造成同进程 identity key 漂移。
- focused regression=`55 passed`，Node cache-policy=`8/8`；privacy scan、artifact hashes 与 release identity 通过，open P0/P1=`0/0`，3 个非阻断 P2 已登记。
- Phase 12.2=`4/4 candidate_pass`，Stage 12=`8/12 in_progress`，v0.2.5=`152/156 (97.44%)`；Phase 12.3、whole-stage review、push、release freeze、production/final acceptance 均未开始。

## v0.2.5 Stage 12 Phase 12.1 - 2026-07-16

- 新增 Stage 12.1 automated real-data E2E release harness：从 4 个 immutable Git objects 读取 8,815 条原始记录，在隔离 SQLite 完成 8,808 条 ledger 与 803 条 review 的 preview、confirm 和 idempotent replay；canonical source 与 canonical database 均零写入。
- 修复 GB18030 固定 64 KiB probe 在多字节字符边界误判 unsupported 的真实 parser 缺陷；使用 strict incremental decoder，并同步 backend release identity hash。
- Holdings source 仍为 `not_loaded`，因此 holding execution 如实为 `not_run`、active holding count=0；5 个报告维持 3 blocked/2 partial，不将缺数伪造成零值或财务通过。
- 正式 10 个一级入口与 10 个代表性二级入口完成真实浏览器验证；20 routes、40 screenshots 的 WCAG 2.2 AA deterministic audit、keyboard、CDP AX、视觉回归和性能证据通过，外部请求 0。
- focused regression=`358 passed, 6 deselected`；6 项均为已登记的 immutable historical-state literal debt，当前状态替代验证通过，open P0/P1=0；未声称 axe-core 通过。
- Phase 12.1=`4/4 candidate_pass`，Stage 12=`4/12 in_progress`，v0.2.5=`148/156 (94.87%)`；Phase 12.2/12.3 与整阶段验收未开始。
- 未使用 Finder/LaunchServices/GUI；未 install、deploy、push、production/final acceptance，严格停止在 Phase 12.2 前。

## v0.2.5 Stage 11 Whole-stage Review - 2026-07-16

- 独立整阶段初审冻结 Phase 11.1/11.2/11.3 product/evidence commit 链与 87 个声明 artifact；结果 `C0/I4/M0`，未把 phase candidate 或已有测试误当整阶段通过。
- 整改 Online Backup：canonical source 使用 SQLite URI `mode=ro` 与 `query_only`，不再在源目录创建 coordination lock；CLI/receipts 移除绝对路径。
- 对真实 canonical operational SQLite 执行 source-zero-write Online Backup；源文件 hash/stat、源目录 entries/stat 均未变化，restore 成功与注入失败自动 rollback 均只作用于隔离临时目标。
- 公共静态边界完成 loopback-only headless browser `23/23`：DOM、CDP accessibility tree、截图、脱敏 trace、未知路由 404、外部请求 0；public source/dist 与 active dependency 扫描零违规。
- 整改后 focused Stage 11 `115/115`，三 Phase commit/artifact、TaskPack、release identity、Python/Node syntax、相邻 Stage 4/5/6/7/8/9/10、完整 archive + exact overlay governance/renderer、隐私与 evidence schema 通过。
- 三条 deterministic final rereview 为 `C0/I0/M0`；Stage 11=`accepted_for_transition`，standing transition authorization 已记录；Stage 12 仅 entry authorized，实施仍 `not_started`。
- v0.2.5 任务进度保持 `144/156 (92.31%)`；未迁移/恢复 canonical DB，未输出私密或财务值，未改 model/formula/parameter 数值，未使用 Finder/LaunchServices/GUI，未外网、deploy、push、install、production/final acceptance。

## v0.2.5 Stage 11 Phase 11.3 - 2026-07-16

- 将 Cloudflare public pseudo-dashboard 收敛为无脚本 static boundary notice；移除应用导航/preview，manifest 固定 active UI/routes/runtime/local connection/Context exposure=false，未知路径使用 `404-page`。
- 新增 `pfi_context.v1` policy/schema/runtime validator：Alpha-only，七项 metadata、八项状态型 payload，read-only、no writeback、no numeric financial values、no additional properties。
- 新增 private Context writer/CLI：精确 state input、64 KiB 上限、0700/0600、no overwrite/no symlink/no public-distribution path，receipt 不含本机路径或财务值。
- 活动 Stage 5/6/home/shell adapter 移除旧金额型 Context；legacy dashboard 只形成 provenance hash，缺当前 validated read model 时 fail closed 为 blocked/not_loaded。
- Cloudflare source/dist scanner 检查 asset type、interactive marker、runtime binding、Context field、私密域、credential、绝对路径、金额、正式 10 入口及 Ralpha/Serenity active import；负向注入被拒绝。
- 将 Context policy/schema/security/CLI/scanner 与活动 adapter 纳入 backend release identity，同步 shell.js frontend hash；version/build/release commit 不变。
- Phase 11.3/11.2/11.1、Stage 5/6、release identity 与 shell closeout `77/77`；public build/双扫描、TaskPack schema、完整 overlay governance/renderer、privacy/artifact hashes 通过。
- TaskPack literal allowlist 缺必要 public/active-adapter/release files；standing authorization 下最小扩展并保留 `allowed_files_obeyed=false`。
- Stage 11 phase tasks=`12/12 candidate_complete`，v0.2.5=`144/156 (92.31%)`；Stage 11 whole-stage review/user acceptance 未开始，下一唯一任务 `STAGE11-WHOLE-REVIEW`。
- 未使用 Finder/LaunchServices/GUI；无 canonical private DB/真实财务行/财务值，官方研究仅访问 `developers.cloudflare.com`；产品/测试 runtime 外网 0，未 deploy/push/install/production/final acceptance。

## v0.2.5 Stage 11 Phase 11.2 - 2026-07-16

- 新增 SQLite Online Backup API 一致快照；拒绝在线文件复制、已有 backup 覆盖与非私有目录，输出固定 `0600` 并 fsync。
- 新增只读 snapshot verifier：`integrity_check`、`foreign_key_check`、required tables/migrations、migration checksum registry、schema hash 与 SELECT-only application invariants。
- restore 先验证 backup 与隔离 candidate，再以 exact target SHA-256、无 sidecar、same-filesystem、exclusive maintenance lock 为原子替换前置条件。
- base/import/holding/job operational transactions 共享 maintenance lock；原子替换后故障自动恢复原 application invariants 并匹配 verified rollback snapshot SHA，rollback 失败不会伪报成功。
- 新增 `inspect/backup/restore` CLI 与 10 项 focused tests；Phase 11.2/11.1、Stage 7/10 相邻回归及 release identity 合计 `82/82`。
- disposable online backup、successful restore、injected rollback、integrity/FK/application invariants、TaskPack schema、完整 overlay governance/renderer、privacy 与 artifact hashes 通过。
- durable job writer 与 release identity closure 为必要 standing-authorized scope override，`allowed_files_obeyed=false`；version/build/release commit 未改变。
- Phase 11.2=`candidate_pass`，Stage 11=`8/12 in_progress`，v0.2.5=`140/156 (89.74%)`；Phase 11.3 与 whole-stage review 未开始。
- 未使用 Finder/LaunchServices/GUI；仅 disposable nonfinancial SQLite，无 canonical private DB/财务值/model/formula/parameter 数值变更；研究层仅访问 `sqlite.org`/`docs.python.org` 官方文档，产品/测试 runtime 外部网络调用为 0；未 push/install，production/final acceptance=false。

## v0.2.5 Stage 11 Phase 11.1 - 2026-07-16

- 新增 SQLite runtime gate：官方修复矩阵覆盖 `3.44.6`、`3.50.7`、`3.51.3+`；当前 Python 3.12.13 / SQLite 3.50.4 的显式 WAL 请求 fail closed。
- 活跃 operational stores 统一 `DELETE` rollback journal、`FULL` synchronous、foreign keys、30 秒 busy timeout、显式 `BEGIN/BEGIN IMMEDIATE`、异常/commit 失败 rollback。
- 新增 checksum-pinned `pfi_operational_migrations` lifecycle：版本化记录、幂等 replay、source drift 拒绝、失败 schema/data/registry 全回滚。
- migration SQL 禁止嵌套 transaction、PRAGMA、SAVEPOINT、ATTACH/DETACH/VACUUM；注释伪装的边界逃逸同样拒绝。
- Stage 11 新测试、Stage 7/10 相邻回归与 release identity `68/68`；disposable evidence 四进程 `100/100` unique writes，实际 SIGKILL 后未提交行 `0`，integrity/FK 通过。
- 将基础 `OperationalStore` 与新 SQLite runtime 纳入 backend identity closure，同步 machine/embedded manifest；build/version 保持不变，release identity `10/10`。
- TaskPack 未列出真实活跃 `application/operational_store.py`，本轮仅对该文件使用 standing-authorized scope override，证据如实记录 `allowed_files_obeyed=false`。
- Phase 11.1=`candidate_pass`，Stage 11=`4/12 in_progress`，v0.2.5=`136/156 (87.18%)`；Phase 11.2/11.3 与 whole-stage review 未开始。
- 仅使用 disposable SQLite；未读写 canonical private DB，未改 model/formula/parameter 值，未使用 Finder/LaunchServices/GUI；研究层仅访问 `sqlite.org` 官方文档，产品与测试 runtime 外部网络调用为 0；未 push/install，production/final acceptance=false。

## v0.2.5 Stage 10 Phase 10.3 - 2026-07-15

- 新增 versioned durable-job trace/span/log migration：同一 job trace 跨 queued/claim/recovery/progress/terminal revision 传播，每个 revision 独立 span；旧 job/event 可 deterministic backfill。
- structured logs 在 SQLite 持久化前脱敏路径、email、secret/token、敏感字段和金额形态，记录 timing/error/impact/retry/cache fallback/hash dimensions，并以 append-only trigger 与 SHA-256 chain 保护。
- 新增 durable runtime supervisor 与 authenticated job API；offline cache refresh 使用三项持久单位，timeout 显式 failed/cache fallback，unsafe external-network declaration 在工作前 fail closed。
- 正式 Shell job timeline 改为 backend SQLite 状态：恢复 job list，显示 revision/trace/retry/error/result/units；移除 synthetic stage/success timers，poll timer 只读取持久状态。
- 真实 subprocess checkpoint 后 `SIGKILL`、新进程 lease recovery，以及正式浏览器离页 10,503ms/reload/retry/3-of-3 recovery 通过；UI/API/DB trace、revision、status、progress 一致。
- Phase target `14/14`、最终产品合并 `121/121`；正式 browser/database/trace privacy pass，外部请求 0，SQLite integrity/FK pass、DELETE journal、WAL=false。
- Phase 10.3=`candidate_pass`，Stage 10 phase tasks=`12/12 candidate_complete`，v0.2.5=`132/156 (84.62%)`；whole-stage review/user acceptance 未开始，Stage 11 未进入。
- 仅使用隔离 SQLite 与临时本机 loopback；未使用 Finder/LaunchServices/GUI、canonical 私有 DB、真实财务值或外网，未修改 model/formula/parameter 值，未 push、install 或 production/final acceptance。

## v0.2.5 Stage 10 Phase 10.2 - 2026-07-15

- 新增 versioned 九域 dependency registry/DAG，覆盖 raw/source/ledger/interconnection/parameter/formula/fx/read-model/report、显式 metric impact、cache scope 与安全 provenance。
- 新增只读 SQLite hash observer：仅查询 content hash、source/parser/status 与非金额 ledger identity/state 列；不返回 amount/description/raw bytes，不创建或迁移数据库。
- 新增 dependency snapshot 与精确 diff：changed domain、downstream closure、impacted/unaffected metrics 分离；raw 不误报全指标，no-diff 严格不重算、不失效缓存、不调用 network/Codex/LLM。
- release-cache CLI/runtime API 统一从 atomic context 生成 dimensions/snapshot；`data_hash=dependency_snapshot_hash`，Streamlit/frontend/process key 等值，TTL=30、persist=false。
- active `version.js` 新增九域 hash、snapshot/component/key/TTL/zero-network fail-closed validation；release frontend/backend closure 纳入 registry/runtime diff 并更新 manifest hash。
- Phase target `7/7`；Phase 10.1 + Stage 1 cache/release `45/45`；Stage 7 operational + Stage 9 report `40/40`；修复 Streamlit AppTest `__main__` 测试间污染后最终合并 `85/85`；Node 行为验证与 release identity 通过。
- Phase 10.2=`candidate_pass`，Stage 10=`8/12 in_progress`，v0.2.5=`128/156 (82.05%)`；Phase 10.3 与 whole-stage review 未开始。
- 未使用 Finder/LaunchServices/GUI；普通 dependency/cache 审计零网络，回归验证仅使用临时本机 loopback、无外网；未读 canonical 私有 DB、未输出财务值、未修改 model/formula/parameter 值，未 push、install 或 production/final acceptance。

## v0.2.5 Stage 10 Phase 10.1 - 2026-07-15

- 新增 versioned `durable_jobs` 与 append-only/hash-chained `durable_job_events`；覆盖 queued/running/retrying/succeeded/failed/cancelled/dead_letter、revision、attempt、lease、heartbeat、进度和终态。
- claim 使用 `BEGIN IMMEDIATE` + revision/prior-status CAS；raw lease token 只返回一次且不落库，错误/过期 token、旧 revision 和取消后的 stale worker 均 fail closed。
- 实现 bounded retry、permanent failed、owner cancel、automatic/manual dead-letter 与 expired-lease recovery；重开隔离数据库后保留进度 checkpoint。
- progress 仅接受单调 `completed_units/total_units/step` 事件，heartbeat/timer 不计进度；100% 前不能 succeeded。
- 财务事实结果只能进入 `pending_human_review`、`publishable=false`，无后台发布、网络或交易路径；public projection 不返回 payload/token。
- 当前 SQLite `3.50.4` 低于 Task Pack WAL-safe `3.50.7` backport，因此 WAL 关闭并使用 `DELETE` journal、FULL synchronous、FK、30s busy timeout、显式 rollback。
- target `7/7`、邻接回归 `19/19`、合并 `26/26`、release identity `10/10`；隔离 probe 7 jobs/20 events/all statuses、integrity/FK/CAS/token/privacy 通过并删除临时 DB。
- Phase 10.1=`candidate_pass`，Stage 10=`4/12 in_progress`，v0.2.5=`124/156 (79.49%)`；Phase 10.2/10.3、正式 UI、真实 PFI DB 与 whole-stage review 未开始。
- 未使用 Finder/LaunchServices/GUI，无外网、真实财务值、model/formula/parameter 值修改、push、install 或 production/final acceptance。

## v0.2.5 Stage 9 Whole-stage Review - 2026-07-15

- 整改正式报告真实绑定：immutable reviewed snapshot 驱动主 renderer；localStorage 仅保存严格 review delta，legacy/full/tampered state 在 render 前 fail closed，ledger 验证后才发布状态。
- 主报告、验证页与四格式导出显示总流出、生活消费、投资资金流出、投资域配置四组件，并明确 activity flow 不等于 net-worth loss；不持久化或发布任何财务金额。
- 5 份报告保持 `3 blocked / 2 partial`；`FORM-PFI-015/019` 有当前证据，`016..018` blocked、`020` structure-only、historical/OOS blocked，不夸大模型有效性。
- 补齐 model validation report、Phase 9.2/9.3 DOM/CDP AX、TaskPack phase normalization、fallback/PyYAML renderer parity、准确 parser 运行时标签与可复制完整 PDF hashes。
- Phase 9.3 validator 新增完整 pack hash、确定性 UI contract、pack/manifest 字段集与 deterministic export bytes 门禁；新增 pack hash、UI thesis，以及重算 manifest/UI/pack hash 后 filename、byte_size、sha256 drift 的 fail-closed tests。
- current-content formal Shell browser `16/16`，四格式同源、实体 PDF、focused/upstream regression、隐私、完整 changed-scope governance/renderer 与三方独立复审 `C0/I0/M0` 通过。
- Stage 9=`accepted_for_transition`，Stage 10 entry authorized but implementation=`not_started`；进度保持 `120/156 (76.92%)`。
- 未使用 Finder/LaunchServices/GUI，仅本机 loopback、无外网；无 raw/DB 读写、model/formula/parameter 值修改、自动交易、push、install 或 production/final acceptance。

## v0.2.5 Stage 9 Phase 9.3 - 2026-07-15

- 新增 2 个只读 decision objects，完整包含 action/horizon/status/confidence/thesis/catalysts/evidence/counter-evidence/invalidation/risks/portfolio effect/model versions/source IDs/human review required。
- 实现 accepted/rejected/deferred/invalidated 四种人工复核结果与 SHA-256 链式 append-only events；accepted 只记录 review，不生成订单或交易，自动交易与执行能力均为 false。
- 正式 Shell 接入决策评审、反证/失效条件与复核 note 持久化；reload 后 metadata/event chain 保持一致，浏览器 `16/16`、外部请求 0。
- HTML/PDF/CSV/Markdown 由同一 immutable report snapshot 生成，四格式 hash 与 manifest 可重建；A4 PDF 无脚本/加密，实体栅格目视无裁切、重叠或黑块。
- Stage 9 Python target `25/25`、release identity `10/10`、selected upstream `68/68`、Node `3/3`；model/formula/parameter 值与 Phase 9.2 analysis pack 未变。
- Phase 9.3=`candidate_pass`，Stage 9 phase tasks=`12/12 candidate_complete`，v0.2.5=`120/156 (76.92%)`；whole-stage review/user acceptance 仍未开始，未进入 Stage 10。
- 未使用 Finder/LaunchServices/GUI，未读写数据库/真实财务行，无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 9 Phase 9.2 - 2026-07-15

- 新增 source-bound 分析构建器与 immutable snapshot：5 份财务报告、6 条公式下钻、4 组敏感性、1 张模型限制/反证卡和 7 个来源复核入口。
- 正式 Shell 接入 Phase 9.2 UI contract；保留本机私有 Stage 5 金额卡时不覆盖金额，公开静态/证据运行只显示 blocked/partial 状态与复核入口。
- net worth/cash/investment 因余额、负债、持仓、价格、FX 或 lineage 缺失保持 blocked；consumption/cashflow 只展示 8,815 条来源覆盖与非金额窗口 impact。
- FORM15/19 继承真实快照验证；FORM16/17/18 继续 blocked，FORM20 structure-only；historical/OOS 缺 ground truth 继续 blocked。未修改任何 model/formula/parameter 值。
- 分析 pack 绑定 Phase 9.1 base manifest 与 data/read-model/formula/parameter hashes；pack、报告状态、公式或敏感性篡改均 fail closed。
- Phase target `10/10`、Stage 9 schema/release identity `27/27`、selected upstream `68/68`、Node contracts pass；正式 loopback browser `11/11`，外网请求 0，公开金额 0。
- Phase 9.2=`candidate_pass`，Stage 9=`8/12 in_progress`，v0.2.5=`116/156 (74.36%)`；Phase 9.3 与 whole-stage review 未开始。
- 未使用 Finder/LaunchServices/GUI，未读写数据库/真实财务行，无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 9 Phase 9.1 - 2026-07-15

- 新增严格 report snapshot schema、complete/partial/blocked completeness rules 与 immutable six-report manifest；保留 Task Pack required fields 并增加 coverage、dependency、gap、review route 和 snapshot hash。
- data quality 在任意依赖状态都可生成；当前 complete。consumption/cashflow 仅 partial source-coverage，net worth/cash/investment blocked 且不输出财务结论。
- 绑定 Stage 2 source manifest、Stage 4 read-model artifact、Stage 7 accepted workflow、当前 formula registry 与 parameter catalog；六类报告共享同一组 data/read_model/formula/parameter hashes。
- 当前 aggregate truth 为 7 sources、8815 transaction records、1571 operational events、11 metrics、lineage complete=0/missing=1571；financial values emitted=0。
- 新增 snapshot/manifest/hash/status/blocked-conclusion/duplicate tamper fail-closed 测试与可重建 Evidence Pack。
- Phase 9.1=`candidate_pass`，Stage 9=`4/12 in_progress`，v0.2.5=`112/156 (71.79%)`；Phase 9.2/9.3 和 whole-stage review 未开始。
- 未读 raw rows/数据库，未改模型/公式/参数值；未使用 Finder/LaunchServices/GUI，无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 8 Whole-stage Review - 2026-07-15

- 产品整改关闭 expected-archetype 自证、title-only workspace clone、180ms timer 假成功、持仓删除缺确认、24px link、timeline 任意标签持久化、旧 Phase 截图与重复 secondary route。
- 当前内容正式 Shell 覆盖 10 核心 + 10 不同二级路由、desktop/mobile 40 PNG；20 唯一路由/3646 文本样本的 WCAG 2.2 AA、键盘、Chrome CDP AX、44px target、错误预防与 reduced-motion 门禁通过。
- Phase 8.1/8.2/8.3 immutable commits 与全部历史 artifact hashes 已绑定；三份 TaskPack evidence 以 whole-review normalized copies 补齐，原提交不改写。Phase 8.2 `allowed_files_obeyed=false` 与站立授权 scope override 明确保留。
- axe-core 不可用，`axe_results.json` 为 `not_run` 且不声明 axe pass；使用 explicit deterministic WCAG/CDP AX substitute。
- 初审 `C4/I14/M2`，整改后同一 frozen overlay 三方复审 `C0/I0/M0`。Stage 8=`accepted_for_transition`；Stage 9 entry authorized but `not_started`，进度保持 `108/156 (69.23%)`。
- finalizer 新增严格三命令集合、严格三位唯一 reviewer 与双 manifest 绑定；`reviewed_evidence_overlay.json` 内容哈希冻结全部 pre-review evidence，空命令、重复/额外 reviewer 或 evidence 篡改均 fail closed。
- release frontend=`0e3da07efc9b569b00e4182d445da1d12cd2cee0e505fd7f913fb74016dd01ca`、backend=`499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`；未改模型/公式/参数值，未加载财务数据。
- 本整阶段未使用 Finder、LaunchServices 或 GUI；历史 Phase 8.3 的一次意外 `lsregister -dump` 如实保留。无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 8 Phase 8.3 - 2026-07-15

- 新增 route announcer、键盘路由 heading focus、main/heading 语义关联、status/alert live region、3px visible focus、44px 控件目标和 forced-colors 降级。
- 导入确认在真实 preview-ready 前保持 disabled；持仓保存/重置、设置保存/重置与导入确认共 5 个财务/数据控制绑定可解析错误预防描述。
- 新增 Playwright/CDP Phase 8.3 harness：10 核心 + 10 重点二级路由、3776 文本样本的 WCAG 2.2 AA 确定性审计为零阻断；键盘、AX tree、隐私与 loopback 网络门禁全绿。
- 修复旧 v0.2.1 暗色反馈卡样式串入亮色正式 Shell 的真实对比度问题；明确本地无 axe-core 且不伪造 axe pass。
- 10 页面 × desktop/mobile 共 20 张 PNG 与 Phase 8.1 基线回归通过，最大 diff `7.8533% <= 12%`；frontend sources `20/20`，frontend hash 更新，backend hash 不变。
- Phase 8.3=`candidate_pass`，Stage 8 phase tasks=`12/12 candidate_complete`，v0.2.5=`108/156 (69.23%)`；该 Phase 当时整阶段独立审查和用户确认尚未开始。未使用 Finder/GUI；收口回归曾意外启动一次 `lsregister -dump` 并立即中止。未读写财务数据/数据库/模型/公式/参数，未 push/install。

## v0.2.5 Stage 8 Phase 8.2 - 2026-07-15

- 新增 100/300/1000/10000ms 真实反馈预算、220ms 状态动效上限、View Transition 渐进增强和 prefers-reduced-motion 零时长降级；动效只使用 transform/opacity，不阻塞交互或隐藏错误。
- 触觉与声音改为双默认关闭、显式 opt-in、user activation 和 capability gate；支持场景实测 vibration，不支持场景静默返回 visual_only。
- 新增 session 级后台任务时间线；queued/running/blocked/succeeded/failed/cancelled 状态可跨 canonical route 保留，只有真实 completedUnits/totalUnits 才显示 progress。
- 缓存刷新改为等待真实本机 API Promise，300ms 才显示 skeleton；settle 后取消所有阶段/durable timer。official Streamlit candidate 改为动态内联 canonical index 的全部 19 个前端来源。
- Phase 8.2 专项 `7/7`、真实浏览器 `17/17`、Phase 8.1/旧反馈兼容 `16/16`、official candidate/release/Stage 7 兼容 `56/56`；trace 私有项 0；最终 frontend hash=`33ef94e054dfc45bda699a5c44dee209868816eb27e107c3b73a3dae80e7be98`。
- Phase 8.2=`candidate_pass`，Stage 8=`8/12 in_progress`，v0.2.5=`104/156 (66.67%)`；Phase 8.3 与 whole-stage review 未开始。未使用 Finder/LaunchServices/GUI 文件操作，未读写财务数据/数据库/模型/公式/参数，未 push/install。

## v0.2.5 Stage 8 Phase 8.1 - 2026-07-15

- 正式 Shell 默认切换为暖白/浅灰亮色设计系统，补齐颜色、间距、字体、圆角、阴影、焦点、状态、图表、target 与 z-index token；强制 OS dark 时产品仍计算为 light。
- 10 个 canonical 一级页面分别绑定 status board、balance sheet、review table、portfolio analytics、spending flow、data pipeline、decision inbox、report library、research workspace 与 control center，不新增第二套路由事实源。
- 图表明确公开 empty/error/stale/ready 状态及 ARIA 文本；empty/error 隐藏 canvas，不生成假曲线。desktop/compact/mobile/compact-mobile 均为正式布局，不展示手机样机。
- 当前 worktree 的 10 路由 × desktop/mobile 共 20/20 浏览器视口通过；console/page/HTTP/external-request errors 均为 0，20 张 PNG 解码通过，sanitized trace 不含私有值、运行 token 或绝对本地路径。
- Phase 8.1=`candidate_pass`，Stage 8=`4/12 in_progress`，v0.2.5=`100/156 (64.10%)`；Phase 8.2/8.3 与 whole-stage review 未开始。未使用 Finder/LaunchServices/GUI 文件操作，未读取或修改财务数据，未改数据库/模型/公式/参数，未 push/install，production/final acceptance=false。

## v0.2.5 Stage 7 Whole-stage Review - 2026-07-15

- 绑定 Phase 7.1/7.2/7.3 三笔线性提交与 12/12 tasks，并以 current-worktree frozen overlay 复验上传/账本、持仓/设置重启、参数/互联/指标下钻三条正式 Shell 工作流。
- 完成 API auth/CORS/size、XSS/CSV/ZIP/input、SQLite 并发/幂等/迁移/raw cleanup、canonical read model、trace privacy 与 fail-closed finalizer 整改。
- 当前 operational economic-event adapter 不存在，11 个 metrics 与 event lineage 保持 blocked/null；immutable Phase 7.3 的历史聚合证据不再作为当前运行时金融事实。
- 三类独立复审的初始治理口径为 `C0/I14/M4`，整改后为 `C0/I0/M0`；最终 verification、reviewer text、artifact index 与 human acceptance 均内容绑定。
- Stage 7=`accepted_for_transition`，只授权 Stage 8 entry；Stage 8 仍 `not_started`。未使用 Finder/LaunchServices/GUI 文件操作，无外网、push、install 或 production/final acceptance。

## v0.2.5 Stage 7 Phase 7.3 - 2026-07-15

- 正式 Shell 新增参数中心、Interconnection Map 与指标下钻三条 canonical 二级路由；15 个中文参数域、96 参数和 20 公式均显示 registry hash，不使用 sidecar HTML。
- 当前互联图以 7 个可点击节点/6 条描述性边展示 `8,815 source = 6,879 complete lineage + 1,936 review + 0 silent drop`，不持久化私有行或财务值。
- 11 个指标显示 data range、formula/parameter/data/read-model hash、来源、经济事件 lineage 与中文阻断；not-ready 保持 null，false-zero=0。
- 修复正式 Streamlit inline asset 闭包与 History route/query 分离，深链 reload 可恢复 `domain/node/metric`；release schema 更新为 `PFIV025Stage7MetricLineageV1`。
- Python focused/compatibility 44 passed、Node 29 passed、正式 Shell 21/21；sanitized trace 复扫绝对路径/numeric value 均 0。Phase 7.3=`candidate_pass`，Stage 7 phase tasks=`12/12 candidate_complete`，whole-stage review 未开始；未使用 Finder、无外网、未 push/install。

## v0.2.5 Stage 7 Phase 7.2 - 2026-07-15

- 新增 revisioned 持仓 create/update/soft-delete API 与 additive SQLite migration；一个 change-set 在单一 transaction 内提交，request id、projection hash 与行 revision 防重复和并发覆盖。
- 已有 SQLite 首次迁移前使用 Online Backup，初始化以进程锁串行；持仓和设置审计事件、FK 与 integrity 均有独立证据。
- 正式 Shell 保存后只同步 holding count、估值依赖缺失状态与 projection hash；无真实持仓/价格/FX 时金额保持 null，非财务 contract sentinel 不计入真实财务验收。
- 设置偏好改由正式 API/SQLite 保存和恢复默认，反馈开关只在设置页显示；正式结果不依赖 localStorage/sessionStorage/IndexedDB。
- cached Playwright/local Chrome 首轮 13/13、浏览器重开与 Runtime API 重启轮 12/12；Phase 7.2=`candidate_pass`，v0.2.5=`92/156 (58.97%)`。未使用 Finder、无外网、未 push/install，Phase 7.3 与 Stage 7 whole-stage review 未开始。

## v0.2.5 Stage 7 Phase 7.1 - 2026-07-15

- 正式 Shell 接入真实 CSV/ZIP byte upload、SHA-256/source/parser 识别、实际解析预览、字段映射与中文失败状态；preview 只 staging，不写统一账本。
- 新增 additive SQLite import/review/ledger migration 与本机 runtime API；确认使用原子 transaction，待复核决定持久化且可撤销。
- 重复上传按 batch fingerprint 幂等复用；已确认批次可补偿回滚、从私有 raw store 重试并再确认；失败解析不生成假预览。
- 真实只读源经 `/tmp` 副本在正式 Shell 验证 1571 条流水、74 条待复核；canonical hash 不变，tracked evidence 只保留 aggregate/hash/date 和脱敏截图。
- Phase 7.1=`candidate_pass`，v0.2.5=`88/156 (56.41%)`；未使用 Finder、无外网、未 push/install，Phase 7.2/7.3 与 Stage 7 whole-stage review 未开始。

## v0.2.5 Stage 6 Whole-stage Review - 2026-07-15

- 绑定 Phase 6.1/6.2/6.3 三笔线性提交与 immutable evidence hash，复核 12/12 tasks、6 项 acceptance criteria、4 项 safety stop 和 Stage Pass Gate。
- 初审 `C0/I4/M1`：缺 whole-stage binding/current-HEAD 联审、三份 evidence schema、final index/human acceptance 与 legacy diagnostic disposition；整改后复审 `C0/I0/M0`。
- cached Playwright + 本机 Chrome 对当前 HEAD 正式 Shell 完成 14/14 checks：10 主入口、10 个代表二级页、7 aliases、History/Reload/Invalid/keyboard/AX/no-JS 全通过。
- 三份 Phase evidence 当前副本符合 Task Pack schema；原 Phase commit evidence 保持不可变并由 hash 绑定。用户阶段授权与 final evidence index SHA-256 绑定。
- Stage 6=`accepted_for_transition`；Stage 7 entry authorized but not_started。未使用 Finder、外部网络、真实财务数据或数据库，未 push/install，production/final acceptance=false。

## v0.2.5 Stage 6 Phase 6.3 - 2026-07-15

- 将正式 HTTP Shell 路由从 hash canonical 收敛为 actual pathname；`file:`/`about:srcdoc` 只保留 hash compatibility，不新增第二份 route state。
- History state 记录 canonical route、workspace、scroll 与来源；back/forward、scroll restoration、直接深链、CDP reload 和重复点击 history delta=0 全部通过。
- 新增可行动 invalid-route 页面：保留请求 URL，显示独立 alert、请求地址与“返回首页总览”，不静默伪装成首页。
- 使用缓存 Playwright、本机 Chrome 和 `Accessibility.getFullAXTree` 验证键盘进入、heading focus 及 AX/DOM 10 个一级入口；console/page/http errors=0。
- Phase 6.3=`candidate_pass`，Stage 6 phase tasks=`12/12 candidate_complete`，但 whole-stage review/user acceptance 未开始。未使用 Finder、外部网络、真实财务数据、数据库、push 或 App install。

## v0.2.5 Stage 6 Phase 6.2 - 2026-07-15

- 新增 45 个独立二级页面合同：每页具有 canonical path、job-to-be-done、唯一 data object、primary action、layout/signature 与 loading/empty/error 状态。
- 现行二级路由全部收敛为 path route；45 个旧 `?tab=` route 仅作兼容 redirect，策略实验室唯一 canonical route 不变。
- Shell 新增页面级 title、breadcrumb、heading focus 与 per-canonical-route scroll restoration；保留既有差异化内容区块但不再以旧 query route 作为页面身份。
- no-JS fallback 扩展为 10 个一级入口与 45 个可读二级页面目录；关闭脚本时不显示无法完成的 release gate。
- formal desktop/mobile/no-JS 浏览器验证通过，截图已人工复核；Phase 6.2=`candidate_pass`，Stage 6=`8/12 in_progress`。未使用 Finder、外部网络、数据库、真实财务数据、push 或 App install。

## v0.2.5 Stage 6 Phase 6.1 - 2026-07-15

- 新增 v0.2.5 navigation contract：一级入口固定为总览、账户、账本、投资、消费、数据、复核、报告、市场与研究、设置，顺序与 canonical routes 对齐 Roadmap Appendix A。
- 将 desktop/mobile 合并为同一 10 节点 responsive DOM，并移除额外 bottom-nav primary stack；no-JS fallback 也只暴露 10 个 canonical primary routes。
- 固定 7 个历史 alias redirect；alias 不进入一级导航或 a11y，策略实验室只保留 `/market-research/strategy-lab` 作为 canonical route。
- 隔离本地 Chrome 在 desktop/mobile 完成全入口点击、alias normalization、single-active 和 release identity ready 验证；tracked screenshot/trace 已脱敏。
- Phase 6.1 为 `candidate_pass`，Stage 6=`4/12 in_progress`；Phase 6.2/6.3 与 whole-stage review 未开始。未使用 Finder、外部网络、数据库、真实财务数据、push 或 App install。

## v0.2.5 Stage 5 Whole-stage Review - 2026-07-15

- 独立初审 `C1/I4/M1`：确认 Phase evidence 尚未整阶段绑定、真实四指标未挂入 formal Web/report、browser/a11y/隐私分层与 schema acceptance 缺失，并记录 Roadmap Allowed Files 与实际 UI Acceptance 的最小范围例外。
- 新增私有运行时四指标 payload，并绑定正式 homepage、consumption_page、report；三页使用同一 payload hash，真实金额只在内存/临时页面验证，tracked screenshot、trace、a11y 与 JSON 全部脱敏。
- 新增 Phase commit binding、headless formal-shell browser 验证、release identity ready/冲突遮罩隐藏断言、final evidence index 与 human acceptance；复审为 `C0/I0/M0`。
- Stage 5 结果为 `accepted_for_transition / pass_with_explicit_blocked_models`；`FORM-PFI-016/017/018/020` 的缺失验证残余继续 blocked。未使用 Finder、未访问外部网络、未 push/install、未开始 Stage 6。

## v0.2.5 Stage 5 Phase 5.3 - 2026-07-15

- 新增 immutable Git blob 真实快照只读验证：`8,815 = 6,879 published + 1,936 review + 0 silent drop`，源对象前后 identity 不变，数据库未读取或修改。
- `FORM-PFI-015/019` 通过真实 invariants、permutation、exact-duplicate、positive-scaling、date-translation 与七窗口 boundary sensitivity；公开证据只包含计数、状态和 hash。
- 新增 model validation card：`FORM-PFI-016/017/018` 按真实依赖缺失 fail closed，`FORM-PFI-020` 为 structure-only，classification accuracy 与 historical/OOS 因缺 ground truth/coverage blocked。
- homepage、consumption_page、report 三个 consumer contract 表面 payload hash 一致；真实 UI/report renderer binding 显式保持 false/open，留给独立 Stage 5 whole-stage review。
- 本 Phase 未修改 model/formula/parameter 值；Phase 5.3 为 `candidate_pass`，Stage 5 phase tasks `12/12 candidate_complete`，整阶段尚未审查或接受。未使用 Finder、network、push 或 App install。

## v0.2.5 Stage 5 Phase 5.2 - 2026-07-15

- 新增 source/economic-event 去重的 gross activity、living consumption、investment funding、investment-domain allocation 四口径；只允许显式 linked refund 冲销，投资活动不冒充净资产损失。
- 新增净资产、现金和余额滚动 exact Decimal invariants；缺依赖或 discrepancy 非零时 fail closed/null，不发布假零。
- 新增 realized/unrealized/total return、显式成本、fee/tax/FX/idle-cash drag 和 date-aware XIRR；零分母、多根、不可括根与不收敛均阻断。
- 现金流窗口固定为 `7/21/30/60/90/180/360`，内部转账独立；延续 L1/L2、恰好一个 primary category、default/custom tag、历史与 all/any view 合同。
- 登记 `MOD-PFI-010`、`FORM-PFI-015..020`、`PARAM-PFI-081..092`，五载体参数一致性纳入测试；总数为 `10/20/92`。
- Phase 5.2 为 `candidate_pass`；真实数据 invariant/metamorphic/sensitivity/model validation 与真实 Web/UI/report binding 未执行，留给 Phase 5.3。未读取/修改真实财务行或数据库，未使用 Finder、network、push 或 App install。

## v0.2.5 Stage 5 Phase 5.1 - 2026-07-15

- 新增 `FORM-PFI-001..014` machine-readable registry：每个版本具备中文定义、输入/输出/单位/参数/边界/依赖/test/effective_from 与可重建 hash；active 同版本内容禁止原地改写。
- 新增 `FORM-PFI-014` 精确 CNY/AUD 单位合同：基础币种 CNY，`AUD/CNY` 固定为 `1 AUD = X CNY`，仅以 `CNY/AUD` rate 相乘；`4.81` 只是方向测试示例，生产默认为 null。
- 公式 JSON、JSON-compatible parameter YAML、Python runtime、application UI payload 与 rendered 模型参数文件五载体一致性为零冲突。
- v0.2.2 的 100 分权重和阈值 70 只保留为记录分类置信度；来源覆盖、对账覆盖、估值覆盖、模型验证、报告完整度独立，`overall_confidence` 被拒绝。
- Phase 5.1 为 `candidate_pass`；Phase 5.2/5.3 与 Stage 5 whole-stage review 未开始。未读取/修改真实财务行或数据库，未使用 Finder、network、push 或 App install。

## v0.2.5 Stage 4 Whole-stage Review - 2026-07-14

- 绑定 Phase 4.1/4.2/4.3 实际 commits 与 evidence SHA-256，复核 `12/12 tasks`、`6/6 Acceptance Criteria`、4 个安全 stop conditions 与 Pass Gate。
- 初审 `C0/I5/M1` 全部整改，复审 `C0/I0/M0`；新增只读 verifier、最终 evidence index 与 schema-valid 阶段验收。
- 本地 Chrome headless 生成 v0.2.5 screenshot/trace/a11y：七个指标均 `not_loaded/null`、五个表面同 hash、false-zero=0；未使用 Finder。
- README/HANDOFF 收敛到 v0.2.5 当前真值。Stage 4=`accepted_for_transition`，Stage 5 entry 已授权但未开始；未 push 或安装 App。

## v0.2.5 Stage 4 Phase 4.3 - 2026-07-14

- 新增 strict Metric State schema 与 Python/JavaScript fail-closed validator：13 个状态完整登记；所有非 ready 状态必须 `value=null`，`ready` 零被拒绝，`confirmed_zero` 只有完整 source/coverage/as_of/hash 证据才允许。
- 新增统一 read model：Stage 2 source manifest、Stage 3 event hash、Stage 4 account/investment hash 与公式/参数合同共同生成 deterministic dependency/read-model hash；page identity 与 observation time 不进入 identity。
- `/api/read-model-status`、homepage、accounts、investment、consumption、report 绑定同一 snapshot；当前七个核心指标全部 `not_loaded/null`，financial values emitted=0，未将 8,815 条交易计数误写成余额、持仓、估值或消费金额。
- 同步 runtime/frontend release source hashes，但不改变 build id/version，不安装 App，不执行网络或 push。
- Phase 4.3 为 `candidate_pass`，Stage 4 三个 Phase 共 `12/12 candidate tasks`；Stage 4 仍为 `in_progress`，whole-stage review、整改、复审与 transition acceptance 必须下一轮独立执行，Stage 5 未开始。

## v0.2.5 Stage 4 Phase 4.2 - 2026-07-14

- 新增持仓 snapshot Draft 2020-12 schema 与 typed Decimal domain contract；quantity、原币种、source hash、quantity_as_of、成本方法及显式交易关联状态均可追溯。
- 成本基础明确为 `acquisition_cost_ex_fees + capitalized_fee_total`；method 必须显式选择已注册策略，缺失或未知时禁止计算。
- 新增 PIT 价格/FX 估值：snapshot 不得晚于 `valuation_as_of`，非 CNY 必须绑定 `BASE_TO_CNY`，CNY 使用恒等汇率 1；全程 exact Decimal、不虚构 rounding/staleness 参数。
- 当前 `SRC-HOLDINGS`、`SRC-MARKET-PRICES`、`SRC-FX-SNAPSHOT` 均为 `not_loaded`；投资市值、成本基础、未实现损益 3/3 metrics 保持 `value=null`，未按交易推断持仓、未猜成本、未提升 legacy FX。
- 登记 `MOD-PFI-007`、`FORM-PFI-009..010`、`PARAM-PFI-061..067`；contract test 数值只验证公式，不构成真实财务或 production acceptance。
- Phase 4.2 为 `candidate_pass`，Stage 4 为 `in_progress`；Phase 4.3 与 Stage 4 whole-stage review 均未开始。
- 未读取或修改真实财务行/数据库，未使用 Finder、network、financial fixture、push 或 App install。

## v0.2.5 Stage 4 Phase 4.1 - 2026-07-14

- 新增账户/负债 opening/closing snapshot Draft 2020-12 schema 与 typed Decimal domain contract；source、coverage、as_of、record count 和 content hash 均为必填 lineage。
- 新增精确现金对账：`expected closing = opening + confirmed net flows + adjustments`；tolerance 为 Decimal 0，任何差异返回 `reconciliation_failed` 且 `value=null`。
- 当前真实 aggregate source manifest 中 `SRC-ACCOUNT-BALANCES` 与 `SRC-LIABILITIES` 均为 `not_loaded`；账户资产、现金、负债 3/3 metrics 保持 `value=null`，交易流水不作为余额证据。
- 账户与首页使用同一 read-model snapshot 和 hash；本 Phase 不扩展到持仓/价格/FX 估值或五页面整体一致性。
- 登记 `MOD-PFI-006`、`FORM-PFI-008`、`PARAM-PFI-058..060`；contract test 数值只验证公式，不构成真实财务或 production acceptance。
- Phase 4.1 为 `candidate_pass`，Stage 4 为 `in_progress`；Phase 4.2/4.3 与 Stage 4 whole-stage review 均未开始。
- 未读取或修改真实财务行/数据库，未使用 Finder、network、financial fixture、push 或 App install。

## v0.2.5 Stage 3 Whole-Stage Review - 2026-07-14

- 独立复核 Phase 3.1/3.2/3.3 的 immutable commit/evidence chain，覆盖 `12/12` tasks、`6/6` Acceptance Criteria、`4/4` Stop Conditions 与 Stage Pass Gate。
- 初审 `C0/I3/M1`：缺 whole-review verifier/Phase binding、final gate index、真实快照残余与 human acceptance binding、canonical governance closeout；四项全部整改，三路复审 `C0/I0/M0`。
- 真实快照保持 `8,815 = 6,879 published + 1,936 review + 0 silent drop`；第二次导入发布 0，collision 0，发布 lineage `6,879/6,879` 完整，五页共享一个 read_model_hash。
- 明确保留残余：1,250 条未确认 transfer 与 249 条未确认 refund 只 fail-closed 到 review queue，不冒充已确认链路；Stage Pass 精确结果为 `pass_with_review_queue`。
- 用户“最终验收前全部同意授权”只绑定 Stage 3 技术范围与上述残余；Stage 3 更新为 `accepted_for_transition`，Stage 4 entry authorized 但 Stage 4 未开始。
- 未修改 model/formula/parameter、真实数据或数据库；未使用 Finder，未执行 network、push、App install、production acceptance 或 final human acceptance。

## v0.2.5 Stage 3 Phase 3.3 - 2026-07-14

- 以 immutable Git-object snapshot 只读解析 8,815 条真实记录；6,879 条形成 lineage-complete Ledger candidates，1,936 条 fail-closed 进入 review queue，silent drop 为 0。
- 同一 blob 重复导入：第一次发布 6,879，第二次发布 0、识别重复 6,879、idempotency collision 0；source identity 前后不变。
- 1,250 条缺显式 link/account-role 的转账与 249 条缺 refund offset 的退款均禁止发布；另有 406 条 upstream review 与 31 条零金额记录进入复核。
- Interconnection Matrix 覆盖 8/8 主链路和 10 类事件 flags；每个 economic event 在同一 metric 最多计数一次，五个页面共享一个 read_model_hash。
- 登记 `MOD-PFI-005`、`FORM-PFI-006..007`、`PARAM-PFI-048..057`；来源日期粒度规范化不声明真实交易时刻精度。
- Phase 3.3 为 `candidate_pass`，Stage 3 三个 Phase 共 `12/12 candidate`；Stage 3 整阶段独立审查、整改、复审与明确验收仍未开始，未进入 Stage 4。
- 未修改真实数据或数据库，未使用 financial fixture、来源名称推断、金额/时间近似挂链、Finder、network、push 或 App install。

## v0.2.5 Stage 3 Phase 3.2 - 2026-07-14

- 新增四份 Draft 2020-12 schema，建立金额/币种/方向/四类时间完整的 NormalizedTransaction、可解释 InterconnectionGroup、EconomicEvent 和 lineage-complete LedgerEvent。
- 新增 explicit-link-only grouping：只按显式 link reference 精确归组，无 link 时保持 singleton；金额/时间/source-name inference 全部禁用。
- 新增 10 类 versioned event impact policy，覆盖自有转账、信用卡还款、退款、投资入金、基金/黄金申购、投资买卖、收入与生活消费；未知类型禁止发布。
- Ledger 保留逐笔 posting，不跨币种聚合；canonical JSON SHA-256 idempotency key 对输入顺序稳定。真实重复导入、对账与 persistence 留给 Phase 3.3。
- 登记 `MOD-PFI-004`、`FORM-PFI-004..005`、`PARAM-PFI-036..047`，并形成 schema inventory、event matrix、脱敏 lineage、privacy/evidence pack。
- Phase 3.2 为 `candidate_pass`，Stage 3 仍 `in_progress`；Phase 3.3 与整阶段验收未开始。
- 未读取或修改真实财务数据/数据库，contract unit values 不作为 production acceptance；未使用 Finder、network、push 或 App install。

## v0.2.5 Stage 3 Phase 3.1 - 2026-07-14

- 新增四份 Draft 2020-12 schema，建立 extensible Source Profile、AccountRoleAssignment、ParserProvenance 与 unknown-role review item；source type/capability 不枚举来源名称。
- 新增纯 domain/application 合同：账户支持多角色及重叠 inclusive effective ranges；Source Profile 强制绑定 parser id/version 与 sha256 source hash。
- 新增 fail-closed role routing：只有显式 role registry 成员可发布，未知角色进入 `review_required` 且 `publish_allowed=false`，不从来源名称推断。
- 登记 `MOD-PFI-003`、`FORM-PFI-003`、`PARAM-PFI-028..035`，并形成 schema inventory、review queue summary、privacy/evidence pack。
- Phase 3.1 为 `candidate_pass`，Stage 3 仍 `in_progress`；Phase 3.2/3.3 与整阶段验收未开始。
- 未读取或修改真实财务数据/数据库，未使用 Finder、network、financial fixture fallback、push 或 App install。

## v0.2.5 Stage 2 Whole-Stage Review - 2026-07-14

- 独立复核 Phase 2.1/2.2/2.3 的 immutable commit/evidence chain，覆盖 `12/12` tasks、`6/6` Acceptance Criteria、`4/4` Stop Conditions 与 Stage Pass Gate。
- 初审 `C0/I3/M1`：缺 whole-review verifier/Evidence、最终 hash index、Stage 2 human acceptance binding 与当前 source disposition；四项全部整改，三路复审 `C0/I0/M0`。
- 用户“最终验收前全部同意授权”被具体绑定为 Stage 2 canonical root、8815-record transaction scope、五个 blocked/null 指标、production FX not_loaded/offline 与 read-only no-fake 边界；不扩展为 production/final acceptance。
- Stage 2 状态更新为 `accepted_for_transition`；Stage 3 entry authorized，但 Stage 3 尚未开始。
- residual risks 保留：private root/SQLite 权限观察为 0755/0644，production FX/余额/负债/持仓/价格 not_loaded，七个时间字段 not_verified，性能 observation 不是 SLA。
- 未修改真实数据/DB、model/formula/parameter；未使用 Finder、未 push、未安装 App。

## v0.2.5 Stage 2 Phase 2.3 - 2026-07-14

- 新增 commit-bound immutable Git-object transaction snapshot 与 operational SQLite 临时隔离副本：临时目录 `0700`、副本 `0600`，只读探测后清理，source identity/hash 前后不变。
- 以真实 8815-record snapshot 完成三次全量读/解析基线：耗时 min/median/max `117.636/123.182/127.156 ms`，peak Python allocation `14491986/14491986/14492499 bytes`；仅为观测值，不声明生产 SLA。
- 新增结构化 no-fake audit、固定十文件 privacy scan 与 TaskPack-compatible Evidence；source 缺失 fail closed，禁止 financial fixture fallback，公开证据不含财务行值、账户标识、SQLite 表名或绝对私有路径。
- 三个 Phase 均为 candidate pass，Stage 2 Evidence 已准备进入独立 whole-stage review；Stage 2 仍 `in_progress`，用户接受 pending，Stage 3 未授权。
- 本 Phase 未改变 model/formula/parameter、真实财务数据或数据库；未执行 Finder、network、push、App install、production acceptance 或 final human acceptance。

## v0.2.5 Stage 2 Phase 2.2 - 2026-07-14

- 新增八字段 temporal contract 与 TaskPack 同源 schema；timezone-aware RFC3339 归一化，缺失字段保持 `not_verified`。
- 新增 Sydney local 06:00 effective FX business-day 规则，覆盖周末、显式 source-closed dates、DST 与 fail-closed 输入。
- 新增 AUD/CNY snapshot identity/hash/current/stale/blocked contract；生产 source 仍 `not_loaded`，rate/hash/id 保持 null，旧 snapshot 仅作 reference。
- 新增 ordinary-runtime AST network audit，Phase 2.2 policy module 的 network import/call 均为 0；未执行 FX refresh、source/DB mutation、Finder、push 或 App install。
- 登记独立规则模型 `MOD-PFI-002`、公式 `FORM-PFI-002` 与参数 `PARAM-PFI-024..027`。Phase 2.2 candidate pass；Stage 2 仍 in_progress，下一任务 `S2-P3-T1`。

## v0.2.5 Stage 1 Whole-Stage Review Candidate - 2026-07-13

- 复核 Phase 1.1 release identity、Phase 1.2 cache governance 与 Phase 1.3 isolated App acceptance；除既有 manifest/trace/live-control/AX 修复外，C12 关闭 candidate legacy downgrade、isolated-empty 历史报告/缓存 FX/伪零显示及单页证据缺口，C13/C14 修正真实 AX 命名规则，C15/C16 修正 identity panel 截图目标，C17 提升 top-bar stacking context，C18 在 snapshot 后关闭 panel 以隔离 10 路由交互状态，C19 让详情面板向视口内展开并使用完整壳层截图，C20 将候选检查、进程监听与 evidence 字段统一为 LaunchServices 语义，最终 remediation content commit 为 `04390bcf17c18de107eb2f1b4ce051c83638f98c`。
- whole-stage remediation 改为真实 production `streamlit_app.py`、12 文件 backend identity、14 文件 frontend identity、same-process read-only runtime API、隔离空数据与精确三成员/三 listener 证据。
- 浏览器证据新增 official shell、fresh profile、真实 `pfi_legacy=1` 尝试、10 个主路由逐页 identity/DOM/live-control/privacy、reload/cache-clear/back-forward、真实 iframe AX tree、完整可展开 release identity、两张 PNG 与 release/cache/read-model API 的交叉验证。
- 初始 `C1/I3/M0`、verifier `C2/I4/M2`、content re-review `C1/I2/M0` 与 C4 live-control re-review `C1/I0/M0` 均已整改；tracked 状态保持 `candidate_pass_pending_postcommit_attestation`，只有 matching external attestation 才激活 Stage 1 `accepted_for_transition`。
- 本轮未 push、未安装 canonical App、未进入 Stage 2、未读取或修改财务数据/SQLite，模型、公式与参数运行行为未改变；Stage 12 最终人工验收仍保留。

## v0.2.5 Stage 0 Phase 0.2 Active Contract Candidate - 2026-07-11

- 新增四个可审计 core contracts：`pfi_v025_active_requirements.json`、`history_deprecation.md`、`scope_boundary.md`、`run_contract.md`，绑定 canonical Roadmap/Task Pack hashes、唯一 Acceptance 与 one-Phase stop rule。
- 按批准的 exact 20-file override 同步 12 个具名 governance companions；保持 model/formula/parameter/task/acceptance 数量 `1/1/23/10/10`，不新增 canonical delivery task。
- 当前结果仅为 `candidate_pending_postcommit_attestation`；真实 command ledger、原子提交和 external post-commit attestation 未全部完成前，不声明 Phase/Stage/release acceptance。
- 本轮没有 runtime、model/formula/parameter value、真实或私有 data、DB、App、migration、安装、GitHub push 或 Phase 0.3 工作。

## v0.2.4 Final Delivery - 2026-07-11

- Tracked transaction 状态为 `pending_live_verifier`；唯一 push 后 live verifier pass 才解析最终 completion postcondition，且不提交第二个 closeout commit。
- 新增 `ACC-PFI-V024-FINAL-DELIVERY` fail-closed verifier，实时核验 GitHub remote main、tracking ref、local HEAD、clean worktree 与 product direct-parent。
- product commit 冻结为 `17b9f59794740f927c5f531ba1aa334621a832e5`；evidence commit 作为其直接子提交，经当前 package 唯一一次 push 上传。
- installer 使用固定 basename 与 `-Wl,-no_uuid`；三处 app entry 重装后 codesign/binding/dry-run 通过，signed hash 一致，Mach-O code-section hash 与 current-source compile 一致。
- runtime shell 为内联 assets 增加 `data-pfi-source`；只读 current-code browser probe 对 app/localhost 两入口逐 filename 计算真实 inline content SHA-256，结果 `8 pass / 0 fail`，browser errors 为 0。
- app acceptance `29 pass / 0 fail / 2 info`；final-delivery focused `11 passed`、v0.2.3 `200 passed`、v0.2.4 `242 passed`、renderer `0/0`、独立 reviewer `APPROVED`。
- `.venv`、`data`、`reports` metadata hash 安装前后相同；future version、交易密码、券商订单、支付与自动真钱动作均未开始。

## v0.2.4 Overall Re-review - 2026-07-10

- `ACC-PFI-V024-OVERALL-REREVIEW` 本地 gate pass；独立只读复核 `APPROVED`，Critical/Important/Minor 均为零。
- 新增 `ACC-PFI-V024-OVERALL-REREVIEW`，按原 `v0.2.3-repair` Task Pack/Roadmap 复核 Stage 0-9、Phase R1、真实数据链路与最终交付边界。
- 机器审计确认 40/40 evidence unit 四件套存在，84 个 JSON 可解析；历史 upload 与当前最终交付状态已拆分。
- 审查修复后逐项核验 40-unit schema/ID/status、10 个 whole-stage acceptance、非空 evidence、有效 UI PNG、派生人工确认/历史 upload，以及精确 `4/8815/2026-06-03/hash/Git object` 数据合同。
- 验证快照：re-review `12 passed`、v0.2.3 `200 passed`、v0.2.4 `231 passed`、11/11 UI validation、46 PNG decode、Git ref == current HEAD；machine gate pass 但 `product_goal_complete=false`。
- 当前 Phase R1/re-review 变更、app reinstall 与 GitHub/app/local consistency 统一保留到单一 `PFI-V024-FINAL-DELIVERY`；`product goal 未完成`。
- 本轮不执行 GitHub upload、app reinstall、future version 或真实财务数据修改。

## v0.2.4 Post-Overall Consistency Remediation - 2026-07-10

- 完成 `post-overall consistency remediation / Phase R1` 本地 gate：恢复 canonical v0.2.4 closeout history，并由既有 renderer 重新生成三份 owner 入口。
- `stage_v023_read_model.py` 新增默认 tracked `MetaDatabase/PFI` 的只读 Git-tree adapter；长期 sparse PFI worktree 无需展开数据路径即可验证 4 个 raw CSV 与 8815 条 processed 记录。
- 修正 v0.2.3 Stage 7 placeholder 扫描边界：共享 JS 改为验证真实 v0.2.3 report view-model 输出，不再把 v0.2.4 合法样本量标识误判为假数据。
- 验证：focused `33 passed`；v0.2.3 `200 passed`；v0.2.4 `219 passed`；Python、Node、diff、check-render 均通过。
- 本轮未执行 overall re-review、GitHub upload 或 app reinstall；future version 未开始。

## Cloudflare L2 redacted public shell — 2026-07-10

- 新增隔离的 `web/cloudflare-public` 静态产品壳、Workers Static Assets 配置、隐私扫描和兼容性回归。
- 页面只展示定性、脱敏结构；不读取真实账户、组合、交易、broker credentials、私密 reports 或本地数据库。
- build、private scan、响应式浏览器验收和 Wrangler dry-run 已通过；真实部署仍因 Workers 授权阻塞，未填写 live URL。

## v0.2.4 Overall Project Review - 2026-07-02

- 完成 `v0.2.4 overall project review`：以整个 PFI v0.2.4 repair package 为目标复审 Stage 0-9、Stage 8/9 用户验收、整体交付证据和 GitHub main 上传状态。
- Stage 8.3 用户验收已由用户回复 `1` 确认；Stage 9.3 用户验收已由用户回复 `1` 确认；future version 未开始。
- 新增 `PFI/tests/test_v024_overall_project_review.py`、`PFI/docs/pfi_v024/OVERALL_PROJECT_REVIEW.md` 和 `PFI/reports/pfi_v024/overall_project_review/` evidence。
- 本轮不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 9 GitHub Main Upload - 2026-07-02

- 完成 `Stage 9 GitHub main upload gate`：将 Stage 9 Phase 9.1、Phase 9.2、Phase 9.3 和 whole-stage review package 上传到 GitHub main。
- 新增 `PFI/tests/test_v024_stage9_github_upload_contract.py`、`PFI/docs/pfi_v024/STAGE9_GITHUB_MAIN_UPLOAD.md` 和 `PFI/reports/pfi_v024/stage_9/github_main_upload/` evidence。
- 上传 gate 重新验证 Stage 9 upload contract、whole-stage review、Phase 9.1/9.2/9.3 回归、Stage 8 upload 边界、JSON evidence、py_compile、diff 和 changed-files 对账。
- 本轮不进入未来版本，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 9 Whole-Stage Review - 2026-07-02

- 完成 `Stage 9 whole-stage review - 复审并解决暴露问题`：复审 Phase 9.1 回归规则、Phase 9.2 交付冻结和 Phase 9.3 用户确认来源。
- 新增 `PFI/tests/test_v024_stage9_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE9_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_9/whole_stage_review/` evidence。
- 记录用户回复 `1` 作为 Phase 9.3 确认来源；复审发现 3 项均已 fixed。
- 本轮不执行 Stage 9 GitHub main upload，不进入未来版本，不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 9 Phase 9.3 - 2026-07-01

- 完成 `Stage 9 / Phase 9.3 - 用户验收`等待包：生成人工验收清单、reply protocol 和 waiting evidence。
- 新增 `PFI/tests/test_v024_stage9_phase93_user_acceptance.py` 和 `PFI/reports/pfi_v024/stage_9/phase_9_3/` evidence。
- README/HANDOFF 只声明 `waiting for user response`，不写验收通过或最终 closeout 完成。
- 本轮不执行 Stage 9 whole-stage review 或 GitHub main upload，不进入未来版本，不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 9 Phase 9.2 - 2026-07-01

- 完成 `Stage 9 / Phase 9.2 - 交付冻结`候选包：生成最终 evidence index、README 候选状态、未做事项和后续风险。
- 新增 `PFI/tests/test_v024_stage9_phase92_delivery_freeze.py` 和 `PFI/reports/pfi_v024/stage_9/phase_9_2/` evidence。
- README 只声明 `Stage 9 delivery freeze candidate`，明确 waiting for Phase 9.3 user acceptance，不声明最终完成。
- 本轮不执行 Phase 9.3 用户验收、Stage 9 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 9 Phase 9.1 - 2026-07-01

- 完成 `Stage 9 / Phase 9.1 - 回归规则`：建立旧 UI signature、入口堆叠、假零、mock 财务数据回归防线。
- 新增 `PFI/src/pfi_v02/stage_v024_stage9_regression_freeze.py`、`PFI/tests/test_v024_stage9_phase91_regression_guardrails.py`、`PFI/docs/pfi_v024/STAGE9_REGRESSION_FREEZE.md` 和 `PFI/reports/pfi_v024/stage_9/phase_9_1/` evidence。
- Guardrail evaluator 解析桌面/移动正式一级入口均为 10 个，确认旧 alias 未回到同层一级入口，非 ready 指标不显示 `CNY 0.00`，正式财务 runtime 未出现 mock/sample/synthetic/fixture/demo/fake 财务数据。
- 本轮不执行 Phase 9.2 交付冻结、Phase 9.3 用户验收、Stage 9 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 8 GitHub Main Upload - 2026-07-01

- 完成 `Stage 8 GitHub main upload gate`：将 Stage 8 Phase 8.1、Phase 8.2、Phase 8.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/docs/pfi_v024/STAGE8_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage8_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_8/github_main_upload/` evidence。
- 上传 gate 重新验证 Stage 8 upload contract、whole-stage review、Phase 8.1/8.2/8.3 回归、JSON evidence、py_compile、diff 和 changed-files 对账。
- 本轮不执行 Stage 9，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 8 Whole-Stage Review - 2026-07-01

- 完成 `Stage 8 whole-stage review - 复审并解决暴露问题`，复审 Phase 8.1 自动验收、Phase 8.2 截图验收和 Phase 8.3 人工验收确认。
- 新增 `PFI/tests/test_v024_stage8_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE8_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_8/whole_stage_review/` evidence。
- 记录用户回复 `1` 作为 Phase 8.3 人工验收通过来源；Phase 8.1/8.2/8.3 证据被绑定到同一个整阶段 pass gate。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 8.3 pending、缺少整阶段命令/证据汇总。
- 本轮不执行 GitHub main upload，不进入 Stage 9，不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 8 Phase 8.3 - 2026-07-01

- 完成 `Stage 8 / Phase 8.3 - 人工验收`准备包：新增 `manual_acceptance.md`、`defects.md` 和 pending-user-confirmation evidence。
- 新增 `PFI/tests/test_v024_stage8_phase83_manual_acceptance.py`，补齐 Phase 8.3 当前 phase 合同、人工验收清单、开放项定位和 no-auto-next-stage 边界。
- 人工验收清单覆盖打开 PFI.app、打开 localhost、10 个一级入口、核心二级页面、浏览器后退/前进、核心指标无假零、报告中心、亮色 UI 和移动端响应式。
- 记录环境开放项：`/Applications/PFI.app` 当前缺失；`~/Downloads/PFI.app` 在 Phase 8.2 证明存在且指向当前 checkout。本轮不重装 app bundle。
- 本轮不声明用户确认，不执行 Stage 8 whole-stage review、Stage 9 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 8 Phase 8.2 - 2026-07-01

- 完成 `Stage 8 / Phase 8.2 - 截图验收`：真实浏览器采集 app home、localhost home、10 个一级入口、移动端响应式和 `desktop_all_pages.png` 截图索引。
- 新增 `PFI/scripts/validate_v024_stage8_phase82_screenshots.js`、`PFI/tests/test_v024_stage8_phase82_screenshot_acceptance.py` 和 `PFI/reports/pfi_v024/stage_8/phase_8_2/` evidence。
- 截图验收使用当前 checkout 临时 Streamlit 服务，验证存在的 `PFI.app` 指向当前 checkout、app/localhost bundle hash 一致、浅色 UI、移动端水平溢出 `0px`，且 console/page/http errors 为空。
- 本轮不执行 Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 8 Phase 8.1 - 2026-07-01

- 完成 `Stage 8 / Phase 8.1 - 自动验收`：用真实浏览器自动验证 10 个一级入口、核心二级页面、入口版本、真实数据状态和报告中心。
- 新增 `PFI/src/pfi_v02/stage_v024_stage8_e2e_acceptance.py`、`PFI/scripts/validate_v024_stage8_phase81_e2e_auto.js`、`PFI/tests/test_v024_stage8_phase81_e2e_auto_acceptance.py` 和 `PFI/reports/pfi_v024/stage_8/phase_8_1/` evidence。
- 自动验收注入 Stage 4 `read_model_status.json` 与 Stage 7 `report_schema.json`，确认 `MetaDatabase/PFI` 8815 条记录、4 个 raw files、非假零阻断状态和 6 类报告中心字段。
- 本轮不执行 Phase 8.2 截图验收、Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 GitHub Main Upload - 2026-07-01

- 完成 `Stage 7 GitHub main upload gate`：将 Stage 7 Phase 7.1、Phase 7.2、Phase 7.3 和 whole-stage review package 上传到 GitHub main。
- 新增 `PFI/tests/test_v024_stage7_github_upload_contract.py`、`PFI/docs/pfi_v024/STAGE7_GITHUB_MAIN_UPLOAD.md` 和 `PFI/reports/pfi_v024/stage_7/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 7 upload contract、whole-stage review、Phase 7.1/7.2/7.3 回归、Stage 6 相邻回归、browser validation、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 8，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 7 Whole-Stage Review - 2026-07-01

- 完成 `Stage 7 whole-stage review - 复审并解决暴露问题`，复审 Phase 7.1 报告结构、Phase 7.2 页面展示和 Phase 7.3 验收。
- 新增 `PFI/tests/test_v024_stage7_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE7_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_7/whole_stage_review/` evidence。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 7.3、缺少整阶段命令/证据汇总。
- 复审确认报告中心 6 类报告、公式/参数/样本量/数据范围可见、数据不足阻断、反单段 AI 文本和无假数据边界均有证据。
- 本轮不执行 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 Phase 7.3 - 2026-07-01

- 完成 `Stage 7 / Phase 7.3 - 验收`：验收报告中心 6 类报告、数据不足报告、公式/参数/样本量/数据范围可见性和反单段 AI 文本退化。
- `PFI/web/app/pages/reports.js` 新增 `PFI-V024-STAGE7-PHASE73-ACCEPTANCE` 合同和 report acceptance gate。
- 新增 `PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js`，生成浏览器验收、数据质量 HTML 和 `formula_visibility.png`。
- 新增 `PFI/tests/test_v024_stage7_phase73_report_acceptance.py` 和 `PFI/reports/pfi_v024/stage_7/phase_7_3/` evidence。
- 本轮不执行 Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 Phase 7.2 - 2026-07-01

- 完成 `Stage 7 / Phase 7.2 - 页面展示`：报告中心页面接入 Phase 7.1 报告结构，展示净资产、现金、投资、消费、现金流、数据质量 6 份报告。
- `PFI/web/app/pages/reports.js` 新增 `PFI-V024-STAGE7-PHASE72-PAGE-DISPLAY` 合同、report center view model 和页面显示验证。
- `PFI/web/app/shell.js` 通过 `PFI_V024_STAGE7_REPORTS` 把结论、公式、参数、样本量、数据范围、置信度、缺口和复核入口映射到 `报告与洞察`。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `reports.js` 和 Phase 7.1 `report_schema.json`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage7_phase72_report_page_display.py` 和 `PFI/reports/pfi_v024/stage_7/phase_7_2/` evidence。
- 本轮不执行 Phase 7.3 验收、Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 Phase 7.1 - 2026-07-01

- 完成 `Stage 7 / Phase 7.1 - 报告结构`：建立 v0.2.4 报告 schema、6 类报告类型、数据不足阻断规则和导出字段。
- 新增 `PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py`、`PFI/tests/test_v024_stage7_phase71_report_schema.py`、`PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md` 和 `PFI/reports/pfi_v024/stage_7/phase_7_1/` evidence。
- 报告结构读取 Stage 4 真实 read model status：`MetaDatabase/PFI` ready，`8815` 条记录，`4` 个原始文件，as of `2026-06-03`；净资产/现金/投资/现金流缺少输入时保持 blocked。
- 本轮不执行 Phase 7.2 页面展示、Phase 7.3 验收、Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 GitHub Main Upload - 2026-07-01

- 完成 `Stage 6 GitHub main upload gate`：将 Stage 6 Phase 6.1、Phase 6.2、Phase 6.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/src/pfi_v02/stage_v024_stage6_experience.py`、`PFI/docs/pfi_v024/STAGE6_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage6_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_6/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 6 upload contract、whole-stage review、Phase 6.1/6.2/6.3 回归、Stage 5 相邻回归、browser validation、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 7，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 6 Whole-Stage Review - 2026-07-01

- 完成 `Stage 6 whole-stage review - 复审并解决暴露问题`，复审 Phase 6.1 设计系统、Phase 6.2 动效反馈、Phase 6.3 触感与设置隔离。
- 新增 `PFI/tests/test_v024_stage6_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE6_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_6/whole_stage_review/` evidence。
- 新增 `PFI/scripts/validate_v024_stage6_whole_review_browser.js`，生成 `desktop_light_home.png`、`mobile_responsive.png` 和 `settings_feedback_isolation.png`。
- 修复复审暴露的亮色 fallback 问题：v0.2.4 body 增加实体 `background-color`，并让趋势图读取 body scoped token，避免旧 root token 造成深色图表槽。
- 复审发现 4 项均已 fixed；本轮不执行 GitHub main upload，不进入 Stage 7，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.3 - 2026-07-01

- 完成 `Stage 6 / Phase 6.3 - 触感与设置隔离`：新增 haptics capability detection、设置页反馈偏好模型和不支持设备的静默视觉降级。
- `PFI/web/app/feedback.js` 新增 v0.2.4 Phase 6.3 haptics contract、runtime capability detection 和 haptics settings model。
- `PFI/web/app/pages/settings.js` 新增反馈设置 view model，明确触感、声音、动效控制只在设置页管理。
- `PFI/web/app/shell.js` 写入 `data-v024-haptic-capability`、`data-v024-haptic-degraded` 和 `data-v024-feedback-setting` 运行态标记，并保持业务页面无反馈控制台。
- 新增 `PFI/tests/test_v024_stage6_phase63_haptics_settings.py`、`PFI/docs/pfi_v024/STAGE6_HAPTICS_SETTINGS.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_3/` evidence。
- 本轮不执行 Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.2 - 2026-07-01

- 完成 `Stage 6 / Phase 6.2 - 动效反馈`：新增页面切换、加载骨架、成功/失败/阻断反馈和报告生成进度的轻量动效。
- `PFI/web/app/feedback.js` 新增 v0.2.4 Phase 6.2 motion contract、feedback model 和 report progress model。
- `PFI/web/app/shell.js` 写入 `data-v024-route-transition`、`data-v024-motion-state`、`data-v024-report-progress` 等运行态标记。
- `PFI/web/styles.css` 新增 `PFI v0.2.4 Stage 6 Phase 6.2 motion feedback` 样式块，并支持 reduced motion。
- 新增 `PFI/tests/test_v024_stage6_phase62_motion_feedback.py`、`PFI/docs/pfi_v024/STAGE6_MOTION_FEEDBACK.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_2/` evidence。
- 本轮不执行 Phase 6.3、Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.1 - 2026-07-01

- 完成 `Stage 6 / Phase 6.1 - 设计系统`：建立 v0.2.4 默认浅色 token、状态色、卡片/表格/图表槽和响应式布局覆盖层。
- `PFI/web/index.html` 锁定 `color-scheme=light`，并新增 `data-v024-stage6-design-system="phase_6_1"`。
- `PFI/web/styles.css` 新增 `body[data-pfi-target-version="v0.2.4"]` 作用域 token，不进入动效或触感实现。
- 新增 `PFI/tests/test_v024_stage6_phase61_design_system.py`、`PFI/docs/pfi_v024/STAGE6_DESIGN_SYSTEM.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_1/` evidence。
- 本轮不执行 Phase 6.2、Phase 6.3、Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 GitHub Main Upload - 2026-07-01

- 准备 `Stage 5 GitHub main upload gate`：将 Stage 5 Phase 5.1、Phase 5.2、Phase 5.3 和 whole-stage review package 上传到 GitHub main。
- 新增 `PFI/src/pfi_v02/stage_v024_stage5_experience.py`、`PFI/docs/pfi_v024/STAGE5_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage5_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_5/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 5 upload contract、whole-stage review、Phase 5.1/5.2/5.3 回归、Stage 3/4 相邻回归、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 6，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 5 Whole-Stage Review - 2026-07-01

- 完成 `Stage 5 whole-stage review - 复审并解决暴露问题`，复审 Phase 5.1 首页、Phase 5.2 二级页面差异化、Phase 5.3 交互状态。
- 新增 `PFI/tests/test_v024_stage5_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE5_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_5/whole_stage_review/` evidence。
- 新增 `PFI/scripts/validate_v024_stage5_whole_review_browser.js`，生成 10 个一级入口和 10 个核心二级页面截图，browser validation 为 pass。
- 修复静态浏览器验收中可选 `/api/read-model-status` 404：`index.html` 关闭静态可选 fetch，Streamlit runtime 显式启用 `readModelStatusApi`。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、缺少截图覆盖、静态 runtime 可选 endpoint 404。
- 本轮不执行 GitHub main upload，不进入 Stage 6，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.3 - 2026-07-01

- 完成 `Stage 5 / Phase 5.3 - 交互状态`：45 个二级业务页面均有 `loading / success / error / empty` 四态。
- 新增 `PFI/web/app/ux_state.js`，暴露 `PFI_V024_STAGE5_UX_STATE`、Phase 5.3 合同、页面状态模型、UX validation 和 history acceptance。
- `PFI/web/app/shell.js` 在二级页面 surface 渲染四态卡片，并把 empty/error 动作接到真实 route，不只显示说明或 toast。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `ux_state.js`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage5_phase53_interaction_states.py`、`PFI/docs/pfi_v024/STAGE5_INTERACTION_STATES.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_3/` evidence。
- 本轮不执行 Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.2 - 2026-07-01

- 完成 `Stage 5 / Phase 5.2 - 二级页面差异化`：10 个正式一级入口共 45 个二级页面，最少每个入口 4 个。
- 新增 `PFI/web/app/pages/stage5Subpages.js`，暴露 `PFI_V024_STAGE5_PAGES`、Phase 5.2 合同、catalog flatten 和 route validation。
- `PFI/web/app/shell.js` 优先读取 v0.2.4 Stage 5 页面目录，并给二级页 DOM 标记 `data-stage5-state-key` 和 `data-stage5-data-object`。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `stage5Subpages.js`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py`、`PFI/docs/pfi_v024/STAGE5_SUBPAGE_DIFFERENTIATION.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json`。
- 本轮不执行 Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.1 - 2026-07-01

- 完成 `Stage 5 / Phase 5.1 - 首页重建`：首页新增“钱、位置、变化、问题、下一步、依据”六问结构。
- 新增 `PFI_V024_STAGE5_HOME`、`buildV024Stage5Phase51Contract()` 和 `buildV024Stage5Phase51HomeViewModel()`，读取 Stage 4 `read_model_status` 生成首页数据状态卡与下一步任务流。
- `PFI/web/index.html` 移除默认 `功能面板 / PFI 功能入口 / 功能已准备 / 进入操作面板` 机械层文案，并加载 `./app/pages/home.js`。
- `PFI/web/app/shell.js` 优先使用 v0.2.4 首页 API，把 `#pfi-read-model-status` 传给首页模型。
- 新增 `PFI/tests/test_v024_stage5_phase51_home_rebuild.py`、`PFI/docs/pfi_v024/STAGE5_HOME_REBUILD.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_1/evidence.json`。
- 本轮不执行 Phase 5.2、Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 GitHub Main Upload - 2026-07-01

- 完成 `Stage 4 GitHub main upload gate`：将 Stage 4 Phase 4.1、Phase 4.2、Phase 4.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/docs/pfi_v024/STAGE4_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage4_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_4/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 4 非假零、read model 挂链、whole-stage review、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 5，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 4 Whole-Stage Review - 2026-07-01

- 完成 `Stage 4 whole-stage review - 复审并解决暴露问题`，复审 Phase 4.1 状态机、Phase 4.2 read model 挂链、Phase 4.3 非假零验收。
- 新增 `PFI/docs/pfi_v024/STAGE4_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage4_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_4/whole_stage_review/evidence.json`。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 4.3、Phase 4.3 浏览器证据需纳入整阶段验收。
- 重新验证 Stage 4 四个测试文件，`21 passed`；JS check、JSON evidence check 和截图 size 证据通过。
- 本轮不执行 GitHub main upload，不重装 app bundle，不修改真实财务数据源，不进入 Stage 5。

## v0.2.4 Repair Pack Stage 4 Phase 4.3 - 2026-07-01

- 完成 `Stage 4 / Phase 4.3 - 验收`：用测试和 Chrome headless 截图验证缺失数据不显示财务 0、真零必须携带证据链。
- 新增 `PFI/tests/test_v024_stage4_phase43_acceptance.py`，覆盖 blocked 指标不渲染 `CNY 0.00`、`confirmed_zero` 缺证据报错、前端 null `record_count/confidence` 不得变成 0。
- 新增 `PFI/scripts/validate_v024_stage4_phase43_chrome.py`，生成 Phase 4.3 browser validation、两张截图和 evidence pack。
- 修复 `PFI/web/app/data_state.js` 与 `PFI/web/app/shell.js`：`record_count=null` 和 `confidence=null` 保持未知，不再显示成 `0 条记录`。
- 当前真实数据状态仍为 `MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；真实生产指标中 `confirmed_zero` 数量为 `0`。
- 本轮不执行 Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 Phase 4.2 - 2026-07-01

- 完成 `Stage 4 / Phase 4.2 - read model 挂链`：新增 shared read model status，把 Phase 4.1 数据状态机接入首页、账户、投资、消费和报告卡片状态。
- 新增 `PFI/src/pfi_os/application/read_model_status.py`，输出 `data_source_scan`、`read_model_status`、`core_metric_states` 和五个 surface 的共享状态。
- `PFI/src/pfi_v02/stage_v021_runtime_api.py` 新增 `/api/read-model-status`；`PFI/src/pfi_os/app/streamlit_app.py` 同步嵌入 `#pfi-read-model-status`。
- `PFI/web/app/data_state.js` 新增 shared surface view model；`PFI/web/app/shell.js` 读取 `/api/read-model-status` 并覆盖首页/账户/投资/消费/报告核心卡片，缺失状态不显示 `CNY 0.00`。
- 当前真实数据状态：`MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；净资产、现金余额和投资市值仍为 `source_missing`，消费总流出为 `ready`。
- 本轮不执行 Phase 4.3 验收、Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 Phase 4.1 - 2026-07-01

- 完成 `Stage 4 / Phase 4.1 - 状态机定义`：冻结核心财务指标数据状态枚举、指标状态 schema、中文阻断原因和禁止假零规则。
- 新增 `PFI/src/pfi_v02/stage_v024_stage4_data_state.py`，提供 `PFI-V024-STAGE4-PHASE41-DATA-STATE` 合同、metric state builder、渲染守卫和运行时禁用词扫描。
- 新增 `PFI/web/app/data_state.js`，供后续 Phase 4.2/4.3 前端挂链复用；非 ready 状态返回中文原因，不渲染 `CNY 0.00`。
- 新增 `PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md`、`PFI/tests/test_v024_stage4_phase41_data_state_contract.py`、`PFI/tests/test_v024_stage4_no_mock_financial_data.py` 和 `PFI/reports/pfi_v024/stage_4/phase_4_1/evidence.json`。
- 本轮不执行 Phase 4.2 read model 挂链、Phase 4.3 验收、Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 3 GitHub Main Upload - 2026-07-01

- 完成 `Stage 3 GitHub main upload gate`：将 Stage 3 Phase 3.1、Phase 3.2、Phase 3.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/docs/pfi_v024/STAGE3_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage3_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_3/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 3 浏览器导航、v0.2.4 回归、v0.2.3 Stage 3 兼容、JSON 和 diff。
- 本轮不执行 Stage 4、不重装 app bundle、不修改 launcher C/Info.plist、不修改真实数据逻辑。

## v0.2.4 Repair Pack Stage 3 Whole-Stage Review - 2026-07-01

- 完成 `Stage 3 whole-stage review - 复审并解决暴露问题`，复审 Phase 3.1、Phase 3.2 和 Phase 3.3 的合同、route、DOM、browser history 和 evidence。
- 新增 `PFI/docs/pfi_v024/STAGE3_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage3_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_3/whole_stage_review/evidence.json`。
- 修复复审发现的 3 个 Stage 3 范围问题：缺少 whole-stage review gate、顶层状态仍停在 Phase 3.3、Phase 3.3 浏览器证据需要 review-time refresh。
- 重新运行 Node Playwright 验收，刷新 `phase_3_3/browser_validation.json`、`legacy_routes_validation.json` 和截图证据。
- Stage 3 本地整阶段复审完成；本轮未执行 GitHub main upload、Stage 4、app bundle reinstall、真实数据逻辑修改。

## v0.2.4 Repair Pack Stage 3 Phase 3.3 - 2026-07-01

- 完成 `Stage 3 / Phase 3.3 - 导航验收`：真实浏览器验证 desktop/mobile 各 10 个一级入口，`市场与研究` 保持第 9 个正式一级入口。
- 新增 `PFI/scripts/validate_v024_stage3_phase33_browser.js`，用 Node Playwright 启动本地静态 HTTP server，实际加载 `PFI/web/index.html` 验证点击导航、direct URL alias 和 browser back/forward。
- 新增 `PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py`，锁定 Phase 3.3 contract、browser validation JSON、legacy route JSON、截图和 evidence pack。
- 扩展 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，新增 Phase 3.3 navigation acceptance contract。
- 新增 `PFI/reports/pfi_v024/stage_3/phase_3_3/` evidence，包括 `browser_validation.json`、`legacy_routes_validation.json`、`desktop_nav.png` 和 `browser_back_after_forward.png`。
- 本轮未执行 Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 3 Phase 3.2 - 2026-07-01

- 完成 `Stage 3 / Phase 3.2 - 路由实现`：`PFI/web/app/routes.js` 暴露 `window.PFI_V024_STAGE3_ROUTES`，可解析一级 route、二级 route 和 v0.1 alias redirect。
- 新增 `PFI/tests/test_v024_stage3_phase32_route_implementation.py`，用 Node 调用真实 route API 验证 10 个一级 route、45 个二级 route 和 6 个旧入口 redirect。
- `PFI/web/app/shell.js` 优先调用 `PFI_V024_STAGE3_ROUTES.resolveRouteAlias()`，再进入旧 fallback；保留 hash、`pushState`、`replaceState`、`hashchange` 和 `popstate` runtime 声明。
- 扩展 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，新增 Phase 3.2 route contract。
- 新增 `PFI/reports/pfi_v024/stage_3/phase_3_2/evidence.json`。
- 本轮未执行 Phase 3.3 浏览器历史验收、Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 3 Phase 3.1 - 2026-06-30

- 完成 `Stage 3 / Phase 3.1 - 导航合同`：正式一级入口固定 10 个，`市场与研究` 保持第 9 个正式一级入口。
- 新增 `PFI/web/app/navigation.js` 和 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，将 v0.2.4 Stage 3 导航合同独立为前端和 Python 可验证资源。
- `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` 保留为 v0.1 alias/command，不作为同级一级入口。
- `PFI/web/index.html` 加载 `navigation.js` 后再加载 `routes.js`；`PFI/src/pfi_os/app/streamlit_app.py` 同步内联该脚本，避免 app/localhost bundle 漂移。
- 新增 `PFI/tests/test_v024_stage3_phase31_navigation_contract.py`、`PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md` 和 `PFI/reports/pfi_v024/stage_3/phase_3_1/evidence.json`。
- 本轮未执行 Phase 3.2、Phase 3.3、Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 2 Whole-Stage Review - 2026-06-30

- 完成 `Stage 2 whole-stage review - 复审并解决暴露问题`，复审 Phase 2.1、Phase 2.2、Phase 2.3 的入口链路、版本链路、真实浏览器验收和 evidence。
- 新增 `PFI/docs/pfi_v024/STAGE2_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage2_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_2/whole_stage_review/evidence.json`。
- 修复复审发现的证据漂移：重新运行 Phase 2.3 真实浏览器验收，使 `phase_2_3/evidence.json` 记录当前 Stage 2 review baseline。
- Stage 2 本地整阶段复审完成；本轮未进入 Stage 3、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.3 - 2026-06-30

- 完成 `Stage 2 / Phase 2.3 - 实机验收`：localhost、app、清缓存浏览器上下文、新 Profile 四条路径均读取同一 Stage 2 build id 和 bundle hash。
- 新增 `PFI/scripts/validate_v024_stage2_phase23_entry.js`，生成 `browser_validation.json` 和四张真实浏览器截图。
- 修复 Phase 2.3 暴露的同路径旧服务复用问题：`PFI/StartPFI.command` 和 `PFI/scripts/startPFI.sh` 只复用带当前 build/UI contract marker 的 Streamlit 服务。
- 当前真实验收服务为 `http://127.0.0.1:8502`；旧 `8501` 同路径服务不再作为当前 build 入口复用。
- 本轮未执行 Stage 2 whole-stage review、未进入 Stage 3、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.2 - 2026-06-30

- 完成 `Stage 2 / Phase 2.2 - 版本链路实现`：页面可见 `PFI v0.2.3 Repair`、build id、bundle version、bundle hash 和 UI contract version。
- 新增 `PFI/web/app/entry_audit.js`，提供 `window.PFI_READ_STAGE2_ENTRY_AUDIT` 给 Phase 2.3 真实 app/local/browser 验收读取。
- `PFI/web/app/version.js` 升级为 Stage 2 entry version metadata，同时保留 Stage 1 shell integrity compatibility fields。
- `PFI/web/app/shell.js` 会把 Streamlit 注入的动态 runtime metadata 写入 body dataset 和入口身份条。
- `PFI/web/styles/tokens.css` 为入口身份条提供稳定 top-bar 布局，并纳入 Stage 2 bundle hash。
- `PFI/StartPFI.command` 和 `PFI/scripts/startPFI.sh` 的 versioned URL 改为 `pfi-v024-stage2-phase22` / `PFI-V024-STAGE2-ENTRY-CONSISTENCY`。
- 本轮未执行 Phase 2.3 实机验收、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.1 - 2026-06-30

- 完成 `Stage 2 / Phase 2.1 - 入口链路映射`：定位 macOS app、StartPFI、Streamlit、静态 HTML、shell runtime 和 version runtime 的当前链路。
- 新增 `src/pfi_v02/stage_v024_stage2_entry_consistency.py`、`tests/test_v024_stage2_phase21_entry_mapping.py` 和 `reports/pfi_v024/stage_2/phase_2_1/evidence.json`。
- 新增 `entry_map.md`、`old_ui_signatures.json` 和 `build_hash_display_spec.md`，记录旧 v0.2.3 Stage 1 入口签名并指定 Phase 2.2 的 build/hash 展示位置。
- 本轮未实现 Phase 2.2、未执行 Phase 2.3 实机验收、未修改 app bundle/launcher/业务 UI/真实数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 1 Whole-Stage Review - 2026-06-30

- 完成 `Stage 1 whole-stage review - 复审并解决暴露问题`，复审 Phase 1.1、Phase 1.2、Phase 1.3 的合同、证据、测试和状态文件。
- 修复复审发现的两个 Stage 1 范围问题：缺少整体复审合同/evidence，以及顶层 run/status 文件仍停留在 Phase 1.3。
- 新增 `docs/pfi_v024/STAGE1_WHOLE_STAGE_REVIEW.md`、`tests/test_v024_stage1_whole_review_contract.py` 和 `reports/pfi_v024/stage_1/whole_stage_review/evidence.json`。
- Stage 1 已本地整体复审完成；Stage 2 和 GitHub main upload 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.3 - 2026-06-30

- 完成 `Stage 1 / Phase 1.3 - 验证`：记录 `node --check`、pytest 合同测试和 changed files audit。
- 新增 `tests/test_v024_stage1_phase13_validation_closeout.py` 和 `reports/pfi_v024/stage_1/phase_1_3/evidence.json`。
- Stage 1 当前为 candidate complete；whole-stage review、复审问题修复和 GitHub main upload 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher、`shell.js` 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.2 - 2026-06-30

- 完成 `Stage 1 / Phase 1.2 - 最小恢复`：在 `shell.js` 中新增 `window.PFI_STAGE1_SHELL`，暴露 version、initialize、mountRoute 和 errorBoundary。
- 新增 `PFI/web/app/version.js`，提供 `window.PFI_STAGE1_VERSION` 和 `window.PFI_READ_STAGE1_VERSION` 版本读取接口。
- 新增 `tests/test_v024_stage1_phase12_shell_repair.py` 和 `reports/pfi_v024/stage_1/phase_1_2/evidence.json`。
- 本轮只做 shell integrity 最小恢复；Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.1 - 2026-06-30

- 完成 `Stage 1 / Phase 1.1 - 现状定位`：保存当前 `PFI/web/app/shell.js` 快照，记录语法检查结果，并定位当前残缺片段范围。
- 新增 `src/pfi_v02/stage_v024_stage1_shell_integrity.py`、`tests/test_v024_stage1_phase11_shell_diagnosis.py` 和 `reports/pfi_v024/stage_1/phase_1_1/evidence.json`。
- 当前 `shell.js` 在 Codex bundled Node 下语法检查通过；未发现 merge marker 或 syntax-fragment range。
- Phase 1.1 不修改 `shell.js`；Phase 1.2 仍需最小 shell integrity repair，Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Whole-Stage Review - 2026-06-30

- 完成 `Stage 0 whole-stage review - 复审并解决暴露问题`，复审 Phase 0.1、0.2、0.3 的合同、证据、测试和状态文件。
- 修复复审发现的两个 Stage 0 范围问题：缺少整体复审合同/evidence，以及顶层 run/status 文件仍停留在 Phase 0.3。
- 新增 `docs/pfi_v024/STAGE0_WHOLE_STAGE_REVIEW.md`、`tests/test_v024_stage0_whole_review_contract.py` 和 `reports/pfi_v024/stage_0/whole_stage_review/evidence.json`。
- Stage 0 已整体复审完成；Stage 1 尚未开始，仍需用户验收或明确指令。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.3 - 2026-06-30

- 完成 `Stage 0 / Phase 0.3 - Stage 0 测试与证据`，用合同测试覆盖 10 个正式一级入口、`市场与研究` 一级入口、禁止假财务数据和 evidence pack 完整性。
- 新增 `tests/test_v024_stage0_phase03_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_3/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录 Phase 0.3 机器合同和 Stage 0 candidate complete 状态。
- 本轮未执行 Stage 0 whole-stage review、Stage 1 或后续阶段，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.2 - 2026-06-30

- 完成 `Stage 0 / Phase 0.2 - 历史约束废弃`，明确历史 9 入口约束、市场与研究一级入口禁令、暗色 AI 控制台方向和样例财务数据验收均已作废。
- 新增 `docs/pfi_v024/HISTORY_DEPRECATION_POLICY.md`、`tests/test_v024_stage0_phase02_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_2/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录废弃约束和仍保留的历史参考原则。
- 本轮未执行 Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.1 - 2026-06-30

- 完成 `Stage 0 / Phase 0.1 - 需求合同冻结`，记录 v0.2.4 修补包定位、10 个正式一级入口、真实数据禁令和每轮最多一个 phase 的执行规则。
- 新增 `docs/pfi_v024/REPAIR_SCOPE_LOCK.md`、`src/pfi_v02/stage_v024_repair_contract.py`、`tests/test_v024_stage0_phase01_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_1/evidence.json`。
- 本轮未执行 Phase 0.2、Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Pre Stage 0 - 2026-06-30

- 建立 `v0.2.4` 修补包 pre stage 0；用户提供的 `v0.2.3-repair` roadmap/taskpack 作为来源输入，但当前 repo artifact 使用 `pfi_v024` 命名空间。
- 重新核验当前 GitHub main：`PFI/docs/pfi_v023` 和 v0.2.3 tests 已存在，`PFI/web/app/shell.js` 通过 `node --check`，TaskPack 内旧 GitHub audit 对当前 checkout 已过时。
- 新增 `docs/pfi_v024/PRE_STAGE0_CONTEXT_LOCK.md`、`SOURCE_TASK_PACK_MANIFEST.md`、`RUN_CONTRACT.md`、`src/pfi_v02/stage_v024_pre_stage0_contract.py` 和 `tests/test_v024_pre_stage0_contract.py`。
- 本轮未执行 Stage 0，未修改业务 UI、app bundle、launcher 或数据逻辑；停止等待用户验收或明确指令进入 Stage 0。

## v0.2.1.1 Product UI Recovery Stage 5/6 - 2026-06-29

- 完成 `v0.2.1.1 Stage 5` 真实图表与最终验收合同：账户、投资、消费趋势统一读取 `/api/trends`，来源限定为 SQLite operational DB 和 `MetaDatabase/PFI/alipay_daily`。
- 删除正式 Web Shell 的硬编码数字趋势回退；运行 API 不可用时只显示中文空状态。
- 隔离旧项目验收功能面板中的合成验收和测试数据路径，正式页面不再暴露 `fixture` 或合成验收入口。
- 新增 `docs/pfi_v0211/STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md`、`docs/pfi_v0211/STAGE6_PROJECT_REVIEW_CLOSEOUT.md` 和 `tests/test_v0211_stage5_6_final_acceptance_contract.py`。
- Stage 6 项目级复审验收作为用户口径的第二阶段 closeout，覆盖跨板块复审、GitHub main 同步、本机 app 入口刷新和非必要缓存清理。

## v0.2.1.1 Product UI Recovery Stage 4 - 2026-06-29

- 完成 `S4 持久化与同步`，把 `投资管理 > 持仓` 保存路径接到本机 SQLite operational DB。
- 新增 `docs/pfi_v0211/STAGE4_PERSISTENCE_SYNC.md`、`tests/test_v0211_stage4_persistence_sync_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 4 合同。
- `src/pfi_v02/stage_v021_runtime_api.py` 新增 `/api/read-model` 和 `/api/reports/holdings`，让首页、投资管理和报告与洞察读取同一持仓读模型。
- 持仓编辑字段补齐账户、更新时间和备注；备注写入 SQLite snapshot 的 `metadata.note`。
- `web/app/shell.js` 保存持仓后刷新后端读模型，并同步更新首页、投资和报告卡片；生产保存不调用浏览器缓存。
- 正式库无真实持仓时继续显示中文空状态，不生成模拟收益或模拟持仓。

## v0.2.1.1 Product UI Recovery Stage 3 - 2026-06-29

- 完成 `S3 真实操作流`，把 Stage 2 页面骨架推进为可点击、可反馈、可复核的上传、账本、持仓和设置操作路径。
- 新增 `docs/pfi_v0211/STAGE3_REAL_OPERATION_FLOWS.md`、`tests/test_v0211_stage3_real_operation_flow_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 3 合同。
- `数据源与上传` 增加解析预览、字段映射、确认入库状态和待复核队列反馈；未选择真实文件时只提示中文空状态，不制造记录数。
- `账本流水` 增加筛选、分类选择、保存复核和导出流水；无真实流水时只导出空表头，不生成虚构流水。
- `投资管理 > 持仓` 保留未提交草稿标识，生产保存路径继续调用本机 `/api/holdings`，不把浏览器缓存作为生产保存来源。
- `设置` 增加保存设置、恢复默认和状态反馈；反馈控制台仍只在设置页显示。
- 本轮不声明 Stage 4 持久化与同步完成，不声明 Stage 5 真实图表与最终验收完成，不新增测试数据、样例流水、模拟持仓或虚构财务事实。

## v0.2.1.1 Product UI Recovery Stage 2 - 2026-06-29

- 完成 `S2 页面骨架与去 AI 化`，为 10 个正式一级入口建立中文页面骨架和二级入口。
- 新增 `docs/pfi_v0211/STAGE2_PAGE_SKELETON_CLEANUP.md`、`tests/test_v0211_stage2_page_skeleton_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 2 合同。
- Web Shell 默认首页改为用户任务语言：净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态。
- 清理正式 UI 中运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心等污染词。
- `数据源与上传` 二级入口固定包含 `上传中心` 和 `导入中心`；`设置` 独立承接反馈、主题、语言、备份恢复等设置项。
- 本轮不做数据库 migration、上传入库闭环、持仓 SQLite 闭环、真实图表数据接入，也不声明 v0.2.1.1 整体完成。

## v0.2.1.1 Product UI Recovery Stage 0 - 2026-06-29

- 建立 v0.2.1.1 前端 UIUX 逻辑优化准备轮，明确当前 v0.2.1 前端优化不再作为正式 UI 完成状态，后续不得继续在旧 AI 化 Web Shell 上补丁式修补。
- 新增 `PRODUCT.md`、`docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md`、`docs/pfi_v0211/ROADMAP_LOCK.md`、`docs/pfi_v0211/STAGE0_PREPARATION.md`、`src/pfi_v02/stage_v0211_ui_recovery.py` 和 `tests/test_v0211_stage0_preparation_contract.py`。
- 将用户纠偏后的执行层级锁定为 6 个 Stage：S0 准备轮、S1 产品壳与路由、S2 页面骨架与去 AI 化、S3 真实操作流、S4 持久化与同步、S5 真实图表与最终验收；每次 run work 最多完成 1 个 Stage。
- 记录 Markdown roadmap 与 RTF 的来源差异：Stage 1 默认采用 RTF 最新稿的 10 个正式主导航入口，并把策略实验室唯一位置默认归到 `市场与研究 > 策略实验室`。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/src/pfi_os/app/streamlit_app.py`，不刷新 app 入口，不清理缓存，不提前实现后续 Stage。

## v0.2.1 复审退回修复 - 2026-06-28

- 正式 Web Shell 删除运行边界/使用限制/隐私边界/只读/实盘/交易密码等用户可见边界类文案；约束保留在合同、测试和文档中。
- 新增 `src/pfi_v02/stage_v021_runtime_api.py`，提供本机 `GET/POST /api/holdings` 和 `GET /api/trends`。
- 持仓编辑保存路径改为 Web Shell -> 本机 API -> `V021HoldingsPersistenceService` -> SQLite operational database；浏览器缓存只保存明确标注的未提交草稿。
- 账户与资产、投资管理、消费管理趋势图改为从 SQLite 运行读模型派生；真实数据不足时显示中文空状态，不使用硬编码 demo 数组。
- 一级入口“策略实验室”和投资管理内部“策略实验室”统一进入 `/investment/strategy-lab`，复用同一功能面板、路由和状态。
- 新增 `tests/test_v021_review_rework_contract.py`，把复审失败项固化为回归测试，并扩展 Stage 2 合同禁词集合。

## v0.2.2 数据库治理 Stage 4 - 2026-06-28

- 完成 Stage 4 `Economic Event 与 Interconnection 逻辑`，覆盖 `S4-P1-T1..S4-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_interconnection.py`，建立 `economic_event_id`、`interconnection_group_id`、event type affects flags、Interconnection Matrix、Metric Dependency Graph 和 no-double-count 聚合函数。
- 新增 `docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`，把 Stage 4 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`，新增 `interconnection.event_type_policies`、`matrix_fields` 和 `metric_dependency_graph`。
- 双消费口径已锁定：投资入金、基金申购、黄金申购、投资买入进入消费总流出但不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费。
- 本轮不实现 Stage 5 分类 taxonomy，不修改 v0.2.1 Web Shell UIUX 基线，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 3 - 2026-06-28

- 完成 Stage 3 `数据源、账户角色与可扩展结构`，覆盖 `S3-P1-T1..S3-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_source_profile.py`，建立 source profile schema、capabilities、`other_source_template`、账户多角色、角色生效期和 role-aware 计算合同。
- 新增 `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 与 `tests/test_v022_stage3_source_account_profiles.py`，把 Stage 3 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage3`，新增 `source_profile_schema`、`capability_labels_zh`、`other_source_template`、`account_role_schema` 和 `role_event_calculation_policy`。
- 本轮不实现 Stage 4 Interconnection Matrix，不修改 v0.2.1 Web Shell 交互架构，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 0 补做复核 - 2026-06-28

- 新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，把 Stage 0 的 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令整理为独立中文验收入口。
- 更新 `docs/pfi_v022/ROADMAP_LOCK.md`、`docs/pfi_v022/README.md`、`STAGE0_BASELINE_REPORT.md`、三基文件和 `HANDOFF.md`，明确 Stage 0 已补做复核且后续仍从 Stage 3 开始。
- 本轮不回滚 Stage 1/2，不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/web/styles/tokens.css`，不新增逻辑审查 HTML，也不做真实交易、自动投资或默认联网抓汇率。

## v0.2.2 数据库治理 Stage 2 - 2026-06-28

- 完成 Stage 2 `CNY 基准与汇率规则`，覆盖 `S2-P1-T1..S2-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_fx.py`，实现 06:00 Australia/Sydney 有效汇率日、普通运行本地快照读取、显式联网刷新、快照 hash 校验、金额转 CNY 和账本金额字段生成。
- 新增真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`：`fx_AUD_CNY_20260628`，`1 AUD = 4.6874 CNY`，来源 `Frankfurter v2 public API`。
- Web Shell 顶部汇率徽标从旧 CNY/AUD 口径更新为当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`，主页等主金额显示以 `CNY` 为主。
- `config/pfi_parameters.yaml`、`模型参数文件.md`、`功能清单.md`、`开发记录.md` 和 `config/parameter_changelog.md` 补齐 Stage 2 汇率、快照、原币辅助、缺失状态和非目标边界。
- 新增 `docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 与 `tests/test_v022_fx_effective_date.py`，把 Stage 2 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- 本轮不实现 Stage 3 数据源结构，不新增参数中心页面，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 1 - 2026-06-28

- 完成 Stage 1 `模型参数文件重构`，覆盖 `S1-P1-T1..S1-P2-T3`。
- `模型参数文件.md` 新增中文参数总目录，覆盖货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化和测试。
- 新增 `config/pfi_parameters.yaml` 作为唯一机器可读参数源；参数草案中的 `config/pfi_v022_parameters.yaml` 已记录为 draft alias，不新增第二个漂移文件。
- 新增 `tests/test_pfi_parameters_consistency.py`，验证 Markdown、YAML、前端合同和 HTML 中的核心参数一致。
- 新增 `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`，记录 Stage 1 验收、非目标、参数命名决策和后续 Stage 2 边界。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`，不实现真实汇率快照读取，不新增真实交易、自动投资、支付或券商提交能力。

## v0.2.1 前端优化 - 2026-06-27

- 建立 v0.2.1 前端优化 Stage 0 准备合同，锁定本轮是 PFI Web Shell 前端、交互、图表、上传命名、设置页和持仓编辑持久化优化，不是 V0.2 重构。
- 新增 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`，记录 roadmap、stage/task、acceptance criteria、stop condition、validation 和后续 pursuing goal 顺序。
- 新增 `src/pfi_v02/stage_v021_frontend_contract.py` 与 `tests/test_v021_stage0_frontend_contract.py`，把 CNY 基准、CNY/AUD 顶栏汇率、HTML 目标、多模态反馈设置页归属、统一导航和 P0-P8 任务清单固化为合同。
- 锁定后续 UI 货币契约：整体系统以 CNY 元为基准，所有页面顶部右上角显示当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）` 徽标，读取当日 06:00 Australia/Sydney 汇率快照，缺失时显示中文空状态且不得伪造汇率。
- 本轮不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口，不提前实现后续 stage。

## 0.2.0 - 2026-06-27

- PFI 根项目确认为当前注册项目根。
- 三基人类入口统一为 Markdown 文件：`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 补齐最小治理文件，记录 Stage 1/2 合同事实和生产未验证边界。
- 完成 PFI V0.2 Stage 2 本地合同验收，覆盖 phases 2A-2H。
- 新增 `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`，记录 phase/task evidence、stop-condition checks、validation results、本地 app-entry evidence 和缓存清理证据。
- 完成 PFI V0.2 Stage 3 本地可读 MVP，覆盖首页总览、账户地图、账本流水、待复核、同步全部、建议和报告入口。
- 新增 `src/pfi_v02/stage3_read_mvp.py` 与 `tests/test_stage3_readable_mvp.py`，将 Stage 3 3A-3D acceptance 固化为本地合同测试。
- Web shell 默认首页接入 Stage 3 read-model，左侧显示 V0.2 8 个一级入口；旧策略回测、盘感训练、大数据模拟器和 QBVS 兼容入口保留。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，覆盖投资总览、收益归因、风险分析、行为复盘、消费总览、分类分析、订阅检测、异常消费和现金流预测。
- 新增 `src/pfi_v02/stage4_analysis_mvp.py` 与 `tests/test_stage4_analysis_mvp.py`，将 Stage 4 4A/4B acceptance 固化为本地合同测试。
- Web shell 首页、投资管理和消费管理接入 Stage 4 analysis read-model；旧策略回测、盘感训练、大数据模拟器和 QBVS 独立系统引用继续保留。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，覆盖 recommendation model、review lifecycle、投资建议、消费建议、Top N ranking、四类报告、导出中心和 `pfi_context_snapshot_v1`。
- 新增 `src/pfi_v02/stage5_advice_report_alpha.py` 与 `tests/test_stage5_advice_report_alpha.py`，将 Stage 5 5A/5B/5C acceptance 固化为本地合同测试。
- Web shell 首页、建议与复盘、报告与洞察接入 Stage 5；仍保持 8 个一级入口，不新增 Alpha/Ralpha/System/Development 产品入口。
- 生产联通、真实账户凭证、支付提交、券商下单、Alpha repo 修改和实盘交易仍为独立后续 gate，未在 Stage 5 声明就绪。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，覆盖 synthetic 多数据源、首页闭环、账本闭环、建议闭环、回归治理、交付回滚和 20 个总验收 gate。
- 新增 `src/pfi_v02/stage6_e2e_stabilization.py` 与 `tests/test_stage6_e2e_stabilization.py`，将 Stage 6 6A/6B/6C acceptance 固化为本地合同测试。
- Web shell 首页和报告与洞察接入 Stage 6；仍保持 8 个一级入口，不新增外部系统产品入口，QBVS 顶层独立且 PFI 不覆盖 QBVS。
- Stage 6 仍只证明本地 synthetic/read-only V0.2 可运行、可验证、可回滚；真实数据连接、外部 context consumer、PDF/ZIP、CDR/Open Banking 和生产发布证据为后续独立 gate。

## v0.2.1.1 Stage 1 - 2026-06-29

- 完成产品壳与路由受控重建：正式侧栏一级入口从旧 15 项收敛为 10 项。
- 新增正式一级入口 `市场与研究`，承接旧 `市场`、`研究` 与 `策略实验室`。
- `策略实验室` canonical route 改为 `/market-research/strategy-lab`；旧 `/strategy-lab` 和 `/investment/strategy-lab` 保留为兼容别名。
- Web Shell 路由从单纯 `replaceState` 升级为 `pushState` + `popstate`，支持浏览器前进后退。
- 新增 `docs/pfi_v0211/STAGE1_PRODUCT_SHELL_ROUTING.md` 与 `tests/test_v0211_stage1_product_shell_contract.py`。
- 本轮不实现图表、上传闭环、持仓编辑或报告。

## v0.2.5 Stage 0 Phase 0.3 Gap Evidence Validation - 2026-07-12

- `ITER-20260711-PFI-V025-S0-P03` 注册 `PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE` / `ACC-PFI-V025-S0-P03-GAP-EVIDENCE`，范围严格限定为 finding 归一化、gap 排序、Stage 0 Evidence Pack 与验收请求。
- 当前 lifecycle 为 `candidate_pass_pending_postcommit_attestation / approved_pending_postcommit_attestation`；second-remediation corrected provisional 与 canonical exact-25 final-tree gates 已通过，仅待 atomic commit 与 external postcommit attestation，不声明 Stage pass、release 或 production acceptance。
- Phase 0.2 external attestation 已以 `resolved_by_approved_override` 解析上一 Phase governance scope conflict；本轮不改写其历史 tracked lifecycle。
- 模型、假设、公式、参数运行值、canonical delivery tasks、actual VERSION、product/runtime/owner truth 均未改变；`PARAM-PFI-003` 仅增加 provenance rationale。
- Stage 0 whole-stage review 与 Stage 1 均为 `not_started`；没有业务 UI、真实/私有 data、DB、App、migration、安装或 GitHub push 变更。

## v0.2.5 Stage 0 Phase 0.3 FND-030 Compensation - 2026-07-12

- `PFI-V025-S0-P03-COMP-FND030` 修正原 candidate 对 FND-030 的错误分类：Roadmap 与 Active Requirements 均未指定 `PFI/web/app/home.js`，正式首页源实际为 `PFI/web/app/pages/home.js`，并已由 Web shell 与 Streamlit asset path 加载。
- FND-030 从 `New/P1/blocking` 改为 `N/A/P1/non-gap`，删除 `GAP-P1-04`；最新计数为 `StillPresent=23 / Fixed=7 / Regressed=0 / N/A=4 / New=4`、开放生产阻断 `27 (P0=22 / P1=5)`、primary gaps `12`、non-gap findings `11`。
- 原 Phase commit `31368570082c34eca50c72c7d7b2ef46b0e6854d` 与原 immutable attestation SHA-256 `b439444de5a110f07f48fe0fa1d566624183a38e4d7270d0f0bc6fb2e6d696d6` 保持不变；当前仅补偿 commit 与 external compensation attestation 待完成。
- 本补偿不新增 iteration、task、Acceptance、version、model、formula 或 parameter，不修改产品逻辑、runtime、App、data/DB，不安装、不 push；Stage 0 whole-stage review 与 Stage 1 均为 `not_started`。

## v0.2.5 Stage 0 Whole-Stage Review - 2026-07-12

- `PFI-V025-S0-WHOLE-REVIEW` 持久绑定 Phase 0.1、Phase 0.2、原 Phase 0.3 与 FND-030 compensation 的 commit-qualified evidence/attestation chain。
- fresh whole-stage review 发现并修复 durable stage index、可执行 verifier/typed result records、lifecycle attestation gate 与 FND-030 历史 selector cardinality 四项 evidence 问题；整改后 review findings 为 `Critical=0 / Important=0 / Minor=0`。
- 六项 Roadmap Acceptance Criteria 与四项 Stop Conditions 复核通过；38 findings、12 primary gaps 和 27 个开放 P0/P1 production blockers 均保持真实开放，没有被文档 pass 覆盖。
- 当前仅为 `Codex candidate pass pending review commit attestation and explicit user acceptance`；`human_acceptance.json` 不存在，Stage 1 未开始。
- 本轮没有业务 UI、产品逻辑、model/formula/parameter registry、App、runtime、data/DB、安装、migration 或 GitHub push 变更。

## v0.2.5 Stage 1 Phase 1.1 Release Identity - 2026-07-12

- `S1-P1-T1..T4` 建立唯一 `config/release_manifest.json`，并将 version/build/content commit/frontend hash/backend hash 绑定到 App plist、launcher query、runtime API 与 frontend embedded manifest。
- release identity 缺失、无效、不可达、部分 query 或 mismatch 时 fail closed：旧 shell 保持隐藏，中文“版本冲突”页提供重新启动、重新安装与清除缓存动作。
- 初始 `65fe4633.../fc2630be...` 与中间 `71147c43.../9cc8e0f6...` pairs 已被 review remediation supersede；final `release_content_commit=a9592b8ce457492fd0e6817f74388f146ca657c6`，identity-binding commit 仍由 external attestation 绑定，避免 tracked self-reference。
- remediation 增加 raw manifest SHA response header、launcher/header 等值门禁、旧 v0.2.4 runtime-config 同步归一化、manifest-load 路径脱敏、Streamlit iframe parent/referrer launcher 门禁、static embedded manifest 验证与 Finder 中文恢复 dialog；focused GREEN 为 Python `10 passed`、Node `15 passed`。
- superseded `9cc8e0f6...` 的独立审查为 `C1/I2/M0`；所有三项已进入新的 content/binding pair，必须经 fresh re-review 到 `C0/I0/M0` 后才能 attestation。
- 用户持续过渡授权已记录为独立 overlay；它不是 `human_acceptance.json`，Stage 12 最终人工验收仍必需。
- 本 Phase 不做 Phase 1.2/1.3、真实 App 安装/Finder、GitHub push、live 8501/8502、财务数据或 SQLite 变更；Stage 1 保持 `in_progress`。

## v0.2.5 Stage 1 Phase 1.2 Cache Governance - 2026-07-12

- `S1-P2-T1..T4` 完成 HTTP、URL assets、PFI `srcdoc` inline assets、Service Worker/CacheStorage、bfcache、Streamlit read-model cache 与 launcher process reuse 的逐层审计和治理。
- same-process Streamlit wrapper 对 HTML 强制 `no-cache, private`，只给 content-hash URL 一年 immutable，未 hash assets 私有重验证；isolated HTTP 证据为 4/4 PASS，含 ETag、Last-Modified 与 conditional 304。
- read-model builder 由 startup adapter 绑定到 public `st.cache_data`：30 秒 TTL、memory-only、显式 composite key；key 含 build/commit/frontend/backend/data/parameter/formula/FX/stable read-model/Streamlit/requirements lock，真实 AppTest 证明 cache hit。
- canonical launchers 的 marker 新增 composite key，并对新进程强制 runtime API port `0`；same-process wrapper 在 Streamlit CLI 前预启动并验证非 8766 loopback owner，import-time backend hash 阻止旧 fixed-port process 用新磁盘 manifest 冒充新 backend。
- frontend 在任何 release fetch 前注销历史 Service Worker、清 dedicated-origin CacheStorage；surviving controller fail closed。`pageshow.persisted` 会先隐藏 shell，再重验 manifest/cache policy，epoch 阻止旧成功覆盖新 mismatch。
- isolated Chromium 旧 worker/cache 治理与 mismatch 证据 10/10 PASS、console/page error 0；真实 navigation type 为 `back_forward`，本次 `persisted=false` 如实保留，合成 persisted event 仅用于确定性 mismatch path。
- 初始 `5edd3788.../df7e2add...` pair 经三路独立复核为 `C0/I4/M0`，已 superseded 且不会 attestation。remediation content commit 为 `b3885f15cd2e983c0839be6a20d7e4a9391c6324`，修复 API owner、value-free stable hash、conditional request precedence/scope 与 trace ZIP 解压隐私扫描；Python `22/22`、Node `23/23`、HTTP `4/4`、Chromium `10/10`。final binding、fresh review 与外部 attestation 仍待完成；Phase 1.3、App install/Finder/new-profile、push、data/DB 与 final human acceptance 未执行，Stage 1 仍 `in_progress`。

## v0.2.5 Stage 1 Phase 1.3 Isolated App Acceptance - 2026-07-12

- `S1-P3-T1..T4` 使用 Stage 0 已批准 override 构建并真实 Finder 双击一次性 `/private/tmp` 候选；未覆盖 `/Applications`、Desktop 或 Downloads 的既有 v0.2.3 条目。
- 候选仅加载 release identity 与空状态：不读取财务数据、SQLite、model、formula、parameter、FX 或 Stage 7 schema，也不启动辅助 Runtime API。
- 实机证据验证三成员唯一 PGID、两个精确 loopback endpoint、仅一个浏览器请求端口、fresh Chromium profile、reload/cache-clear/history 生命周期与 release-only cache key；所有 browser checks 通过，错误计数为 0。
- finalize 仅停止候选进程组，释放两个端口，注销候选 LaunchServices 记录，证明 canonical/protected metadata/Git 状态不变并删除候选根。
- `release_content_commit=128c6b889c91f5d7f64c7cd9635466fa2caf0275`；direct binding successor、fresh post-commit reviews 与 external attestation 仍需完成。Stage 1 保持 `in_progress`，不进入 Stage 2。

<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_BEGIN -->
Stage 1 Phase 1.3 Isolated App Acceptance
owner_view_conflict_id=PFI-V025-CONFLICT-OWNER-VIEWS
owner_view_conflict_status=blocked
owner_evidence_state=unified_owner_view_not_proven
owner_view_resolution_task=S12-P3-T1
owner_views_unified=false
v0.2.5_accepted=false
stage_1_status=in_progress
canonical_install_gate=S12-P2-T1
<!-- PFI_V025_S1_P13_GOVERNANCE_OVERLAY_END -->

## v0.2.5 Stage 2 Phase 2.1 - 2026-07-14

- 新增固定候选根只读 inventory：MetaDatabase/PFI、PFI/MetaDatabase、$PFI_DATA_HOME、~/.pfi。
- 选定 $PFI_DATA_HOME 为 canonical private runtime root，其他位置显式 alias/只读来源；无数据迁移。
- 新增与 Task Pack 语义一致的单 source schema 和严格 collection wrapper schema，Source Manifest 只保存脱敏 metadata/hash。
- 新增 SQLite fail-closed probe：逐组件拒绝 symlink/仓库内私有根/双根冲突、不可遍历目录、非 regular candidate、任意 sidecar 与 WAL header；实际 rollback-journal DB 使用 `mode=ro` 共享只读事务、`query_only`、deny-write authorizer，并复核前后目录、候选集与 DB 指纹；不输出 table/row/private path。
- 固定九输入 privacy scan 对路径、原始文件名、财务行、账户标识、常见 credential 形式、SQLite table 名、Finder、source mutation 与 fake fallback 全部 fail-closed；CLI 使用 dir-FD/O_NOFOLLOW、0600、no-overwrite hard-link commit point。
- Source Registry 成为 Manifest 定义输入；余额、负债、持仓、价格、FX 因尚未绑定可验证 source-level aggregate metadata 记为 `not_loaded`，不冒充已证明 `source_missing`。
- 新增 metric computability matrix：交易只证明 source input available；分类、CNY 消费、现金、持仓市值和净资产仍因 source 与后续合同依赖未完成而 blocked/null。
- Phase 2.1 candidate pass；Stage 2 仍 in_progress。未使用 Finder，未 push，未安装 App，未修改真实数据/DB、model/formula/parameter 或 production truth。
