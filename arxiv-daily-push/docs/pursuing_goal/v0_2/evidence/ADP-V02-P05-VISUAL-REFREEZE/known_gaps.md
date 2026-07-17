# Known gaps · ADP-V02-P05 — 六主题视觉/动效门重新冻结

## 1. 这个任务修的是「门本身失效」，不是产品功能
本任务 **NOT_DEPLOYED**：worker 一行没动，线上仍是 `204c97eb5406`。修的是**保护你六主题的那道门自己坏了**：
- **基线陈旧**：T077 把契约冻在 live `b189d3cc0703`。此后 T079/T080（base_css）、T082（keyframes）各改了恰好一个契约元素，**均已独立复核、批准、并已随 P01 部署上线**。于是 `run_ci` 对着 T077 基线**无条件 BLOCK**——**连对 HEAD 自己也 BLOCK**。一道对什么都拦的门 = **没有信息量 = 等于没有门**。
- **没有入口**：`visual_regression_ci.py` **没有 `__main__`**，`python3 visual_regression_ci.py` **exit 0 且零输出**——任何「跑了这道门」的调用者拿到的是**空跑通过**。

## 2. 重冻**不是**橡皮图章（这是本任务最重要的自我约束）
`visual_baseline_refreeze.py` **拒绝**在下列情况下出基线（返回 2，且 `--write` 也不写）：
- 有任何漂移元素**不在 `ATTRIBUTION`**（= 没有已批准且已部署的任务能解释它）→ 那是**真回归**，重冻会把它悄悄祝福掉；
- **per-theme 哈希变了** → 那是 Owner 在 T077 亲自签的**六主题身份本身**，改它必须走 Owner 视觉门，不能由重冻代劳。

实测漂移集恰为 `['base_css','keyframes','master_visual']`，逐条可归因；**per-theme 与 contract_root 逐字节未变**——即**你签过的六主题身份没有被动过一根汗毛**。独立复核**没有采信我的叙述**，而是**从每个历史 worker 版本重算 asset_hashes**，确认：T077 的哈希 == build `b189d3cc0703` 的那个 commit；新基线的哈希 == T082 之后直到 HEAD；期间**只有** T079/T080/T082 动过契约元素，**T081/T083/T084/P01–P04 一个都没动**。

## 3. ★复核发现的逃逸，我选择关掉而不是记账★
复核指出一个**先前就存在**（T078 设计缺陷）、并说「本次不重开」的问题：
`run_ci` 计算 `specific = changed - AGGREGATE`，而 `AGGREGATE = {master_visual, contract_root}`。于是**只动聚合哈希**的改动**不会被拦**。具体逃逸：往 `CSS` 常量里塞一条**未注册主题** `[data-theme="neon"]{...}`——`base_css` 会把它当作已注册主题**剥离掉**（`base_css` 不变），`per_theme` 只覆盖注册主题（不覆盖 neon），于是**只有 `master_visual` 动**→ **PASS，exit 0**。
`VB.partition_consistency()` 正是为此而写的补偿控制，**但没有任何人调用它**。
**我把它接进了门的判决**（连同 `theme_set_consistency`）。**实测证明**（干净探针，前两次探针和复核首次一样被污染过——注入的换行会带动 base_css）：注入后 `moved == ['master_visual']`（纯聚合逃逸成立）、`run_ci` 仍报 `PASS`、而门 **exit 1**（`unregistered_themes: ['neon']`）。**修复前这个输入会让未注册主题静默进生产。**
> 判断依据：P05 的全部前提就是「这道门重新变真」。带着一个已知逃逸交付，等于重演我这轮反复在修的那类「看着绿、其实什么都不查」的毛病。

## 4. 仍然存在的边界（诚实）
- **像素层未启用**：`PIXEL_LAYER_ENFORCED=False`。这道门是**源码哈希级**契约门，**不做截图/像素比对**。T077 记录的 `screenshot_schema` / `interaction_recording_schema` 是**未来层的策略**，本任务**未实现**，只是**原样带回**（见 §5）。
- **`<=0.1% 像素容差` 是文档策略，不是本门执行的检查**（沿用 T078 的诚实标注）。
- **这道门没有接进 GitHub CI**：它现在**可以**被运行且 exit code 载重，但仓库的 CI 工作流并未调用它。要真正长期护住六主题，需要把它加进 CI（未做，属下一步）。
- `/library` 等 V0.2 新路由**不在** T077 的 `route_labels` 矩阵里；因页面走标准 `PAGE()` 壳、继承主题，且像素层未启用，故不影响本门判定——但矩阵**未随新路由更新**。
- 逃逸面只在 `partition_consistency` 覆盖的范围内被堵：**未注册 theme / fx 名**（CSS 里的 `[data-theme="X"]` / `.fx-X` / `[data-fx="X"]`）。复核复验确认这一类已全部 exit 1。

