# Phase 2.1 Risk and Rollback

- Risk tier：`T3_PRIVACY`。
- Canonical decision：`$PFI_DATA_HOME`，当前由 `~/.pfi` 显式 alias 解析；没有移动、复制、合并或删除数据。
- Read-only proof：SQLite 在连接前阻断不可遍历目录、非 regular candidate、任何 `pfi.sqlite-*` sidecar 与 WAL header；实际 header 为 rollback-journal `1/1`，连接使用 `mode=ro + shared read transaction + query_only + deny-write authorizer`；before/after sidecar、operational directory、candidate set、device、inode、size、mtime_ns、ctime_ns、mode 与 SHA-256 完全一致。
- Privacy：固定九输入扫描对绝对私有路径、原始文件名、table 名、row、账户标识、金额、常见 credential key/assignment/Bearer、Finder、mutation 与 fake fallback 全部 fail-closed；Evidence 当前九项均为零。
- Data truth：8815 条交易仅证明 source input available；分类、现金、持仓市值、净资产与 CNY 消费总额因 source/contract dependencies 未完成保持 blocked/null，不显示或暗示 0；未验证来源统一为 not_loaded。
- Open risk：private root `0755`、SQLite `0644` 存在 group/other 权限；本 Phase 不改权限。SQLite source-level count/coverage/as-of 未定义，保持 `null`。
- Rollback：revert 本 Phase commit；不对原始数据做 rollback。
- Stop：任何 source 指纹变化、sidecar/symlink/conflict、隐私泄漏、fake fallback 或 false zero 均使 candidate fail closed。
