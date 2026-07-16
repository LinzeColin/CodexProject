# TASK_REPORT · ADP-S7-P03-T082｜优化环境动效而不改变视觉语义

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P03-T082（Stage S7 / S7-P03 RUM、CWV、动效与数据性能，size S）
- **release_mode**: NOT_DEPLOYED（改 worker 源 + 重算 BUILD `8c19387c846b`→`0cb3acee6bf3`，不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P03-T081

## 6 个前置问题
1. **哪里慢（jank 源）？** — 审计 10 个 @keyframes：9 个已只动合成器安全属性（transform/opacity/filter）；**唯一** `meteor` 动 `left/top`（每帧强制 layout+paint）——这是唯一环境动效 jank 源。
2. **怎样 >=55 FPS？** — 把 meteor 从 left/top 转为 `transform:translate(112vw,56vh) rotate(18deg)`（GPU 合成）。转后**所有环境无限循环 keyframe 只动合成器安全属性** → 合成器线程跑、不阻塞主线程 → ≥55 FPS **确定性保证**。
3. **怎样「不改变视觉语义」？** — meteor 屏幕路径**等价**（`.fx` 是 viewport-fixed，left:-12%→100%=translateX 0→112vw，top:8%→64%=translateY 0→56vh；base rotate(18deg) 保留、translate 在屏幕空间）。**唯一改的合同元素是 `keyframes`**；6 主题身份/base 布局/主题引擎/fx 层全 byte-identical。
4. **怎样「低端降级但前景不消失」？** — router 注入 FX_PERF_JS：低端(deviceMemory/核数低或省流量)→data-fx-lite→隐藏最重层(meteor/band)、简化星云；**只碰环境层、绝不碰前景(按钮)选择器**；前景反馈(T080 button:active)保留。
5. **暂停离屏/后台？** — FX_PERF_JS 监听 visibilitychange→隐藏时 `.fx *` animationPlayState=paused（省 CPU/电，离屏零渲染），可见时恢复。
6. **NOT_DEPLOYED？** — 改源+重算 build_id，不部署；live 不变。

## 交付物
- **meteor keyframe 转换**（left/top→transform，唯一合同改动，走 T078 approved-change）。
- **FX_PERF_JS**（router 注入，不碰任何合同哈希）：暂停+低端降级。
- **before/after trace** `before_after_trace.json`：meteor layout(True)→compositor(False)；等价性推导。
- **工具** `tools/ambient_perf_audit.py`：keyframe_props/ambient_loops/ambient_compositor_safety/meteor_converted/has_pause_offscreen/has_lite_degradation/foreground_preserved/preserves_theme_identity（判别性，pre-fix 负控制）。
- **浏览器证明** `browser_measurements.json`（内置 Chromium）：暂停 7/7；低端降级+前景存活；meteor transform。
- **pre_fix_worker.js/pre_fix_baseline.json**（T081 基线）、**fx_perf_harness(.._lowend).html**、**独立对抗复核** adversarial_review.md。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/ambient_perf_tests.txt`（ACCEPTANCE = PASS）。

1. **中位 >=55 FPS** — 7/7 环境 loop 合成器安全（transform/opacity/filter）；meteor left/top→transform（before/after: layout True→False）；**pre-fix 负控制**：全合成器安全=False（meteor left/top）。
2. **低端降级+前景不消失** — FX_PERF 检测低端→降级最重层+不碰前景；浏览器：lite 隐藏 meteor/band+简化星云、**保留 stars 底层氛围 + button:active 前景反馈**；暂停 7/7 隐藏→恢复。
3. **不改变视觉语义** — 唯一改 `keyframes`；per_theme/base_css/theme_js/fx_css/hero byte-identical；meteor 屏幕路径等价（推导）；门 BLOCK 无 approval / PASS_APPROVED 带 keyframes approval。

## 实时未回归
NOT_DEPLOYED：改源+重算 build_id(0cb3acee6bf3)，不部署。live `/build.json`=b189d3cc0703（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model 0；cloud 0（NOT_DEPLOYED）。只读 GET 1；in-app 渲染 2（normal+lowend）；人工=keyframe 转换+FX_PERF 控制器+审计工具+浏览器测试+验证器+复核。**真实 FPS 数值**须部署到前台浏览器测（preview 节流 rAF）。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
