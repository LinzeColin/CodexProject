# Risk Register

- Risk: treating pending group review rows as active owner authorization.
  Mitigation: the validator requires valid group decision count to remain zero in this NO_GO phase and keeps all downstream gates closed.
- Risk: leaking private row-level routing publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; the pending queue is private runtime only.
