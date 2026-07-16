# Stage 11 whole-review risk and rollback

- Current SQLite 3.50.4 remains outside the approved WAL-safe set; production connections stay on DELETE/FULL.
- The real canonical database was read only through SQLite URI mode=ro; no canonical migration or restore was performed.
- All restore success/failure targets and private backup artifacts were isolated temporary copies and were deleted on exit.
- Roll back by reverting remediation commit `9c450ea48` and the later evidence/governance commit; do not touch the canonical database.
- Stage 12, push, canonical PFI.app installation, production and final acceptance remain outside this run.
