# 对抗复核记录 · ADP-S4-P03-T050（分批省级回填 自审→加固→确认）

用独立 skeptic 对分批回填编排器做对抗复核（试图证明「验收 PASS 而宣称为假」）。

## 结论：CONFIRMED_SOUND（所有承重宣称成立）
- **批门先于下批**：真。`orchestrate` 对失败批 `break` + `halted_at`；负控制（空 fetcher → 0 文档 → 门失败）走同一路径，实测 halted_at=0/下批不跑。
- **失败省隔离**：真。`run_province` try/except 返回 ok=False 不 raise；注入抛异常的 fetcher 也不 crash，存活省仍过门；广东真实被挡、记录、不阻塞批 0。
- **9 真实 A1 文档 + 正确日期**：真。canonical_id 独立重算 `ttl:sha256(url)[:16]` 全不同；真实 gov.cn 文章 URL + 省份文号；日期为文档发布日期（非 Maketime/URL 渲染时间戳，T049 修复生效）。
- **幂等**：真（内容寻址，重跑 0 新）。
- **零文档批不能过门**：真。

## 加固（关闭 skeptic 指出的 rigor gap）
skeptic 指出 `normalize` 硬编码 `authority_level="A1"`，回填路径未调 `verify()`——A1 是**假定非赢得**。已改 `run_province`：对每篇调 `connector.verify()`，仅保留 `is_official and authority_level=="A1"` 的文档，doc 的 authority_level 取自 **verify 的身份判定**（非硬编码）。3 省仍全过（官方省 .gov.cn + directory + 非中央 → A1），但 A1 现**赢得**；非官方页会被拒（rejected_non_a1 计数）。复跑：同 9 文档、幂等、门控、隔离、负控制全绿，ACCEPTANCE=PASS。

实现者不自签任务 PASS —— 交独立复核。
