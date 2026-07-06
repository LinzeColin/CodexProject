# Risk Register

- Risk: treating conservative decision intake as resolved blockers.
  Mitigation: resolution_applied remains false and all reconciliation, lineage, formal report and delivery gates stay closed.
- Risk: leaking private queue details.
  Mitigation: public artifacts contain only decision counts and track-level public-safe codes; target-level decisions stay in ignored runtime.
