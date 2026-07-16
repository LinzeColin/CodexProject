# TASK_REPORT · ADP-S7-P01-T077｜冻结六主题视觉与关键动效录屏基线

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P01-T077（Stage S7 UI/UX, Motion & Performance / S7-P01 六主题与高级动效不可破坏基线，size S）
- **release_mode**: NOT_DEPLOYED（只读 worker 源 + 只读 GET；生产未触；实时 build `b189d3cc0703` == T040 不变）
- **Depends**: ADP-S0-P02-T004（线上域名与核心路由基线）
- **Owner gate**: S7 视觉「Owner 确认基线」= 人工签署，实现者不自签 → 本包 READY_FOR_OWNER_CONFIRMATION

## 6 个前置问题
1. **「不可删除合同」的对象是什么？** — 六主题(warm/minimal/fresh/techno/cosmos/forest)的颜色 tokens + THEME_NAV/FX/HERO 映射 + hero 视频 + 氛围(fx)层 DOM + reduced-motion 规则 + keyframes。
2. **怎样使其「不可删除」？** — 从部署 worker 源提取合同并算**确定性 asset hash**；任一元素删改 → hash 变 → `detect_regression` 告警。
3. **矩阵维度？** — 6 主题 × 6 路由(today/queue/radar/system/history/search) × 5 视口(320/375/768/1280/1440) = 180 cell。
4. **reduced-motion 怎么「单独记录」？** — 独立 hash + schema 独立 `reduced_motion_variant`（每录制在 reduce 下重跑）。
5. **截图/录屏怎么交付且不违反 Low-Token？** — asset hash 骨干 + 180-cell 截图 schema + **live 合同校验**（实测 live serve 完整合同）替代二进制 PNG；像素 PNG 留待 Owner 确认/T078。
6. **Owner gate 怎么处理？** — 产出机器可验证骨干 + 证据，标注 `owner_confirmation_required`，**不自签**。

## 交付物
- **工具** `tools/visual_baseline.py`：extract_contract(从 worker 源提取六主题合同)/asset_hashes(每主题指纹+reduced-motion独立+fx-layers+keyframes+contract_root)/baseline_matrix(180 cell)/build_baseline(矩阵+hash+schema)/detect_regression(候选源重算 hash 与冻结基线 diff)。
- **基线 manifest** `visual_baseline_manifest.json` = 6 主题 × 6 路由 × 5 视口矩阵 + asset hash + 截图/交互录屏 schema + reduced_motion_separate。
- **live 合同校验** `test-results/live_contract_check.py/.txt`：实测 live 生产站 serve 完整六主题合同。
- **known_gaps.md**：Owner 不自签、截图形式(hash+schema+live 替代二进制)、源级 vs 像素级边界。
- **独立对抗复核** `adversarial_review.md`。

## 验收（机器可验证骨干 PASS，verifier 独立重算 hash）
证据：`test-results/visual_baseline_tests.txt`（ACCEPTANCE = PASS，exit 0），verifier `t077_verify.py`。

1. **6 主题 × 路由 × 5 视口** — 矩阵恰 6 主题 + 6 路由 + 5 视口 = 180 cell；每主题 tokens/nav/fx/hero 齐。
2. **asset hashes（完整主题/动效身份表面 + 布线）** — 可复现 + 6 个 per-theme hash 互异 + **master_visual 完整性锚**(覆盖整 CSS+HERO_CSS+THEME_JS+HEAD_INIT+FX_LAYERS+**hero/dashboard 标记**+**DOM 生产者 blurChars/sparkSVG**+**PAGE 壳布线**+映射)；覆盖非浅(per-theme 规则数 warm2/minimal7/techno7/cosmos3/forest12，氛围 fx 规则 cosmos11/minimal5/techno5)；**不可删除合同负控制(19 个 load-bearing)**：删主题 / 改 token / 改 fx 映射 / 改 hero 视频 / 改氛围动效 CSS / 改组件规则 / 改 HERO_CSS / 改 keyframe / 删 hero `<video>` / 改 cosmos gaugeArc / 掏空 blurChars / sparkSVG 改色 / PAGE 删 `${FX_LAYERS}` / PAGE 删 `${THEME_JS}` / 删 THEME_OPTIONS entry / 改 THEME_OPTIONS key / heroSection `return` 改 / hero 视频字节换 / **todayPage 丢 `{ hero }` 传递** **全部告警** + **主题集一致性交叉校验**；benign 非视觉/内容编辑**不误报**。（七轮修复：token 块→完整表面→hero DOM(`_hero_markup`)→DOM 生产函数(`_fn_body`)→PAGE 壳布线(`_tmpl` 箭头)→THEME_OPTIONS 枚举(`_theme_options`+一致性)→heroSection 组装 + hero 视频字节(`_asset_sha`)→todayPage hero 布线守卫(`_hero_wiring` 结构化非 hash 内容) + live check 去空跑(改为断言 hero 真渲染 `id="heroVideo"`/`gaugeArc`，此前只查永远内联的 JS map=tautological)。**范围=主题/动效身份层 + 三层布线(PAGE+heroSection+todayPage 传递) + 主题枚举 + hero 资产字节**，非全站内容/通用结构生成器。）
3. **reduced-motion 单独记录** — 独立 hash(≠contract_root) + schema 独立 variant；负控制：删 reduced-motion 规则 → 告警。
4. **screenshot + recording schema** — schema 覆盖全 180 cell；motion themes 恰 {minimal,techno,cosmos,forest}(fx≠none 或有 video)。
- **live 合同校验**：live today 页 serve 全部 6 token 块 + 4 fx 层 + reduced-motion + 映射 + hero 视频(build b189d3cc0703==T040)。

## 实时未回归
只读任务：读 worker 源 + 2 次只读 GET(today/build.json)。无 worker/D1/R2/cron 改动。基线仅**冻结**现状，不改任何主题。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model_calls 0；recurring cloud 0；只读 GET 2 次；人工=工具/验证器/live 检查/复核撰写 + Owner 视觉确认(独立人工)。

## 独立验证 & Owner gate
实现者**不自签 PASS**，也**不自签 Owner 视觉确认**。机器骨干交独立 Agent 复核(见 adversarial_review.md)；视觉基线交 Owner 确认。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION（机器骨干）+ READY_FOR_OWNER_CONFIRMATION（S7 视觉 gate）
