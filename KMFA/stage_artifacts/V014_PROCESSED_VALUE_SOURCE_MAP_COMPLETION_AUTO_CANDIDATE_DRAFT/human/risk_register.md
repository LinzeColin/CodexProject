# Risk Register

- Risk: automatic context matching can be ambiguous when several raw numeric candidates share similar field context.
  Mitigation: the generated file is a private draft only and keeps every item owner-review-required.
- Risk: raw business detail leakage.
  Mitigation: public artifacts are aggregate-only and private files remain under ignored runtime.
- Risk: false reconciliation claim.
  Mitigation: this phase does not compare raw and processed values or verify business consistency.
