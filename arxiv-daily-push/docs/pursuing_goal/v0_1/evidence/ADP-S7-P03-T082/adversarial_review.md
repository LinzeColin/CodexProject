# 独立对抗复核 · ADP-S7-P03-T082｜优化环境动效而不改变视觉语义

实现者**不自签 PASS**。由独立 skeptic Agent（`general-purpose`，不共享推理）对抗复核，目标**证伪**验收。

## 结论：CONFIRMED_SOUND

复核 Agent 独立重算全部五向量，无法证伪：

- **(a) meteor 等价 — SOUND（严格证明）**。`.fx` 是 `position:fixed;inset:0`=100vw×100vh，故 left −12%→100%=**112vw**、top 8%→64%=**56vh** 精确；translate 外层（屏幕空间）、rotate 内层（同对角线）。**代数证明**：「按插值 left/top 定位再绕中心旋转」== 「按 base 定位再 translate(Δ)∘rotate 绕 base 中心旋转」**每帧相等**。0%=translate(0,0)=base（起始不跳）。宽度 200px/旋转/box-shadow 全保留（base 规则字节不变）。浏览器确认 meteor 在 base(−153.6px=−12%) + transform 动画。
- **(b) compositor 安全 / FPS — SOUND**。复核自枚举全部 8 个无限动画：pulse(opacity)/banddrift/nebfloat/shaft/clouddrift/sway(transform)/twinkle(opacity)/meteor(transform+opacity)——**全 compositor 安全，无 filter/layout 动画**。≥55 FPS **诚实降级**为确定性 compositor-only 保证（preview rAF 节流），非杜撰数字。
- **(c) 低端 + 前景 — SOUND**。`.fx` 是 pointer-events:none；`.meteor/.band/.neb` **只**出现在 fx-cosmos 层，从不在前景；FX_PERF_JS 不碰任何 button/组件状态选择器（审计+手 grep）。浏览器：低端(deviceMemory=2) 隐藏 meteor/band、降星云 blur、**保留 stars + button:active**；暂停 7/7 后恢复。
- **(d) 合同 / 视觉语义 — SOUND**。`detect_regression` = **只** {keyframes, master_visual(aggregate)}；per_theme(6 主题含 cosmos)/base_css/fx_css/theme_js/reduced_motion/hero 全 byte-identical。**无 CSS 污染**（每个 `.fx-<名>`/`@keyframes NAME{` 匹配都在 CSS const 内，注释里的全角括号/「theme-prefixed」措辞不匹配抽取正则）。BUILD 自哈希从零**精确重现 `0cb3acee6bf3`**；live=`b189d3cc0703`→NOT_DEPLOYED 成立。
- **(e) 回归 — SOUND**。node --check 过；FX_PERF_JS 全 try/catch；三个 visibilitychange 监听独立（RUM flush / hero 视频 / FX 暂停，无冲突）；reduced-motion `*{animation:none!important}` 使 meteor 停在 base opacity:0（不可见，与原一致）；CSP `script-src 'self' 'unsafe-inline'` 内联注入 OK（与既有 THEME_JS/HEAD_INIT/RUM 一致）。负控制：pre-fix meteor `['left','opacity','top']`→all_safe=False，审计真判别。

## 复核的两点精确澄清（非 hole，已采纳）
1. **`contract_root` 未变**：detect_regression 只动 {keyframes, master_visual}（aggregate），`contract_root` 不变（因 cosmos per-theme 字节不变）——比初稿措辞更干净。
2. **工具 `ambient_loops` 返回 7（漏 `pulse`）**：pulse 定义在 HERO_CSS（工具的 `_tmpl(src,"CSS")` 不扫描该常量），故未计入。**无害**：pulse 只动 opacity（compositor 安全），漏掉它不隐藏任何重的动画；复核手工枚举全 8 个确认全安全。

## 底线
验收（1）中位 >=55 FPS（确定性 compositor-only 保证）（2）低端降级但前景反馈不消失，均由**判别性审计 + 代数等价证明 + 内置浏览器行为证明 + 合同重算(仅 keyframes)**证明；build 自哈希与 NOT_DEPLOYED 诚实；FPS 未实测如实披露、以确定性保证替代。

**VERDICT: CONFIRMED_SOUND**（复核原文），实现者据此提交。
