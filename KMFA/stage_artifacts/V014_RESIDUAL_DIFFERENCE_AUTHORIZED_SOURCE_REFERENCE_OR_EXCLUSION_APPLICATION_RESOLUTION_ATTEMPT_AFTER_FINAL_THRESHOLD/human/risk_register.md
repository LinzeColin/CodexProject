# Risk Register

- Risk: a resolution attempt is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison, reconciliation and business consistency flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private resolution outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase reads existing ignored private final-threshold artifacts only and does not touch the raw inbox.
