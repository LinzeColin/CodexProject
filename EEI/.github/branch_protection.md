# Branch Protection Contract

This repository expects `main` to be protected before release.

Required rule set:

- Require pull request before merge.
- Require review from CODEOWNERS.
- Require branches to be up to date before merge.
- Require signed or traceable commits where the host account policy supports it.
- Block force pushes and branch deletion.

Required status checks:

- `EEI validation / verify`
- `governance-validation / validate`
- `governance-validation / visual-validation`

Operational note:

- The root `LinzeColin/CodexProject` workflow runs `EEI validation / verify` for changes under `EEI/**`.
- The packaged EEI repository also carries `.github/workflows/governance-validation.yml` for clean-room repository validation.
- Actual GitHub branch protection must be applied in repository settings or through the GitHub API; this file is the versioned source contract for those settings.
