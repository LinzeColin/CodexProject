# FIFA S5PBT01 中文结构验收报告

- 任务：`S5PBT01`
- 验收：`ACC-S5PBT01`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

FIFA 的 S5PBT01 把主动研究流水线、legacy 实现、生成产物和本地 ops 资料分清楚。默认开发和测试入口仍是 `FIFA/tab-research-pipeline/`。`legacy/fifa-analysis-system/` 只用于历史追溯，`artifacts/` 只保存生成结果，`ops/` 只保存本地运维参考；本任务不启用投注自动化。

## 中文验收标准

- Owner 不读英文表也能判断哪个目录是主动源码，哪个目录只是历史或输出。
- 必须明确禁止：下注、提交票据、绕过 TAB 控制、把 artifacts 当源码。
- 结构治理只记录边界，不改变产品运行结果和外部集成。

## 停止条件与结果

- legacy 参与默认运行：`未触发`
- active pipeline 路径被改变：`未触发`
- generated artifacts 被当作源码事实：`未触发`
- ops docs 被当作 runtime source：`未触发`
- betting automation 被启用：`未触发`
- private values 被输出：`未触发`

## 回滚

优先用 git revert 回退 S5PBT01 任务提交。本任务不移动 legacy、artifact、ops 或 active pipeline 文件，回滚只删除结构合同、结构报告、smoke log、README/AGENTS 边界说明、测试和 run manifest。

## 下一步

后续 Wave2 gate 只能确认边界和证据，不得把 FIFA 从 research-only 提升到投注或交易自动化。

---

## 原技术记录

# FIFA S5PBT01 结构报告

任务：`S5PBT01`
验收：`ACC-S5PBT01`
日期：2026-06-25

## 范围

本报告绑定 Wave 2 manifest 之后的 FIFA 项目结构。主动 pipeline、legacy 实现、生成产物和本地 ops 资料已明确分层，产品 runtime 行为没有改变。机器可读合同：
`governance/stage_gates/s5pb/fifa_structure_contract.yaml`.

## 结构边界

| 层级 | 路径 | 职责 | 默认运行路径 |
|---|---|---|---|
| 主动 pipeline | `FIFA/tab-research-pipeline/` | parser、validation、export smoke、app scripts、tests | 是 |
| Legacy | `FIFA/legacy/fifa-analysis-system/` | 只读历史实现和测试 | 否 |
| Artifacts | `FIFA/artifacts/` | 生成的最新报告和备份 | 否 |
| Ops docs | `FIFA/ops/` | 本地 launch agent、cleanup、slim/audit 说明 | 否 |

## S5PBT01 决策

- `tab-research-pipeline/` remains the only default active pipeline path.
- `legacy/fifa-analysis-system/` 为追溯和回滚上下文保留原位，但默认 FIFA smoke 路径不会 import 或执行它。
- `artifacts/latest/` 和 `artifacts/backups/` 仍是生成输出层；它们的 S5PAT02 archive candidates 保持 checksum-bound，S5PBT01 不移动。
- `tab-research-pipeline/assets/app_icon/` 仍是主动 UI asset 资料，本任务不归档。
- `ops/` 只是本地运行文档和 launch metadata，不是 application source。

## Legacy 引用审计

- 主动脚本或代码对 `legacy/fifa-analysis-system` 的引用：未观察到。
- 文档对 `legacy/fifa-analysis-system` 的引用：保留在 `FIFA/tab-research-pipeline/HANDOFF.md`，作为历史清单。
- 默认命令路径：`cd FIFA/tab-research-pipeline`，随后执行 focused parser/validation/export smoke tests。

## Smoke 证据

日志：`governance/stage_gates/s5pb/fifa_smoke_tests.log`

Focused smoke 命令：

```text
set PYTHONPATH=C:\Users\linze\Documents\Codex\2026-06-23\xian\work\test_stubs;.&& C:\Users\linze\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m unittest tests.test_pipeline.PipelineTests.test_parse_market_pairs tests.test_pipeline.PipelineTests.test_parse_market_pairs_rejects_invalid_decimal_odds_tokens tests.test_pipeline.PipelineTests.test_matches_gate_blocks_invalid_raw_decimal_odds tests.test_pipeline.PipelineTests.test_write_outputs tests.test_pipeline.PipelineTests.test_write_outputs_fails_closed_without_success_deliverables_when_gate_blocks tests.test_pipeline.PipelineTests.test_write_outputs_legacy_blocked_export_requires_explicit_flag -q
```

结果：`通过`，6 个测试通过。

## 回滚方式

回滚优先使用 git revert 回退 S5PBT01 任务提交。由于 S5PBT01 不移动 legacy、artifact、ops 或 active pipeline 文件，回滚只移除结构合同、结构报告、smoke log、README/AGENTS 边界说明、测试和 run manifest。

## 停止条件保持情况

- FIFA legacy 参与默认运行：未触发。
- active pipeline 路径被改变：未触发。
- generated artifacts 被当作源码事实：未触发。
- ops docs 被当作 runtime source：未触发。
- betting automation 被启用：未触发。
- private values 被输出：未触发。
