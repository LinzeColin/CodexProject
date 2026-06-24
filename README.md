# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Lean v2 standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- Project human-entry files: `功能清单`, `开发记录`, `模型参数文件`

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
| `Alpha` | `Alpha` | https://github.com/LinzeColin/Alpha |
| `EEI` | `EEI` | https://github.com/LinzeColin/CodexProject/tree/main/EEI |
| `EVA_OS` | `EVA_OS` | https://github.com/LinzeColin/EVA_OS |
| `FIFA` | `FIFA` | https://github.com/LinzeColin/FIFA |
| `OpMe_System` | `OpMe_System` | https://github.com/LinzeColin/OpMe_System |
| `OpenAIDatabase` | `OpenAIDatabase` | https://github.com/LinzeColin/CodexProject/tree/main/OpenAIDatabase |
| `PFI_BIG_DATA_SIMULATOR` | `PFI/大数据模拟器` | https://github.com/LinzeColin/CodexProject/tree/main/PFI/%E5%A4%A7%E6%95%B0%E6%8D%AE%E6%A8%A1%E6%8B%9F%E5%99%A8 |
| `Serenity-Alipay` | `Serenity-Alipay` | https://github.com/LinzeColin/Serenity-Alipay |
| `whkmSalary` | `whkmSalary` | https://github.com/LinzeColin/whkmSalary |
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

## Current Governance Snapshot

- Other8 remediation baseline: `main@e25be8d65e67fe89af18e18e1562191a60066449`
- Roadmap kind: `portfolio_remediation`; it must stay separate from product roadmaps in project `开发记录`.
- S1 review evidence is local, untracked evidence under `.git/codex-review/other8-s1pa-e25be8d6/`, `.git/codex-review/other8-s1pb-e25be8d6/`, and `.git/codex-review/other8-s1pc-e25be8d6/`.

This repository is the source-level project hub. Each project directory must keep Lean v2 canonical facts and human-entry files synchronized with implementation evidence. Root dashboards and portfolio summaries are generated on demand as CI artifacts instead of committed source files.
