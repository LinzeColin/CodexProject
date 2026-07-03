# Sensitive Material Exclusion Check

## Pack-Level Check

The zip listing contains only non-sensitive report files and
`README_SANITIZED_PACK.md`. It does not include actual directories named:

- `sensitive_local_state/`
- `raw_trial_outputs/`
- `logs/`
- `tool_work/`

It also does not include `messages.jsonl`, decrypted DBs, key configs, raw
message outputs, or raw command logs.

## Inventory Metadata Caveat

`generated_artifact_inventory.csv` lists old-computer local artifacts as
metadata. That file references sensitive local paths, but the referenced
artifacts themselves were not transferred in the report pack.

Inventory summary:

- total listed artifacts: `138`
- listed as sensitive: `26`
- listed as non-sensitive: `112`
- listed `sensitive_local_state/` artifacts: `1`
- listed `raw_trial_outputs/` artifacts: `5`
- listed `logs/` artifacts: `20`
- listed `tool_work/` artifacts: `110`
- listed `messages.jsonl` artifacts: `0`

## Rule For Sprint 2I-B

Do not transfer:

- `sensitive_local_state/`
- `raw_trial_outputs/`
- raw logs
- key configs
- decrypted DBs
- message outputs
- screenshots or UI artifacts containing message content

Only non-sensitive shape reports and decision reports may be transferred back to
the new computer unless the user later gives a separate explicit approval.

