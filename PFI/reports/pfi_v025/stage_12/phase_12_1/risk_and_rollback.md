# Phase 12.1 风险与回滚

- 真实支付宝源仅从 immutable Git objects 读取，并写入临时 0600 snapshots；canonical source 与 operational DB 均未修改。
- `SRC-HOLDINGS` 当前为 `not_loaded`，持仓真实流程记录为 `not_run`；仅“正确阻断”门禁通过，未宣称真实持仓验收通过。
- axe-core 本机不可用，未伪报 axe pass；使用当前内容 20 routes 的 deterministic WCAG 2.2 AA、Chrome CDP AX、键盘与 40 screenshots visual regression 作为显式替代证据。
- 6 个旧测试绑定历史阶段/外部环境 literal，保留为 P2 test debt，不改写 immutable historical Evidence；Stage 12 current-state replacements 已通过。
- 回滚：恢复 import probe 的单文件补丁及 release identity hash 同步；删除本 Phase 新增 harness/Evidence。临时数据目录由 harness 自动清理。
- 停止边界：不进入 Phase 12.2，不安装 App，不调用 Finder/LaunchServices，不 push，不冻结 release，不声明 production/final acceptance。
