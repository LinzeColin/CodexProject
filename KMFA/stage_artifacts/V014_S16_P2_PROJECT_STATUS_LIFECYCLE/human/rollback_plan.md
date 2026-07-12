# KMFA v0.1.4 S16-P2 rollback plan

Rollback is local-only: remove the V014_S16_P2_PROJECT_STATUS_LIFECYCLE artifact directory, remove the v014 S16-P2 tool, validator, and test file, then revert governance entries from this phase before any future upload gate. The ignored private runtime report can be deleted locally if desired; no raw/private inbox file is modified by this phase.
