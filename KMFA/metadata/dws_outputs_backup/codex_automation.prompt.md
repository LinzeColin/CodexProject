# 每日钉钉 DWS 归档 automation prompt

Resolve and follow the locally installed `dingtalk-dws-archive` skill from the
private Codex skill registry before acting.

Operate only the existing DWS archive workflow. Do not create a replacement automation.

Hard boundaries:

- Do not change the automation RRULE or schedule. The user owns all run times.
- Resolve `DWS_PROJECT_DIR`, `CODEXPROJECT_REPO_ROOT`, and
  `DWS_SOURCE_PACKAGE` from private runtime configuration. Do not write their
  values to public artifacts or logs intended for publication.
- The DWS working directory is intentionally not a Git repository.
- Every Git operation must use the explicit `CODEXPROJECT_REPO_ROOT`.
- Use only the privately configured `DWS_SOURCE_PACKAGE`.
- Never commit the ZIP, expanded DWS files, message bodies, private IDs, tokens, cookies, credentials, or browser/session data.
- Never create a branch, pull request, issue, worktree, merge commit, rebase, or force push.

Run contract:

1. Run the existing DWS doctor/preflight and stop on an authentication, source, configuration, or archive failure.
2. Run the existing controlled archive command. Preserve its private-data boundaries and existing group scope.
3. Confirm `reports/daily_summary.json` reports `success=true` and identifies the current `run_id`.
4. Confirm `${DWS_SOURCE_PACKAGE}` exists and is the current archive output.
5. From the DWS working directory, run the existing validator and write its complete JSON stdout to `reports/dws_output_validation_latest.json`. Stop if its top-level, mirror, cold-storage, local-output-root, or any group gate is not `ok=true`.
6. Attempt the existing Notion sync. Record `synced` when it succeeds and `pending` when credentials or the remote service are unavailable. Notion pending must not block the GitHub manifest-only backup.
7. Invoke the deterministic manifest publisher from any working directory:

   ```bash
   python3 "${CODEXPROJECT_REPO_ROOT}/KMFA/tools/automation/backup_dws_output_manifest.py" \
     --dws-project "${DWS_PROJECT_DIR}" \
     --repo-root "${CODEXPROJECT_REPO_ROOT}" \
     --source-package "${DWS_SOURCE_PACKAGE}" \
     --summary-json "${DWS_PROJECT_DIR}/reports/daily_summary.json" \
     --validation-json "${DWS_PROJECT_DIR}/reports/dws_output_validation_latest.json" \
     --notion-status pending \
     --push
   ```

   Use `--notion-status synced` only when step 6 really succeeded. The publisher must fail closed on invalid archive evidence, a non-`main` checkout, tracked worktree changes, unrelated local commits, or diverged Git history. It stages only `KMFA/metadata/dws_outputs_backup/` and pushes only `origin main`.
8. Read back `HEAD`, `origin/main`, the pushed commit subject, `latest/manifest.json`, and `runs/<run_id>.json`. Report success only when the remote `main` contains the current run manifest and no raw ZIP is tracked.

The final run report must distinguish archive success, validation success, Notion status, manifest commit status, and push/readback status. A pending Notion sync is a visible warning, not a GitHub backup failure.
