# Memory Atlas v1.2 S02 P1 Source Data Model

## Metadata

- task_id: `MA-V12-S02P1`
- acceptance_id: `ACC-MA-V12-S02P1`
- status: `phase_s02_p1_source_data_model_completed_pending_s02_p2`
- validator: `validate:v1.2-s02-p1`
- model: `机器治理/数据契约/source_data_model.v1_2_s02_p1.json`

## Result

S02 P1 defines the shared source data model for ChatGPT, Codex and future other
agents. It does not create the S02 P2 source registry file and does not create
the S02 P3 human sync page.

## Required Fields

| Field | Purpose |
|---|---|
| `source_id` | Stable source identifier for later registry entries. |
| `source_type` | Supports `chatgpt`, `codex` and `other_agent`. |
| `agent_name` | Human-readable agent or connector name. |
| `raw_root` | Future repo-relative public raw root. |
| `sync_mode` | One of manual, scheduled, on_demand or dry_run. |
| `public_backup_mode` | Public backup strategy, currently `plaintext_public`. |
| `connector_capability` | Connector capability list such as browser_readonly, official_export_fallback, local_session_sync, local_file, api or manual_import. |

## Boundary Model

Each source must distinguish transcript 与 credential:

- Transcript examples: conversation_content, message_text, metadata and tool_call_summary.
- Credential examples: cookies, session_tokens, passwords, API keys, private keys, OAuth tokens and browser credential stores.
- Credential material is never transcript data and must fail closed before commit or public backup.

## Source Types

- `chatgpt`: ChatGPT browser readonly and official export fallback capability.
- `codex`: Codex local session sync capability.
- `other_agent`: future agent adapters through local_file, browser, api or manual_import capability.

## Phase Boundary

- No source registry file in this phase.
- No human sync page in this phase.
- No connector implementation in this phase.
- No raw archive change.
- No GitHub main upload in this phase.
- pending S02 P2.
