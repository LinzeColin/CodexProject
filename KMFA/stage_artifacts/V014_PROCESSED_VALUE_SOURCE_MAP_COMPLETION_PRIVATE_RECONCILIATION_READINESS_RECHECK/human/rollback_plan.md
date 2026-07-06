# Rollback Plan

- Remove this phase's public artifacts and metadata copies.
- Remove ignored private diagnostic files under the phase runtime directory.
- Re-run the previous decision-intake validator before retrying readiness recheck.
