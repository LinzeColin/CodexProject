# KMFA v1.4 S01-P1 Risk Register

| Risk | Severity | Status | Control |
|---|---:|---|---|
| v1.4 taskpack declares main-repo project path while this Mac uses project-level worktree | High | CONTROLLED | Use canonical KMFA worktree and record path adaptation |
| Delivery ZIP contains private/raw payload members | Critical | CONTROLLED | Do not extract or commit private payloads or raw member names |
| S01-P1 drifts into S01-P2 implementation | Medium | CONTROLLED | Scope lock marks `next_phase_started=false` |
| Raw data inbox accidentally read or modified | Critical | CONTROLLED | This phase does not read/list raw inbox and validator checks false flags |
| UIUX gate treated as static visual reference | High | CONTROLLED | v1.4 human-flow audit is recorded as active baseline |
| Future validators depend on local Downloads ZIP | Medium | CONTROLLED | Validator only requires source package with an explicit local flag |

Residual risk: S01-P2 must decide how much of the public-safe v1.4 package to sync into repo without committing raw/private payloads.
