# ADP V0.1 · CURRENT_SCOPE（本轮唯一可执行范围）

> 冻结自 ADP_V0.1_FINAL_EXECUTION_TASK_PACKAGE_2026-07-15。任务 `ADP-S0-P01-T001` 交付物。
> 权威顺序见 [PRECEDENCE.md](PRECEDENCE.md)；机器可读指令见 [OWNER_DIRECTIVES.yaml](OWNER_DIRECTIVES.yaml)。

## Pursuing Goal（单行，唯一真相）

> 在不破坏已上线 MVP、六主题高级动效与实时稳定运行的前提下，以单一事实源、A0–A2 官方原文、2016+ 可恢复历史、证据化人话内容、可回测预测和量化成本收益为硬约束，逐 Stage/Phase 将 ADP 建成多板块、全面、权威、及时、深度且长期稳定的前沿认知系统。

## 本轮包含（IN SCOPE）

1. 来源/部署**单一真相**（一个 Source Registry、一个 Deployment Manifest）。
2. **内容质量**与事实漂移修复（人话/机制/证据去模板化，Board 3 非政策内容清理）。
3. 中国 **A0–A2** 官方来源（中央/省级/重点城市/重要区·功能区；A0/A1/A2 三级，不含 A3+）。
4. **2016+ 可恢复历史**回填（可回放、可 as-of 查询）。
5. **证据与版本**（官方原文、Claim→Evidence、Document/Version identity）。
6. **数据性能**（D1/R2/快照/查询延迟基线与优化）。
7. **竞品收益对齐**（同等或更好的用户收益，非复制页面/按钮）。
8. **可回测预测**（rolling-origin、无时间泄漏、须优于基线才可见）。
9. 保留六主题的 **UI/UX 与性能打磨**（视觉基线冻结 + 视觉/动效回归 CI）。

## 本轮不包含（OUT OF SCOPE）

- 公开运行入口安全、认证、多租户。
- 商业套餐、TAM/定价。
- 全面导航重做、替代现有视觉身份。
- A3/A4/B/C/D 来源层级；通用 SaaS IA。

## 简洁性不变量（任何新增系统必须替代重复真相，不得成为第 N 份配置）

```
一个 Source Registry · 一个 Deployment Manifest · 一个 Content Contract
一个 Document/Version identity model · 一个 Stage/Phase/Task Roadmap · 一个 Value-Cost Scorecard
```

## 绝不能破坏的既有基线（硬约束）

- 已上线 MVP（Today/Review/Radar/System）与实时稳定运行。
- **六主题**（暖纸/简约专注/清新/炫技/宇宙星河/森林）与**高级动效**：hero 首屏整屏视频（简约/炫技/森林，自托管 `/media/*.mp4`）、宇宙星河知识体征仪表盘、氛围动效层、主题自愈与 `no-store` 缓存。
- 当前生产数据与行为，除非某任务显式以 feature-flag 授权受控变更。

## 执行护栏（摘自 09_ANTI_BLACK_HOLE）

- 同一时间 1 Stage `ACTIVE`；每会话 1 Task；默认 ≤12 文件/任务。
- 无 big-bang：不一次接 171 源、不先灌 20TB、不先上向量库、不默认 Workflows、不用新框架重做六主题。
- 两次失败换路径；实现者不得自签 Stage Gate；出现 Stop-the-line 条件立即回滚/隔离。
