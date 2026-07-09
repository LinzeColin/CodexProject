# DWS Outputs Backup

This directory is the GitHub main-line backup target for the upstream DingTalk
DWS archive package used by KMFA workflows.

Automation contract:

- Source package priority:
  1. `/Users/linzezhang/onedrive/DWS_Outputs.zip`
  2. `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`
- Backup target:
  - `latest/DWS_Outputs.zip`
  - `latest/manifest.json`
  - `runs/<run_id>.json`
- The DWS archive automation may update this directory only after its existing
  archive, validation, and sync goals have completed without a blocking failure.
- Updates must commit and push directly to `main`.
- No branch, pull request, issue, or extra worktree is allowed.
- Manifests must not include tokens, cookies, full open conversation IDs,
  Keychain data, browser cookies, or private authentication material.

