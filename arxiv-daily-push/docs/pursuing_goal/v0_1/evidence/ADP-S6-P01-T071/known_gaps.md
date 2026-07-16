# Known gaps · ADP-S6-P01-T071

- **首个统计模型的 MODEL 治理（in-evidence，非运营 MODEL_SPEC）**：这是 v0_1 认知系统 S6 回测层的**第一个真统计模型**。正式规格（公式/假设/参数/可复现/回滚）记于 `MODEL_baselines.md`。运营 `docs/governance/MODEL_SPEC.md`（122 个已部署交付系统模型）与 `formula_registry.yaml` **未改**——该注册跟踪**已部署**系统，本模型 **NOT_DEPLOYED**，运营 ID 注册**门控于认知层向生产 promotion**。这与 v0_1 全部 46 个前置工具一致（均 in-evidence 记录，未注入运营注册以免破坏其 count 校验 CI）。**若/当认知层 promote 到生产**，须把本模型的 model/formula/parameter 注册进运营 MODEL_SPEC 并 bump counts。
- **基线类型**：本任务两类——frequency（基础发生率）与 seasonality（月份率 Laplace 平滑）。可扩展 persistence（上期结果）、趋势、周/季度桶等，但**每个可结算目标至少一个可重跑基线**是硬约束。
- **min_history=1**：`benchmark` 仅在目标历史 ≥ min_history 有标记结果时才 `has_reproducible_baseline=True`。**无历史目标无可重跑基线**（rate 会是无意义 0.0），故门 `may_develop_advanced`=False——「无基线不得开发高级模型」。默认 min_history=1（可调高以要求更多样本）。
- **季节性桶=历法月**：月份桶 1-12；样本稀疏时 Laplace α=1 防过拟合、未见月回退平滑全局率。真实目标可能需周/季度或事件驱动桶——按需扩展。
- **eval 独立**：metrics 在**独立于训练历史的 eval 集**上计算（无用 eval 拟合的泄漏）；真实回测的 train/eval 时间切分由 T072 Rolling-origin Backtest 负责（本任务提供基线与 metrics 原语）。
- **无时钟/随机/网络**：确定性统计；相同 history → 相同基线 → 相同 metrics；`benchmark` 可重跑。**模型调用 0**（本地统计，无 LLM）。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。**收尾 S6-P01（预测标签、快照和基线）**；后接 T072（2016+ Rolling-origin Backtest，size M）。
