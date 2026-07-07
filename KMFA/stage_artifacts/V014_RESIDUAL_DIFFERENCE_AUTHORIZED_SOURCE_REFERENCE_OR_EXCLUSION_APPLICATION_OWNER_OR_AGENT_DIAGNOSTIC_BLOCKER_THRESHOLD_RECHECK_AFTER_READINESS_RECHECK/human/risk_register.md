# Risk Register

- Risk: blocker threshold recheck is mistaken for permission to import responses or close differences.
- Control: decision remains NO_GO and valid/actionable/binding/comparison counts remain zero.
- Risk: private handles leak into public artifacts.
- Control: public artifacts contain aggregate counts only; private threshold outputs stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored blocker audit artifacts only and does not touch the raw inbox.
