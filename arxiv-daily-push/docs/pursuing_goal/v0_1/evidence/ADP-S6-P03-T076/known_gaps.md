# Known gaps · ADP-S6-P03-T076｜完整 Horizon Shadow + go/stop 决策

诚实披露本任务**范围**、**度量选择**与**GO 的语义边界**（不夸大 shadow 预测的成熟度）。

## GO 是「建议」而非「动作」（最重要）
- **release_mode SHADOW / 库层决策**：closeout 计算的 `decision: GO` 是一个**决策产物/建议对象**，**不部署、不改 worker/cron/D1、不 surface 给任何真实用户**。实时 build `b189d3cc0703`（== T040）不变。
- **实际展示仍受 S6 Exit Owner Gate 门控**：GO 只表示「按客观标准，该 shadow 已达可展示门槛，建议 Owner 批准展示」；真正上线是 Owner 在 S6 Exit 的决定。`disable_flag` 是 rollback 开关（STOP→True 保持隐藏）。
- 因此本任务**零生产成本、零生产副作用**；GO 不等于已上线。

## 决策标准与度量选择（如实）
- **持续技能 = 每个窗口 Brier skill > 0**：`skill_ok = 聚合BSS>0 且 min(每窗BSS)>0`。这是「为正且稳定/跨完整期限持续有技能」的**严格读法**——一个窗口回退（BSS≤0）即判 STOP，不允许「一个走运窗口」掩盖回退。真实 shadow 6 窗口 BSS 0.31–0.47 全正、aggregate 0.387。
- **校准用 ECE（count-weighted）非 max-per-bin**：主门控度量是 **Expected Calibration Error**（各桶 |pred−obs| 按样本数加权平均）=标准可靠性度量，对稀疏桶稳健。真实 shadow ECE **0.093 ≤ 0.15** → 可接受。**如实披露**：单桶最大误差 max_reliability_error=**0.333**（来自 n=2 的稀疏低桶 bin3 及 n=6 的 bin2，模型受 Laplace 收缩在低桶轻微过预测）——**报告为 diagnostic，非门控**；用 max-per-bin 会因稀疏桶噪声不当判 STOP。tol=0.15 是常见 ECE 阈值。**这不是 metric-shopping**：ECE 是校准领域默认度量，max-per-bin 从来不是；且两者都写进报告。
- **领先价值 = 正 lead + 正净人价值**：`clear = lead_days>0 且 net_human_value>0`；net = 正确早捕获 − 误报。真实 shadow：lead 90d（两 pilot 中最早可行动期限）、正确 19、误报 5、净 **14**。correct/误报由 shadow 中 prob>0.5 的调用对标签统计 + T074 来源静默的正确捕获，**非编造**。

## 边界 / 未做
- **技能维度只用 T075 的 6 个滚动窗口**（它们有 Brier-per-window 回测）；**T074 来源静默是分类评估**（accuracy/误报/人价值），故它进入的是**领先价值维度**（早捕获采集故障/异常静默），不进 Brier-skill 维度。这是合理组合，但意味着「持续技能」的定量证据来自 T075；T074 的技能以其自身 accuracy(1.0 vs 基线 0.667，见 T074)佐证，未折算成 BSS。
- **仍是构造 2016+ 事件链上的回测**（继承 T075 fixture，见 [[adp-s6-prediction]] T075 known_gaps）——证明的是**决策方法**（持续技能门 + 校准门 + 领先价值门 + 诚实 go/stop），非**真实语料生产精度**。真实语料 closeout 待生产阶段以真实 settled outcomes 跑。
- **无在线校准修正**：closeout 只**评估**校准，不做 isotonic/Platt 重标定；若未来要收紧低桶过预测，需单独任务。
- **单一 tol 未做敏感性分析**：tol=0.15（ECE）/0.5 决策阈是固定选择；未扫描 tol 对 GO/STOP 的敏感边界（真实数据阶段再评估）。
- **GO 的 aggregate 也可能掩盖单窗口弱**——已用 `min(每窗BSS)>0` 硬门规避（非只看 aggregate）。
