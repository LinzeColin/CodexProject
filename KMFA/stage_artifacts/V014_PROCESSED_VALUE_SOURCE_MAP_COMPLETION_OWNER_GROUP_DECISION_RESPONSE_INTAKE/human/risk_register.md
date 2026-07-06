# Risk Register

- Risk: treating delegated default decisions as full active authorization.
  Mitigation: non-actionable decisions keep source-map reapplication closed until a later phase explicitly resolves them.
- Risk: leaking private group-level response context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; diagnostics stay in private runtime.
