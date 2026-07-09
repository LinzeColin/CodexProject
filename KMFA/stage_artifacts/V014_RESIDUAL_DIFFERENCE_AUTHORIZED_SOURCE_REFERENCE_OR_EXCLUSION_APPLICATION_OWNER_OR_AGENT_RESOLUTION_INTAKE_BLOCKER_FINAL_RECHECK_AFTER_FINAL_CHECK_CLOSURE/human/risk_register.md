# Risk Register

- Risk: final blocker observation is mistaken for authorization to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private resolution-intake blocker queue details leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed recheck queue stays ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing resolution-intake artifacts only and does not touch the raw inbox.
