# S2PFT04 Special Zone Discovery

Timestamp: `2026-06-25T15:20:00+10:00`

## Scope

`S2PFT04` / legacy `S2P5T04` implements China special-zone metadata-only
discovery evidence after `S2PFT03` first key-city coverage evidence.

It validates:

- 10 required special-zone IDs are present: Xiongan New Area, Shanghai Pudong
  New Area, Shenzhen Qianhai, Hengqin Guangdong-Macao, Hainan Free Trade Port,
  Shanghai Lingang, Beijing Zhongguancun, Suzhou Industrial Park, Tianjin Binhai
  New Area, and Chongqing Liangjiang New Area.
- each zone has a supported zone type, policy focus areas, parent-city mapping
  to S2PFT03 observed cities, official domain, source URL, evidence refs,
  `authority_gate=pass`, and `dedupe_gate=pass`.
- each zone covers the required authority roles: zone governing committee,
  government portal, development and reform, commerce, science and technology,
  industry and information, market regulation, data or digital authority,
  customs, taxation, and financial regulation.
- allowed health tiers are enforced.
- metadata-only boundaries hold with PDF/full-text, production, SMTP, queue,
  schema, V7.2 contract, mail/schema pre-run, and production enablement flags
  all disabled.

## V7.2 Receipt

- current contract: `ADP-PRODUCT-CONTRACT-V7.2`
- CURRENT pointer: `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`
- root lock: `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
- V7.1 baseline: read-only history; not changed.
- revalidation result: compatible with V7.2 Stage2 shadow/source exception.
- shared V7.2 contract files changed: false.
- Email V1 status: merged to main per Stage 2 sync; S2PFT04 does not modify
  mail runtime paths and preserves the Email V1 contract/readiness gate.

## Explicit Non-Scope

This task does not claim:

- `D3_FULL_SOURCE_DOMAIN_ACCEPTED`
- `STAGE2_PRODUCTION_ACCEPTED`
- `INTEGRATED_PRODUCTION_ACCEPTED`
- real SMTP
- scheduler installation
- Release upload
- queue/schema migration
- production restore
- public schema change
- Email V1 production operation

## Validation

- py_compile: PASS
- focused Stage2 source tests: 63 OK
- full arxiv-daily-push unittest: 292 OK
- semantic extractor: 70 formulas / 480 parameters checked
- V7.2 contract validator: PASS
- ADP project governance: errors 0 warnings 0
- lean check-render: drift_count 0 reference_issue_count 0
- changed-only lean governance: errors 0 warnings 0
- changed JSON/YAML/JSONL/CSV parse: OK
- git diff --check: PASS

## Next

Next S2PF task is `S2PFT05` / legacy `S2P5T05`: full D3 governance and
coverage qualification. It must still stay blocked from production inclusion
until inherited V7.1 P0/P1 blockers are individually closed and the final Stage2
integrated acceptance gate is passed.
