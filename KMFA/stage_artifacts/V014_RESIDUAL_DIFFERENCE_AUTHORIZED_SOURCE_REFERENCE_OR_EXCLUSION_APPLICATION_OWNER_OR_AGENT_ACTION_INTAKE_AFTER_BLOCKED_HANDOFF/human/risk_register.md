# Risk Register

- Risk: action intake is mistaken for permission to bind fields or compare values.
- Control: decision remains NO_GO and all downstream gates remain false.
- Risk: private owner-action handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; detailed blocker rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing action-readiness artifacts only and does not touch the raw inbox.
