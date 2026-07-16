
# PFI v0.2.5 Production Truth & Human Workflow Completion

中文名：**PFI v0.2.5 真实财务智能与人类工作流完成版**  
版本：`v0.2.5`  
审计基线日期：`2026-07-10`（Australia/Sydney）  
目标仓库：`LinzeColin/CodexProject/PFI`  
结构：**Stage → Phase → Task**

> 本 Roadmap 是 v0.2.5 唯一执行路线。每次 Codex 运行最多执行一个 Phase；每个 Stage 完成后必须等待用户明确验收。不得一次执行完整 Roadmap，不得自动进入下一 Stage，不得以 README、测试摘要或报告文字替代真实产品验收。

## 0. 版本定位

v0.2.5 不以继续扩展功能为目标，而是把已有 PFI 从“合同、状态机、文档和静态 UI 壳”推进为真实可使用、可解释、可恢复的人类个人财务产品。

优先完成四个事实：

1. 用户从 Finder App 和 localhost 看到同一最新 UI。
2. 真实数据是否挂载、可计算、过期或失败能够被明确区分；非 ready 状态绝不显示财务 0。
3. 10 个一级入口和差异化二级页面遵循正常软件路由与工作流。
4. 公式、参数、报告、SQLite 持久化和 Evidence 能被真实验证。

## 1. 全局执行规则

- 当前产品根目录是 `PFI/`；不要启用 `PFI_OS/` 作为第二产品根。
- 一级入口正好 10 个：`首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置`。
- Alpha 是独立系统，只能读取版本化的 PFI Context；不进入 PFI 导航。不存在 Ralpha。Serenity-Alipay 完全排除。
- `系统与开发` 不是一级入口；Cloudflare public shell 不是私有本地 PFI 的完成证据。
- 禁止 mock/sample/demo/synthetic/fixture/fake 财务数据参与产品验收。真实数据不可用时必须 `blocked/not_run`，不得 fallback。
- 财务测试使用真实数据的只读副本或隔离快照；日志和 Evidence 只保存 hash、计数、日期范围和脱敏 ID。
- 每轮最多一个 Phase；实现前声明读取/修改文件、命令、风险、迁移和回滚；完成后输出 diff、真实命令、Evidence 和剩余风险。
- 内部审查过程不得写入 Codex-facing 交付物；只交付事实、发现、修复、验证和风险。

## 2. Stage 总览

| Stage | 名称 | 结果 |
|---:|---|---|
| 0 | 只读重基线、最新需求锁定与历史去影响 | 当前事实与最新合同 |
| 1 | 发布身份、App 入口、缓存与真实重装闭环 | 同一新 UI 入口 |
| 2 | 真实数据根目录、Source Manifest 与时间真相 | 真实来源与时间真相 |
| 3 | 标准化交易、Economic Event、Interconnection 与统一账本 | 统一账本与关联 |
| 4 | 账户、持仓、估值 Read Model 与禁止假零 | 可信核心指标 |
| 5 | 公式注册表、财务口径与模型有效性验证 | 可验证财务模型 |
| 6 | 10 入口信息架构、真实路由与共享上下文 | 正常软件路由 |
| 7 | 差异化人类工作流与真实持久化 | 真实业务闭环 |
| 8 | 明亮高级设计系统、动态反馈、触感与无障碍 | 明亮高质感体验 |
| 9 | 分析结论、报告、敏感性与决策复盘 | 可审计分析报告 |
| 10 | Durable Jobs、Runtime Diff、缓存依赖与可观测性 | 可恢复后台任务 |
| 11 | SQLite 并发、迁移、备份恢复、隐私与系统边界 | 可靠本地数据层 |
| 12 | 真实 E2E、目标 Mac UAT、回归防线与发布冻结 | 真实发布验收 |


# Stage 0 — 只读重基线、最新需求锁定与历史去影响

## Pursuing Goal Point

先把当前仓库、运行入口、数据根目录、版本状态和历史约束重新核实为当前事实；将本对话最新决策设为唯一产品合同，历史材料只保留可验证的风险与架构参考。

## 范围

只读审计、状态台账、最新需求合同、历史决策废弃表、P0/P1/P2 差距清单。

## 非范围

不改业务 UI，不迁移数据，不重装 App，不修改财务公式，不进入 Stage 1。

## Allowed Files / Data Boundary

