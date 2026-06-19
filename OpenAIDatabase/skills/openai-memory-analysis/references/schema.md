# Memory Schema

## Canonical Memory Candidate

Use JSONL for machine-readable memory records. Each line is one object:

```json
{
  "id": "mem_...",
  "action": "add",
  "date": "2026-06-15",
  "source": "OpenAI-export.zip:conversation:<id>",
  "category": "preference",
  "statement": "用户偏好默认中文、高密度、可执行输出。",
  "importance": "高",
  "validity": "长期",
  "confidence": "high",
  "reason": "用户明确使用持久性偏好措辞。",
  "sensitivity": "private",
  "secret_ref": "",
  "credential_policy": {},
  "review_status": "pending",
  "evidence": [
    {
      "source": "OpenAI-export.zip",
      "conversation_id": "...",
      "timestamp": "2026-06-15T00:00:00Z",
      "summary": "Matched durable-memory trigger in a user-authored message."
    }
  ]
}
```

Required user-facing fields:

- `date`
- `source`
- `category`
- `importance`: `高`, `中`, `低`
- `validity`: `长期`, `半年`, `项目结束前`, `临时`
- `confidence`
- `reason`

## Categories

- `answering_rule`: future response or collaboration rules.
- `preference`: stable user preference.
- `decision`: explicit decision or locked choice.
- `project_context`: durable project context.
- `workflow`: reusable process or operating pattern.
- `security_boundary`: authorization, safety, or privacy rule.
- `deprecated_info`: information marked obsolete or replaced.
- `temporary_or_sensitive`: one-off, short-lived, or unsafe-to-store content.

## Secret Reference Fields

When source material contains a credential or high-risk secret, do not store plaintext in GitHub. Store only redacted metadata:

- `secret_ref`: stable opaque reference such as `secretref_...`
- `credential_policy`: intended workflow, required user approval, local resolver requirement, and trading/broker fail-closed boundary
- `security_findings`: redacted finding types and hashes only

Finance, trading, and broker agents may use `secret_ref` to request authorized local access. They must not treat GitHub memory records as a plaintext credential source.

## Repository Layout

```text
OpenAIDatabase/
  skills/openai-memory-analysis/
  config/memory_schema.json
  data/
    memory/
      active/active_memory.jsonl
      curation/core_profile_review.json
      candidates/*.memory_candidates.jsonl
      secret_refs/*.secret_refs.jsonl
      deprecated/*.deprecated.jsonl
    derived/
      weekly/*.weekly_memory_pack.md
      monthly/*.monthly_memory_pack.md
      human_reviews/*.human_memory_review.md
      incremental/*.incremental_change_report.md
      context_packs/*.md
      profile/CORE_PROFILE.md
    processed/
      conversations/conversation_manifest.jsonl
      indexes/memory_index.sqlite
    raw_encrypted/
  .local_keys/                 # ignored
```

Markdown and JSONL are the source of truth. SQLite is a rebuildable read index.

## Core Profile Curation

`data/memory/curation/core_profile_review.json` stores manual review overrides
for memory IDs. Supported override fields include `statement`, `category`,
`importance`, `validity`, `confidence`, `reason`, `memory_tier`, `sensitivity`,
`status`, and `review_reason`.

Use curation to keep project-specific workflows, dashboards, code snippets,
logs, one-off commands, and short-term operational details out of high-weight
`核心画像`. The derived `data/derived/profile/CORE_PROFILE.md` is generated from
active memory after applying these overrides.
