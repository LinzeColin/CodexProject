# KMFA Delivery Plan

product_version: 0.1.0-s01p3

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
| GitHub upload | ready_with_clean_worktree |

## Upload Scope

Only these paths may be staged for Stage 1 upload:

- `KMFA/`
- `README.md`
- `governance/projects.yaml`

The canonical checkout contains unrelated dirty state and is behind `origin/main`; final upload must be prepared in a clean worktree based on `origin/main`.

## Rollback

For S01-P2, rollback is:

```bash
rm -rf KMFA
```

Then remove the KMFA row from root `README.md` and the KMFA entry from `governance/projects.yaml`.
