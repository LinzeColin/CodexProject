# Canonical Memory Record V2

The normative schema is `config/memory.schema.json`. The only editable logical
truth is the sharded JSONL dataset discovered through
`data/memory/records/manifest.json`.

Every record has one of four statuses in the same schema:

- `candidate`: unverified review candidate.
- `active`: verified current truth; at most one unresolved active record per
  `memory_key` and scope.
- `disputed`: unresolved conflict.
- `retired`: historical or rejected material retained for audit.

Required record groups are identity (`id`, `memory_key`, `kind`, `statement`,
`status`), scope and time, source provenance, supersession/conflict state,
verification, sensitivity, retrieval aids, and the deterministic record hash.
Use the JSON Schema for exact enums, patterns, conditionals, and canonical hash
rules; do not maintain a second prose copy of those constraints here.

## Repository Layout

```text
OpenAIDatabase/
  config/memory.schema.json
  data/memory/records/
    manifest.json
    records-NNNN.jsonl
  data/derived/
    profile/CORE_PROFILE.md
    weekly/*.weekly_memory_pack.md
    monthly/*.monthly_memory_pack.md
    human_reviews/*.human_memory_review.md
    incremental/*.incremental_change_report.md
    context_packs/*.md
  data/processed/indexes/memory_index.sqlite  # local, ignored, rebuildable
```

The former `data/memory/active/`, `candidates/`, `curation/`, and
`secret_refs/` trees are byte-locked, read-only migration evidence. They are
not sources for normal retrieval and must never receive a dual write.

## Security And Evidence

Canonical records may contain only public text or redacted summaries.
`sensitivity.credential_present` is always false, and plaintext credentials,
tokens, cookies, sessions, private keys, or recovery codes are prohibited.
Source and verification evidence must remain traceable through stable refs and
SHA-256 values without embedding secret values.

SQLite and Markdown are derived views. They may be rebuilt from the canonical
manifest but never become an editable source of truth.
