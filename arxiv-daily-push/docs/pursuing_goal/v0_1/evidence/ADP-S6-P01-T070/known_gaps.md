# Known gaps · ADP-S6-P01-T070

- **observed_at 由摄取管线提供**：泄漏防线的关键是 **observed_at = ADP 实际抓取/知道该文档的时间戳**（与 doc_date 政策发布时点分离）。回填文档的 observed_at = **回填运行的时点**（如 2026），故其历史 doc_date（如 2016）不会让它在历史快照中"假装已知"。真实 observed_at 由摄取/回填管线在写入时打戳；本任务消费之并强制其语义。缺失/malformed observed_at 的文档被**排除**（快照）且**视为泄漏**（guard）——知晓时点不可验证不得纳入回测。
- **snapshot_id 为确定性哈希**：`snapshot_id` = 对含入文档的 `(canonical_id, observed_at, content_hash|version)` 排序后 sha256 前 16 位。序无关、可复现；碰撞概率忽略。用于"任何预测可重建其当时数据集"的可验证性（重建 → 同 id）。真实 D1 快照物化/ID 表由部署阶段负责。
- **泄漏 guard 在外部注入数据集上测**：`assert_no_leakage` 对**传入的 dataset**（可能被外部注入未来文档）逐一校验 observed_at，而非仅信任 `snapshot()` 的过滤输出——故"注入未来文档使测试失败"是**真 tripwire**（即便一个有 bug 的快照忘了过滤，guard 仍会抓）。
- **边界语义**：`observed_at <= as_of` 含 as_of 当日（inclusive）；malformed as_of → raise（不静默返回空）。
- **无时钟**：as_of 由调用方传入（确定性、可重放），不读 wall-clock。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。S6-P01 后接 **T071（历史频率/季节性/统计基线）**——届时进入真正统计模型，须登记 MODEL_SPEC/formula_registry。
