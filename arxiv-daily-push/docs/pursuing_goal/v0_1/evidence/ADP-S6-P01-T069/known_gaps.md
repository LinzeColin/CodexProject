# Known gaps · ADP-S6-P01-T069

- **settlement 谓词为 3 类客观类型**：`SETTLEMENT_TYPES` = `official_doc_exists` / `status_transition` / `count_at_least`——每类都是**官方证据的确定性谓词**，可扩展但**每新增一类须保持「可由未来官方原文客观 0/1 结算」**（否则该目标不 settleable、不入回测）。主观/自由文本谓词（如 is_important）**永不 settleable**。
- **label SQL 由部署阶段编译**：TASK_INDEX 交付含「label SQL」。本任务出**确定性 Python 结算**（`settle`）与谓词契约；将谓词编译为 D1 label SQL（在真实版本链上打标）由部署阶段负责，须保持相同 official-only + observed_at 窗口语义。本层为其确定性规范与可复核实现。
- **official-only = A0/A1**：结算只计 `authority_level ∈ {A0, A1}`（官方原文）；媒体/A2/None **不结算**。若未来把 A2（地方官方）纳入某目标结算，属谓词扩展、须显式登记。
- **observed_at 窗口防泄漏**：结算只计窗口 `[origin, origin+horizon]` **内观测**的证据（含端点）；窗口外（尤其**未来观测**）不计——回测不泄漏未来。窗口未过且无匹配→`pending`（不臆断 0）。`horizon_days` 用日历日期算术（传入日期，不读 wall-clock）。malformed/None `observed_at` 的文档被安全排除。
- **模型路由（T2/T3）**：S6 为模型领域。**本任务是预测目标/Outcome Rule 的定义（确定性结算规则，非训练模型/统计公式）**，故未动 MODEL_SPEC/formula_registry。真正统计/ML 模型自 **T071（历史频率/季节性基线）** 起，届时登记 MODEL_SPEC 与 formula_registry。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。**开启 Stage S6（预测、校准与失败历史）**；后接 T070（Dataset Snapshot + observed_at 泄漏防线）、T071（基线）、T072（Rolling-origin Backtest）。
