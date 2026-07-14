# KMFA v0.1.4 S17-P2 Notification Policy Rollback Plan

- Remove only `KMFA/stage_artifacts/V014_S17_P2_NOTIFICATION_POLICY/` and `KMFA/metadata/notifications/v014_s17_p2_*` if rollback is required.
- Remove paired v014 S17-P2 governance entries only after confirming no later phase depends on them.
- Do not touch raw/private inbox contents.
