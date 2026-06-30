# Stage 4 Phase 4.1 Risk And Rollback

## Scope

This run defines the Stage 4 data state machine only. It does not wire the read
model, does not change home/account/investment/consumption/report rendering,
does not reinstall app bundles, and does not upload GitHub main.

## Risks

- Status names could drift from the repair taskpack.
- A non-ready state could accidentally render a financial zero.
- A true zero could be accepted without source, time, sample count, formula, and
  confidence evidence.
- Forbidden financial data terms could enter runtime payloads.

## Controls

- Python and JS contracts share the same status list and required fields.
- Tests reject non-ready statuses with financial values.
- Tests require a full evidence chain for `ready` and `confirmed_zero`.
- Runtime JS is scanned for forbidden financial-data terms.

## Rollback

Remove the Phase 4.1 files and restore the status docs. No Stage 3 navigation
or app entry files need to be reverted.
