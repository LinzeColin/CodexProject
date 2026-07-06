# Risk Register

- Risk: treating an empty response draft as owner approval.
  Mitigation: intake requires choice, owner/delegate, reason, and ready flag; current valid count is zero.
- Risk: leaking private response details publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private queues stay in ignored runtime.
