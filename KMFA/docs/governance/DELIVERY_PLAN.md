# KMFA Delivery Plan

product_version: 0.1.0-s05-github-upload

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
| S05-P2 | completed_validated_local_only_owner_downgrade |
| S05-P3 | completed_validated_local_only_public_safe_authority_lock |
| Stage 5 review | passed_upload_ready_local_only |
| Stage 5 GitHub upload | completed |
| S06-P1 | not_started |

## Upload Scope

Stage 4 GitHub upload is complete on `origin/main`; the reviewed content commit was `25c85dcee55679d0789f8462a7c7875188d0aa9f`.

The active development baseline is `KMFA/taskpack/v1_2/`. S05-P1 is complete and locally validated with public-safe A0 file registration. S05-P2 has generated the public-safe field contract and A0 golden fixture candidates, recorded hash-only private values and source anchors for 40 PDF field candidates, and resolved the Excel candidate through an active owner/authorized downgrade decision as cross-source support only. S05-P3 has locked those 40 public-safe hash/source-anchor fields into the A0 authority baseline and excluded the 5 Excel fields from Q5 calculation baseline. Stage 5 review and final GitHub upload are complete with `S05_STAGE_REVIEW` evidence. S06-P1 has not started.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
