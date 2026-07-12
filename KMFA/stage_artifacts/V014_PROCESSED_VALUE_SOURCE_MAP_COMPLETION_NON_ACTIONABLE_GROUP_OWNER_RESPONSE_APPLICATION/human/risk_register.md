# Risk Register

- Risk: treating an empty private checklist as owner approval.
  Mitigation: application requires filled choice, owner/delegate, reason, and ready flag; current applied count is zero.
- Risk: leaking private group or target details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; application details stay in ignored runtime.
