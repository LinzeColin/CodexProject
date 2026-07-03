# New vs Old Computer Execution Plan

## New Computer

Role: WDA Control Plane.

- Owns WDA repo, governance docs, validation, and future database/RAG/Web stack.
- Receives only approved generated artifacts, not the whole WeChat cache.
- Converts approved trial output into WDA Raw Import Pack if the route succeeds.
- Runs import validation after an approved trial produces files.

## Old Computer

Role: high-value data source and likely automated acquisition host.

- Runs only the explicitly approved acquisition trial.
- Uses a tiny trial scope before any broad export.
- Writes output to an owner-approved local metadata path.
- Does not host heavy RAG/database/Web workloads.

## Transfer Boundary

Only trial artifacts and validation reports should be transferred to the new
computer. Do not copy the entire old 47GB WeChat cache as the next step.

## Recommended Placement

For Sprint 2H, use a path shaped like:

`/Users/linzezhang/Downloads/WDA_MetaData/stage2_trials/sprint2h_automated_acquisition_trial_YYYYMMDD/`

Expected subfolders:

- `tool_evidence/`
- `raw_output/`
- `wda_raw_import_pack/`
- `validation_report/`

