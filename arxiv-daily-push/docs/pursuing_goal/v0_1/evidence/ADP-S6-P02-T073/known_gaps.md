# Known gaps · ADP-S6-P02-T073

- **校准 = 等宽 10 桶可靠性图**：`calibration` 把预测概率分入 10 个等宽桶 [0,0.1)..[0.9,1.0]，每桶报 pred_mean/obs_rate/n（可靠性图数据）。`has_calibration(p)` 仅当 p 所在桶有历史数据（n>0）才 True——**用户可见概率必落在有历史的桶**，否则不算"有校准"（负控制已验）。可扩展为**分位桶**（等频）以更稳的稀疏尾部；本任务用等宽（简单、确定）。
- **Forecast Ledger 篡改可检测（库层）+ 生产强不可删**：ledger 为 append-only，`append` 记成功与失败并**哈希链**（每记录 chain=sha256(prev+seq+core)），`delete()` **raise**，`verify_integrity()` 重算链——**删/改/重排任一记录（尤其失败）→ False，可检测**。Python 对象皆可变，故库层是**篡改可检测**而非物理不可变；**生产级"失败记录不可删除"由 D1 append-only 表（无 DELETE 授权）落地**，本层提供其可检测契约。
- **skill 参考 = base-rate/climatology**：`brier_skill_score` = 1 − mean(model)/mean(ref)，参考为便宜基线（T071/base-rate）。**负技能诚实报告不掩盖**（worse model → BSS<0）。ref Brier=0 时返回 None（不除零）。可扩展多参考。
- **指标非新模型**：calibration/skill 是对 **T072 回测输出**的评估指标 + append-only 记账，**非新预测模型**，故运营 MODEL_SPEC/formula_registry 未改（预测模型的正式规格是 T071 的 MODEL card）。
- **无时钟/随机/网络**：确定性；相同 forecasts/ledger → 相同校准/skill/链哈希。**模型调用 0**（本地指标，无 LLM）。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。S6-P02 后接 S6-P03（T074 Shadow 静默预测 / T075 主题加速扩散 / T076 完整 Horizon Shadow 与上线/停止决策）。
