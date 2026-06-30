# Agent Loop Validation Matrix

| Stage | Validator | Blocks merge | Evidence |
|---|---|---|---|
| Task Pack ingestion | `validate_taskpack.py` | Yes | metadata and section report |
| Plan | `validate_plan.py` | T2 yes, T1 if required | plan artifact |
| Plan no-write | `git diff --quiet` | Yes | workflow log |
| Implementation | Task Pack validation commands | Yes | validation summary |
| Changed files | `changed_files_policy.py` | Yes | changed file report |
| Codex review | prompt + review output | P0/P1 block | review artifact |
| Architect Review | `architect_review.py` | P0/P1 block if run | architect review artifact |
| Autofix | Codex autofix loop | Yes if unresolved | autofix artifact |
| Merge | `merge_policy.py` | Yes | merge policy report |

Validation commands must be safe for the repository and must not deploy
production in this bootstrap.
