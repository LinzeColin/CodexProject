# root_contract_diff.md

状态：PASS

本文件是 S2-GATE 只读证据快照，不是新的事实源。根合同事实仍以
`README.md`、`AGENTS.md`、`docs/governance/STANDARD.md`、工作流文件和已提交
run manifest 为准。

## 检查对象

| 合同面 | 当前事实 | 证据 |
|---|---|---|
| 根 README 普通开发命令 | 普通 PR 和本地开发使用 `python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main` | `README.md` |
| 根 README 写入边界 | write-mode generator 不属于普通 PR fast gate，生成视图写入 artifact dir | `README.md` |
| AGENTS 中文主视图 | `功能清单`、`开发记录`、`模型参数文件` 不可降级为链接页；中文优先，默认全局中文 | `AGENTS.md` |
| STANDARD CI 合同 | PR 运行 `lean_governance.py ci --changed-only`；schedule/manual all 才跑 full semantic、dashboard、attestation | `docs/governance/STANDARD.md` |
| 实际 CI 工作流 | PR/main 走 changed-only fast gate；full validator tests 不在 pull_request 上运行 | `.github/workflows/project-governance.yml` |
| Stop Hook | advisory only，不读文件、不起子进程、不阻塞普通开发；只提示 changed-only fast gate | `.codex/hooks/governance_stop.py` |

## S2 入口一致性结论

- 根 README、AGENTS、STANDARD 与当前实际命令一致。
- 产品项目人类视图仍由 `docs/governance/project.yaml`、`roadmap.yaml`、`events.jsonl` 渲染。
- 全局治理整改事实保留在 run manifest 和本 gate 证据中，不写入任何项目产品开发记录。
- 普通 PR 的默认治理计算从全量语义/仪表板/attestation 移出，只保留 changed-only fast gate。

## 绑定提交

- S2PAT01 根 README 快门：`cb43ffe6`
- S2PAT02 项目 README 中文导航：`42fc1d00`
- S2PAT03 人类入口质量门：`55ba4d1e`
- S2PCT02 Hook/CI/预算：`44dc559f`

