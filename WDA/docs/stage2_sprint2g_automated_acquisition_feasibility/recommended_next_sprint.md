# Recommended Next Sprint

## Sprint 2H

Name: controlled automated acquisition trial.

Recommended route: one local CLI exporter in the `wechat-cli` / `wx-cli` family.

Recommended host: old computer.

New computer role: WDA Control Plane, validation host, and later RAG/Web/database
host.

## Why This Route

- Manual artifact preparation is deprecated for WDA core viability.
- Low-risk read-only/APFS/schema-only routes did not produce message-level data.
- A local CLI route is the most auditable first automated route because it can
  be pinned to a repository/commit and can potentially write deterministic local
  files.
- MCP, WeChatTweak, PyWxDump, chatlog/EchoTrace, and self-developed raw adapter
  routes remain backup or higher-risk options.

## What Sprint 2H Must Not Do Without Approval

- Run a third-party tool.
- Extract keys.
- Decrypt databases.
- Access protected stores.
- Export broad chat history.
- Upload data.
- Implement RAG/Web/Matrix.

## Approval Needed

Before Sprint 2H begins, the user must approve:

- exact route/tool/repo/commit
- old-computer execution host
- live WeChat requirement
- admin/sudo allowance
- key extraction allowance
- local DB decryption allowance
- output path
- trial scope
- stop conditions

Until that approval exists, the next state is planning complete and execution
blocked.

