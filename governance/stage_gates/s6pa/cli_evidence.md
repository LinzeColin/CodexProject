# S6PA-GATE CLI 证据

本文件满足 Roadmap 的 `screenshots_or_cli_evidence` 证据要求。本轮 S6PA 改动是 Owner/Agent 可读路径，不是产品 UI 重构，因此使用 CLI、README 第一屏和 manifest 证据，不要求截图。

## 证据边界

- 中文优先，默认全局中文；用户可读优先。
- 证据来自 S6PAT01 矩阵、8 个 S6PAT02 单项目 manifest、对应 README 第一屏和 PR/main CI。
- 本 Gate 不运行外部账户、不发邮件、不触发 OpenD、不安装 launchd、不打包 app、不移动项目文件。
- Alpha 与 EVA_OS 的 pytest 依赖缺口保持 blocker，不把未运行测试写成通过。

## 8 项目 CLI 证据

| 项目 | Owner 路径证据 | CLI/阻塞证据 |
|---|---|---|
| Alpha | README 第一屏提供当前状态、结构边界、最小测试路径 | `No module named pytest`、`No module named yaml` 环境 blocker 已记录 |
| EVA_OS | README 第一屏提供当前状态、下一 Gate、风险、运行/测试/证据路径 | `No module named pytest` 环境 blocker 已记录 |
| OpMe_System | README 第一屏提供 active source、delivery bundle、demo input、失败去向和回滚 | `set PYTHONPATH=backend&& .venv\Scripts\python.exe -m pytest backend\tests -q` -> `8 passed, 1 warning in 6.66s` |
| whkmSalary | README 第一屏提供最小测试命令、配置位置、source/config/startup 边界 | `python -B -m unittest discover -s tests -q` -> `Ran 10 tests in 0.173s; OK` |
| FIFA | README 第一屏提供 active pipeline、legacy、artifact、ops 边界和最小 smoke 路径 | tab-research-pipeline unittest smoke -> `Ran 6 tests in 0.192s; OK` |
| OpenAIDatabase | README 第一屏提供隐私边界、默认入口、private export 安全确认 | privacy/context/memory unittest smoke -> `Ran 3 tests OK; Ran 1 test OK; Ran 1 test OK` |
| PFI_BIG_DATA_SIMULATOR | README 第一屏提供 qbvs/config/tests/runs/reports 边界和最小 unittest 路径 | `python -B -m unittest tests.test_s3pct02_lifecycle -q` -> `Ran 1 test in 1.277s; OK` |
| Serenity-Alipay | README 第一屏提供 app/tests/data/manual/runtime/output/external automation 边界 | `python -B -m unittest tests.test_s3pct03_lifecycle -q` -> `Ran 4 tests in 0.053s; OK` |

## Feedback 与撤销

- 进行中反馈：每个 README 第一屏显示当前任务/Gate 或下一 Gate。
- 成功反馈：已运行的项目记录 PASS/OK；不能运行的项目记录环境 blocker。
- 错误/空状态反馈：每个项目保留失败去向、依赖缺口或日志位置。
- 安全确认：高风险项目明确不触发交易、外部自动化、OpenD、真实邮件、launchd 或 app 打包。
- 可撤销：每个 S6PAT02 manifest 和本 Gate 均记录 revert/rollback 路径。

## Gate 结论

`S6PA-GATE` 在 Owner/Agent 操作路径范围内通过。下一步是 `S6PBT01`，不能跳过三 Agent 独立复审，也不能提前声明 `S6-GATE` 通过。
