# Known gaps · ADP-S2-P01-T022

- **flag 仍关（RAW_DUALWRITE=false）**：本任务交付的是双写机制 + flag 默认关（=基线）+ 幂等/预算验证；**真正的 SHADOW 跑（flag 开、7 日/1000 artifact）是 T023**。
- **压缩存 none（原始字节）**：为「不可变原始证据」保真，存原始字节不 gzip（T021 合同允许 none）；如需省存储，后续可对 text/* gzip（CompressionStream），但会改变字节需重定合同。
- **selftest 对象保留**：/api/raw-selftest 写了 1 个 76B 测试对象作证据；可后续清理，占额度可忽略。
- **budget 计数存 cn_meta 月度键**：r2_YYYYMM_ca/cb/bytes；跨 Worker 实例并发自增用 D1 CAS，极端并发下计数可能略偏，但保守 guard 0.9 留足余量。
- **/api/raw-selftest 为管理验证端点**：显式写 1 测试对象，不受全局 flag 限制；低风险（1 对象）；如需可后续下线。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
