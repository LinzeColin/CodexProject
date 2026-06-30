# Agent Loop Scripts

These scripts are stdlib-only helpers for the Agent Loop workflows.

| Script | Purpose |
|---|---|
| `extract_taskpack.py` | Store approved workflow input as taskpack files and metadata. |
| `validate_taskpack.py` | Validate dual-plane Task Pack metadata and Markdown sections. |
| `validate_plan.py` | Validate Codex plan-first output and no-write behavior. |
| `changed_files_policy.py` | Ensure actual changed files stay inside Task Pack scope. |
| `merge_policy.py` | Enforce T1/T2 merge gates. |
| `extract_result_pack.py` | Validate result pack sections. |
| `architect_review.py` | Run optional OpenAI-based Architect Review or report N/A. |
| `write_summary.py` | Build a compact Markdown summary artifact. |

All scripts avoid third-party dependencies so GitHub Actions can run them on a
stock runner.
