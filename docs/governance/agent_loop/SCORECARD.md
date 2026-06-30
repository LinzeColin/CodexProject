# Agent Loop Scorecard

Use this scorecard in audit issues and retrospectives.

| Field | Status | Evidence |
|---|---|---|
| Task Pack valid | TBD | workflow log |
| Executor mode resolved | TBD | `agent-loop-roi-summary.md` |
| Paid calls attempted | TBD | `agent-loop-roi-summary.md` |
| Paid call limit respected | TBD | `agent-loop-roi-summary.md` or `PAID_CALL_LIMIT_REACHED` |
| Plan generated | T1: N/A / T2: required later | artifact |
| Plan no-write verified | T1: N/A / T2: required later | `git diff --quiet` |
| Plan validation passed | T1: N/A / T2: required later | validator output |
| Implementation completed | TBD | PR |
| Validation commands passed | TBD | validation summary |
| Changed-files policy passed | TBD | policy output |
| Codex review completed | Default: ROI skipped | review artifact |
| Architect Review completed or N/A | Default: ROI skipped | architect artifact |
| Autofix loops within limit | Default T1: 0 | workflow log |
| Merge policy passed | TBD | merge policy output |
| Squash merged | TBD | PR |
| Audit issue closed | TBD | issue |
| Failure artifact captured | TBD | failure git status/diff artifacts |
| Blind rerun avoided | TBD | issue comments / labels |
