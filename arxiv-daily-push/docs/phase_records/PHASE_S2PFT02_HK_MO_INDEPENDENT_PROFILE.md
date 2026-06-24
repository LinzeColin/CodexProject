# S2PFT02 Hong Kong And Macau Independent Profile

Timestamp: `2026-06-25T09:20:00+10:00`

## Scope

`S2PFT02` / legacy `S2P5T02` implements metadata-only Hong Kong and Macau
independent jurisdiction profile evidence after `S2PFT01` mainland provincial
template coverage.

It validates:

- `hong_kong` and `macau` jurisdiction IDs are both present.
- `zh_hant`, `en`, and `pt` language profiles are represented.
- `common_law` and `civil_law_portuguese_heritage` legal system states are
  represented.
- each profile has jurisdiction name, government structure model, legal status
  reference, official domain, source URL, evidence refs, and
  `authority_gate=pass`.
- mainland province/city template reuse is blocked.
- metadata-only boundaries hold with PDF/full-text, production, SMTP, queue,
  schema, V7.2 contract, mail/schema pre-run, city, and special-zone flags all
  disabled.

## V7.2 Receipt

- current contract: `ADP-PRODUCT-CONTRACT-V7.2`
- CURRENT pointer: `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`
- root lock: `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
- V7.1 baseline: read-only history; not changed.
- revalidation result: compatible with V7.2 Stage2 shadow/source exception.
- shared V7.2 contract files changed: false.
- Email V1 status: PR #152 and PR #153 merged to main; S2PFT02 does not modify
  mail runtime paths and preserves the Email V1 contract/readiness gate.

## Explicit Non-Scope

This task does not claim:

- `D3_FULL_SOURCE_DOMAIN_ACCEPTED`
- `STAGE2_PRODUCTION_ACCEPTED`
- `INTEGRATED_PRODUCTION_ACCEPTED`
- key-city coverage
- special-zone discovery
- real SMTP
- scheduler installation
- Release upload
- queue/schema migration
- production restore
- public schema change
- Email V1 production operation

## Validation

- focused Stage2 source tests: 55 OK
- full arxiv-daily-push unittest: 284 OK
- semantic extractor: 68 formulas / 461 parameters checked
- V7.2 contract validator: PASS
- ADP project governance: errors 0 warnings 0
- lean check-render: drift_count 0 reference_issue_count 0
- changed-only lean governance: errors 0 warnings 0
- JSON/YAML/JSONL/CSV parse: OK
- git diff --check: PASS

## Next

Next S2PF task is `S2PFT03` / legacy `S2P5T03`: first key-city coverage. It
must stay metadata-only and no-send unless a later contract explicitly grants
broader authority.
