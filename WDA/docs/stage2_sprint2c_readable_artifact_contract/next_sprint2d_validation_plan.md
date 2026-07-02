# Next Sprint 2D Validation Plan

Generated: 2026-07-03T09:12:39+10:00

Sprint 2D should run only if the user provides or approves a small owner-authorized sample artifact.

## Goal

Validate artifact shape and authorization, not message meaning.

## Inputs

Expected local artifact package:
- `import_manifest.json`
- Optional small `messages.jsonl`
- Optional small `conversations.jsonl`
- Optional small `contacts.jsonl`
- Optional `media_index.csv`

## Allowed Operations

- Read manifest fields.
- Verify checksums and file sizes.
- Count JSONL/CSV rows.
- Validate required field presence and primitive types.
- Validate cross-file IDs.
- Produce a local validation report.

## Forbidden Operations

- Decrypt, extract keys, or bypass protected stores.
- Open `key_info`, login, MMKV, KVDB, key-value stores, protected DBs, WAL, or SHM.
- Select message/contact/business rows from protected DB bundles.
- Parse protected raw message content.
- Run third-party WeChat export/decrypt tools.
- Access the external hard drive unless the user explicitly provides the sample artifact there for read-only copy.
- Upload raw data.
- Implement RAG/Web/Matrix.

## Acceptance

- Validation report says whether the sample satisfies the Sprint 2C contract.
- Raw Gate remains `Conditional Investigation` unless a separately approved gate decision upgrades it.
- WDA RAG/Web/Matrix remains blocked until the artifact path is accepted and a later import stage is approved.
