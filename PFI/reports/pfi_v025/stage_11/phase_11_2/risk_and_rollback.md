# Phase 11.2 Risk and Rollback

- 仅 PFI lock-aware transaction 受 maintenance lock 协调；外部 client 必须 quiesce。
- sidecar、stale target hash、unsafe permissions、cross-filesystem replace 均 fail closed。
- 只使用 disposable nonfinancial SQLite；canonical private DB 未读写。
- Phase 11.3、whole-stage review、push、install、production/final acceptance 未开始。
- 研究层只访问 sqlite.org 与 docs.python.org 官方文档；产品/测试 runtime 外网调用为 0。

Rollback：先 revert Phase 11.2 evidence/governance commit，再 revert bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b。
