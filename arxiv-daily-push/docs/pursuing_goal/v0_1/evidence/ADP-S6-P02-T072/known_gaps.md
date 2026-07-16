# Known gaps · ADP-S6-P02-T072

- **回测 harness 复用 T071 基线模型（非新模型）**：本任务是**回测框架**，在每个滚动窗口拟合并评分 T071 的 frequency/seasonality 基线（其正式 MODEL card 见 `evidence/ADP-S6-P01-T071/MODEL_baselines.md`）。**未引入新模型/公式**，故运营 `MODEL_SPEC.md`/`formula_registry.yaml` 未改（与 v0_1 惯例一致；运营注册门控于 promotion）。
- **rolling = expanding-origin**：训练集为"观测<=起点"的**扩张窗**（起点前移 → 训练增大）。可扩展为固定长度滑窗、多目标并行、可变 horizon；但**≥3窗口 + 训练/验证时间不交叉 + 可重跑**是硬约束。
- **训练/验证时间不交叉（真回测核心）**：train 观测 <= origin；val 观测 ∈ (origin, origin+horizon]（严格 origin 之后）。观测于 val_end 之后的结果**既不在 train 也不在该窗口 val**——对该起点是未来、正确排除，会出现在更晚起点的窗口。每 train 集额外经 **T070 泄漏 guard**（无未来观测混入拟合）。日期用日历算术（datetime，传入 origins，不读 wall-clock）。
- **run manifest**：`run_manifest` = 对 (target, origins, horizon, per-window metrics) 的确定性 sha256——可重跑可审计、内容敏感（改 horizon/origins/outcomes 变 manifest）。真实 D1 run manifests 物化由部署阶段负责。
- **无时钟/随机/网络**：确定性；相同 (outcomes, origins, horizon) → 相同 windows + 相同 manifest。**模型调用 0**（本地统计，无 LLM）。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。**开启 S6-P02（滚动回测、校准与 Ledger）**；后接 T073（校准/Ledger）。
