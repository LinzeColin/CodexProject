# Risk Register

- Risk: treating private fill candidates as verified materialized values.
  Mitigation: this phase only stages a private fill draft; replay and raw-to-processed comparison remain closed.
- Risk: leaking private candidate fingerprints publicly.
  Mitigation: public artifacts contain aggregate counts only; candidate-level fingerprints stay in ignored runtime.
