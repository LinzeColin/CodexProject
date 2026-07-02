# IDS Metadata Raw Data Boundary

- Boundary ID: `IDS-METADATA-RAW-DATA-BOUNDARY`
- Recorded at UTC: `2026-07-02T10:48:44Z`
- Local raw metadata root: `/Users/linzezhang/Downloads/IDS_MetaData`
- Repository path for the boundary record: `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`
- GitHub repository: `LinzeColin/CodexProject`
- Product scope: `KM_IDSystem`

## Purpose

This record writes the local IDS metadata database root into the GitHub-tracked
project governance files without committing, copying, scanning, modifying, or
deleting any raw database content.

## Raw Data Rules

- `/Users/linzezhang/Downloads/IDS_MetaData` is a read-only raw metadata
  database source.
- Codex must not create, edit, delete, move, clean, rewrite, normalize, rename,
  or compact files inside that local raw metadata root.
- Codex may only modify files inside the active project worktree and only under
  the task-approved `KM_IDSystem/` scope.
- Raw filenames, table contents, row values, schema details, credentials,
  private business values, and derived dumps from the raw metadata root must not
  be committed to GitHub unless the user explicitly provides a future
  sanitized/export-approved artifact.
- Existence checks such as `test -d /Users/linzezhang/Downloads/IDS_MetaData`
  are allowed; recursive listing, content hashing, database opening, row reads,
  and data extraction are not allowed unless a future stage explicitly grants
  that scope.

## Real Data Only Policy

- IDS runtime corpus, database-backed content, analytics inputs, reports,
  indexes, manifests, and committed examples must use real user-approved data.
- New fake industrial records, fake database rows, fake business documents,
  placeholder corpora, and fabricated evidence are forbidden.
- Validation may use temporary structural paths or scalar boundary values only
  when they are clearly test harness state, are not ingested as IDS corpus, and
  are not presented as business data or evidence.

## Current Verification

- Local existence check: `IDS_METADATA_ROOT_EXISTS`
- Verification command: `test -d /Users/linzezhang/Downloads/IDS_MetaData`
- Raw directory content read: `no`
- Raw directory content modified: `no`
- Raw directory content copied into GitHub: `no`

## Stop Conditions

- Any step requires reading, listing, hashing, opening, copying, moving,
  rewriting, or deleting raw metadata database content.
- Any implementation proposes fake IDS corpus data, fake database rows, fake
  source documents, or fabricated evidence.
- A future stage cannot distinguish test harness state from user-approved real
  IDS data.

## Rollback

Revert this boundary record and the governance references to it. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData` during rollback.
