# Memory Atlas v1.2 S02 P2 Source Registry

## Metadata

- task_id: `MA-V12-S02P2`
- acceptance_id: `ACC-MA-V12-S02P2`
- status: `phase_s02_p2_source_registry_completed_pending_s02_p3`
- validator: `validate:v1.2-s02-p2`
- registry: `机器治理/同步与备份/sync_source_registry.json`
- model_ref: `机器治理/数据契约/source_data_model.v1_2_s02_p1.json`

## Result

S02 P2 establishes `sync_source_registry.json` from the S02 P1 source data model.
The registry is not hardcoded to only ChatGPT and Codex: it includes
`future_agent_template` with `other_agent` source type.

## Registered Sources

| Source | Source Type | Connector |
|---|---|---|
| `chatgpt` | `chatgpt` | ChatGPT browser connector with official export fallback. |
| `codex` | `codex` | Codex local sync through local session transcripts. |
| `future_agent_template` | `other_agent` | `future_agent_adapter` for later local file, browser, API or manual import sources. |

## Boundaries

- Every source uses `plaintext_public` public backup mode.
- Every source includes transcript/credential boundaries.
- Credentials remain excluded: cookies, session tokens, passwords, API keys, private keys, OAuth tokens and browser credential stores.
- No human sync page in this phase.
- No connector implementation in this phase.
- No GitHub main upload in this phase.
- No raw archive change.
- pending S02 P3.
