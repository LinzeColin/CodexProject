# OpenAIDatabase S5PBT02 Structure Report

task_id: `S5PBT02`
acceptance_id: `ACC-S5PBT02`
mode: `BOUNDARY_ONLY_NO_PRIVATE_VALUE_EMISSION`

## Owner Summary

S5PBT02 separates OpenAIDatabase's operational defaults into four visible
layers while preserving Review9 Wave 2 privacy truth:

- App: `OpenAIDatabase/apps/memory-atlas/`
- Skills: `OpenAIDatabase/skills/openai-memory-analysis/`
- Context: `OpenAIDatabase/context/`, `OpenAIDatabase/config/context_sources/`,
  and redacted derived agent-context packs
- Private exports: external, encrypted, or ignored local paths only

No tracked private-memory files were moved in this task. The existing 104
OpenAIDatabase private candidates remain checksum-bound by
`governance/stage_gates/s5pa/wave2_archive_manifest.json` and summarized by
`governance/stage_gates/s5pa/privacy_manifest.md`.

## Default Entry Contract

- Default startup remains `OpenAIDatabase/AGENTS.md`.
- Resource routing remains `OpenAIDatabase/scripts/route_agent_resources.py`.
- App runtime remains `OpenAIDatabase/apps/memory-atlas/`.
- Agent context entry remains redacted derived context, not raw export data.
- Local absolute paths are non-default historical examples or test fixtures.

## Privacy Contract

- Raw OpenAI exports are not committed.
- Private imports are not committed.
- Future private export folders are ignored by project-level and root-level
  `.gitignore` rules.
- Ignored private export paths include `private_exports/`,
  `exports/private/`, and `data/private/`.
- S5PBT02 evidence emits path classes, counts, checksums, and policy markers
  only; it emits no personal content values.
- Privacy log mode is `PATH_AND_MARKER_ONLY_NO_VALUES`.

## Smoke Evidence

- `python -B -m pytest OpenAIDatabase/tests -q`: `NOT_RUN`, local Python
  environments do not include `pytest`.
- `python -B -m unittest tests.test_s3pdt01_privacy -q`: `PASS`, 3 tests OK.
- `python -B -m unittest tests.test_agent_context_pack -q`: `PASS`, 1 test OK.
- `python -B -m unittest tests.test_codex_memory_sync -q`: `PASS`, 1 test OK.

Result: `PASS_WITH_PYTEST_ENV_BLOCKER_RECORDED`, privacy and context smoke tests
passed through the available `unittest` runner.

## Stop Conditions

- OpenAIDatabase examples contain real personal content: `false`
- Private exports default to tracked plaintext paths: `false`
- Absolute local paths used as default entries: `false`
- Private values emitted in S5PBT02 evidence: `false`
- App reads raw exports by default: `false`

## Rollback

Rollback is governance-only: remove the S5PBT02 report, contract, privacy log,
run manifest, README/AGENTS boundary text, and OpenAIDatabase private-export
ignore additions. No product runtime, tracked private data, or generated memory
files were moved by this task.
