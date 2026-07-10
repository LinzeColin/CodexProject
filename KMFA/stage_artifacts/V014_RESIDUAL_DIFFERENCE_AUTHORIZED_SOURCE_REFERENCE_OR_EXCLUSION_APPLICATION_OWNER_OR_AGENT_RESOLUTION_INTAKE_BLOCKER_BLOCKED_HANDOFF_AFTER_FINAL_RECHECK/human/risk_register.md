# Risk Register

- Risk: blocked handoff is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private owner-resolution handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; handoff and owner-resolution rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private final-recheck artifacts only and does not touch the raw inbox.
