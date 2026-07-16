# Known gaps · ADP-S1-P01-T009

- **绑定仓库文件 sha256，非线上运行时 build**：manifest 证明「此 commit 的源文件集」，与「Cloudflare 线上部署的 version」的绑定属后续任务（FACT-014 严格逐 host 一致，S1 部署纪律）。当前可用 T006 记录的 live version 455afd98 侧面对照。
- **prompt / parser 内联于 worker_cloud.js**：未拆分为独立文件，故 prompt.sources 与 parser 都指向 worker 入口的 sha256（note 已标明）。若后续拆分 prompt/parser，manifest 绑定粒度可细化。
- **model 绑定为治理文档 + thresholds**：MODEL_SPEC.md + formula_registry.yaml + parameter_registry.csv + thresholds_v0_3.yaml 的 sha256；若模型逻辑另有代码实现，后续可加入。
- **redaction 是启发式**：覆盖 Bearer/token/长 hex；manifest 只存 hash 不存内容，本就不泄露 secret，redact() 是双保险。
- **content_hash 不含 generated_at/generator_note**（设计如此，允许字段）；这两个字段变化不影响 hash，符合验收「除允许字段外 hash 一致」。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
