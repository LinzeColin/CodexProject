# 对抗复核记录 · ADP-S4-P02-T048（QA gate 自审→加固→复验）

用 4-skeptic workflow（每 gate 一个独立怀疑者，各自试图证明「gate 能 PASS 而其宣称的性质为假」）对 QA gate 做对抗复核。**这本身就是 QA gate 该有的自证：不自签，找洞，堵洞，再验。**

## 第 1 轮（wf_8d2ca5fc-133）
- **attachment_gate**：SOUND（115/115 distinct 真可读；HTML 软 404 正确拒绝）。留 1 个未利用隐患：magic 用真值性而非白名单。
- **revision_gate**：SOUND。
- **as_of_gate**：**HOLE** —— `future_leakage` 同义反复：resolver 先按 `observed_at<=query` 过滤，检查又只标 `>query`，逻辑上不可能触发；且字符串比较、未测真实 resolver。
- **gap_gate**：**HOLE** —— `infer_source_windows` 恒给真值窗口 → UNEXPLAINED 结构不可达 → 「0 未解释」同义反复；窗口内真漏藏为 `not_backfilled`。

## 加固
- **attachment**：magic 改**白名单成员**判定 + sha256 正则。
- **as_of**：重写为 `_parse_date`→(y,m,d) 元组**按解析日期比较**；`resolve_as_of` 正确 resolver + **独立 oracle**（filter-sort-last 异算法）；对抗 fixture（乱序/3–5 版/边界）；**negative control**：故意写错的 resolver 必被抓（control_catches_broken）；**畸形日期必 raise**（malformed_rejected）。495 样本 0 泄漏 0 分歧。
- **gap**：重构为对 **attempted 单元**判定 + 真实 T047 ndrc/cac 失败 surface 为 fetch_failed + **可达 silent-hole 检测器**（真实变异触发）；真值完整性明确推迟 T056。

## 第 2 轮（wf_066fbd9f-fe8）+ gap 单独复核（a98feae5）
- **attachment / revision / as_of**：全 **CONFIRMED_SOUND**（as-of：确认解析日期非字符串、oracle 独立、控制项有效，无缺陷）。
- **gap_gate**：第 2 轮仍指出「ghost 控制不可达真实管道」→ 遂改用**真实 ndrc/cac 尝试失败**作可达正信号 + 真实变异 silent-hole 控制；gap 单独复核（a98feae5）判定 **CONFIRMED_SOUND**：control 经同一 status_of/classify 路径、真判别；silent_holes==0 为真命题且有正控制背书；fetch_failed surfacing 靠 setdefault 注册使先前被丢弃的源进入网格；范围诚实，无 pass-while-false。

**结论：四 gate 全 CONFIRMED_SOUND。** 实现者不自签任务 PASS —— 交独立复核。
