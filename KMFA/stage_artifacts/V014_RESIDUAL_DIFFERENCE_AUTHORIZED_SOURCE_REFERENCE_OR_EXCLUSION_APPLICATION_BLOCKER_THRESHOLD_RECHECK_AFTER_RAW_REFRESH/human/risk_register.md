# Risk Register

- Risk: threshold recheck is mistaken for authoritative binding or discrepancy closure.
- Control: binding, comparison and downstream gate flags remain false.
- Risk: private slot or resolution details leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private threshold details stay ignored.
- Risk: raw inbox is modified.
- Control: this phase reads existing ignored private audit artifacts only and does not touch the raw inbox.
