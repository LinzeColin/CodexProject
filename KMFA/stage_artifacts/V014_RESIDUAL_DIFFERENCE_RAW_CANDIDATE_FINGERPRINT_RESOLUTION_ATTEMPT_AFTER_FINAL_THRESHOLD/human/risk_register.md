# Risk Register

- Risk: a resolution attempt is mistaken for raw-to-processed comparison.
- Control: public evidence keeps value comparison, reconciliation and business consistency false.
- Risk: private candidate records leak business details.
- Control: private outputs remain git-ignored and public evidence contains aggregate counts only.
- Risk: raw data is modified during the attempt.
- Control: this phase reads existing ignored private artifacts only and does not touch the raw inbox.
