# 每日钉钉 DWS 归档 automation prompt

Read and follow `/Users/linzezhang/.codex/skills/dingtalk-dws-archive/SKILL.md` before acting.

Operate only the existing DWS archive workflow. Do not create a replacement automation.

Hard boundaries:

- Do not change the automation RRULE or schedule. The user owns all run times.
- The DWS working directory is `/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p` and is intentionally not a Git repository.
- The Git repository is `/Users/linzezhang/CodexProject`; every Git operation must use that explicit repository root.
- The only source package is `/Users/linzezhang/onedrive/DWS_Outputs.zip` (use the documented OneDrive alias only when the primary path is absent).
- Never commit the ZIP, expanded DWS files, message bodies, private IDs, tokens, cookies, credentials, or browser/session data.
- Never create a branch, pull request, issue, worktree, merge commit, rebase, or force push.

Run contract:

1. Run the existing DWS doctor/preflight and stop on an authentication, source, configuration, or archive failure.
2. Run the existing controlled archive command. Preserve its private-data boundaries and existing group scope.
3. Confirm `reports/daily_summary.json` reports `success=true` and identifies the current `run_id`.
4. Confirm `/Users/linzezhang/onedrive/DWS_Outputs.zip` exists and is the current archive output.
5. From the DWS working directory, run the existing validator and write its complete JSON stdout to `reports/dws_output_validation_latest.json`. Stop if its top-level, mirror, cold-storage, local-output-root, or any group gate is not `ok=true`.
6. Attempt the existing Notion sync. Record `synced` when it succeeds and `pending` when credentials or the remote service are unavailable. Notion pending must not block the GitHub manifest-only backup.
7. Invoke the deterministic manifest publisher from any working directory:

   ```bash
   python3 /Users/linzezhang/CodexProject/KMFA/tools/automation/backup_dws_output_manifest.py \
     --dws-project /Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p \
     --repo-root /Users/linzezhang/CodexProject \
     --source-package /Users/linzezhang/onedrive/DWS_Outputs.zip \
     --summary-json /Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p/reports/daily_summary.json \
     --validation-json /Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p/reports/dws_output_validation_latest.json \
     --notion-status pending \
     --push
   ```

   Use `--notion-status synced` only when step 6 really succeeded. The publisher must fail closed on invalid archive evidence, a non-`main` checkout, tracked worktree changes, unrelated local commits, or diverged Git history. It stages only `KMFA/metadata/dws_outputs_backup/` and pushes only `origin main`.
8. Read back `HEAD`, `origin/main`, the pushed commit subject, `latest/manifest.json`, and `runs/<run_id>.json`. Report success only when the remote `main` contains the current run manifest and no raw ZIP is tracked.

The final run report must distinguish archive success, validation success, Notion status, manifest commit status, and push/readback status. A pending Notion sync is a visible warning, not a GitHub backup failure.
