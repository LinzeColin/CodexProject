# 验收、质量与 ROI 指标

## 质量必须零回退

| 指标 | 验收标准 |
|---|---|
| 旧链失败样本 | 候选不得判定可跳过，false negative = 0 |
| 中文三文件 | 结构、事实和 drift 检查不削弱 |
| Roadmap | Stage/Phase/Task、工时/占比、Stop Condition/Gate、Acceptance/Evidence 保持 |
| T2/T3 | 不得降级；full/manual/release 不变 |
| Git/base 错误 | fail-closed |
| READ_ONLY/CI | tracked 写入 = 0 |
| 范围 | EEI/arxiv 和项目业务目录写入 = 0 |
| Required Check | workflow/job 身份不变 |
| 回滚 | 一条明确命令或单提交回滚已实际演练 |

## 速度与信息效率

先测量后定论。建议 Gate：

- T0/T1 candidate p50 <= legacy p50 的 70%；
- T0/T1 candidate p95 <= legacy p95 的 85%；
- full/nightly 等价路径性能回归 <= 10%；
- compact stdout <= 2 KB；
- Agent 初始读取 <= 5 个文件、<= 12 KB（与现行 Standard 一致）；
- 每次普通任务 selected project = 0 或 1，根契约变化除外；
- 纯验证不生成 Git diff；
- 因治理误报导致的 PR 重跑率 < 5%。

这些是激活门槛，不是可以编造的报告值。若现有基线不支持某项，标记 UNKNOWN 并保留 raw evidence。

## 运行和极限测试矩阵

- 0、1、8 个 selected project；
- 干净与已有无关修改的工作树；
- validator 新增写入；
- 中文路径、rename、delete；
- 初始提交、错误 base、detached HEAD；
- 两实例并发；
- 20 次重复确定性；
- timeout、SIGTERM/CI cancellation；
- 临时目录、缓存、后台子进程清理；
- 旧链与候选退出码、问题集合、证据集合 parity；
- 两个真实代表性 PR/commit shadow。

## 完成结论

- `SHIP`：所有阻塞门槛通过，可有限激活/合并。
- `FIX-ONE`：仅一个明确阻塞，范围固定，修复后重复 Gate。
- `STOP`：路径错误、false negative、越界或无法回滚，回到 legacy。
