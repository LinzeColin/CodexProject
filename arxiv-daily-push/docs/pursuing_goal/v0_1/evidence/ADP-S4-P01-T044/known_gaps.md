# Known gaps · ADP-S4-P01-T044

- **NOT_DEPLOYED（任务边界，非缺陷）**：看板在 source-year 网格上运行，未接生产。`measured` 成本接真实用量（Worker 分析/R2 用量键 `r2_YYYYMM_{ca,cb,bytes}`/模型计数）后填充；本任务只演示 2 个测得 source-year + 其余诚实 UNKNOWN。
- **多数成本 UNKNOWN（有意，非缺陷）**：历史各 source-year 的 fetch/storage/AI 成本尚未逐年测量 → **UNKNOWN（绝不填 0）**，正是「未知成本不得用 0」的落实。真实扩 cohort 前须测得目标 cohort 的成本使其 computable。
- **成本单位为资源、非货币**：免费档（DIR-007）经常性 ≈$0；看板用资源单位（子请求/字节/模型调用）作真约束。货币化（超免费档后）须 Owner 授权（DIR-007）。
- **accepted_events 为演示标记**：本任务用确定性标记（每 3 条 1 个 accepted）近似 accepted material event；真实接 cn_selections（abstain=0）计数。
- **人工维护/失败为 ops field**：接真实工单/失败日志后填充；本任务作字段占位（UNKNOWN 或测得）。看板 UI 未做（属后续）。
