# 基线、范围与事实等级

## 观察基线

| 字段 | 值 |
|---|---|
| 仓库 | `LinzeColin/CodexProject` |
| 观察分支 | `main` |
| 观察 SHA | `2d2e6eb9401dceb127f9f1f2041bcce57564d5c6` |
| 观察提交 | `Add Other8 S4PCT02 whkm structure` |
| 当前可见治理任务 | `S4PCT02` |
| Task Pack 类型 | 根治理执行链优化；不是项目产品 Roadmap |

执行时先运行：

```bash
git branch --show-current
git rev-parse HEAD
git status --short
git log -1 --format='%H%n%s%n%cI'
```

若 HEAD 与观察基线不同：

1. 不自动回退或覆盖；
2. 只读检查从 `2d2e6eb9401dceb127f9f1f2041bcce57564d5c6` 到当前 HEAD 是否触及允许文件；
3. 重跑 S1 基线；
4. 重新绑定实施 base；
5. 把差异写入本地审查目录，不改产品 Roadmap。

## 读取范围

优先读取：

- `AGENTS.md`
- `docs/governance/STANDARD.md`
- `governance/projects.yaml`
- `scripts/lean_governance.py`
- `scripts/validate_project_governance.py`
- `.github/workflows/project-governance.yml`
- `tests/governance/` 中直接覆盖上述入口的测试
- 当前任务的 run manifest 与 PR/CI 证据

禁止默认读取全部项目业务代码。只有 fixture/reference 需要时，才读取 validator 已声明的最小路径。

## 写入范围

默认 S1/S2：零写入。

S3-S5 允许的最小候选范围：

- `scripts/lean_governance.py`
- `tests/governance/**`
- 必要时 `.github/workflows/project-governance.yml`
- 必要时 `README.md`（仅移除易漂移动态快照）
- 必要时 `AGENTS.md`、`docs/governance/STANDARD.md`（仅在执行合同确有变化且测试先行）
- 一个与本整改对应的 `governance/run_manifests/*.json`

禁止写入所有项目目录，尤其：`EEI/**`、`arxiv-daily-push/**`。

## 事实等级

- `VERIFIED`：由当前代码、命令输出或 CI 结果直接证明。
- `PARTIALLY_VERIFIED`：部分证据成立，但尚缺真实运行/边界证明。
- `PROPOSED`：建议，尚未实施。
- `UNKNOWN`：不能确认，必须关联具体任务。
- `CONTRADICTED`：现有证据相互冲突。
- `STALE`：曾正确但与当前 HEAD 不一致。

任何 Agent 不得把 `PROPOSED` 写成 `VERIFIED`，也不得把没有运行的压力测试写成通过。
