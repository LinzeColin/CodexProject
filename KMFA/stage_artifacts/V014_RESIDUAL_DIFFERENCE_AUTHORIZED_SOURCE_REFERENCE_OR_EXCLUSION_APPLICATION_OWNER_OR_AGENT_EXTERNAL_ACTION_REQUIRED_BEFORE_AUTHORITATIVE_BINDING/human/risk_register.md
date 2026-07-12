# Risk Register

- Risk: binding requirement queue is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private source handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed requirement rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing follow-up artifacts only and does not touch the raw inbox.
