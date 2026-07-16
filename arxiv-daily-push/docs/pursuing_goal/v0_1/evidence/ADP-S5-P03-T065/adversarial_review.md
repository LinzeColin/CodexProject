# Adversarial review · ADP-S5-P03-T065｜引用支持/反驳/关系证据

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 不由标题/模型印象（标题是否泄漏进分类、是否有隐藏启发式充当"印象"、判别控制是否真证明 context≠title 驱动）；(b) 可查上下文/可回溯（非 mention 线索是否逐字在上下文、子串陷阱 unlike⊂unlikely / consistent⊂inconsistent / support⊂supportive、多次出现、CJK 偏移、空/None）；(c) 分类稳健（earliest-wins + counter 先 tie-break、双重否定等语义边界——区分"语义不完美但诚实线索支撑[可接受]"与"标签无上下文支撑[空洞]"）；(d) graph（边带证据、同论文 support/counter 并存）；(e) 非空跑/负控制（verifier 从工具而非 report 现推、fixture 是否充分）；NOT_DEPLOYED（无网络/写/时钟/随机/模型）。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
- **(a) 不由标题**：复核者自造双向标题/上下文冲突（标题 counter+上下文 support→support；标题 support+上下文 mention→mention；CJK 标题 support+上下文 counter→counter）——**标签恒随上下文**。`classify_citation` 签名**仅 context**；`build_citation_graph` 只传 `c["context"]`，title 仅展示。纯有界词表正则，**无隐藏启发式/印象**。
- **(b) 可查/子串**：词边界防 `unlike⊄unlikely`、`consistent with⊄inconsistent with`、`support⊄supportive/unsupported`、`replicat⊄unreplicated`、`corroborat⊄uncorroborated`；词干仍配屈折；CJK 否定前缀（不支持/不一致）因最早+counter 先压过内嵌正向；多次出现取最早；空/None→mention。**每个非 mention 线索字符精确在其 offset（quote==cue==ctx 切片）**。
- **(c)**：双重否定/"could not reproduce" 语义不完美但**线索确在上下文**（诚实线索支撑）→ 按验收（可查上下文 + 不由标题，非完美 NLP）**可接受**；**未发现任何标签无线索支撑**。
- **(d)**：query_graph 带完整证据；同一被引 B1 的 support+counter **并存为不同边**。
- **(e)**：verifier 从**工具+fixture 现推**（不读 report JSON）；复核者内存 monkeypatch 三处回归均被**抓到**（朴素子串匹配→词边界控制失败；mention→support 静默升级→golden+query 控制失败；title 泄漏进 context→冲突+判别+query 控制全失败）。NOT_DEPLOYED 确认：仅 `import re`，无网络/时钟/随机/模型/subprocess。
- 复核者注意到复核中工具从**弱 naive-find 版**更新为**词边界正则版**，并核验**当前文件**为 sound。

## 非致命 nit 的主动闭合（4 项）
1. **"byte-exact/逐字节"措辞**：offset/length 实为 Python **字符索引**（非 UTF-8 字节）；`quote==context[offset:offset+length]` 在字符空间一致成立、消费侧（label_has_viewable_context）亦字符切片，无功能 bug——但下游若把 offset 当字节偏移（CJK）会被误导。**已修**：工具 docstring 明确 offset/length 为字符索引、非字节偏移。
2. **tie-break docstring 与代码不符**：原 docstring 说"counter 先于 support 再取更长"，代码实为位置优先再长度优先（同位仅当等长才 counter 胜）。**已修**：`_find_earliest_cue` 改为 `min` over `(pos, label_rank[counter<support], -length)`——**位置最早→同位 counter 先→更长**，与 docstring 一致；加对称控制（counter-earliest→counter / support-earliest→support）。
3. **语义假阳（双重否定/反讽）**：验收范围外、且线索恒在上下文可查——known_gaps 诚实披露。
4. **中途更新**：非问题，当前文件已被复核者核验 sound。

## 残留（诚实披露，非空洞、恒线索支撑）
- 确定性词表非 LLM 语义：双重否定/隐含转折按字面线索判；线索恒逐字在上下文可查、绝不由标题/印象。CJK 线索罕见被更长短语包含时按最早线索判。语义级分类留待后续（须保留可查上下文契约）。known_gaps 已列。

## 结论
复核 **CONFIRMED_SOUND**；两验收条款（标签有可查看上下文 / 不由标题或模型印象）有 load-bearing 判别负控制（monkeypatch 三回归均被抓）、非空跑。4 项非致命 nit 主动闭合（字符索引措辞、tie-break 代码/文档一致 + 对称控制、语义边界披露）。确定性、零副作用、无模型调用。实时无回归（live build_id b189d3cc0703 == T040）。**收尾 S5-P03**。判定：**可交独立验证 / SHIP**。
