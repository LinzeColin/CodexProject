# Remediation Options Matrix

| Option | Host | What it does | Expected value | Risk | Decision |
|---|---|---|---:|---:|---|
| Bounded primary-route remediation | Old computer | Retry only the pinned `r266-tech/wechat-cli`/`wxkey` route with stricter timeouts and narrower commands | High | Medium-high | Recommended |
| Transfer sensitive state to new computer | New computer | Move key config/raw outputs/logs for local debugging | Medium | Very high | Reject for current boundary |
| Run fallback exporter immediately | Old computer | Try another exporter after primary key bootstrap | Medium | High | Defer; needs separate approval after primary remediation fails |
| Full export attempt | Old computer | Attempt broad export without minimal sample | Medium | Very high | Reject |
| Start RAG/Web/Matrix | New computer | Build downstream system without `messages.jsonl` | Low | High | Reject |
| Fully self-developed raw adapter | Old/new computer | Build raw DB/key adapter | Unknown | Very high | Reject unless explicitly authorized later |

## Recommended Choice

Run one bounded primary-route remediation sprint on the old computer.

The purpose is to determine whether the existing installed/pinned route can
produce one minimal message-level sample without broad export or transferring
sensitive local state.

