# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Owner portfolio: [OWNER_PORTFOLIO.md](OWNER_PORTFOLIO.md)
- Engineering dashboard: [GOVERNANCE_DASHBOARD.md](GOVERNANCE_DASHBOARD.md)
- Project registry: [governance/projects.yaml](governance/projects.yaml)
- Standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)

## Snapshot Metadata

- source_base_commit: `932446fd2154ac477ea0cb6862a60098b1e1ed55`
- source_tree_hash: `a661be1db22d99ff3afe6183ac1ae8f4c444be18`
- source_snapshot_hash: `sha256:39f6165dbead37182eef8b06f68527bd352681fbd2f5db107c87cbfde847f622`
- generator_version: `3.0.0`
- final_commit_binding: `PRECOMMIT_TREE_BOUND_PENDING_CI_ATTESTATION`

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

```bash
python3 scripts/validate_project_governance.py --all --semantic --drift-report
python3 scripts/validate_information_quality.py --all --fast --fail-on-error
python3 scripts/generate_governance_dashboard.py --write
```

This repository is the source-level project hub. Each project directory must keep canonical governance files, assurance status, owner status, and traceability records synchronized with implementation evidence.
