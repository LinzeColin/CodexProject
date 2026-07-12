# Operating Contract

## No simulation

Production outputs cannot contain simulated, fake, estimated, or demonstration financial data. Template placeholders are allowed only in schema/config files and must never be included in management results.

## Evidence hierarchy

A. Original bank export/electronic receipt/e-tax voucher/e-invoice original.
B. Bank app or web transaction detail screenshot with date, amount, account tail, transaction id.
C. Human-made DingTalk/Excel screenshot with date and amount.
D. Chat/cropped/partial screenshot without enough fields.

Only A/B can directly support final facts. C/D may support management clues but require review before final accounting conclusions.

## Internal transfer净化

A transfer-like pair must be excluded from operating cash flow when it meets enough of these rules:

* Same or near date.
* Same or near amount.
* Both accounts belong to known internal companies/persons.
* Summary contains 转账、调拨、归还、借款、理财赎回、账户转入/转出.
* One side is outflow and the other side is inflow.

Unpaired transfer-like rows go to exception queue, not operating cash flow.

## Git governance

No branch. No PR. No open branch. No worktree. Commit and push to main only when validation passes. If validation fails, do not push; write failure summary and leave working tree inspectable.
