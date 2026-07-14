# Source of Truth Contract

1. Raw input files are immutable evidence. Never overwrite them.
2. A generated ledger row must reference source file, sheet/image, row number if available, evidence_id, and extraction status.
3. If two sources disagree, do not pick one silently. Output both and create an exception task.
4. Sales-accounting receipt tables are preferred for正式回款口径, but bank records and DingTalk evidence remain cross-check sources.
5. Tax screenshots with no payment date enter tax risk tracking but do not enter daily cash flow until matched to actual payment evidence.
6. Bills/acceptances, wealth-management products, deposits, and receivables must never be collapsed into T0 cash.
