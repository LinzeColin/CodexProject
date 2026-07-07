# Risk Register

- Risk: generated diagnostic responses are mistaken for source binding or value reconciliation.
- Control: valid response and actionable/binding/comparison gates are recorded separately; downstream gates remain closed.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; generated response rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private diagnostic artifacts only and does not touch the raw inbox.
