# TASK_REPORT · ADP-S0-P03-T008｜安装小任务证据、验证和独立复核框架

## 唯一目标（达成）

确保一个任务一个结果、可回滚、可机器验收且由独立上下文复核 —— 交付 task runner、schema validator、evidence template、dependency DAG checker。

## 六个开始前问题（已回答，方允许编码）

1. 唯一目标：安装任务级证据/验证/独立复核工具，机器可验收且不允许自签 PASS。
2. 允许修改文件：仅 `docs/pursuing_goal/v0_1/TASK_INDEX.csv` + `docs/pursuing_goal/v0_1/tools/*`（check_dag.py、validate_evidence.py、task_runner.py、EVIDENCE_TEMPLATE.md、README.md）+ 本证据包 + 治理同步文件；无 worker/schema/生产代码。
3. 绝不能改变：已上线 MVP、六主题、高级动效、实时稳定；工具**只读**，不修改仓库/生产。NOT_DEPLOYED。
4. 基线：main `d2399d91`（= origin/main，T007 已合入）；90 任务索引源自最终包 06_TASK_INDEX.csv。
5. 验收：90 个 task ID 唯一、依赖无环；缺证据时状态不能 PASS；实现者不能自签 Stage Gate。
6. 回滚：`git revert <sha>`；纯工具/文档新增，NOT_DEPLOYED，无生产影响。

## 交付物

- `docs/pursuing_goal/v0_1/TASK_INDEX.csv` —— 90 任务机器索引（task_id/stage/phase/priority/size/dependencies/release_mode/…）。
- `tools/check_dag.py` —— 依赖 DAG 检查（唯一/存在/无环）。
- `tools/validate_evidence.py` —— 证据 schema 校验（必需文件/完成标记/未自签 PASS/cost 可解析）。
- `tools/task_runner.py` —— 一任务一结果 + 依赖门 + 证据校验。
- `tools/EVIDENCE_TEMPLATE.md` —— 每任务证据包模板。
- `tools/README.md` —— 用法与硬规则。

## 验收结果（实测，见 test-results/tool_selftest.txt）

- **90 唯一 + 无环**：`check_dag.py` → `RESULT: PASS`（unique task_ids 90，dependency edges 123，无 dangling，无环），exit 0。
- **缺证据不能 PASS**：`validate_evidence.py ADP-S1-P01-T009`（无 bundle）→ `STATUS: INCOMPLETE`，exit 1。
- **完整证据也只到 READY（不 PASS）**：`validate_evidence.py ADP-S0-P02-T007` → `READY_FOR_INDEPENDENT_VERIFICATION`（显式声明不发 PASS），exit 0。
- **依赖门**：`task_runner.py ADP-S1-P01-T009`（依赖 T008 未就绪）→ `BLOCKED_BY_DEPS`，exit 1；`ADP-S0-P02-T007`（依赖已就绪）→ READY，exit 0。
- **未知任务**：`task_runner.py BOGUS-ID` → `UNKNOWN_TASK`，exit 2。
- **实现者不能自签**：validator 检测 TASK_REPORT 中的 `Verifier: PASS / gate: pass` 等自签模式并判 INCOMPLETE；所有工具最强只到 READY。

## Data / Performance / Visual

- Data：无写入（工具只读）。
- Performance：本地/CI 计算，毫秒级。
- Visual：无变更。

## Value / Cost

- Value：防止大包开发和虚假完成 —— 每任务须过 DAG + 证据 + 依赖门，且 PASS 只能由独立上下文判定。
- Cost：**仅 CI/本地计算**，0 经常性云成本。

## Known gaps

见 `known_gaps.md`（工具为静态校验；运行时/内容质量不在其内；status 字段不自动回写）。

## 不适用证据项

`migration.sql/rollback.sql`（无 schema）、`benchmarks`（无性能压测）、`screenshots-or-videos`（无 UI）、`data-samples`（无数据）、`deployment_manifest.preview.json`（NOT_DEPLOYED）—— 均 N/A。

## 完成声明

```text
Task: ADP-S0-P03-T008
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: TASK_INDEX.csv + 5 tools/* + 证据（含 test-results）+ 治理同步（见 changed_files.txt）
Tests: tool_selftest.txt —— check_dag PASS / validate READY|INCOMPLETE / runner READY|BLOCKED|UNKNOWN（exit 码符合预期）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: check_dag 90 唯一无环；validator 缺证据=INCOMPLETE 且从不发 PASS；runner 依赖门 + 一任务一结果
Data/Performance/Visual: N/A（工具只读）
Value: 防大包/防虚假完成；PASS 仅独立复核可判
Cost: 0 经常性云成本（仅 CI/本地计算）
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯工具/文档新增）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
