# Artifact Storage Contract

Generated: 2026-07-03T09:51:08+10:00

Future user-provided readable artifacts should be placed under:

```text
/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/owner_authorized_readable_artifacts/
```

Recommended package layout:

```text
owner_authorized_readable_artifacts/
  <artifact_id>/
    import_manifest.json
    messages.jsonl
    conversations.jsonl
    contacts.jsonl
    media_index.csv
    media/
```

Allowed variants:
- A single `.zip` package under the storage root.
- A folder containing `import_manifest.json` and readable files.
- A small sample package for Sprint 2G validation.

Required metadata:
- Source route.
- Owner authorization.
- Data time range.
- Subject/contact scope if known.
- Privacy level.
- Whether original content or redacted content.
- File checksum.
- Import manifest.

Storage rules:
- Keep artifacts local.
- Do not commit artifacts to git.
- Do not upload artifacts.
- Do not place protected DBs, WAL/SHM, key stores, MMKV/KVDB, or raw WeChat cache files in this intake folder.
