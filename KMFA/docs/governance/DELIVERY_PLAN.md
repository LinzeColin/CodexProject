# KMFA Delivery Plan

product_version: 0.1.0-s04p2

## Delivery Rule

KMFA delivery follows the owner contract:

1. One pursuing goal handles one Stage.
2. One run work solves at most one Phase.
3. Intermediate Phase completion is not uploaded to GitHub.
4. Whole Stage review happens after all Stage phases finish.
5. Review findings are fixed before overall GitHub upload.

## Current Delivery Scope

| Item | Status |
|---|---|
| S01-P1 | completed |
| S01-P2 | completed_validated |
| S01-P3 | completed_validated |
| Stage 1 review | passed |
| Stage 1 GitHub upload | completed |
| S02-P1 | completed_validated |
| S02-P2 | completed_validated |
| S02-P3 | completed_validated |
| Stage 2 review | passed |
| Stage 2 GitHub upload | completed |
| v1.2 full task pack baseline | completed_validated |
| Stage 1 v1.2 replay | completed_validated |
| S03-P1 | completed_validated_local_only |
| S03-P2 | completed_validated_local_only |
| S03-P3 | completed_validated_local_only |
| Stage 3 review | passed_upload_ready |
| Stage 3 GitHub upload | completed |
| S04-P1 | completed_validated_local_only |
| S04-P2 | completed_validated_local_only |
| S04-P3 | planned |
| Stage 4 review | not_started |
| Stage 4 GitHub upload | not_allowed |

## Upload Scope

Stage 2 GitHub upload is complete on `origin/main`; the reviewed content commit was `834ff75516405ddbc8289f00ba67579691473709` and the final remote main commit observed before this rebaseline was `6178b5215f92f12d6facad9a990e8659b3a70ba4`.

The active development baseline is `KMFA/taskpack/v1_2/`. S04-P1 is complete and locally validated with amount normalization and no-float checks. S04-P2 is complete and locally validated with field standardization and missing-field quality status. S04-P3 is not started. Stage 4 has not been reviewed, so GitHub upload is not allowed.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
