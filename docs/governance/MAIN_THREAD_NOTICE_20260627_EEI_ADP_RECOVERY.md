# Main Thread Notice - EEI / ADP Recovery

Timestamp: 2026-06-27 Australia/Sydney

## Canonical Address

Use this as the only active local product root for `LinzeColin/CodexProject`:

```text
/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject
```

Do not continue active work from duplicate `CodexProject*`, `PFI_OS`, `EVA_OS`,
or project-specific shadow folders. Persistent source changes must land under
this GitHub root.

## Recovery Changes Made

- Root `AGENTS.md` and `README.md` now document the single-checkout rule and
  launcher/cwd verification requirement.
- EEI app launcher now points to
  `CodexProject/EEI`.
- ADP LaunchAgents were corrected from the stale
  `CodexProject_adp_local_runner_current` checkout to the canonical
  `CodexProject` root. They remain `Disabled=true`; no schedule or SMTP
  enablement was performed.
- Alpha launcher scripts were made executable and Serenity launchd wrapper now
  resolves root dynamically. These are cross-project recovery changes, not EEI
  or ADP feature changes.

## EEI State

- Source root: `CodexProject/EEI`.
- `HANDOFF.md` says G1/G2/G3 are proven PASS, G4 remains `IN PROGRESS`.
- MVP release preflight validator currently passes:
  `python3 -B scripts/validate_mvp_release_gate.py validate`.
- A209/T1307 release readiness is still blocked: `validate_operator_soak_evidence.py
  validate --require-release-ready` reports missing/partial 24h operator evidence.
- Do not claim MVP release-ready, A209 DONE, or final release acceptance until a
  clean 24h operator soak has committed artifacts and validator passes.

## ADP State

- Source root: `CodexProject/arxiv-daily-push`.
- Current contract pointer is
  `arxiv-daily-push/docs/pursuing_goal/CURRENT.yaml`.
- Current global Stage 2 pointer remains `S2PMT07` blocked precheck; integrated
  production acceptance is false.
- Local sanity test passed with:
  `PYTHONPATH=src python3 -B -m pytest tests/test_handoff.py -q`.
- Do not enable real SMTP, automatic scheduler install, daily operation,
  production restore, release packaging, or final-video claims until V7.2
  blockers are explicitly closed by evidence.

## Required Next Step For Main Thread

Before continuing EEI or ADP development, re-read root `AGENTS.md`, this notice,
and each project contract/HANDOFF. Verify active process cwd and LaunchAgents
before starting work. Do not create or use a second checkout as the development
base.
