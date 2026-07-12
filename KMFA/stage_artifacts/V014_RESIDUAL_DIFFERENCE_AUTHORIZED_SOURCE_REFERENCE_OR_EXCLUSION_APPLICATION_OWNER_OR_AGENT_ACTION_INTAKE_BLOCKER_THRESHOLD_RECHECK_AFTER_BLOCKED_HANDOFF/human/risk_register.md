# Risk Register

- Risk: second blocker observation is mistaken for authorization to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private action-intake blocker queue details leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed threshold records stays ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing action-intake artifacts only and does not touch the raw inbox.
