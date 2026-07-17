# DWS Outputs Backup

This directory is the GitHub main-line public metadata target for the upstream
DingTalk DWS archive used by KMFA workflows. Raw resources and private receipts
stay in private storage and are not committed to GitHub.

Automation contract:

- Private source lookup is configured outside this repository. Public manifests
  refer to it only as `SOURCE-PACKAGE-DWS-PRIVATE`.
- The local archive is referenced only as `LOCAL-RESOURCE-DWS-PRIVATE`.
- Backup target:
  - `latest/manifest.json`
  - `runs/<run_id>.json`
- Raw-resource boundary:
  - Do not commit source packages or expanded DWS output files.
  - Public manifests contain only allowlisted aggregate run and validation
    status. Absolute paths, private hashes, private byte sizes, dynamic group
    names, and private receipt payloads are forbidden.
  - `private_receipt_required=true` states the control requirement; it does not
    claim that a private receipt was produced or publish a receipt identifier.
- The DWS archive automation may update this directory only after archive and
  structure validation complete without a blocking failure. Notion sync is
  best-effort: a recorded `pending` state does not block the manifest backup.
- Publishing is performed by
  `KMFA/tools/automation/backup_dws_output_manifest.py` with an explicit
  private `CODEXPROJECT_REPO_ROOT`, because the upstream DWS project directory
  is intentionally not a Git checkout.
- Updates must commit and push directly to `main`.
- No branch, pull request, issue, or extra worktree is allowed.
- Manifests must not include tokens, cookies, full open conversation IDs,
  Keychain data, browser cookies, raw message bodies, report bodies, group
  names, private resource digests, filesystem paths, or authentication material.
