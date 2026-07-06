# Risk Register

- Risk: treating a diagnostic request as active authorization.
  Mitigation: this phase records the confirmation sequence but keeps active authorization and source-map application closed.
- Risk: private row-level diagnostics leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags.
