# S2PFT01 China Provincial Template Coverage

Timestamp: `2026-06-25T08:30:00+10:00`

## Scope

`S2PFT01` / legacy `S2P5T01` implements metadata-only China mainland
provincial-level template coverage evidence after `S2PDT04` D3 readiness.

It validates:

- all 31 mainland provincial-level IDs are present.
- `province`, `autonomous_region`, and `municipality` locality types are covered.
- every provincial record has the required local core department roles:
  `government_portal`, `development_reform`, `science_technology`,
  `industry_information`, `finance`, and `market_regulation`.
- every record has an allowed health tier and explanation.
- official identity, official domain, source URL, evidence refs, and
  `authority_gate=pass` are present.
- metadata-only boundaries hold with PDF/full-text, production, SMTP, queue,
  schema, V7.2 contract, mail/schema pre-run, Hong Kong/Macau, city, and
  special-zone flags all disabled.

## V7.2 Receipt

- current contract: `ADP-PRODUCT-CONTRACT-V7.2`
- CURRENT pointer: `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`
- root lock: `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
- V7.1 baseline: read-only history; not changed.
- revalidation result: compatible with V7.2 Stage2 shadow exception.
- shared V7.2 contract files changed: false.

## Explicit Non-Scope

This task does not claim:

- `D3_FULL_SOURCE_DOMAIN_ACCEPTED`
- `STAGE2_PRODUCTION_ACCEPTED`
- `INTEGRATED_PRODUCTION_ACCEPTED`
- Hong Kong/Macau independent profiles
- key-city coverage
- special-zone discovery
- real SMTP
- scheduler installation
- Release upload
- queue/schema migration
- production restore
- public schema change

## Validation

- focused Stage2 source tests: 51 OK
- semantic extractor: 67 formulas / 451 parameters
- ADP project governance: errors 0 warnings 0

## Next

Next S2PF task is `S2PFT02` / legacy `S2P5T02`: Hong Kong and Macau
independent profiles. It must stay metadata-only and no-send unless a later
contract explicitly grants broader authority.

