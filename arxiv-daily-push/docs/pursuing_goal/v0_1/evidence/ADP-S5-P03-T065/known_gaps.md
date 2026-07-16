# Known gaps · ADP-S5-P03-T065

- **确定性线索词表（非 LLM 语义、无模型印象）**：support/counter/mention 由**有界、显式的线索词表**（`consistent with/corroborat/支持/一致…`；`contradict/in contrast to/矛盾/不支持…`）+ **最早出现优先**（counter 先于 support 做确定性 tie-break）决定。**优点**：完全确定性、**无模型印象/无 LLM 调用**、标签恒由可查上下文线索支撑、可复现。**代价**：不覆盖**语义细节**——双重否定（"not inconsistent with"）、反讽、隐含转折等会按字面线索判。**但线索词恒逐字节在上下文可查**（满足「标签有可查看上下文」），且**绝不由标题或模型印象**（满足第二条款）；语义级引用分类（如 LLM + 证据回链）留待后续，且须保留本可查上下文契约。
- **ASCII 词边界 / CJK 子串**：ASCII 线索用词边界匹配（`unlike` 不误配 `unlikely`、`consistent with` 不误配 `inconsistent with`），词干（corroborat/replicat/reproduc）仅前边界以配其屈折形；CJK 无词边界用子串（`不一致/不支持` 因 counter 先检+最早优先，正确压过 `一致/支持`）。残留：CJK 线索仍可能被更长短语包含的罕见情形按最早线索判——恒可查、非编造。
- **双线索上下文**：一句含 support 与 counter 双线索时取**最早出现**者（确定性），并记该线索。真实「对 X 支持、对 Y 反驳」应按**每被引论文各自的上下文**分别成边（本模型每条引用自带针对该被引的 context）。
- **引用上下文来源**：`context` 由上游引文抽取提供（本任务消费之），完整的从 PDF/全文抽取引文句由摄取阶段负责；本任务专注「给定上下文→可查证据化标签」。
- **关系类型**：本任务 support/counter/mention 三类（对齐 Scite）。ResearchRabbit/Litmaps 式的共被引/文献耦合图可在此 graph 底座上扩展。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，无模型调用，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。**收尾 S5-P03（研究集合、证据与反证）**：T063 元数据增强 + T064 Research Set/比较/筛选 + T065 引用证据。
