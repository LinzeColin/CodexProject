# PHASE S2PAT05 LEGACY MAIL SCAN C011

## Summary

- phase: `S2PA`
- task_id: `S2PAT05-LEGACY-MAIL-SCAN-C011`
- acceptance_id: `ACC-S2PAT05-LEGACY-MAIL-SCAN`
- finding_id: `C-011`
- status: `local_validation_passed_closure_not_claimed`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- generated_at: `2026-06-27 07:40:20 Australia/Sydney`

This phase record refreshes inherited P1 finding `C-011` with dedicated local evidence. It proves the current checkout uses the Email V1 `M1`-`M4` 3+1 mail contract, keeps `legacy_five_mail_active=false`, and classifies old B1-B5/five-mail/English visible-frontstage markers as absent from active runtime or isolated to filters, tests, history, compatibility, or governance evidence.

## Evidence

- [C-011 run manifest](../../../governance/run_manifests/ADP-S2PAT05-LEGACY-MAIL-SCAN-C011-20260627.json)
- [Owner-facing scan page](../../用户中心/旧邮件标识兼容扫描.md)
- [Focused tests](../tests/test_stage2_sources.py)
- [Mail renderer](../src/arxiv_daily_push/mail_templates.py)
- [P1 review receipt](./PHASE_S2PMT07_P1_INDEPENDENT_REVIEW_RECEIPT.md)

## Scan Result

| Metric | Value |
|---|---:|
| scanned scopes | 4 |
| marker hits classified | 271 |
| active legacy runtime hits | 0 |
| active owner-surface legacy hits | 0 |
| unclassified hits | 0 |
| observed mail products | M1, M2, M3, M4 |
| legacy five mail active | false |

## Boundaries

No P1 closure, no independent final signoff, no S2PLT04 completion, no final acceptance bundle creation, no real SMTP send, no scheduler installation, no Release upload, no production restore, no public schema change, no DB migration, no production queue mutation, no ranking/source-adapter change, no CURRENT pointer change, no V7.1/V7.2 contract-file edit, no `DAILY_OPERATION`, and no `INTEGRATED_PRODUCTION_ACCEPTED` claim.

## Next

Independent review must inspect the C-011 manifest and decide whether this evidence is sufficient to close the finding. Until then C-011 remains open under inherited P1 and S2PMT07 remains blocked.
