# Stage 2 Phase 2.3 真实数据安全测试沙盒

## 隔离层

### 交易来源

- 来源：`SRC-TRANSACTIONS-ALIPAY`
- 路径别名：`MetaDatabase/PFI`
- 隔离方式：先把 `HEAD` 解析为 commit，再固定 tree/blob OID；所有读取只使用 immutable blob。
- 不执行 sparse checkout、文件复制、source write、网络请求或 Finder 操作。
- Evidence 只保存 commit/tree/blob identity、bytes、record count、field count、耗时与 peak allocation，不保存 header、row 或金额。

### Operational SQLite

- 来源：`SRC-OPERATIONAL-SQLITE`
- 路径别名：`$PFI_DATA_HOME/private/operational/pfi.sqlite`
- source 必须位于 repo 外、路径链无 symlink、单一 regular database、无 WAL/SHM/journal sidecar 且 header 为 rollback-journal。
- 复制前后比较 source identity/hash；副本位于 `0700` 临时目录，文件 mode 为 `0600`。
- 只在副本执行 `query_only`、`quick_check` 与已知表数量统计；不读取或输出 table name/row。
- 退出路径必须删除副本与临时目录；cleanup 不完整即 blocked。

## no-fake 合同

- Baseline API 只接受 repo root、Git ref 与 iterations，不接受 records、rows、transactions 或 fixture 注入。
- 真实 Git object 不存在、解析失败或 source identity 改变时返回 blocked，record count 与性能结果保持 null。
- 不使用 demo/sample/synthetic/fake 财务数据补齐成功路径。

## 性能口径

- `elapsed_ms`：每轮从 immutable manifest/CSV blob 读取开始，到 JSON manifest 与 CSV 全量计数完成为止。
- `peak_python_alloc_bytes`：同一测量窗口的 `tracemalloc` peak；它是 Python allocation baseline，不代表整机 RSS。
- 数值用于后续回归对比，不是硬 SLA，也不是财务模型参数。

## 状态边界

Phase 2.3 完成只表示真实数据安全沙盒与 Stage 2 evidence 已准备。Stage 2 whole-stage review、问题整改、复审与用户验收仍须独立完成；Stage 3 entry 保持 false。
