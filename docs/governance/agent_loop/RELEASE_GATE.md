# Release Gate

Agent Loop separates code merge from delivery and production release.

## Merge To Main

Merge to `main` means the Task Pack implementation passed validation,
review, changed-files policy, and merge policy. It does not mean production
deployment.

## Staging

Staging may be added by a separate Task Pack. This bootstrap does not deploy
staging automatically.

## Production

Production deployment is disabled by default. A production Task Pack must
explicitly authorize production behavior and must pass separate release gates.

## Delivery Acceptance

Delivery acceptance is the Owner-readable evidence that acceptance criteria were
met. It may include PR, audit issue, artifacts, validation logs, and result pack.

## Rollback

Default rollback is reverting the bootstrap PR or implementation PR. No data
migration or production rollback is assumed unless the Task Pack explicitly
states otherwise.
