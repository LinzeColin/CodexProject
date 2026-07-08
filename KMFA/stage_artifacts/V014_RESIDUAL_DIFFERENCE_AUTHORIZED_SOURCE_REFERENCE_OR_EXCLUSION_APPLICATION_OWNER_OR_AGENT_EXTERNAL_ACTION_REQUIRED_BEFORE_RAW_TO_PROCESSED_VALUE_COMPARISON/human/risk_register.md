# Risk Register

- Risk: raw comparison requirement queue is mistaken for permission to compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private source handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed requirement rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing requirement artifacts only and does not touch the raw inbox.
