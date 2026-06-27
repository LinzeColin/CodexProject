# PHASE S2PMT01 Trust Boundary A005

## Summary

- phase: `S2PM`
- task_id: `S2PMT01-TRUST-BOUNDARY-A005`
- parent_task_id: `S2PMT01`
- acceptance_id: `ACC-S2PMT01-SECURITY`
- finding_id: `A-005`
- model_id: `MOD-ADP-114`
- formula_id: `FORM-ADP-116`
- parameter_ids: `PARAM-ADP-955` through `PARAM-ADP-959`
- status: `completed_local_validation_no_production`
- generated_at: `2026-06-27T11:30:00+10:00`

This record refreshes inherited P0 finding `A-005` with dedicated current evidence. It verifies that external source content is always treated as untrusted data and cannot request tools, read secrets, write repository files, send email, or render unsafe URLs.

## Probe Results

| Probe | Expected result | Current result |
|---|---|---|
| `source_content_labeled_untrusted` | Source content is labeled `UNTRUSTED_DATA` | pass |
| `unsafe_url_schemes_blocked` | `javascript:`, `data:`, `file:`, and credential URLs are blocked | pass |
| `unsafe_hosts_blocked` | Unapproved hosts do not render as safe public links | pass |
| `source_content_tool_requests_blocked` | Source text cannot request tools or actions | pass |
| `secret_access_blocked` | Source/model boundary cannot read secrets | pass |
| `repository_write_blocked` | Source/model boundary cannot write repository files | pass |
| `email_send_blocked` | Source/model boundary cannot send email | pass |

## Evidence

- [A-005 run manifest](../../../governance/run_manifests/ADP-S2PMT01-TRUST-BOUNDARY-A005-20260627.json)
- [security_boundary.py](../../src/arxiv_daily_push/security_boundary.py)
- [test_security_boundary.py](../../tests/test_security_boundary.py)
- [Owner-facing scan page](../../用户中心/来源信任边界扫描.md)
- [P0 review receipt](PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)

## Boundaries

No SMTP was sent, no scheduler was installed or enabled, no Release assets were uploaded, no production restore was executed, no public schema or DB migration was changed, no production queue was mutated, no source adapter or ranking algorithm changed, no `CURRENT` or V7.1/V7.2 contract file changed, and no inherited P0/P1 closure, `DAILY_OPERATION`, or `INTEGRATED_PRODUCTION_ACCEPTED` claim was made.

## Remaining Gate

`A-005` remains open until S2PMT07 independent review inspects or reruns this evidence and explicitly closes the finding. This local evidence refresh does not change inherited P0/P1 counters.
