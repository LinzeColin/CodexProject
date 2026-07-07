# Risk Register

- Risk: readiness can be mistaken for actual source-map correction.
  - Control: application/write/comparison/reconciliation/upload flags stay false.
- Risk: private target details leak into public artifacts.
  - Control: public artifacts carry aggregate counts and status refs only.
- Risk: raw inbox accidentally becomes a workspace.
  - Control: this phase does not read, list, parse, hash, write or mutate raw inbox files.
