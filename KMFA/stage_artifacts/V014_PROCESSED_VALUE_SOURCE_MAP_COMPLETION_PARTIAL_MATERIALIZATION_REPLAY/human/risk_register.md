# Risk Register

- Risk: mistaking partial materialization replay for raw data reconciliation.
  Mitigation: raw-to-processed comparison, business consistency, lineage full check and formal report remain closed.
- Risk: leaking private materialized slot details publicly.
  Mitigation: public artifacts contain aggregate counts only; row-level replay evidence stays in ignored runtime.
