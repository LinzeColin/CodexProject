# TASK_REPORT · ADP-S0-P01-T003｜落库一句话 Pursuing Goal 与机器合同

## 唯一目标（达成）

让每个 Codex/Claude/ChatGPT 任务开工前先读取同一目标和硬约束 —— 交付严格单行 `PURSUING_GOAL.txt`、可解析 `MACHINE_CONTRACT.yaml` 与可校验的合同 hash。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：把单一目标 + 硬约束固化为可被任何 agent 首读、可 hash 校验的机器合同。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/` 下新增 `PURSUING_GOAL.txt`、`MACHINE_CONTRACT.yaml`、`MACHINE_CONTRACT.sha256` + 本证据包 + 治理同步文件；无代码/worker/schema/CSP。
3. 绝不能改变：已上线 MVP、六主题、高级动效（hero 视频/仪表盘/氛围层/自愈/no-store）、实时稳定与生产行为。NOT_DEPLOYED。
4. 基线：main `76e80edf`（= origin/main，T002 已合入）；线上 worker = 自托管视频版；无数据变更。
5. 验收：`PURSUING_GOAL.txt` 严格单行（body 无内嵌换行）；`MACHINE_CONTRACT.yaml` 经 `yaml.safe_load` 解析通过；`MACHINE_CONTRACT.sha256` 经 `shasum -a 256 -c` 校验 OK；合同内 `pursuing_goal_sha256` 与 `PURSUING_GOAL.txt` 实际 sha256 一致。
6. 回滚：`git revert <sha>`；NOT_DEPLOYED 无生产影响；未改写数据。

## 交付物

- `docs/pursuing_goal/v0_1/PURSUING_GOAL.txt` —— 严格单行的一句话目标（1 行；body 内嵌换行数 = 0）。
- `docs/pursuing_goal/v0_1/MACHINE_CONTRACT.yaml` —— 机器可读合同：pursuing_goal（含 sha256）、authority_order、hard_constraints、out_of_scope、owner_gates、execution_protocol、baseline_refs（指向 CURRENT_SCOPE/OWNER_DIRECTIVES/PRECEDENCE/CONFLICT_LEDGER/ARCHIVED_NOT_CANONICAL）、canonical_governance、how_to_use。
- `docs/pursuing_goal/v0_1/MACHINE_CONTRACT.sha256` —— 合同 hash（sha256sum 风格，可 `shasum -c` 校验），供后续任务引用：`d7451cb7bf8dd83d95f830aeb5279bdc58a1a479a8dbd153ad2acb3fa3b234e6`。

## 验收结果

- `PURSUING_GOAL.txt`：`awk END{NR}` = 1 行；Python body `"\n" not in body` = True → **严格单行**。
- `MACHINE_CONTRACT.yaml`：`yaml.safe_load` 解析通过（17 个顶层键）；`pursuing_goal_one_line` 无内嵌换行。
- `pursuing_goal_sha256` = `eace98cb…dc4dec2c`，与 `sha256(PURSUING_GOAL.txt)` **一致**。
- `MACHINE_CONTRACT.sha256`：`shasum -a 256 -c` → `MACHINE_CONTRACT.yaml: OK`。合同 hash = `d7451cb7…3b234e6`。
- “后续任务均引用合同 hash”：`how_to_use` 明确要求每个任务先校验 `pursuing_goal_sha256` 与 `MACHINE_CONTRACT.sha256`；本证据登记该 hash 作为引用锚点。

## 业务证据（实际结果）

产出了跨线程/跨 agent 的单一首读入口：任何 ADP V0.1 任务先读 `PURSUING_GOAL.txt` + `MACHINE_CONTRACT.yaml`，用 hash 确认合同未被篡改，再按 authority_order/CONFLICT_LEDGER 裁决冲突，最后才编码 —— 目标一致、可验证、防漂移。

## Data / Performance / Visual

N/A —— 纯文档任务，无数据、无性能、无 UI/视觉变更（六主题与动效基线未触碰）。

## Value / Cost

- Value：跨线程/代理目标一致 + 合同可 hash 校验，降低偏航与被历史材料污染的风险。
- Cost：**0 经常性云成本**；NOT_DEPLOYED（无 worker 部署、无 D1/R2 操作、无 API 调用）。UNKNOWN 项见 known_gaps.md（不记为 0）。

## Known gaps

见 `known_gaps.md`（私有 Cloudflare 事实 FACT-011..015 待 S0-P02；合同 hash 需在后续任务真正被读取校验才形成闭环）。

## 不适用证据项（doc-only）

`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI 变更）、`benchmarks/before|after`（无性能变更）、`data-samples`（无数据）、`test-results`（无代码测试；治理门见提交步骤）、`deployment_manifest.preview.json`（NOT_DEPLOYED）—— 均标记 N/A。

## 完成声明

```text
Task: ADP-S0-P01-T003
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: 3 交付文件 + 治理同步（见 changed_files.txt）
Tests: 单行校验 PASS + YAML 解析 PASS + shasum -c OK（commands.log）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: PURSUING_GOAL.txt（单行）+ MACHINE_CONTRACT.yaml + MACHINE_CONTRACT.sha256（合同 hash d7451cb7…）
Data/Performance/Visual: N/A（未触碰）
Value: 跨线程/代理目标一致 + hash 可校验，降低漂移
Cost: 0 经常性云成本（UNKNOWN 私有事实待 S0-P02，不记为 0）
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（未改写生产数据，已验证为纯文档新增）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
