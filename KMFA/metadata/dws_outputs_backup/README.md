# DWS Outputs Backup

This directory is the GitHub main-line metadata backup target for the upstream
DingTalk DWS archive package used by KMFA workflows. The raw DWS output zip
stays in OneDrive and is not committed to GitHub.

Automation contract:

- Source package priority:
  1. `/Users/linzezhang/onedrive/DWS_Outputs.zip`
  2. `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`
- Backup target:
  - `latest/manifest.json`
  - `runs/<run_id>.json`
- Raw package boundary:
  - Do not commit `DWS_Outputs.zip` or expanded raw DWS output files.
  - Manifests may record package path, byte size, SHA-256, file count, and
    DWS run summary only.
- The DWS archive automation may update this directory only after its existing
  archive, validation, and sync goals have completed without a blocking failure.
- Updates must commit and push directly to `main`.
- No branch, pull request, issue, or extra worktree is allowed.
- Manifests must not include tokens, cookies, full open conversation IDs,
  Keychain data, browser cookies, raw message bodies, report bodies, or private
  authentication material.
