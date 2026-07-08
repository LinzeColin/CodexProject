# Risk Register

- Risk: third external-action blocker observation is mistaken for authorization to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private reminder queue or final-threshold records leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed records stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing handoff artifacts only and does not touch the raw inbox.