## 4b. ★仍存在一类聚合逃逸，但已证明是惰性的（不隐瞒）★
复核在复验时**又找到一类**：往 **`THEME_FX` / `THEME_HERO` / `HERO_VIDEO`** 里加一个**未注册主题名**的键（如 `neon: 'cosmos'`）——
只会移动 `master_visual`，`run_ci` 报 PASS，且 `partition_consistency` 与 `theme_set_consistency` **都报 consistent** → **GATE: PASS, exit 0**。
根因：`master_visual` 含这三张 map 的整体 repr，但 `per_theme` 只遍历 `VB.THEMES`，而 `theme_set_consistency` 只钉 `option_keys` 与 `nav_keys`，**没钉 fx/hero/video 的键集**。
**为什么它带不进真实回归（复核实证）**：`worker_cloud.js:875` 的主题选择走 `hasOwnProperty.call(THEME_NAV, s)`——**`THEME_NAV` 才是运行时白名单，且它已被钉住**（实测：`THEME_NAV` 多一个键 → BLOCK；用 options+nav 正经加第 7 个主题 → BLOCK）。代码里**没有**对这三张 map 做 `Object.keys/entries` 遍历，故多余键是**不可达的死数据**。
**为何本任务不顺手修**：正确修法是扩展 `theme_set_consistency` 去钉 fx/hero/video 键集，但那是 `v0_1` 的共享函数，`t077_verify`/`t078_verify` 等都依赖它，改它属于**超出本任务范围且会波及既有验收**。故**如实记录 + 给出修法**，不夹带。
复核同时排除了 `contract_root`-only 逃逸（构造上不可能：它动必有 `per_theme` 动，而后者会发出具体的 `theme:{t}` 元素），并确认这些都被正确 BLOCK：`[data-theme="neon2"]`、`[data-theme="Warm"]`、未加引号的 `[data-theme=neon]`、`[data-theme="neon" i]`、`.fx-glow2`、`@keyframes neon-pulse`。

## 4c. 复核对我新代码的其余发现（已修 3 条 / 记录 2 条）
**已修**：
1. **死循环（我的真 bug）**：`for c in rep.get("changes", [])` —— `run_ci` 的键是 **`changed`（`list[str]`）**，不是 `changes`，**这段永不执行**，人读输出从不列出被改元素。已改为 `rep.get("changed", [])` 并实测打印。
2. **`--json` 对机器消费者仍自相矛盾**：仅一致性失败时 JSON 里 `decision: "PASS"`、`blocked: false` 却 exit 1。已让 JSON 的 `decision`/`blocked`/`blocked_on` 与 `gate_result` 一致，并**诚实保留** `decision_run_ci_only` 以免抹掉「run_ci 单看是放行的」这一事实。
3. `theme_set_consistency` 失败打印对 nav-key 失败无信息（只印 options 差集）。已补 `themes/option_keys/nav_keys` 全量。

**记录不修**：
4. NC3 缺**正控制**（未断言「可归因漂移时 `main(--write)` 确实会写」，也未断言 abort 是由哪个元素触发）。复核已在外部补做（基线字节可复现即等价正控制）。
5. `coverage` / `cells` 是**从 T077 拷贝**而非现算。复核核对过：**今天数值属实**；但若将来某次重冻的漂移触及规则计数，拷贝会带来**陈旧的 coverage**。（`partition_consistency`/`theme_set_consistency` 是现算的，不受此影响。）

## 5. 基线键位不得静默丢失（复核发现，已修）
我最初写的新基线**比 T077 少了 9 个键**：`cells`/`coverage`/`interaction_recording_schema`/`iteration`/`owner_confirmation_required`/`partition_consistency`/`reduced_motion_separate`/`screenshot_schema`/`theme_set_consistency`。
其中 **`partition_consistency` 正是 §3 那个逃逸的补偿控制**，**`owner_confirmation_required` 是 Owner 视觉门开关**——新基线已是**权威基线**，让这些从中消失属于**证据回归**。已全部带回（`set(T077键) - set(新键)` 现为**空**）；且 `partition_consistency`/`theme_set_consistency` 是**现算**而非拷贝。

## 6. 我自己的验收曾弱于它的声称（复核发现，已修）
`refreeze_verify.py` 的 NC3 原先只把 `RF.drift()` 当纯函数喂了个毒化字典，**从未证明 `main()` 真的返回 2、真的拒绝写盘**——即**测试没有建立它所声称的结论**。已改为：毒化 `RF.FROZEN_T077` → 驱动**真实 `main()` 且带 `--write`** → 断言 `返回 2` **且**盘上基线**逐字节未变**。（NC1/NC2 本就有 `assert mut != src` 锚点保护，不会因锚点消失而静默通过。）
