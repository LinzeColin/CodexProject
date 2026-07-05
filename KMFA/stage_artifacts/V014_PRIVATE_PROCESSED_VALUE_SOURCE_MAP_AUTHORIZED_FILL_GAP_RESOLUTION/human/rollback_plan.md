# Rollback Plan

1. Remove this phase's public artifacts and metadata quality copies.
2. Remove ignored private runtime folder for this phase.
3. Re-run the previous authorized-fill validator to restore the prior NO_GO gate.
4. Do not touch the raw inbox during rollback.
