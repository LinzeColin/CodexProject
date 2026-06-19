# 12 Evidence And Audit Rules

## Evidence Labels

Every candidate conclusion must label claims as:

- FACT
- INFERENCE
- OPINION
- OBSERVATION

## Evidence Strength

- Strong: official filings, fund company announcements, fund contracts, prospectuses, exchange documents, official platform records.
- Medium: reputable financial media, trade publications, specialist research with visible assumptions.
- Weak: social posts, screenshots with unclear origin, forum discussions, unexplained price action.
- Needs checking: important facts awaiting verification.

## Required Audit Tables

- `source_log`
- `audit_log`
- `missing_data_log`
- `manual_review_queue`
- `conflict_log`
- `decision_record`
- `rebalance_event_log`

## Source Chain Rules

Every critical field must have source chain:

- NAV.
- current holdings.
- subscription status.
- redemption status.
- fees.
- benchmark return.
- drawdown metric input.
- target weight basis.

## Conflict Handling

If sources conflict:

1. Record all source values.
2. Rank source authority.
3. Show conflict note in report.
4. Downgrade action grade.
5. Never silently choose the more favorable value.

## Fallback Handling

Aggregated fallback data is allowed only when:

- Primary/official source is unavailable.
- `fallback_aggregated=true` is recorded.
- Output grade is capped unless official sources later confirm.

## Manual Review Triggers

- Missing NAV/holding > 2 days.
- Fee/redemption status missing.
- Official source count < 2.
- MDD/recovery-time conflict.
- High score but weak evidence chain.
- Alipay position import stale or absent.

