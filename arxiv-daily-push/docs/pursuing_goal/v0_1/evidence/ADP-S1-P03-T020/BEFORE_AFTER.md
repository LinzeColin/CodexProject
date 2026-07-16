# Before / After · 内容质量（ADP-S1-P03-T020，500 样本）

> BEFORE = 原始 item（当前线上直显）；AFTER = 经 S1-P03 内容契约（factsheet→render payload）后的内容 bundle。build_id `bd67a78020a3`，provisional_machine。

## BEFORE（原始 500 item 缺陷）
- items_with_any_defect：**460/500**
- english_direct_output：**361/500**（中文 UI 直显英文摘要，FACT-002）
- empty_section：53 · templating：58 · board_pollution：44 · duplication：3

## AFTER（500 render payload 经 Release Gate）
- **RESULT: RELEASE**
- key_claim_evidence_100：**通过**（key_unlocated=0）
- empty_or_template_leak_0：**通过**（empty_or_template=0）
- p0_fact_accuracy：**1.0**（≥0.99 阈值；机器抽取保真=P0 字段逐字取自原文；人工准确率 provisional 待抽查）

## 结论
S1-P03 契约（T016 factsheet 抽取 → T017 缺陷基线 → T018 L0-L3 人话版 + evidence locator → T019 QA/回退 → T020 Golden Set/Release Gate）把 460/500 的内容缺陷在**发布契约层**收敛：英文原文进 L3 显式标注、L0/L1 中文事实层每条挂 locator、关键声明证据 100%、空/模板泄漏 0。**Release Gate 失败只阻断内容 bundle，不阻断部署**。
