# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Execution contract: [AGENTS.md](AGENTS.md)
- Lean v2 standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- Project human-entry files: `功能清单.md`, `开发记录.md`, `模型参数文件.md`

## Canonical Local Root

On Linze's machine, active work for this GitHub product hub must use one local
checkout:
```text
/Users/linzezhang/Documents/Codex/CodexProject
```
Do not treat duplicate `CodexProject*`, `PFI_OS`, `EVA_OS`, or per-project
shadow folders as product roots. Before cleanup or migration, verify `.app`
launchers, LaunchAgents, PID files, and listening process cwd so PFI, EEI,
Alpha, Serenity, OpenAIDatabase/Memory Atlas, and arxiv-daily-push continue to
resolve to this checkout.

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
| `Alpha` | `Alpha` | https://github.com/LinzeColin/CodexProject/Alpha |
| `EEI` | `EEI` | https://github.com/LinzeColin/CodexProject/tree/main/EEI |
| `FIFA` | `FIFA` | https://github.com/LinzeColin/CodexProject/FIFA |
| `KM_IDSystem` | `KM_IDSystem` | https://github.com/LinzeColin/CodexProject/tree/main/KM_IDSystem |
| `OpenAIDatabase` | `OpenAIDatabase` | https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase |
| `MetaDatabase` | `MetaDatabase` | https://github.com/LinzeColin/CodexProject/tree/main/MetaDatabase |
| `KMFA` | `KMFA` | https://github.com/LinzeColin/CodexProject/tree/main/KMFA |
| `PFI` | `PFI` | https://github.com/LinzeColin/CodexProject/tree/main/PFI |
| `QBVS` | `QBVS` | https://github.com/LinzeColin/CodexProject/tree/main/QBVS |
| `Serenity-Alipay` | `Serenity-Alipay` | https://github.com/LinzeColin/CodexProject/Serenity-Alipay |
| `whkmSalary` | `whkmSalary` | https://github.com/LinzeColin/CodexProject/whkmSalary |
| `arxiv-daily-push` | `arxiv-daily-push` | https://github.com/LinzeColin/CodexProject/tree/main/arxiv-daily-push |

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
