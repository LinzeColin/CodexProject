# Automated Route Requirements

## Required Capability

An acceptable automated route must produce a local WDA Raw Import Pack:

- `import_manifest.json`
- `messages.jsonl`
- `conversations.jsonl`
- `contacts.jsonl`
- optional `media_index.csv`
- checksums for every produced artifact

## Required Controls

- Owner approval before execution.
- Local-only execution; no upload of raw data.
- Output written only under `/Users/linzezhang/Downloads/WDA_MetaData/`.
- Trial scope limited before any broad export.
- Reproducible tool source, version, commit, command, and configuration.
- Explicit stop conditions before execution.
- Raw private outputs kept out of git.

## Required Data Coverage

- Message-level records.
- Conversation/session identifiers if available.
- Contact metadata or stable sender/contact identifiers if available.
- Enough provenance to map each artifact to source route, device, WeChat
  version, and time range.

## Required Decision Boundary

The route may be considered for a controlled trial only after the user approves
the exact route and any sensitive operations it requires, including live WeChat
process access, admin privileges, key extraction, database decryption, or local
process memory access.

