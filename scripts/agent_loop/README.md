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
| `submit_taskpack.py` | Submit an approved Task Pack through `gh` issue, dispatch, or workflow modes. |
| `build_prefilled_issue_url.py` | Build a prefilled GitHub issue URL for C3 browser submission. |
| `route_taskpack.py` | Resolve a Task Pack to one routing-matrix project or block/split safely. |
| `autofill_taskpack_metadata.py` | Fill missing project/path/validation metadata only when routing is unambiguous. |

All scripts avoid third-party dependencies so GitHub Actions can run them on a
stock runner.

## C3 Issue Form Behavior

Issue Form labels are convenience only. The main workflow starts on trusted
`issues: opened` and `issues: edited` events when the issue body contains
`AGENT_LOOP_METADATA` and metadata `source` is `chatgpt-approved`. The workflow
creates missing labels itself and then routes/autofills before any Codex
implementation step.

## Routing And Autofill

Routing reads `docs/governance/agent_loop/PROJECT_ROUTING_MATRIX.md` as the
source of truth:

```bash
python3 scripts/agent_loop/route_taskpack.py \
  --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack.md
```

Autofill writes a normalized Task Pack:

```bash
python3 scripts/agent_loop/autofill_taskpack_metadata.py \
  --input docs/governance/agent_loop/examples/minimal_t1_taskpack.md \
  --output /tmp/agent_loop_normalized_taskpack.md
```

## Local Submission

The D1 submitter uses existing GitHub CLI authentication:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --mode issue \
  --repo LinzeColin/CodexProject
```

Supported modes:

- `issue`: create a Task Pack issue and add `agent:run` after
  `source:chatgpt-approved`.
- `dispatch`: send `repository_dispatch` with event type `agent_loop_taskpack`.
- `workflow`: trigger `Agent Loop - Run Approved Task Pack` as fallback.

Use `--dry-run-local` to validate without calling GitHub.
