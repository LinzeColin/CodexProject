# KMFA Delivery Plan

product_version: 0.1.0-s07-github-upload

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
| S08-P1 | not_started |

## Upload Scope

Stage 5 and Stage 6 GitHub uploads are complete on `origin/main`. Stage 6 upload reconciled with latest `origin/main`, reran validation, and recorded push proof under `KMFA/stage_artifacts/S06_STAGE_REVIEW/`. S07-P1, S07-P2, S07-P3 and Stage 7 review are complete local-only and have not been uploaded as standalone phases.

The active development baseline is `KMFA/taskpack/v1_2/`. S05-P1 is complete and locally validated with public-safe A0 file registration. S05-P2 has generated the public-safe field contract and A0 golden fixture candidates, recorded hash-only private values and source anchors for 40 PDF field candidates, and resolved the Excel candidate through an active owner/authorized downgrade decision as cross-source support only. S05-P3 has locked those 40 public-safe hash/source-anchor fields into the A0 authority baseline and excluded the 5 Excel fields from Q5 calculation baseline. Stage 5 review/upload, Stage 6 review/upload and Stage 7 review/upload are complete. S07-P1 financial file adaptation is complete with 9 finance categories, 45 field candidates, and 9 read-only field reports. S07-P2 WPS file adaptation is complete with 4 WPS export types, 20 field mappings, 4 conversion guidance records, 4 read-only field reports, and 1 mapping rule version. S07-P3 redcircle postponement policy is complete with 4 reserved export templates, automatic connector blocked for D15 file MVP, and future read-only/hash/rollback/manual approval controls. Next scope is S08-P1 project composite key only.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
