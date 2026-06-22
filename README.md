# CodexProject

Active Codex-related project hub for LinzeColin.

## Governance Entry

- Owner portfolio: [OWNER_PORTFOLIO.md](OWNER_PORTFOLIO.md)
- Engineering dashboard: [GOVERNANCE_DASHBOARD.md](GOVERNANCE_DASHBOARD.md)
- Project registry: [governance/projects.yaml](governance/projects.yaml)
- Standard: [docs/governance/STANDARD.md](docs/governance/STANDARD.md)

## Snapshot Metadata

- source_base_commit: `05c69c6522a74901f33350e03046f03a6f47b061`
- source_snapshot_hash: `sha256:c42f6bf28748680a7dc675517659bde21260d9bcb5a1c4d45d41d5837a583688`
- generator_version: `2.0.0`
- final_commit_binding: `CI_ATTESTATION_REQUIRED`

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
