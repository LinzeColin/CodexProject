# Phase 12.2 风险与回滚

- 用户已明确禁止 Finder 操作；本 Phase 只使用 CLI 原子安装与 bundle 原生可执行文件，未调用 Finder、LaunchServices、`open` 或 GUI 文件操作。
- 真实系统 sleep/wake 未执行；使用仅作用于本 run 已验证进程组的 `SIGSTOP/SIGCONT` 作为服务暂停/恢复代理，并明确保留为 P2 限制，不冒充内核休眠。
- 安装前的旧 App 已保存为 owner-only 私有归档；替换中任何校验失败都会恢复同文件系统 rollback bundle。
- canonical 私有 SQLite 仅以 query-only/Online Backup API 读取，源文件与目录状态不变；restore 与自动 rollback 只作用于隔离副本。
- 磁盘不足仅在 `hdiutil -nobrowse` 临时小卷制造真实 `SQLITE_FULL`，没有填充主机卷，临时卷已卸载删除。
- `SRC-HOLDINGS` 仍为 `not_loaded`；UAT 验证正确阻断和无假零，不宣称真实持仓编辑通过。
- Desktop/Downloads 非 canonical 入口仅做 CLI census，不修改；最终入口治理继续留给 Phase 12.3 release freeze。
- 回滚：从私有 pre-v0.2.5 归档恢复 `/Applications/PFI.app`；回退本 Phase 代码、测试、治理和 Evidence；隔离 runtime/data 已删除。
- 停止边界：不进入 Phase 12.3，不 push，不生成最终 `human_acceptance.json`，不冻结或声明 production accepted。
