# S2PFT03 Key City Coverage

Timestamp: `2026-06-25T10:30:00+10:00`

## Scope

`S2PFT03` / legacy `S2P5T03` implements the first China key-city
metadata-only coverage evidence after `S2PFT02` Hong Kong and Macau independent
profile evidence.

It validates:

- 24 required key-city IDs are present: Beijing, Shanghai, Shenzhen, Guangzhou,
  Tianjin, Chongqing, Hangzhou, Nanjing, Suzhou, Hefei, Wuhan, Xian, Chengdu,
  Changsha, Wuxi, Dongguan, Foshan, Zhuhai, Shenyang, Ningbo, Qingdao, Xiamen,
  Dalian, and Zhengzhou.
- each city has aliases, province/locality context, region group, official
  domain, source URL, evidence refs, and `authority_gate=pass`.
- each city covers the required local department roles: party committee,
  government portal, development and reform, science and technology, industry
  and information, finance, commerce, market regulation, data, and financial
  regulation.
- allowed region groups and health tiers are enforced.
- metadata-only boundaries hold with PDF/full-text, production, SMTP, queue,
  schema, V7.2 contract, mail/schema pre-run, and special-zone flags all
  disabled.

## V7.2 Receipt

- current contract: `ADP-PRODUCT-CONTRACT-V7.2`
- CURRENT pointer: `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`
- root lock: `arxiv-daily-push/docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`
- V7.1 baseline: read-only history; not changed.
- revalidation result: compatible with V7.2 Stage2 shadow/source exception.
- shared V7.2 contract files changed: false.
- Email V1 status: PR #152 and PR #153 are merged to main; S2PFT03 does not
  modify mail runtime paths and preserves the Email V1 contract/readiness gate.

## Explicit Non-Scope

This task does not claim:

- `D3_FULL_SOURCE_DOMAIN_ACCEPTED`
- `STAGE2_PRODUCTION_ACCEPTED`
- `INTEGRATED_PRODUCTION_ACCEPTED`
- special-zone discovery
- real SMTP
- scheduler installation
- Release upload
- queue/schema migration
- production restore
- public schema change
- Email V1 production operation

## Validation

- py_compile: PASS
- focused Stage2 source tests: 59 OK
- full validation pending this PR/CI closeout.

## Next

Next S2PF task is `S2PFT04` / legacy `S2P5T04`: special-zone discovery. It
must stay metadata-only and no-send unless a later contract explicitly grants
broader authority.
