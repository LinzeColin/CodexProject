# Risk Register

- Risk: diagnostic packet is mistaken for discrepancy closure.
- Control: decision remains NO_GO and binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or owner-action details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private diagnostic outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored blocked-handoff artifacts only and does not touch the raw inbox.
