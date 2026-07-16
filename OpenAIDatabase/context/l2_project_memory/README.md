# L2 Project Memory

Purpose: accepted active memory, project index, decision log, workflows,
medium/long-term constraints, and reusable project context.

Canonical sources:

- `data/memory/records/manifest.json`
- `data/memory/records/records-NNNN.jsonl`
- `data/derived/project_index/PROJECT_INDEX.md`
- `data/derived/decision_log/DECISION_LOG.md`

Only canonical V2 records are editable truth. The Markdown files are derived
views; the former active/candidate/curation/secret-ref trees are read-only
migration evidence.

Future updates that affect `history`, `pattern`, or `project_context` must
update this layer or explicitly log why the update is not applicable.
