# Changelog

## 0.1.0 - 2026-06-20

- Established CodexProject governance baseline for Alpha without changing product behavior.
- Added canonical model, formula, parameter, delivery, version, and traceability registries under `docs/governance/`.
- Preserved committed safety posture: live trading remains disabled and real-money broker submission remains fail-closed.
- Converted legacy governance notes into compatibility indexes pointing at canonical governance files.
- S3PBT01 adds locked atomic JSON persistence for ApprovalQueue and PaperBroker so concurrent local paper loops do not overwrite queue or portfolio state; shutdown/stop behavior remains a later S3PB task.
- S3PBT02 hardens AutoPaperAgent stop truthfulness and dashboard PID lifecycle: drained stops report stopped, timeout stops report `stop_timeout` with the task still running, and start/stop scripts preserve PID evidence until process exit.

Product runtime version is inherited from `pyproject.toml` `0.1.0`; this governance repair does not introduce a product feature change.
