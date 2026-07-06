# Risk Register

- Risk: treating an unfilled template as owner authorization.
  Mitigation: intake requires ready_for_intake plus required owner/delegate fields; current ready count is zero.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private queue stays in ignored runtime.
