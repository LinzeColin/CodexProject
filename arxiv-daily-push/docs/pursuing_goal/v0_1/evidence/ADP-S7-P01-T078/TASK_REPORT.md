# TASK_REPORT · ADP-S7-P01-T078｜建立 Visual/Motion Regression CI

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P01-T078（Stage S7 UI/UX, Motion & Performance / S7-P01 六主题与高级动效不可破坏基线，size S）
- **release_mode**: NOT_DEPLOYED（纯门逻辑读 T077 源哈希 + 1 次只读 GET；生产未触；实时 build `b189d3cc0703` == T040 不变）
- **Depends**: ADP-S7-P01-T077（冻结六主题视觉+动效 un-deletable 合同）

## 6 个前置问题
1. **门建在什么之上？** — T077 `visual_baseline.detect_regression`(七轮复核 CONFIRMED_SOUND，19 负控制)。门对候选源重算合同、diff 出变化元素。
2. **什么 BLOCK？** — 任一 specific 主题/动效元素(theme:X/fx_layers/keyframes/hero_*/dom_producers/reduced_motion/theme_options/page_shell/…)变化且**无有效 approved-change** → BLOCK。
3. **approved-change 怎样才有效？** — `{element, 非空 reason, 非空 approver}`；空任一/错 element/aggregate 均无效。**per-element、需说明**。
4. **视觉 diff 阈值？** — 源哈希**精确**(容差 0)；截图层像素容差 0.1%(字体/GPU 噪声)有 note。
5. **recording checks 是什么？** — 变化分类 visual vs **motion**(keyframes/fx/hero/producers/reduced-motion)；motion 回归进 `recording_checks.motion_regressions`。
6. **怎样不是橡皮图章？** — 6 主题+所有动效删改全 BLOCK(无 false-negative)；benign 非视觉编辑 PASS(不过度阻断)；approval 绕过尝试(aggregate/空 reason/错 element)全 BLOCK。

## 交付物
- **工具** `tools/visual_regression_ci.py`：`run_ci(baseline, candidate_src, approvals)` → decision(BLOCK/PASS/PASS_APPROVED)+blocked_on+approved_changes+approval_reasons+changed_by_category(visual/motion)+recording_checks+thresholds。AGGREGATE 集(master_visual/contract_root)过滤、不可用于绕过。
- **报告** `visual_regression_ci_report.json`：6 个模拟 PR 的门判定。
- **known_gaps.md**：源级 vs 像素级、per-element 说明、未接 CI runner/持久化/真实截图 diff 的边界。
- **独立对抗复核** `adversarial_review.md`。

## 验收（PASS，verifier 独立重算基线 + 跑真门）
证据：`test-results/visual_regression_ci_tests.txt`（ACCEPTANCE = PASS，exit 0），verifier `t078_verify.py`。

1. **删除任一主题/氛围层的模拟 PR 会被阻断** — delete-theme(forest token 块)→ **BLOCK**(blocked_on=[theme:forest])；delete-fx-layer(cosmos 氛围)→ **BLOCK**(fx_layers)；**判别负控制**：benign 非视觉编辑 → **PASS**(不过度阻断)。**扩展核**：6 主题全 BLOCK + fx/keyframe/hero 视频/生产者/reduced-motion 全 BLOCK。
2. **允许的像素差有说明 + approved-change process** — 有说明的 approved 变化(reason+approver)→ **PASS_APPROVED**(记录 reason)；**负控制**：空 reason → BLOCK；空 approver → BLOCK；错 element(approve cosmos 却删 forest)→ BLOCK；approve aggregate(master_visual/contract_root)→ BLOCK(不能绕过)。
3. **visual diff thresholds** — 源精确(0，唯一执行层)；像素 0.1% 容差**诚实标注为文档化 policy、本任务不执行**(pixel_layer_enforced=False)。**recording checks** — keyframe/fx-layer/**THEME_JS/HEAD_INIT/氛围动画 CSS(fx_css)** → motion regression；colour token/base-CSS → visual(分类正确非 tautological)。
- **★对抗复核 fatal 已修★**：THEME_JS(客户端动效行为)/HEAD_INIT/base-CSS 此前只喂 aggregate master_visual、无 specific hash → 掏空关键动效**竟 PASS**。已扩展 T077 共享工具加 `theme_js`/`head_init`/`base_css`/`fx_css` specific hash(additive、master/per_theme 不变、T077 verifier 仍 PASS)；现 THEME_JS 动效掏空/HEAD_INIT 引导删/氛围动画改 **全 BLOCK 且进 motion 通道**。附带闭合氛围 CSS motion 分类、像素阈值诚实标注、malformed approvals fail-safe(不崩)。
- **可复现**：run_ci 两次一致。malformed(no-changes PASS/空 approvals BLOCK/approvals=None/非 list/非 dict entry 均 fail-safe BLOCK 不崩)。

## 实时未回归
纯门逻辑：读 T077 源哈希 + 1 次只读 GET(build.json)。无 worker/D1/R2/cron 改动。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model_calls 0；recurring cloud 0；只读 GET 1；人工=门/生成器/验证器/复核撰写(未来每 PR 自动跑 0 人工)。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核(见 adversarial_review.md)。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
