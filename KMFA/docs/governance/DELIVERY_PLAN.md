# KMFA Delivery Plan

product_version: 0.1.0-s02p1

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
| S02-P2 | not_started |
| S02-P3 | not_started |
| Stage 2 review | blocked_until_s02_p2_p3_complete |
| Stage 2 GitHub upload | blocked_until_stage2_review_fix |

## Upload Scope

No GitHub upload is allowed after S02-P1 alone. The next upload may happen only after S02-P1/P2/P3 are complete, Stage 2 review is complete, and review findings are fixed.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