- 只读：PFI/README.md、VERSION、PRODUCT.md、HANDOFF.md、功能清单.md、开发记录.md、模型参数文件.md
- 只读：PFI/web、PFI/src、PFI/tests、PFI/config、PFI/docs、PFI/reports、PFI/macos、PFI/scripts
- 只读：MetaDatabase/PFI、PFI/MetaDatabase、$PFI_DATA_HOME、~/.pfi（不得输出私密值）
- 可写：PFI/docs/pfi_v025/stage_0/*、PFI/reports/pfi_v025/stage_0/*、PFI/config/pfi_v025_active_requirements.json

## Phase → Task

### Phase 0.1 — 当前事实重基线

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S0-P1-T1 | 记录 Git/分支/HEAD/remote 与工作树。 | `git_state.txt` | 信息可复现 |
| S0-P1-T2 | 盘点活动 UI、启动入口、App、端口、版本与 bundle。 | `entry_inventory.json` | 入口来源明确 |
| S0-P1-T3 | 盘点代码、测试、报告、数据库和数据根目录。 | `repository_inventory.json` | 无全仓改动 |
| S0-P1-T4 | 运行只读语法、测试收集与 SQLite 版本检查。 | `terminal.log` | 失败真实记录 |

### Phase 0.2 — 最新需求与历史去影响

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S0-P2-T1 | 冻结 v0.2.5 Active Requirements。 | `pfi_v025_active_requirements.json` | 10 入口与边界正确 |
| S0-P2-T2 | 生成 Superseded / Reference-only 决策表。 | `history_deprecation.md` | 旧约束不再驱动开发 |
| S0-P2-T3 | 确认 PFI、Alpha、PFI OS、Cloudflare public shell 的边界。 | `scope_boundary.md` | 无第二活动 UI |
| S0-P2-T4 | 建立单 Phase 执行与 Stage 用户验收规则。 | `run_contract.md` | 不得自动推进 |

### Phase 0.3 — 差距与修复排序

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S0-P3-T1 | 把历史发现标为 StillPresent / Fixed / Regressed / N/A / New。 | `finding_ledger.csv` | 每项有证据 |
| S0-P3-T2 | 生成 P0/P1/P2 当前差距清单。 | `gap_register.md` | 优先级可执行 |
| S0-P3-T3 | 生成 Stage 0 Evidence Pack。 | `reports/pfi_v025/stage_0` | 可审计 |
| S0-P3-T4 | 停止并等待用户验收。 | `acceptance_request.md` | 不进入 Stage 1 |


## Acceptance Criteria

- 记录 git 分支、HEAD、origin/main、工作树状态和最近提交。
- 列出所有当前入口、活动 UI、启动脚本、App bundle、服务端口和版本来源。
- 列出所有候选数据根目录、数据库、原始文件、记录数、时间范围、hash 与权限状态，但不泄露内容。
- 把 8/9/6 入口旧约束、旧原型、旧 closeout 声明标为非当前产品合同。
- 机器合同固定 10 个一级入口并包含“市场与研究”。
- README、HANDOFF、开发记录、VERSION、页面 build identity 的冲突被列为阻断，不得自行宣称已统一。

## Stop Condition

- 工作树存在无法解释的未提交改动。
- 当前分支或 remote main 无法确认。
- 读取数据需要修改、移动、解密或上传私密文件。
- 发现当前运行实例与仓库不是同一代码来源。

## Pass Gate

用户接受只读基线、最新需求合同、历史废弃表和差距清单后，才可进入 Stage 1。

## Validation

```bash
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git log -5 --oneline
python3 --version && node --version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests -q --collect-only
```

## Evidence Pack

- baseline.json
- git_state.txt
- current_state_matrix.md
- data_root_inventory.json
- history_deprecation.md
- terminal.log

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

本 Stage 不修改业务代码；删除新建的 v0.2.5 基线文档即可回滚。

## Human Acceptance

用户确认当前事实、10 入口、版本边界和“先完成真实产品、不扩功能”的方向。

> **Stage 0 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 1。


# Stage 1 — 发布身份、App 入口、缓存与真实重装闭环

## Pursuing Goal Point

彻底解决“声称重装但用户点击仍是旧 UI”的复发问题，让 Finder App、localhost、后端、前端和静态资源拥有同一可验证发布身份。

## 范围

四方 release manifest、App bundle 版本、启动 URL、缓存/Service Worker/Streamlit 缓存策略、真实重装和 Finder 启动证据。

## 非范围

不修财务数据，不重构页面信息架构，不用版本文案冒充入口生效。

## Allowed Files / Data Boundary

- PFI/VERSION、PFI/config/release_manifest.json、PFI/web/app/version.js、PFI/web/index.html（只限身份/缓存握手）
- PFI/src/pfi_v02/stage_v021_runtime_api.py（只限 release manifest API）
- PFI/macos/*、PFI/StartPFI.command、PFI/StopPFI.command、PFI/scripts/*（只限启动/安装/诊断）
- PFI/tests/test_v025_stage1_*、PFI/web/tests/v025/stage1_*、PFI/reports/pfi_v025/stage_1/*

## Phase → Task

### Phase 1.1 — 四方发布身份

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S1-P1-T1 | 建立机器可读 release manifest。 | `config/release_manifest.json` | 字段完整 |
| S1-P1-T2 | 绑定 App plist 与 launcher URL。 | `macOS bundle/config` | 版本一致 |
| S1-P1-T3 | 绑定后端 API 与前端嵌入 manifest。 | `API + version.js` | 握手一致 |
| S1-P1-T4 | 实现 mismatch fail-visible。 | `中文错误页` | 不静默加载旧 UI |

### Phase 1.2 — 缓存与旧 UI 根因治理

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S1-P2-T1 | 审计 HTTP、Service Worker、bfcache 和 Streamlit cache。 | `cache_audit.md` | 每层有状态 |
| S1-P2-T2 | 实现 hashed asset + HTML revalidation。 | `headers/build config` | 旧资源不可复用 |
| S1-P2-T3 | 实现 Service Worker 更新/旧 cache 清理或明确禁用。 | `sw evidence` | 无旧 worker 控制 |
| S1-P2-T4 | 实现 pageshow 与 runtime manifest 再校验。 | `frontend guard` | bfcache 可恢复 |

### Phase 1.3 — 真实安装与入口验收

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S1-P3-T1 | 备份并真实重装 App bundle。 | `install log` | 非文档声明 |
| S1-P3-T2 | Finder、localhost、新 profile、清缓存验收。 | `screenshots + trace` | 同一 bundle |
| S1-P3-T3 | 验证 /Applications、Desktop、Downloads 候选入口。 | `entry matrix` | 唯一 canonical app |
| S1-P3-T4 | 生成 Evidence 并停止。 | `stage_1 evidence` | 等待用户验收 |


## Acceptance Criteria

- CFBundleShortVersionString、CFBundleVersion、launcher URL、后端 manifest、前端 manifest 同一版本/build/commit。
- HTML 使用可重验证策略；内容变更的 JS/CSS 采用 hash URL；若存在 Service Worker，版本激活和旧 cache 清理有证据。
- pageshow/bfcache 与前后端 manifest mismatch 能检测并给出中文恢复操作。
- Streamlit read model 缓存 key 至少包含 build、data_hash、parameter_hash、fx_snapshot_id。
- 真实备份并重装 App bundle；从 Finder 点击启动，不能只开浏览器 URL。
- 全新浏览器 profile、普通刷新、强制刷新、前进/后退均显示同一 v0.2.5 build。

## Stop Condition

- 无法确定当前 App bundle 来自哪个源目录。
- App 重装需要覆盖未知用户文件或私密数据。
- 四方身份不一致。
- 必须通过手工清浏览器历史才能看到新 UI。

## Pass Gate

用户从 Finder 启动 App，页面显示同一 v0.2.5 release identity；localhost 与 App 的 frontend hash、backend hash、commit 相同。

## Validation

```bash
plutil -p <PFI.app>/Contents/Info.plist
shasum -a 256 PFI/web/index.html PFI/web/app/*.js
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests/test_v025_stage1_release_identity.py -q
npx playwright test PFI/web/tests/v025/stage1_release_entry.spec.* --trace on-first-retry
curl -fsS http://127.0.0.1:8501/api/release-manifest
```

## Evidence Pack

- release_manifest.json
- app_info_plist.json
- asset_hashes.json
- cache_headers.json
- service_worker_audit.md
- finder_launch.png
- browser_validation.json
- playwright_trace.zip

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

重装前保存旧 App bundle 的 hash 和备份；失败时恢复旧 bundle，不触碰用户数据目录。

## Human Acceptance

用户亲自从 Finder 点击 App，确认不是旧 UI，并确认页面内 release identity 与 Evidence 一致。

> **Stage 1 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 2。


# Stage 2 — 真实数据根目录、Source Manifest 与时间真相

## Pursuing Goal Point

把“有数据”转换成可审计的数据清单，明确哪些真实数据可支持哪些指标；建立 source、coverage、as-of、hash 和时间语义，禁止再把未挂链误写为 0。

## 范围

数据根目录选择、source manifest、只读真实数据测试沙盒、时间字段、FX 有效日与数据可计算性矩阵。

## 非范围

不删除或移动原始数据，不直接计算最终净资产，不把 8815 条流水等同于账户余额或持仓。

## Allowed Files / Data Boundary

- PFI/config/sources/*、PFI/config/schemas/v025/*、PFI/src/pfi_os/data/*、PFI/src/pfi_v02/stage_v025_*
- PFI/scripts/v025/data_inventory.py、PFI/tests/test_v025_stage2_*、PFI/docs/pfi_v025/stage_2/*、PFI/reports/pfi_v025/stage_2/*
- 只读：候选 MetaDatabase 与 PFI 私有数据根目录；禁止把真实内容写入 Git

## Phase → Task

### Phase 2.1 — 数据根目录与来源清单

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S2-P1-T1 | 盘点所有候选真实数据根目录。 | `data_root_inventory.json` | 只读 |
| S2-P1-T2 | 选定 canonical root 与 alias 策略。 | `data_root_decision.md` | 不搬数据 |
| S2-P1-T3 | 生成 Source Manifest。 | `source_manifest.json` | 状态与 hash 完整 |
| S2-P1-T4 | 生成指标可计算性矩阵。 | `metric_computability_matrix.json` | 依赖明确 |

### Phase 2.2 — 时间真相与 FX

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S2-P2-T1 | 建立八类时间字段与时区合同。 | `temporal_truth.md` | Australia/Sydney |
| S2-P2-T2 | 实现 06:00 有效 FX 日规则。 | `fx_policy.py/schema` | 周末/假日回退 |
| S2-P2-T3 | 建立 FX snapshot/source/hash/stale 状态。 | `fx_snapshot_status.json` | 不硬编码 |
| S2-P2-T4 | 验证普通运行不联网。 | `network audit` | 无隐式请求 |

### Phase 2.3 — 真实数据安全测试沙盒

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S2-P3-T1 | 创建真实数据只读快照/临时隔离副本机制。 | `sandbox spec` | 不写生产 |
| S2-P3-T2 | 建立脱敏日志和禁止财务 fixture 检查。 | `privacy/no-fake tests` | 无真实值泄露 |
| S2-P3-T3 | 对真实规模运行读/解析基线。 | `performance baseline` | 记录耗时与内存 |
| S2-P3-T4 | Evidence 与用户验收。 | `stage_2 evidence` | 不进入 Stage 3 |


## Acceptance Criteria

- 确定一个 canonical private data root；其他位置只作为显式 alias，不自动搬迁。
- 每个 source 有 source_id、类型、capabilities、路径别名、record_count、coverage、as_of、hash、status。
- 明确“交易流水可用”不等于“账户余额/净资产/持仓可计算”。
- 时间模型至少含 transaction_time、posted_at、effective_at、imported_at、reconciled_at、valued_at、fx_effective_at、report_as_of。
- 真实数据测试只使用只读副本/切片；若不可用，财务测试标记 blocked，不得 fallback 到 fake。
- FX 4.81 只作为语义示例；生产 rate 来自实际 snapshot，普通运行不联网。

## Stop Condition

- 候选数据根目录存在冲突且无法判断 canonical。
- 读取真实数据会改变源文件、文件时间或数据库。
- 需要暴露真实账户、交易明细或密钥到日志/仓库。
- FX 来源、有效日或方向语义不明确。

## Pass Gate

Source Manifest、可计算性矩阵和时间真相合同获用户接受；所有核心指标的缺失依赖明确。

## Validation

```bash
python3 PFI/scripts/v025/data_inventory.py --read-only --redact --json-out <evidence>/source_manifest.json
python3 -m pytest PFI/tests/test_v025_stage2_source_manifest.py -q
python3 -m pytest PFI/tests/test_v025_stage2_temporal_truth.py -q
python3 -m pytest PFI/tests/test_v025_stage2_fx_policy.py -q
```

## Evidence Pack

- source_manifest.json
- data_root_decision.md
- metric_computability_matrix.json
- temporal_coverage.json
- fx_snapshot_status.json
- privacy_scan.txt

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

只撤销 registry/schema 变更；不对原始数据执行回滚，因为本 Stage 禁止修改数据。

## Human Acceptance

用户确认 canonical data root、数据范围和“哪些指标当前可算/不可算”。

> **Stage 2 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 3。


# Stage 3 — 标准化交易、Economic Event、Interconnection 与统一账本

## Pursuing Goal Point

建立来源记录到真实经济事件再到统一账本的可追溯链路，防止多来源重复计算、转账误算、退款未抵消和页面口径分裂。

## 范围

Source/Profile、账户角色、标准化交易、interconnection_group、economic_event、ledger、对账与幂等。

## 非范围

不直接设计全部页面，不生成 AI 自由文本结论，不把数据源名称写死为业务类别。

## Allowed Files / Data Boundary

- PFI/config/sources/*、PFI/config/event_types/*、PFI/config/schemas/v025/*
- PFI/src/pfi_os/domain/*、PFI/src/pfi_os/application/*、PFI/src/pfi_os/infrastructure/*
- PFI/tests/test_v025_stage3_*、PFI/docs/pfi_v025/stage_3/*、PFI/reports/pfi_v025/stage_3/*

## Phase → Task

### Phase 3.1 — 来源与账户角色

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S3-P1-T1 | 建立可扩展 Source Profile。 | `source profile schema` | 无名称硬编码 |
| S3-P1-T2 | 建立多角色账户与生效期。 | `account role schema` | 角色可重叠 |
| S3-P1-T3 | 绑定 parser/version/source hash。 | `parser provenance` | 可追溯 |
| S3-P1-T4 | 未知角色进入复核。 | `review queue` | 不自动猜测发布 |

### Phase 3.2 — 标准化与经济事件

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S3-P2-T1 | 标准化交易字段与方向。 | `normalized schema` | 金额/币种/时间完整 |
| S3-P2-T2 | 建立 Interconnection Group。 | `grouping engine` | 可解释规则 |
| S3-P2-T3 | 建立 Economic Event 与影响 flags。 | `event policy` | 口径明确 |
| S3-P2-T4 | 发布统一 Ledger Event。 | `ledger model` | 幂等 key |

### Phase 3.3 — 对账、幂等与差异

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S3-P3-T1 | 真实数据重复导入测试。 | `idempotency result` | 零重复发布 |
| S3-P3-T2 | 转账/退款/投资链路对账。 | `reconciliation result` | 差异可定位 |
| S3-P3-T3 | 生成 Interconnection Matrix。 | `formal UI data contract` | 主链路覆盖 |
| S3-P3-T4 | Evidence 与用户验收。 | `stage_3 evidence` | 停止 |


## Acceptance Criteria

- source/account profile 支持 capabilities、多角色和角色生效期。
- 每条发布记录能追溯 raw_record_id、normalized_transaction_id、interconnection_group_id、economic_event_id、ledger_event_id。
- 同一源文件重复导入不产生重复账本事件。
- 自有账户转账、信用卡还款、退款、投资入金、基金/黄金申购、投资买卖有明确影响 flags。
- 同一 economic event 在同一 metric 内只计算一次；跨页面可展示但 read_model_hash 一致。
- 对账差异不能静默消失，必须进入 review_queue。

## Stop Condition

- 无法区分 source record 与 economic event。
- 一笔真实事件在同一指标重复计算。
- 账户角色仍按“支付宝=消费、券商=投资”硬编码。
- 需要修改用户真实数据来让测试通过。

## Pass Gate

真实数据只读副本上的重复导入、转账、退款和投资链路对账通过，lineage 可回溯。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage3_source_profiles.py -q
python3 -m pytest PFI/tests/test_v025_stage3_interconnection.py -q
python3 -m pytest PFI/tests/test_v025_stage3_no_double_count.py -q
python3 -m pytest PFI/tests/test_v025_stage3_idempotency.py -q
```

## Evidence Pack

- event_type_matrix.json
- lineage_samples_redacted.json
- reconciliation_summary.json
- idempotency_result.json
- review_queue_summary.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

数据库 migration 必须可逆或前向补偿；执行前使用 SQLite Online Backup/VACUUM INTO 创建一致快照。

## Human Acceptance

用户能从任一指标向下追到来源、关联组、经济事件和账本事件。

> **Stage 3 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 4。


# Stage 4 — 账户、持仓、估值 Read Model 与禁止假零

## Pursuing Goal Point

把账户余额、资产负债、持仓、价格、汇率和时间快照连接成统一 Read Model；非 ready 状态不得显示真实 0。

## 范围

账户/余额快照、持仓/成本基础、价格/FX、负债、估值、metric state、跨页同源。

## 非范围

不以交易流水推测不存在的期初余额，不用样例持仓补全，不修改真实账户数据。

## Allowed Files / Data Boundary

- PFI/src/pfi_os/domain/accounts*、holdings*、valuation*、PFI/src/pfi_os/application/read_models/*
- PFI/src/pfi_v02/stage_v021_runtime_api.py、PFI/web/app/data_state.js（只限 read model contract）
- PFI/tests/test_v025_stage4_*、PFI/docs/pfi_v025/stage_4/*、PFI/reports/pfi_v025/stage_4/*

## Phase → Task

### Phase 4.1 — 账户与余额

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S4-P1-T1 | 建立账户/余额/负债快照合同。 | `account snapshot schema` | 边界明确 |
| S4-P1-T2 | 处理 opening/closing balance 与现金对账。 | `cash read model` | 不推测假零 |
| S4-P1-T3 | 建立账户 coverage 与 status。 | `coverage report` | 缺失可见 |
| S4-P1-T4 | 实现账户与首页同源接口。 | `read model API` | hash 相同 |

### Phase 4.2 — 持仓、成本与估值

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S4-P2-T1 | 建立持仓 snapshot 与交易关联。 | `holding model` | 数量可追溯 |
| S4-P2-T2 | 明确成本基础与费用。 | `cost basis policy` | 不可猜测 |
| S4-P2-T3 | 绑定价格、FX 与估值时间。 | `valuation model` | PIT 对齐 |
| S4-P2-T4 | 生成投资 read model。 | `investment snapshot` | 来源完整 |

### Phase 4.3 — Metric State 与跨页一致性

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S4-P3-T1 | 扩展 metric state machine。 | `metric_state schema` | 非 ready 无 0 |
| S4-P3-T2 | 实现 read_model_hash 与依赖 hash。 | `hash contract` | 可重建 |
| S4-P3-T3 | 验证首页/业务页/报告同源。 | `consistency result` | 零差异 |
| S4-P3-T4 | Evidence 与用户验收。 | `stage_4 evidence` | 停止 |


## Acceptance Criteria

- 净资产、现金、资产、负债、投资市值等每个 metric 有状态、来源、coverage、as_of、valuation、formula 和 hash。
- 状态至少覆盖 ready、confirmed_zero、partial_coverage、source_missing、not_loaded、path_error、parse_failed、outdated_snapshot、permission_denied、calculation_failed、reconciliation_failed、valuation_missing、filtered_empty。
- 只有 confirmed_zero 且证据完整时可显示 CNY 0.00。
- 交易数据存在但期初余额/持仓/价格缺失时，页面显示缺失依赖，不推断为零。
- 首页、账户、投资、消费、报告使用同一 read_model_hash。
- 持仓估值明确 original currency、price_as_of、fx_effective_at 与 valuation_as_of。

## Stop Condition

- 无法获得账户期初/期末余额或持仓快照。
- 成本基础规则无法确定。
- 价格/汇率时间点无法与持仓对齐。
- 任何非 ready 状态被渲染为 0。

## Pass Gate

核心 metric 状态在真实输入下可解释；无假零；跨页面数值和 hash 一致。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage4_metric_states.py -q
python3 -m pytest PFI/tests/test_v025_stage4_accounts_read_model.py -q
python3 -m pytest PFI/tests/test_v025_stage4_holdings_valuation.py -q
python3 -m pytest PFI/tests/test_v025_stage4_cross_page_consistency.py -q
```

## Evidence Pack

- core_metric_states.json
- read_model_status.json
- valuation_coverage.json
- cross_page_hashes.json
- no_false_zero_result.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

read model 是可重建派生层；回滚代码和 schema 后重建，不覆盖 raw/ledger/用户输入。

## Human Acceptance

用户可清楚判断：真为零、数据缺失、数据过期、估值缺失还是计算失败。

> **Stage 4 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 5。


# Stage 5 — 公式注册表、财务口径与模型有效性验证

## Pursuing Goal Point

让每个财务指标都能回答“怎么算、用什么参数、基于哪些数据、是否有效、调整会怎样”，并把用户指定的双消费口径准确落地。

## 范围

公式/参数版本、CNY/FX、双消费口径、分类/标签、置信度维度、投资与现金流模型、不变量与敏感性验证。

## 非范围

不把 AI 文本当计算引擎，不以单个“置信度”掩盖 coverage/估值/模型问题，不自动交易。

## Allowed Files / Data Boundary

- PFI/模型参数文件.md、PFI/config/pfi_parameters.yaml、PFI/config/formulas/*、PFI/config/schemas/v025/*
- PFI/src/pfi_v02/*formula*、*model*、*analysis*、PFI/src/pfi_os/application/metrics/*
- PFI/tests/test_v025_stage5_*、PFI/docs/pfi_v025/stage_5/*、PFI/reports/pfi_v025/stage_5/*

## Phase → Task

### Phase 5.1 — 公式与参数治理

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S5-P1-T1 | 建立公式注册表和版本生命周期。 | `formula_registry.json` | 定义完整 |
| S5-P1-T2 | 同步 Markdown/YAML/代码/UI 参数。 | `consistency test` | 零冲突 |
| S5-P1-T3 | 实现 CNY/FX 公式和单位检查。 | `unit/FX tests` | 方向正确 |
| S5-P1-T4 | 拆分多维可信度。 | `confidence schema` | 不混为一分 |

### Phase 5.2 — 财务模型与用户口径

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S5-P2-T1 | 实现双消费与投资流出组件。 | `dual metrics` | 用户口径可解释 |
| S5-P2-T2 | 实现净资产/现金/资产负债不变量。 | `core formulas` | 账本守恒 |
| S5-P2-T3 | 实现投资收益、成本、XIRR 与拖累。 | `investment formulas` | 时间/费用完整 |
| S5-P2-T4 | 实现现金流七窗口、分类和标签规则。 | `cashflow/taxonomy` | 参数一致 |

### Phase 5.3 — 有效性、敏感性与校准

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S5-P3-T1 | 在真实只读数据上运行不变量/变形测试。 | `invariant result` | 不破坏生产 |
| S5-P3-T2 | 运行参数敏感性与边界分析。 | `sensitivity report` | 可解释 |
| S5-P3-T3 | 生成模型验证卡与限制。 | `model card` | 不夸大 |
| S5-P3-T4 | Evidence 与用户验收。 | `stage_5 evidence` | 停止 |


## Acceptance Criteria

- 公式注册表含 formula_id/version/中文定义/输入/输出/单位/参数/边界/依赖/test/effective_from/hash。
- 主币种 CNY；AUD/CNY 方向固定为 1 AUD = X CNY；4.81 仅示例。
- 主 UI/报告同时显示消费总流出、生活消费、投资资金流出/配置金额。
- 消费总流出是用户定义的活动口径，不得解释为净资产损失；同一 source record 不重复，同一经济事件按公式规则计数。
- 置信度拆为记录分类、来源覆盖、对账覆盖、估值覆盖、模型验证、报告完整度，不用一个总分替代。
- 保留 v0.2.2 中文评分权重作为记录分类置信度；阈值 70，不按 source 分层。
- 现金流 7/21/30/60/90/180/360、投资收益/成本/XIRR/费用/汇率/现金拖累等公式有真实验证结果。

## Stop Condition

- 公式与用户业务口径冲突。
- 投资入金/买入链路存在未解释的双计。
- 没有足够真实数据验证某模型却仍宣称有效。
- Markdown、YAML、代码、UI 使用不同参数值。

## Pass Gate

公式注册表一致性、真实数据不变量、回归/敏感性和跨页指标验证通过；未验证模型明确标记 blocked。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage5_formula_registry.py -q
python3 -m pytest PFI/tests/test_v025_stage5_dual_consumption.py -q
python3 -m pytest PFI/tests/test_v025_stage5_financial_invariants.py -q
python3 -m pytest PFI/tests/test_v025_stage5_model_validation.py -q
```

## Evidence Pack

- formula_registry.json
- parameter_consistency.json
- dual_consumption_reconciliation.json
- invariant_results.json
- sensitivity_results.json
- model_validation_card.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

公式变更使用 effective_from/version；旧版本保留可回放，禁止原地篡改历史报告使用的公式。

## Human Acceptance

用户能读懂双口径、公式、参数和模型局限，并可判断是否要调整。

> **Stage 5 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 6。


# Stage 6 — 10 入口信息架构、真实路由与共享上下文

## Pursuing Goal Point

把 PFI 从长页/模板切换恢复为正常软件：10 个固定一级入口，二级页有唯一 URL、独立页面语义、浏览器历史和稳定共享上下文。

## 范围

导航、route registry、alias、breadcrumbs、history、focus/scroll restoration、页面差异化合同、无 JS fallback。

## 非范围

不在本 Stage 完成所有业务功能，不增加第 11 个一级入口，不复制旧入口工作区。

## Allowed Files / Data Boundary

- PFI/web/index.html、PFI/web/app/routes.js、shell.js、navigation.js、PFI/web/styles/*（只限 IA/路由）
- PFI/src/pfi_v02/stage_v025_navigation.py、PFI/tests/test_v025_stage6_*、PFI/web/tests/v025/stage6_*
- PFI/docs/pfi_v025/stage_6/*、PFI/reports/pfi_v025/stage_6/*

## Phase → Task

### Phase 6.1 — 导航与 alias

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S6-P1-T1 | 固定 10 个一级入口和顺序。 | `nav contract` | 正好 10 |
| S6-P1-T2 | 建立旧入口 alias matrix。 | `alias matrix` | 不显示为一级 |
| S6-P1-T3 | 统一策略实验室 canonical route。 | `route registry` | 单实例 |
| S6-P1-T4 | 删除隐藏/底部/辅助树入口污染。 | `DOM audit` | 无 16 栈 |

### Phase 6.2 — 独立二级页面合同

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S6-P2-T1 | 为每个二级页定义 job-to-be-done。 | `page contracts` | 非模板克隆 |
| S6-P2-T2 | 定义页面独有数据、主操作与状态。 | `page data/actions` | 结构差异 |
| S6-P2-T3 | 实现 breadcrumb/title/focus/scroll。 | `navigation behavior` | 可恢复 |
| S6-P2-T4 | 实现深链与无 JS fallback。 | `fallback pages` | 不空白 |

### Phase 6.3 — 浏览器历史与验收

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S6-P3-T1 | 实现 History API 状态恢复。 | `route runtime` | back/forward 正常 |
| S6-P3-T2 | 测试刷新、深链、重复点击和无效 route。 | `Playwright result` | 错误可行动 |
| S6-P3-T3 | 测试可访问性树只含 10 入口。 | `a11y result` | 无隐藏污染 |
| S6-P3-T4 | Evidence 与用户验收。 | `stage_6 evidence` | 停止 |


## Acceptance Criteria

- 视觉、DOM、accessibility tree 和无 JS fallback 都只有 10 个一级入口。
- 固定入口：首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置。
- 旧首页/市场/研究/持仓/策略实验室/数据与系统只作为 alias 或二级路由，不创建重复状态。
- 每个二级入口有 canonical URL、页面 title、breadcrumb、主任务、独立空/错/加载状态。
- pushState/replaceState/popstate 正确恢复前进后退；刷新深链不丢页面。
- 策略实验室只有 `/market-research/strategy-lab` 一个 canonical 实例。

## Stop Condition

- 页面仍靠锚点滚动或 display:none 长页冒充路由。
- 视觉 10 入口但隐藏/辅助树仍暴露 16 个同层入口。
- 二级页面仅更换标题和相同卡片模板。
- route state 与 URL 不一致。

## Pass Gate

10 个一级入口和选定二级深链在 desktop/mobile/keyboard/back-forward/reload/no-JS 中全部通过。

## Validation

```bash
node --check PFI/web/app/shell.js
python3 -m pytest PFI/tests/test_v025_stage6_navigation_contract.py -q
npx playwright test PFI/web/tests/v025/stage6_routes.spec.* --trace on-first-retry
npx playwright test PFI/web/tests/v025/stage6_a11y_tree.spec.*
```

## Evidence Pack

- route_registry.json
- alias_matrix.json
- page_contracts.json
- browser_history_validation.json
- a11y_tree.json
- nojs_navigation.png

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

保留旧 route registry 快照；失败时恢复但不得把旧 16 入口重新设为正式导航。

## Human Acceptance

用户逐一点击 10 个一级入口和重点二级入口，确认每次像进入新页面而非模板换标题。

> **Stage 6 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 7。


# Stage 7 — 差异化人类工作流与真实持久化

## Pursuing Goal Point

完成用户真正会使用的核心闭环，不再展示“任务已准备”：上传→预览→复核→入账；持仓编辑→SQLite→刷新/重启；指标/报告→下钻→证据/参数。

## 范围

上传导入、复核、账本、持仓 CRUD、参数中心、Interconnection Map、指标下钻、设置持久化。

## 非范围

不自动交易，不把 toast 当成功，不在本地存储冒充数据库。

## Allowed Files / Data Boundary

- PFI/web/app/pages/*、components/*、PFI/web/styles/*、PFI/src/pfi_v02/runtime API
- PFI/src/pfi_os/application/use_cases/*、infrastructure/operational_store*、migrations/*
- PFI/tests/test_v025_stage7_*、PFI/web/tests/v025/stage7_*、PFI/docs/pfi_v025/stage_7/*、PFI/reports/pfi_v025/stage_7/*

## Phase → Task

### Phase 7.1 — 上传、导入、复核、账本

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S7-P1-T1 | 实现真实上传与 hash/source 识别。 | `upload use case` | 无外传 |
| S7-P1-T2 | 实现解析预览、映射和错误状态。 | `import preview` | 不虚构 |
| S7-P1-T3 | 实现待复核队列和确认入账。 | `review workflow` | 可撤销 |
| S7-P1-T4 | 验证幂等、失败恢复和账本同步。 | `E2E evidence` | 闭环 |

### Phase 7.2 — 持仓与设置持久化

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S7-P2-T1 | 实现持仓新增/编辑/删除 API。 | `holding API` | 输入校验 |
| S7-P2-T2 | 写入 SQLite 并更新 read model。 | `DB + projection` | 事务一致 |
| S7-P2-T3 | 验证刷新/浏览器关闭/服务重启。 | `persistence evidence` | 仍存在 |
| S7-P2-T4 | 实现设置偏好正式持久化。 | `settings store` | 设置页隔离 |

### Phase 7.3 — 指标、参数与关联下钻

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S7-P3-T1 | 正式集成参数中心。 | `secondary page` | 中文可读 |
| S7-P3-T2 | 正式集成 Interconnection Map。 | `secondary page` | 可点击 |
| S7-P3-T3 | 实现指标到来源/公式/事件的下钻。 | `metric drilldown` | lineage 完整 |
| S7-P3-T4 | Evidence 与用户验收。 | `stage_7 evidence` | 停止 |


## Acceptance Criteria

- 上传真实文件后显示来源、大小、hash、解析器、预览、字段映射、错误和待复核数量。
- 确认入库后统一账本更新；重复导入不重复；失败可重试/回滚。
- 持仓编辑通过 API 写 SQLite；刷新、关浏览器、重启服务后仍存在；首页/投资/报告同步。
- 参数中心与 Interconnection Map 是正式二级页面，不是旁路审查 HTML 或开发控制台。
- 指标下钻显示数据范围、formula/parameter/data/read-model hash、来源和阻断。
- 设置偏好写入 SQLite 或正式配置存储；仅设置页显示反馈控制。

## Stop Condition

- 保存只改变前端 state/localStorage/sessionStorage/IndexedDB。
- 按钮只弹 toast，无 API/DB 证据。
- 真实文件解析失败却生成虚构预览。
- 参数中心或 Interconnection 仍是旁路 HTML。

## Pass Gate

三条真实核心流程在浏览器和数据库层闭环通过，并有刷新/重启证据。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage7_import_review_ledger.py -q
python3 -m pytest PFI/tests/test_v025_stage7_holding_persistence.py -q
python3 -m pytest PFI/tests/test_v025_stage7_metric_drilldown.py -q
npx playwright test PFI/web/tests/v025/stage7_workflows.spec.* --trace on-first-retry
sqlite3 "$PFI_DB" 'PRAGMA foreign_key_check; SELECT COUNT(*) FROM holding_snapshots;'
```

## Evidence Pack

- upload_import_trace.json
- ledger_before_after.json
- holding_db_before_after.json
- restart_persistence.json
- metric_drilldown.json
- parameter_center.png
- interconnection_map.png

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

每个写操作有 transaction/compensation；数据迁移前备份；失败恢复快照并保留失败 evidence。

## Human Acceptance

用户实际完成一次导入/复核、一次持仓编辑和一次指标下钻，确认操作逻辑自然。

> **Stage 7 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 8。


# Stage 8 — 明亮高级设计系统、动态反馈、触感与无障碍

## Pursuing Goal Point

在真实工作流基础上建立明亮、克制、有质感的个人财务软件体验；动效和触感服务状态与操作，不制造 AI 痕迹或炫技。

## 范围

design tokens、组件、数据可视化、响应式、motion、haptics、状态反馈、WCAG 2.2 AA。

## 非范围

不复制 KMFA，不默认暗色，不用动画掩盖慢任务，不显示 AI 正在思考。

## Allowed Files / Data Boundary

- PFI/web/styles/*、PFI/web/app/components/*、PFI/web/app/motion.js、haptics.js、accessibility.js
- PFI/web/index.html（只限语义/组件挂载）、PFI/tests/test_v025_stage8_*、PFI/web/tests/v025/stage8_*
- PFI/docs/pfi_v025/stage_8/*、PFI/reports/pfi_v025/stage_8/*

## Phase → Task

### Phase 8.1 — 设计系统与可视化

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S8-P1-T1 | 建立亮色 token 和组件规范。 | `design system` | 默认亮色 |
| S8-P1-T2 | 为页面 archetype 建差异化布局。 | `page patterns` | 不克隆 |
| S8-P1-T3 | 建立可访问图表和空/错/过期状态。 | `chart system` | 不画假线 |
| S8-P1-T4 | 完成 desktop/mobile 响应式。 | `responsive CSS` | 无手机样机 |

### Phase 8.2 — 动效、进度与触感

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S8-P2-T1 | 实现页面/组件状态动效。 | `motion runtime` | 可降级 |
| S8-P2-T2 | 实现反馈延迟预算。 | `feedback system` | 无假进度 |
| S8-P2-T3 | 实现 haptics/sound opt-in。 | `settings + capability` | 默认克制 |
| S8-P2-T4 | 实现长任务后台时间线。 | `job UI` | 可离开页面 |

### Phase 8.3 — 无障碍与人工质感验收

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S8-P3-T1 | 完成 WCAG 2.2 AA 自动检查。 | `axe/contrast` | 零阻断 |
| S8-P3-T2 | 完成人工键盘/焦点/屏幕阅读流程。 | `manual a11y` | 可操作 |
| S8-P3-T3 | 完成视觉回归和跨 viewport 截图。 | `visual evidence` | 稳定 |
| S8-P3-T4 | Evidence 与用户验收。 | `stage_8 evidence` | 停止 |


## Acceptance Criteria

- 默认亮色：温暖白/浅灰基底，蓝/绿/金语义点缀；暗色仅可选。
- 视觉 token 覆盖颜色、间距、字体、圆角、阴影、焦点、状态和图表。
- 0–100ms pressed/focus；100–300ms 页面/缓存结果；>300ms skeleton；>1s 进度；>10s durable job。
- 动效支持 prefers-reduced-motion；View Transition 只作渐进增强。
- 触感能力检测、默认轻量、设置可关；不支持时静默降级。
- 满足 WCAG 2.2 AA：键盘、焦点、对比、target size、状态消息、财务/数据错误预防。
- 桌面与移动均为正式布局，桌面不展示手机模型。

## Stop Condition

- 默认仍为暗色控制台。
- 多个页面仅换标题而视觉结构相同。
- 动效造成阻塞、眩晕或隐藏错误。
- 自动 accessibility scan 或人工键盘流程失败。

## Pass Gate

核心 10 页面及重点二级页通过视觉、响应式、reduced-motion、keyboard、axe/WCAG 与人工质感验收。

## Validation

```bash
npx playwright test PFI/web/tests/v025/stage8_visual.spec.* --trace on-first-retry
npx playwright test PFI/web/tests/v025/stage8_accessibility.spec.*
python3 -m pytest PFI/tests/test_v025_stage8_design_tokens.py -q
python3 -m pytest PFI/tests/test_v025_stage8_feedback_budget.py -q
```

## Evidence Pack

- design_tokens.json
- desktop_pages/*.png
- mobile_pages/*.png
- reduced_motion.json
- keyboard_flow.json
- axe_results.json
- contrast_results.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

设计 token 和组件版本化；回滚不改变业务数据和公式。

## Human Acceptance

用户确认明亮、专业、有质感，操作反馈自然，整体不再像 AI 机械堆叠。

> **Stage 8 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 9。


# Stage 9 — 分析结论、报告、敏感性与决策复盘

## Pursuing Goal Point

让用户真正看到可判断模型正确性和有效性的分析，而不是只有图表、占位状态或 AI 总结；每份报告都能回到公式、参数、数据和异常。

## 范围

报告 schema、完整度状态、净资产/现金/投资/消费/现金流/数据质量报告、敏感性、模型卡、建议生命周期、导出。

## 非范围

不生成无来源事实，不自动下单，不把未满足依赖的报告伪装成完整报告。

## Allowed Files / Data Boundary

- PFI/src/pfi_os/application/reports/*、analysis/*、decisions/*、PFI/web/app/pages/reports/*、review/*
- PFI/config/reports/*、PFI/tests/test_v025_stage9_*、PFI/web/tests/v025/stage9_*
- PFI/docs/pfi_v025/stage_9/*、PFI/reports/pfi_v025/stage_9/*

## Phase → Task

### Phase 9.1 — 报告合同与完整度

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S9-P1-T1 | 建立报告 schema 和 manifest。 | `report schema` | 可追溯 |
| S9-P1-T2 | 建立 complete/partial/blocked 状态。 | `completeness rules` | 不假结论 |
| S9-P1-T3 | 实现数据质量与缺口报告。 | `quality report` | 任何状态可生成 |
| S9-P1-T4 | 绑定同一 read model/formula/parameter。 | `hash checks` | 跨页一致 |

### Phase 9.2 — 财务分析与模型验证

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S9-P2-T1 | 实现净资产/现金/投资/消费/现金流报告。 | `report set` | 只生成可算内容 |
| S9-P2-T2 | 实现公式下钻和敏感性预览。 | `validation UI` | 参数影响可见 |
| S9-P2-T3 | 实现模型验证卡和限制。 | `model cards` | 不夸大 |
| S9-P2-T4 | 实现异常到来源的复核入口。 | `drilldown` | 可行动 |

### Phase 9.3 — 建议、复盘与导出

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S9-P3-T1 | 实现建议生命周期和人工复核。 | `decision objects` | 不自动交易 |
| S9-P3-T2 | 实现反方证据和失效条件。 | `review UI` | 可反驳 |
| S9-P3-T3 | 实现多格式同源导出。 | `exports + manifest` | 一致 |
| S9-P3-T4 | Evidence 与用户验收。 | `stage_9 evidence` | 停止 |


## Acceptance Criteria

- 报告包含 data range、sample count、coverage、as_of、formula/parameter/data/read_model hash、结论、异常、限制、复核入口。
- 缺数据时仍可生成数据质量报告，但完整财务报告为 blocked/partial，不生成假结论。
- 主报告展示双消费口径及其组件，并解释活动口径与净资产损失不同。
- 模型验证页展示不变量、敏感性、历史/样本外结果（若有）、局限和调整影响。
- 建议对象含证据、反方证据、失效条件、风险、组合影响、人工复核状态。
- HTML/PDF/CSV/Markdown 导出来自同一 report snapshot，不同格式 hash/manifest 可追踪。

## Stop Condition

- 报告只有自然语言总结，没有数据/公式/范围。
- 完整度不足仍输出确定性建议。
- 页面与导出使用不同 read_model 或参数。
- 建议可以直接触发交易。

## Pass Gate

至少数据质量报告与当前可计算的财务报告通过真实输入、跨格式一致性和人工复核。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage9_report_schema.py -q
python3 -m pytest PFI/tests/test_v025_stage9_report_consistency.py -q
python3 -m pytest PFI/tests/test_v025_stage9_model_validation.py -q
npx playwright test PFI/web/tests/v025/stage9_reports.spec.* --trace on-first-retry
```

## Evidence Pack

- report_manifest.json
- data_quality_report.*
- report_consistency.json
- model_validation_report.html
- sensitivity_view.png
- decision_review_trace.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

报告不可变、按 report_id/version 保存；新版本失败不覆盖旧报告。

## Human Acceptance

用户能用报告判断数据是否够、公式是否正确、模型是否有效、参数如何调整。

> **Stage 9 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 10。


# Stage 10 — Durable Jobs、Runtime Diff、缓存依赖与可观测性

## Pursuing Goal Point

把上传、解析、重算和报告生成从伪进度升级为可恢复的持久化任务；只在依赖变化时重算，并能用 trace 定位失败。

## 范围

job lifecycle、claim/lease/heartbeat/retry/cancel/dead-letter、dependency hash、runtime diff、trace/log、失败恢复。

## 非范围

不在普通运行中自动联网或触发 LLM，不让后台任务直接发布未经验证的财务事实。

## Allowed Files / Data Boundary

- PFI/src/pfi_os/application/jobs/*、infrastructure/jobs/*、supervisor/*、observability/*
- PFI/src/pfi_v02/runtime_diff*、PFI/web/app/jobs/*、PFI/config/jobs/*
- PFI/tests/test_v025_stage10_*、PFI/web/tests/v025/stage10_*、PFI/docs/pfi_v025/stage_10/*、PFI/reports/pfi_v025/stage_10/*

## Phase → Task

### Phase 10.1 — 持久任务生命周期

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S10-P1-T1 | 实现 durable job schema。 | `job tables` | 状态完整 |
| S10-P1-T2 | 实现 claim/lease/heartbeat/CAS。 | `worker protocol` | 避免重复 |
| S10-P1-T3 | 实现 retry/cancel/dead-letter。 | `recovery policy` | 可恢复 |
| S10-P1-T4 | 实现真实进度事件。 | `job events` | 非计时器 |

### Phase 10.2 — 依赖 Diff 与缓存

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S10-P2-T1 | 建立 dependency graph/hash。 | `dependency registry` | 可解释 |
| S10-P2-T2 | 实现 impacted metrics 收紧。 | `diff engine` | 不全量误报 |
| S10-P2-T3 | 绑定 Streamlit/前端 cache key 与 TTL。 | `cache contract` | 不陈旧 |
| S10-P2-T4 | 验证普通运行零联网。 | `network audit` | 通过 |

### Phase 10.3 — 可观测性与故障恢复

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S10-P3-T1 | 传播 trace_id/span_id。 | `trace context` | 跨阶段 |
| S10-P3-T2 | 实现结构化日志与脱敏。 | `logs` | 不泄露私密值 |
| S10-P3-T3 | 测试 kill/restart/offline/超时。 | `failure matrix` | 状态一致 |
| S10-P3-T4 | Evidence 与用户验收。 | `stage_10 evidence` | 停止 |


## Acceptance Criteria

- 任务支持 queued/running/retrying/succeeded/failed/cancelled/dead_letter，带 revision/lease/heartbeat。
- 超过 10 秒任务可离开页面，重启后可恢复/确认失败。
- runtime diff 覆盖 raw/source/ledger/interconnection/parameter/formula/fx/read-model/report hash。
- 无 diff 不联网、不重算、不触发 Codex/LLM。
- 每个任务有 trace_id/span_id、阶段时间、错误、影响范围、重试和缓存回退。
- UI 进度来自真实任务状态，不用计时器模拟。

## Stop Condition

- 任务仅存在进程内存。
- 无 lease/CAS 导致重复执行。
- 任务失败后 UI 仍显示成功。
- 普通启动触发网络或全量重算。

## Pass Gate

长任务在 kill/restart/offline 场景可恢复或明确失败，依赖 diff 精确，UI 与 DB 状态一致。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage10_job_lifecycle.py -q
python3 -m pytest PFI/tests/test_v025_stage10_runtime_diff.py -q
python3 -m pytest PFI/tests/test_v025_stage10_crash_recovery.py -q
npx playwright test PFI/web/tests/v025/stage10_jobs.spec.* --trace on-first-retry
```

## Evidence Pack

- job_state_transitions.json
- crash_recovery.json
- runtime_diff.json
- impacted_metrics.json
- trace_export.json
- network_audit.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

任务 schema 迁移可回滚/补偿；未发布的任务可取消，已发布财务快照不可原地删除。

## Human Acceptance

用户看到真实步骤、进度、失败原因、重试和结果入口，不再看到假排队/假进度。

> **Stage 10 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 11。


# Stage 11 — SQLite 并发、迁移、备份恢复、隐私与系统边界

## Pursuing Goal Point

让本地数据库和运行环境真正可长期使用：安全版本、事务、迁移、完整性检查、原子备份恢复和清晰的公共/私有边界。

## 范围

SQLite runtime gate、WAL/rollback/busy timeout、migration、backup/restore、integrity、数据域隔离、Alpha read-only Context、Cloudflare public isolation。

## 非范围

不把 Cloudflare public shell 当私有 PFI 完成证据，不把 Alpha/Ralpha/Serenity 变成 PFI 功能。

## Allowed Files / Data Boundary

- PFI/src/pfi_os/infrastructure/operational_store*、migrations/*、backup/*、security/*
- PFI/scripts/pfi、PFI/scripts/v025/*、PFI/config/data_domains/*、PFI/shared/context/*
- PFI/tests/test_v025_stage11_*、PFI/docs/pfi_v025/stage_11/*、PFI/reports/pfi_v025/stage_11/*

## Phase → Task

### Phase 11.1 — SQLite 安全与并发

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S11-P1-T1 | Gate SQLite version 与 WAL 风险。 | `runtime gate` | 安全版本 |
| S11-P1-T2 | 配置 WAL/timeout/foreign keys/transactions。 | `store config` | 可审计 |
| S11-P1-T3 | 建立 migration 生命周期。 | `migration registry` | 可恢复 |
| S11-P1-T4 | 运行并发、断电模拟与 rollback 测试。 | `stress evidence` | 不损坏 |

### Phase 11.2 — 备份、恢复与完整性

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S11-P2-T1 | 实现一致在线备份。 | `backup command` | snapshot 完整 |
| S11-P2-T2 | 实现隔离 restore rehearsal。 | `restore command` | 不覆盖生产先验 |
| S11-P2-T3 | 运行 integrity/foreign_key/应用不变量。 | `verification` | 全部通过 |
| S11-P2-T4 | 实现失败自动回滚。 | `rollback evidence` | 可恢复 |

### Phase 11.3 — 产品与数据域边界

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S11-P3-T1 | 隔离 public Cloudflare shell。 | `boundary contract` | 非第二 UI |
| S11-P3-T2 | 实现最小只读 PFI Context Export。 | `context schema` | 版本化/脱敏 |
| S11-P3-T3 | 扫描 Alpha/Ralpha/Serenity/私密泄露。 | `boundary scan` | 零违规 |
| S11-P3-T4 | Evidence 与用户验收。 | `stage_11 evidence` | 停止 |


## Acceptance Criteria

- 记录并 Gate SQLite runtime version；WAL 并发使用已修复 WAL-reset bug 的版本或安全 backport。
- 连接配置 foreign_keys=ON、busy_timeout、显式 transaction/rollback；migration 有版本和恢复策略。
- 备份使用 SQLite Online Backup API/VACUUM INTO 等一致快照方式，而非在线 cp。
- restore 在隔离副本验证 integrity_check 与 foreign_key_check 后原子替换；失败自动回滚。
- public Cloudflare shell 不读取 PRIVATE_USER/PRIVATE_DERIVED；不成为第二活动 UI。
- Alpha 只能读取版本化、最小化、只读 PFI Context；无 Ralpha；Serenity-Alipay 排除。

## Stop Condition

- SQLite 版本处于已知 WAL-reset 风险范围且启用高并发 WAL。
- backup/restore 不能在隔离环境演练。
- 恢复可能覆盖未知数据且无回滚。
- 公共 surface 或日志包含私有财务值/密钥/绝对路径。

## Pass Gate

并发、迁移、完整性、真实备份恢复演练和数据域扫描通过；公共/Alpha 边界明确。

## Validation

```bash
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
python3 -m pytest PFI/tests/test_v025_stage11_sqlite_concurrency.py -q
python3 -m pytest PFI/tests/test_v025_stage11_migrations.py -q
python3 -m pytest PFI/tests/test_v025_stage11_backup_restore.py -q
python3 -m pytest PFI/tests/test_v025_stage11_data_domain_isolation.py -q
```

## Evidence Pack

- sqlite_runtime.json
- pragma_settings.json
- concurrency_result.json
- migration_rehearsal.json
- backup_restore_rehearsal.json
- integrity_checks.txt
- private_distribution_scan.txt

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

保留 pre-migration 和 pre-restore 一致快照；恢复失败自动回到原生产副本。

## Human Acceptance

用户确认 backup/restore 可操作，公共页面不暴露私密数据，Alpha 不是 PFI 入口。

> **Stage 11 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 12。


# Stage 12 — 真实 E2E、目标 Mac UAT、回归防线与发布冻结

## Pursuing Goal Point

用真实 App、真实数据状态、真实路由、真实数据库和真实报告完成最终验收；形成防止旧 UI、假零、模板页面和文档式完成复发的回归防线。

## 范围

自动化 E2E、目标 Mac 生命周期、Finder App、性能/无障碍/恢复、Evidence index、用户验收绑定和 release freeze。

## 非范围

不在验收阶段新增功能，不以用户回复单个数字替代明确验收对象，不自动开始 v0.2.6。

## Allowed Files / Data Boundary

- PFI/tests/test_v025_stage12_*、PFI/web/tests/v025/stage12_*、PFI/scripts/v025/release_acceptance.py
- PFI/docs/pfi_v025/stage_12/*、PFI/reports/pfi_v025/stage_12/*、PFI/README.md、HANDOFF.md、VERSION（仅最终状态）
- 必要的回归修复只能回到对应 Stage allowed files，不得在 Stage 12 偷改功能。

## Phase → Task

### Phase 12.1 — 自动化真实 E2E 与回归

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S12-P1-T1 | 运行 release identity/route/data/report 回归。 | `test matrix` | 无 P0/P1 |
| S12-P1-T2 | 运行真实导入/持仓/报告流程。 | `E2E trace` | 非 fixture |
| S12-P1-T3 | 运行 accessibility/performance/visual。 | `quality evidence` | 达标 |
| S12-P1-T4 | 验证 no old UI/no false zero/no template clone。 | `regression result` | 通过 |

### Phase 12.2 — 目标 Mac 与 Finder UAT

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S12-P2-T1 | 真实安装并从 Finder 启动。 | `app evidence` | 同一 build |
| S12-P2-T2 | 运行启停/重复启动/休眠唤醒/断网恢复。 | `lifecycle matrix` | 可恢复 |
| S12-P2-T3 | 运行磁盘/备份/恢复演练。 | `resilience evidence` | 数据完整 |
| S12-P2-T4 | 用户完成人类任务 UAT。 | `UAT result` | 缺陷记录 |

### Phase 12.3 — 状态统一与发布冻结

| Task | 任务 | 交付物 | 验收短句 |
|---|---|---|---|
| S12-P3-T1 | 统一 VERSION/README/HANDOFF/三基状态。 | `current summary` | 无冲突 |
| S12-P3-T2 | 生成 final evidence index 与 hash。 | `index + sha256` | 不可篡改 |
| S12-P3-T3 | 生成绑定 release 的验收请求。 | `human_acceptance.json` | 范围明确 |
| S12-P3-T4 | 用户接受后冻结；否则保持 blocked。 | `release state` | 不自动下一版 |


## Acceptance Criteria

- 从 Finder App 和 localhost 完成关键真实流程，release identity 完全一致。
- 真实数据可用时完成导入/复核、持仓保存、指标/报告下钻；缺失时正确阻断且绝不假零。
- Playwright 保留失败 trace、截图、视频/网络记录；axe/WCAG、性能和 accessibility tree 通过。
- 目标 Mac 完成 start/stop/restart/repeated start、浏览器关闭、sleep/wake、offline/recovery、磁盘不足、backup/restore。
- README/HANDOFF/三基文件仅保留当前摘要，详细历史移入版本化 docs；状态一致。
- 用户验收对象绑定 version、build、commit、evidence index hash、时间、已知缺陷和明确接受范围。

## Stop Condition

- 任何 P0/P1 未关闭。
- App bundle 未真实安装。
- 真实财务流未运行且被写成 pass。
- Evidence 缺命令、截图、数据库或 trace。
- 用户验收未绑定具体 release/evidence。

## Pass Gate

所有阶段 Gate、回归、目标 Mac UAT 和用户明确验收通过，才可标记 v0.2.5 accepted；否则保持 candidate/blocked。

## Validation

```bash
python3 -m pytest PFI/tests/test_v025_stage12_release_gates.py -q
npx playwright test PFI/web/tests/v025/stage12_e2e.spec.* --trace on-first-retry
python3 PFI/scripts/v025/release_acceptance.py --real-data-required --finder-app-required --evidence-out PFI/reports/pfi_v025/stage_12
python3 PFI/scripts/validate_project_governance.py --project PFI
git diff --check
```

## Evidence Pack

- final_evidence_index.json
- release_identity.json
- real_data_e2e.json
- playwright_traces/*
- target_mac_lifecycle.json
- backup_restore_result.json
- accessibility.json
- performance.json
- human_acceptance.json

每个 Phase 还必须生成：`evidence.json`、`terminal.log`、`changed_files.txt`、`risk_and_rollback.md`。涉及浏览器、App、数据库或报告的 Phase 必须增加对应截图、trace、DB before/after、manifest/hash。

## Rollback Plan

Release freeze 前保留上一个可恢复 App 和数据库备份；任何失败回到具体 Stage，不在最终验收中临时补丁。

## Human Acceptance

用户按 UAT 清单逐项确认，并明确接受绑定的 v0.2.5 release；未确认不得 closeout。

> **Stage 12 停止点：**完成候选只能写“等待用户验收”；未经用户明确接受，不得进入 Stage 下一版本。


# 附录 A — 固定一级入口与 alias

| 一级入口 | Canonical route |
|---|---|
| 首页总览 | `/overview` |
| 账户与资产 | `/accounts` |
| 账本流水 | `/ledger` |
| 投资管理 | `/investment` |
| 消费管理 | `/consumption` |
| 数据源与上传 | `/data` |
| 建议与复盘 | `/review` |
| 报告与洞察 | `/reports` |
| 市场与研究 | `/market-research` |
| 设置 | `/settings` |

兼容 alias：

- `/home` → `/overview`
- `/market` → `/market-research/market`
- `/research` → `/market-research/research`
- `/holdings` → `/investment/holdings`
- `/strategy-lab`、`/investment/strategy-lab` → `/market-research/strategy-lab`
- `/data-system` → `/settings/data-system`

alias 不能出现在一级导航、accessibility tree 或无 JS 一级入口列表中。

# 附录 B — 最低发布 Gate

只有以下全部满足，v0.2.5 才能进入最终用户验收：

1. Finder App 已真实安装，四方 release identity 一致。
2. 真实数据 Source Manifest 与 metric computability 可审计。
3. 非 ready 指标不显示 CNY 0.00。
4. 10 个一级入口和真实二级路由通过浏览器前进/后退/刷新。
5. 上传复核账本、持仓 SQLite 持久化、指标报告下钻形成真实闭环。
6. 双消费口径、FX、公式、参数和报告同源。
7. 亮色设计、动态反馈、触感降级和 WCAG 2.2 AA 通过。
8. 长任务、缓存、备份恢复、SQLite 完整性和失败恢复通过。
9. Evidence 有真实命令、截图、trace、DB 和 hash。
10. 用户验收绑定 version/build/commit/evidence hash；不得用单个数字或模糊“继续”替代。
