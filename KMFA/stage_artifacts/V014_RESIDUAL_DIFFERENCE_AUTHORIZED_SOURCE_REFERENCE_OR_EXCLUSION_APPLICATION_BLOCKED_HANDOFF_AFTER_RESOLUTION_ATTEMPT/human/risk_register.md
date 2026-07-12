# Risk Register

- Risk: a blocked handoff is mistaken for discrepancy closure.
- Control: decision remains NO_GO and binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or owner-action details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private blocked-handoff outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private resolution-attempt artifacts only and does not touch the raw inbox.
