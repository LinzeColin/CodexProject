# KMFA Delivery Plan

product_version: 0.1.0-s08-github-upload

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
| S06-P1 | completed_validated_local_only |
| S06-P2 | completed_validated_local_only |
| S06-P3 | completed_validated_local_only |
| Stage 6 review | passed |
| Stage 6 GitHub upload | completed |
| S07-P1 | completed_validated_local_only |
| S07-P2 | completed_validated_local_only |
| S07-P3 | completed_validated_local_only |
| Stage 7 review | passed_upload_ready_local_only |
| Stage 7 GitHub upload | completed |
| S08-P1 | completed_validated_local_only |
| S08-P2 | completed_validated_local_only |
| S08-P3 | completed_validated_local_only |
| Stage 8 review | passed_upload_ready_local_only |
| Stage 8 GitHub upload | completed |
| S09-P1 | not_started |

## Upload Scope

Stage 5, Stage 6, Stage 7 and Stage 8 GitHub uploads are complete on `origin/main`. Stage 8 upload reconciled with latest `origin/main`, reran validation, and recorded push proof under `KMFA/stage_artifacts/S08_STAGE_REVIEW/`. S08-P1, S08-P2 and S08-P3 were not uploaded as standalone phases; they were uploaded as part of the full Stage 8 upload gate.

The active development baseline is `KMFA/taskpack/v1_2/`. S05-P1 is complete and locally validated with public-safe A0 file registration. S05-P2 has generated the public-safe field contract and A0 golden fixture candidates, recorded hash-only private values and source anchors for 40 PDF field candidates, and resolved the Excel candidate through an active owner/authorized downgrade decision as cross-source support only. S05-P3 has locked those 40 public-safe hash/source-anchor fields into the A0 authority baseline and excluded the 5 Excel fields from Q5 calculation baseline. Stage 5 review/upload, Stage 6 review/upload, Stage 7 review/upload and Stage 8 review/upload are complete. S08-P1 project composite key is complete with 4 public-safe profiles, 3 match records, 2 manual-review queue records, integer weights and no raw business values. S08-P2 business entity model is complete with 8 public-safe entity types, 14 relationships, 32 lifecycle statuses, schema docs and metadata. S08-P3 matching quality test is complete with 4 public-safe scenarios, 4 quality cases, 3 manual-review queue records and an entity_matching_report. Next scope is S09-P1 project cost fact layer only; S09-P2/report/UI work remains blocked.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
