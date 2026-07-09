# Risk Register

- Risk: first blocker observation is mistaken for authorization to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private resolution-intake details leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed audit queue stays ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing resolution-intake artifacts only and does not touch the raw inbox.
