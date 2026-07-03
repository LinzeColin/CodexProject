# Controlled Trial Plan

## Selected Route For Trial

Select one local CLI exporter route in the `wechat-cli` / `wx-cli` family.

Reason: this route is the most direct path to deterministic local files that can
be converted into WDA Raw Import Pack artifacts. It has lower integration
surface than an MCP server and lower runtime-modification surface than a
WeChatTweak-style route.

## Execution Host

Recommended host: old computer.

Reason: the old computer is the high-value WeChat data source. The new computer
remains the WDA Control Plane and validation/RAG/Web host.

## Required Approval Before Running Sprint 2H

The user must explicitly approve all of the following before any command runs:

1. Exact tool route, repository, version, and commit.
2. Execution host: old computer recommended.
3. Whether live WeChat must be running and logged in.
4. Whether admin/sudo is allowed.
5. Whether process-memory access is allowed.
6. Whether key extraction is allowed.
7. Whether local DB decryption is allowed.
8. Output root under `WDA_MetaData`.
9. Trial scope, preferably one small selected conversation or the smallest
   supported export.
10. Network boundary: local-only, no remote upload.
11. Stop conditions and rollback action.

## Sprint 2H Trial Phases

1. Preflight: document tool source, checksum, commit, expected commands, WeChat
   version, macOS version, and output path. Do not export data yet.
2. Dry run if supported: verify configuration/output path without message
   export.
3. Minimal acquisition: produce the smallest possible message-level output.
4. Local validation: verify file types, checksums, and schema shape without
   committing raw content.
5. WDA Raw Import Pack conversion: only if minimal output is valid.

## Stop Conditions

- Tool attempts remote upload.
- Tool writes outside approved WDA_MetaData path.
- Tool requires an unapproved sensitive operation.
- Tool cannot constrain trial scope.
- Tool crashes or modifies source data.
- Output lacks message-level records.
- Output cannot be validated without exposing raw private content in git.

