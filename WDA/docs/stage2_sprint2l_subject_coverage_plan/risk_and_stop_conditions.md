# Risk And Stop Conditions

## Key Risks

- Subject identity ambiguity.
- Alias collision between target and noise candidates.
- Payment/invoice subject may require content search rather than session label
  search.
- Media-related rows may map as message-level records but cannot resolve media
  paths while `include_media_paths=false`.
- Weak/noise sample may be misinterpreted as target evidence.
- Full Raw Gate Go may be overstated from bounded evidence.

## Stop Conditions

Stop Sprint 2M immediately if:

- A command requires full export.
- A command requires all-history traversal beyond the bounded selected
  conversations.
- A command requires full-contact export.
- A command requires media DB enhancement.
- A command requires transferring keys, configs, DBs, broad logs, or
  `sensitive_local_state/`.
- A candidate resolves to `李晶工作交接`.
- Total planned rows exceed `500`.
- `include_media_paths=false` cannot be enforced.
- Any tool attempts upload, message sending, or UI automation.

## Rollback

Delete only the Sprint 2M local output folder if the run fails. Do not clean or
modify WeChat source directories.

