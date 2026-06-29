# KMFA Delivery Plan

product_version: 0.1.0-s05p2-private-backfill-partial

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
| S04-P3 | completed_validated_local_only |
| Stage 4 review | passed |
| Stage 4 GitHub upload | completed |
| S05-P1 | completed_validated_local_only |
| S05-P2 | in_progress_partial_hash_only_backfill_excel_pending |
| S05-P3 | not_started |
| Stage 5 review | not_allowed |
| Stage 5 GitHub upload | not_allowed |

## Upload Scope

Stage 4 GitHub upload is complete on `origin/main`; the reviewed content commit was `25c85dcee55679d0789f8462a7c7875188d0aa9f`.

The active development baseline is `KMFA/taskpack/v1_2/`. S05-P1 is complete and locally validated with public-safe A0 file registration. S05-P2 has generated the public-safe field contract and A0 golden fixture candidates, and 40 of 45 field candidates now have hash-only private values and source anchors from local private input. Five Excel candidate fields remain pending. Stage 5 review and GitHub upload are not allowed until S05-P2 private backfill is complete or explicitly resolved, S05-P3 is complete, full Stage 5 review runs, and review fixes are complete.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
