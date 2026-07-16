# Phase 11.1 Risk and Rollback

- 当前 SQLite `3.50.4` 不在 WAL-safe 集合；显式 WAL 请求 fail closed，默认使用 `DELETE` rollback journal。
- 只验证 disposable SQLite 的并发、SIGKILL、migration 与 rollback；canonical private PFI DB 未读取、未迁移、未修改。
- TaskPack 未列出真实活跃基础入口 `PFI/src/pfi_os/application/operational_store.py`；standing authorization 下仅对该文件作必要 scope override，`allowed_files_obeyed=false` 如实保留。
- Phase 11.2 online backup、隔离 restore、原子替换及失败恢复未开始；任何 canonical migration 前仍须通过该 Phase。
- Phase 11.3 公共/私有分发边界与 Stage 11 whole-stage review 未开始。
- 研究层仅访问 SQLite 官方文档核对当前安全公告；产品/测试 runtime 外网调用为 0。未使用 Finder、LaunchServices、GUI、push 或 app install；model/formula/parameter 数值未修改。

Rollback：先 revert Phase 11.1 证据/治理提交，再依次 revert release-identity 提交 `ad16901505f7e6f23653aa8b1e03945211dc4e93` 与主产品提交 `b07709d0453d3d2c6d36a10375d823dbb0870c53`。本轮没有 canonical DB 或安装面副作用。
