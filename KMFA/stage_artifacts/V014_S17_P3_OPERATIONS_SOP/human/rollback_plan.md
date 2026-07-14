# KMFA v0.1.4 S17-P3 Operations SOP Rollback Plan

- Remove only `KMFA/stage_artifacts/V014_S17_P3_OPERATIONS_SOP/` and `KMFA/metadata/operations/v014_s17_p3_*` if rollback is required.
- Remove paired v014 S17-P3 governance entries only after confirming no later phase depends on them.
- Do not touch raw/private inbox contents or production runtime state.
