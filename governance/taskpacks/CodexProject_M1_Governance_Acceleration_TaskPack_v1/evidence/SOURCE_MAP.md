# Source Map（执行时须重新验证）

观察日期：2026-06-25 (Australia/Sydney review time)

| 事实 | 来源 |
|---|---|
| 观察 HEAD / S4PCT02 | GitHub commit `2d2e6eb9401dceb127f9f1f2041bcce57564d5c6` |
| 双平面、三个中文文件、Roadmap、T0-T3、零写入 | `AGENTS.md`, `docs/governance/STANDARD.md` |
| changed-only 固定 semantic/enforce-sync/check-render | `scripts/lean_governance.py::run_changed_only_ci` |
| 整个工作树 clean 作为退出条件 | `scripts/lean_governance.py` 中 `dirty = git_status_porcelain(root)` / `zero_diff = not dirty` / exit expression |
| root governance fan-out | `ROOT_GOVERNANCE_PREFIXES`, `build_changed_scope` |
| EEI/arxiv 排除 | `governance/projects.yaml::root_governance.changed_scope_excluded_projects` |
| PR/push changed-only；scheduled/manual all | `.github/workflows/project-governance.yml` |
| README stale current snapshot | `README.md::Current Governance Snapshot` |
| 优化建议来源 | 用户上传 `优化治理V0.1.rtf` |

## 外部官方参考

- Codex subagents：只在显式要求时 spawn；适合独立只读工作，但增加 Token。
- Codex worktrees：用于相互隔离的并行写入；只读审查无需为每个 Agent 复制工作树。
- AGENTS.md：保持短而实用；详细重复工作流放 Skill/标准，按需加载。

本包不复制仓库源码，以避免快照成为新的漂移事实。Codex 必须直接读取执行时 HEAD。
