# Risk Register

- Risk: treating private partial staging as canonical source-map mutation.
  Mitigation: canonical source-map mutation remains false and full reapplication remains closed.
- Risk: leaking private target slots or group refs publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; slot-level rows stay in ignored runtime.
