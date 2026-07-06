# Risk Register

- Risk: treating pending response-template values as owner authorization.
  Mitigation: the validator requires valid_group_decision_count=0 and keeps all downstream gates closed.
- Risk: leaking private group-level response context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; diagnostics stay in private runtime.
