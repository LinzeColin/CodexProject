# Risk Register

- Risk: final threshold is mistaken for permission to bind fields or compare values.
- Control: this phase records a blocked state only and keeps binding and value comparison closed.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; final-threshold rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private threshold artifacts only and does not touch the raw inbox.
