# ADP V0.2 · P05 — 六主题视觉/动效门重新冻结（NOT_DEPLOYED）

## 为什么做这个：保护你六主题的那道门，自己已经失效了
这不是新功能，是**修一道坏掉的保险**。它同时坏在两处：

1. **基线陈旧 → 对什么都拦 → 等于没有门**
   T077 把六主题契约冻结在 live `b189d3cc0703`。之后 T079/T080 改了 `base_css`、T082 改了 `keyframes`（各自都独立复核、批准，并已随 P01 上线）。于是 `run_ci` 对着 T077 基线**无条件 BLOCK**——**连拿 HEAD 自己去测也 BLOCK**。一个恒 BLOCK 的门和一个恒 PASS 的门一样没用：**它的判决不再携带任何信息**。
2. **没有入口 → 裸跑就是空跑通过**
   `visual_regression_ci.py` **没有 `__main__`**：`python3 visual_regression_ci.py` **exit 0、零输出**。任何以为自己「跑了这道门」的调用者，拿到的是**空跑 PASS**。（这条是 P02 的复核者发现并写进记录的。）

## 交付
- **`v0_2/tools/visual_baseline_refreeze.py`**：把基线重冻到**线上 build `204c97eb5406`**，但**只有在每个漂移元素都可归因于「已批准且已部署」的任务、且 per-theme 身份未变**时才出基线；否则 **ABORT（返回 2，`--write` 也不写）**。
- **`v0_2/evidence/.../visual_baseline_manifest.json`**：新权威基线，记录 `supersedes`（T077/b189d3cc0703）、漂移集、逐条归因、per-theme 未变；**T077 的全部键位一个不落地带回**（见下）。
- **`v0_1/tools/visual_regression_ci.py` 补 `__main__`**：加载当前基线（优先 v0_2 重冻，回退 T077 并标注 STALE）、门控 worker、**exit code 载重**（BLOCK → 1），并输出**合并后的单一 `GATE:` 判决**（避免出现「decision: PASS」却 exit 1 的自相矛盾）。

## 关键事实：你签过的六主题，一根汗毛没动
漂移集恰为 `['base_css','keyframes','master_visual']`（`master_visual` 是聚合哈希，其分量动它必动）。
**`per_theme` 与 `contract_root` 逐字节未变** → **Owner 在 T077 亲签的六主题身份本身未被触碰**。
独立复核**没有采信我的叙述**，而是**从每个历史 worker 版本重算 asset_hashes**：T077 哈希 == build `b189d3cc0703` 的 commit；新基线哈希 == T082 之后直到 HEAD；期间**只有** T079/T080/T082 动过契约元素，**T081/T083/T084/P01–P04 一个都没动**。归因属实。

## ★复核发现的逃逸：我选择关掉，而不是记账★
复核指出一个**先前就存在**的设计缺陷并明言「本次不重开」：`run_ci` 算 `specific = changed - AGGREGATE`，`AGGREGATE={master_visual, contract_root}`，故**只动聚合哈希的改动不会被拦**。
可复现的逃逸：往 `CSS` 常量塞一条**未注册主题** `[data-theme="neon"]{...}` → `base_css` 把它当注册主题**剥离**（base_css 不变）、`per_theme` 不覆盖它 → **只有 `master_visual` 动** → **PASS / exit 0**，未注册主题静默进生产。
`VB.partition_consistency()` 就是为此写的补偿控制，**却没有任何人调用它**。
**已把它（连同 `theme_set_consistency`）接进门的判决**。干净探针实测（我前两次探针与复核首次一样被污染——注入的换行会带动 base_css/hero_css）：`moved == ['master_visual']`（纯聚合逃逸成立）、`run_ci` 仍 `PASS`、**门 exit 1**（`unregistered_themes:['neon']`）。
> 依据：P05 的全部前提就是「门重新变真」。带着已知逃逸交付，等于重演这轮我反复在修的那类「看着绿、其实什么都不查」。

另两条复核发现也已修：新基线曾**少 9 个键**（含逃逸的补偿控制 `partition_consistency` 与 Owner 视觉门开关 `owner_confirmation_required`）→ **全部带回，`set(T077键)-set(新键)` 现为空**，且两个一致性控制是**现算**而非拷贝；我的 **NC3 曾弱于其声称**（只测纯函数，未证明 `main()` 真返回 2、真拒写）→ 已改为驱动**真实 `main()` 且带 `--write`**，断言返回 2 **且**盘上基线逐字节未变。

## 验收（test-results/refreeze_tests.txt，ACCEPTANCE = PASS）
| 情形 | 结果 |
|---|---|
| 干净 worker vs 新基线 | **GATE: PASS**, exit **0** |
| 篡改 keyframe（未批准漂移） | **GATE: BLOCK**, exit **1** |
| 删除主题标志性动效（meteor） | **GATE: BLOCK**, exit **1** |
| **纯聚合逃逸**（未注册主题 neon） | **GATE: BLOCK**, exit **1**（`run_ci` 单看仍 PASS） |
| 陈旧 T077 基线 vs HEAD | **BLOCK** ← 正是被修的缺陷 |
| 不可归因漂移 → 重冻 | **ABORT(2) 且不写盘**（NC3 端到端） |

## 边界（known_gaps）
像素层仍未启用（本门是**源码哈希级**，不做截图比对）；**这道门尚未接进 GitHub CI**（现在可运行且 exit code 载重，但工作流未调用它——下一步）；`/library` 等新路由未进 T077 矩阵；只堵住了**已证明可复现**的那一类聚合逃逸。

release_mode **NOT_DEPLOYED**：worker 一行未动，线上仍 `204c97eb5406`。未自签。
Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
