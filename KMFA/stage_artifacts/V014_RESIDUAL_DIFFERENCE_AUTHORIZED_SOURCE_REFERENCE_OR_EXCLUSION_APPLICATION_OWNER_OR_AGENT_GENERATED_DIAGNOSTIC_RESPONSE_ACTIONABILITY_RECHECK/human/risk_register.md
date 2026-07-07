# Risk Register

- Risk: generated diagnostic responses are mistaken for actionable source binding.
- Control: actionability is rechecked separately and all 48 rows are retained as blockers.
- Risk: private diagnostic handles leak into public evidence.
- Control: public artifacts contain aggregate counts only; actionability rows stay ignored.
- Risk: raw inbox is modified.
- Control: this phase consumes existing ignored private diagnostic artifacts only and does not touch the raw inbox.
