> # ⚠️ 仓库拆分迁移进行中 —— 给所有 Agent 的最高优先级指令
>
> **本仓库正在被拆分为多个独立仓库。目录会陆续消失。这是有意的，不是数据丢失。**
>
> ## 绝对禁令（优先级高于本文件其余全部规则）
>
> 1. **禁止恢复任何消失的目录或文件。** 不要从 git 历史 `checkout`、不要 `revert`、不要重建、不要从备份还原。
> 2. **禁止把目录消失报告为事故、损坏或数据丢失。** 它不是。
> 3. **禁止"修复"下方表格中已标记为已迁出的项目。**
> 4. 如果你发现某个项目不见了，**先查下表**。表里有 = 已迁走 = 一切正常，继续做你的事。
>
> 违反以上任何一条，都会与迁移过程形成**恢复—删除的死循环**，破坏迁移并可能造成真实的数据损坏。
>
> ## 已迁出项目
>
> | 项目 | 新位置 | 状态 |
> |---|---|---|
> | `whkmSalary` | [LinzeColin/KMOS](https://github.com/LinzeColin/KMOS) | 已迁出，即将从本仓库移除 |
> | `Alpha` | [LinzeColin/MetaDatabase](https://github.com/LinzeColin/MetaDatabase) | 已迁出，即将从本仓库移除 |
> | `FIFA` | [LinzeColin/MetaDatabase](https://github.com/LinzeColin/MetaDatabase) | 已迁出，即将从本仓库移除 |
> | `QBVS` | [LinzeColin/MetaDatabase](https://github.com/LinzeColin/MetaDatabase) | 已迁出，即将从本仓库移除 |
> | `MetaDatabase/` | [LinzeColin/MetaDatabase](https://github.com/LinzeColin/MetaDatabase) → 改名为 `LinzeDatabase/` | 已迁出，即将从本仓库移除 |
> | 治理框架 | [LinzeColin/Governance](https://github.com/LinzeColin/Governance) | 已迁出（本仓库暂保留副本） |
>
> 每一项都已通过 **git tree hash 逐字节比对**，与本仓库内容完全一致后才标记为已迁出。
>
> ## 数据去向
>
> - 全部 agent 历史数据、会话记录 → **`LinzeColin/AgentDatabase`（私有）**，以 Release 附件形式保存
> - 各项目源码 → 见上表
> - **所有迁移都经过 sha256 逐字节校验后才从本仓库移除。没有任何数据丢失。**
>
> ## 若你需要确认
>
> 迁移由 owner 主导。**有疑问就停下并询问 owner，不要自行恢复。**

# CodexProject 主仓库

LinzeColin 的多项目 GitHub main tree 与本机主 checkout。这里是治理与同步入口，不是普通并行开发 worktree。

## Owner 首屏

- 当前用途：多个受治理项目的源码级 GitHub hub 与本机主仓库入口。
- 当前事实源：GitHub `main` 加下方本机 main checkout；普通项目推进应在长期项目 worktree 中做，不在这个主 checkout 中做。
- 过时或高风险根目录：重复 `CodexProject*`、独立项目副本、旧电脑路径、app caches、以及每项目 shadow folders。
- 下一步阅读：先读 [AGENTS.md](AGENTS.md)，再读 [docs/governance/STANDARD.md](docs/governance/STANDARD.md)；进入具体项目时读项目根目录的 `功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 没有明确 run contract 时不要触碰：secrets、runtime DB/WAL/SHM、browser profiles、raw private datasets、caches、以及无关项目目录。
- 待决策：项目级 owner decision 写在项目 human-entry files，以及任何 active `docs/pursuing_goal/**/V*_ROOT_LOCK.yaml`。
- 证据位置：治理事实收敛到项目 `docs/governance/`、`VERSION`、`CHANGELOG.md`、tests、validators、以及 commit-bound evidence。
- 未知处理：如果项目 human-entry files 没有清楚说明当前 Stage/Phase/Task，把状态视为 `UNKNOWN`，并停止等待更窄 handoff。
- 最小下一步：选择一个 project/worktree，验证 `cwd`、git root、branch、remote、HEAD、status，然后只读该项目入口文件再编辑。

## 治理入口

- 执行契约：[AGENTS.md](AGENTS.md)
- Lean v2 标准：[docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- 项目 human-entry files：`功能清单.md`、`开发记录.md`、`模型参数文件.md`

## 本机权威根目录

在 Linze 的本机上，这个 GitHub product hub 的 active 主 checkout 只有一个：
```text
/Users/linzezhang/Documents/Codex/CodexProject
```
不要把重复 `CodexProject*`、`PFI_OS`、`EVA_OS`、或每项目 shadow folders 当作 product roots。清理或迁移前必须验证 `.app` launchers、LaunchAgents、PID files、以及 listening process cwd，确保 PFI、EEI、Alpha、Serenity、OpenAIDatabase/Memory Atlas、arxiv-daily-push 仍解析到这个 checkout。

总工作区：/Users/linzezhang/Documents/Codex

主仓库 / 主 working tree：/Users/linzezhang/Documents/Codex/CodexProject

GitHub source of truth：https://github.com/LinzeColin/CodexProject.git

worktree 根目录：/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/

## Assurance Vocabulary

- `structural_completeness`: required governance files parse and cross-reference.
- `implementation_congruence`: documented implementation values and fingerprints match extractable code/config sources.
- `parameter_source_quality`: active parameter values have source selectors or explicit unresolved tasks.
- `empirical_validation`: model claims are supported by calibration, backtest, fixture, or experiment evidence.
- `operational_validation`: runtime, CI, soak, or production-trial evidence exists.
- `delivery_evidence`: delivery gates and completed tasks have acceptance evidence.
- `evidence_freshness`: events are tree-bound, commit-bound, or honestly listed as legacy unbound.

`machine_verified` is not a production claim. It only maps to implementation congruence when code/config extraction proves documented facts.

## Projects

| Project | Path | Repository |
|---|---|---|
| `EEI` | `EEI` | https://github.com/LinzeColin/CodexProject/tree/main/EEI |
| `KM_IDSystem` | `KM_IDSystem` | https://github.com/LinzeColin/CodexProject/tree/main/KM_IDSystem |
| `OpenAIDatabase` | `OpenAIDatabase` | https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase |
| `KMFA` | `KMFA` | https://github.com/LinzeColin/CodexProject/tree/main/KMFA |
| `PFI` | `PFI` | https://github.com/LinzeColin/CodexProject/tree/main/PFI |
| `Serenity-Alipay` | `Serenity-Alipay` | https://github.com/LinzeColin/CodexProject/Serenity-Alipay |
| `arxiv-daily-push` | `arxiv-daily-push` | https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push |

## Retired projects

- `WDA` is retired by Owner decision on 2026-07-13. Its tracked history stays in
  `WDA/`, but it is not an active/required governance project and cannot be changed
  without an explicit Owner-authorized reactivation task.

## Required Checks

Use read-only changed-scope checks for ordinary PR and local development:

```bash
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
```

Write-mode generators are not part of the ordinary PR fast gate. Run them only
for scheduled/manual/release governance evidence, and write root generated views
to an artifact directory instead of the tracked repository root:

```bash
python3 scripts/generate_governance_dashboard.py --write --changed-only --base-ref origin/main --root-artifact-dir /tmp/governance-generated-views
```

This repository is the source-level project hub. Each project directory must keep Lean v2 canonical facts and human-entry files synchronized with implementation evidence. Root dashboards and portfolio summaries are generated on demand as CI artifacts instead of committed source files.
