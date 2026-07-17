# 独立对抗复核 — ADP V0.2 P05 六主题视觉/动效门重新冻结

复核者：独立 general-purpose skeptic（非实施者；实施者不自签）。两轮。

## 第一轮：CONFIRMED_SOUND —— 但归因是**被重算验证**的，不是被采信的

复核**没有采信 TASK_REPORT 的叙述**，而是**从每个历史 worker 版本重算 `asset_hashes`**：
- T077 冻结的哈希 **逐字节等于 commit `8b77d4035`**，而该 commit 的 `build_id` 恰为 **`b189d3cc0703`** —— 与 manifest 自称的锚点吻合。
- 新基线的哈希 **逐字节等于 `1af78540d`（T082）直到 HEAD `f9b30b08f`（`204c97eb5406`）**。
- 两锚点之间，**只有** `b792d1272`(T079, base_css)、`d5ed72910`(T080, base_css)、`1af78540d`(T082, keyframes) 动过契约元素。
  **T081/T083/T084/P01/P02/P03/P04 一个都没动** → 没有别的东西被当作「可归因」蒙混过关。
- 内容 diff 与叙述逐条吻合（T079 的 `main img,main svg,main video{max-width:100%}` + `@media(max-width:520px)` 表格滚动 + `.card` overflow-wrap；T080 的 `:active/:disabled/[aria-busy]/:focus-visible/[data-state]/undo`；T082 的 meteor `left/top`→`transform:translate`，且是**唯一**被动的 keyframe）。
- 三个任务的证据目录各自带**独立 CONFIRMED_SOUND**。
- **`per_theme` 与 `contract_root` 逐字节未变** → Owner 亲签的六主题身份未被触碰。
- **重冻不是橡皮图章**：喂入不可归因的 `theme_js` 漂移 → `main()` 返回 **2**、**即便带 `--write` 也不写盘**；per-theme 规则漂移 → 同样 2。
- **门真的会判**：干净→PASS(0)；改 keyframe→BLOCK(1)；删 meteor→BLOCK(1)；空 worker→BLOCK 21 元素；从切换器删掉一个主题→BLOCK。approvals 路径正常（合法→PASS_APPROVED(0)、空理由→BLOCK、dict 非 list→BLOCK、元素不匹配→BLOCK）。
- **未破坏既有调用者**：带敌意 `sys.argv` 导入无副作用；`t077_verify`/`t078_verify` PASS；`soak_stopline_drill` exit 0。
- **NOT_DEPLOYED 属实**：worker 与 HEAD 逐字节相同；复核**独立**用自排除哈希复算出 `204c97eb5406`，与 P04 的 `deploy_verify.txt` 吻合。

### 第一轮的非阻塞发现（实施者选择全部处理）
1. **聚合逃逸**（复核标注为 T078 既有设计缺陷、「本次不重开」）：`run_ci` 算 `specific = changed - AGGREGATE`，故**只动 `master_visual`** 的改动不被拦。
2. 新基线**丢了 9 个键**（含逃逸的补偿控制 `partition_consistency` 与 Owner 视觉门开关 `owner_confirmation_required`）→ **证据回归**。
3. NC3 **弱于其声称**（只测 `RF.drift()` 纯函数，未证明 `main()` 真返回 2、真拒写）。

## 实施者的处理（不是记账，是修）
1. 把 `partition_consistency` + `theme_set_consistency` **接进门的判决**；用**干净探针**证明逃逸真实存在且已被堵（前两次探针与复核首次一样被污染——注入换行会带动 `base_css`/`hero_css`；干净构造：在 `CSS` 常量内紧贴 `[data-theme="warm"]{...}` 后插入 `[data-theme="neon"] .card{color:red}`，**`moved == ['master_visual']`**、`run_ci` 仍 `PASS`、门 **exit 1**）。并输出合并后的单一 `GATE:` 判决，消除「decision: PASS 却 exit 1」的自相矛盾。
2. 9 个键**全部带回**（`set(T077键) - set(新键) == ∅`），两个一致性控制**现算**而非拷贝。
3. NC3 改为**驱动真实 `main()` 且带 `--write`**，断言返回 2 **且**盘上基线**逐字节未变**。

## 第二轮：CONFIRMED_SOUND
- **逃逸确已关闭**：复核用**自己的**干净 neon 探针复现并确认现在 `GATE: BLOCK (run_ci decision: PASS)` exit 1；`.fx-glow` / `[data-fx="glow"]` / `.fx-aurora` 同样 exit 1。
- **基线字节可复现**（4 次重算稳定 `d735549d…`）；`partition_consistency` **确为现算**（把 `VB.WORKER` 指向被 neon 污染的源，报告随之翻为 `unregistered_themes:['neon']`）；带回的键值与现算一致，无陈旧。
- **NC3 已端到端**；`gate_result` 在四种组合下均正确；**NOT_DEPLOYED 属实**。

### 第二轮发现（3 条已修 / 2 条记录 / 1 条惰性）
- **★死循环（实施者真 bug）★**：`for c in rep.get("changes", [])` —— `run_ci` 的键是 **`changed`（`list[str]`）**，故**这段永不执行**，人读输出从不列出被改元素。**已修并实测打印**。
- **`--json` 仍对机器消费者自相矛盾**：仅一致性失败时 JSON 报 `decision:"PASS"`、`blocked:false` 而 exit 为 1。**已修**（JSON 判决与 `gate_result`/exit 一致，同时保留 `decision_run_ci_only` 不抹掉事实）。
- `theme_set_consistency` 失败打印对 nav-key 失败无信息 → **已补全量**。
- 记录：NC3 缺正控制；`coverage`/`cells` 为拷贝（今日属实，未来漂移触及规则计数时会陈旧）。
- **惰性逃逸（记录不修）**：`THEME_FX`/`THEME_HERO`/`HERO_VIDEO` 多一个未注册键只动 `master_visual` 且两个一致性控制都报 consistent → PASS。但复核**实证其不可达**：运行时白名单是 `THEME_NAV`（`worker_cloud.js:875` 的 `hasOwnProperty` 门），而 `THEME_NAV` **已被钉住**，且代码未对这三张 map 做键遍历 → **不可达死数据**。正确修法是扩展 `theme_set_consistency` 覆盖这些键集，但那是 `v0_1` 共享函数、`t077/t078_verify` 均依赖，超出本任务范围 → **如实记录于 known_gaps §4b**。

**终判：VERDICT: CONFIRMED_SOUND（两轮）**
