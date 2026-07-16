# Known gaps · ADP-S1-P03-T019

- **未接入 worker 发布路径**：content_qa.publish()/fallback() 是发布前的质量门逻辑，worker 尚未调用它（现仍直显英文摘要）；接入属后续部署任务（须保六主题 + 部署验证 + T017 defect baseline before/after）。
- **generate() 回调待接模型**：publish() 用 generate 回调生成 L2；未接模型前以自测桩验证（timeout/garbage/dup/good）；接模型时把真实生成接上，重试与回退逻辑不变。
- **QA 判据 provisional**：language(ASCII 比)/template(停用词)/duplicate(batch 内)/unsupported(locator) 为确定性 provisional 判据；Owner 抽查后可调阈值。
- **duplicate 仅 batch 内**：跨天去重未覆盖。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
