# Adversarial review · ADP-S5-P03-T063｜研究元数据增强（DOI/Crossref/OpenAlex）

独立对抗复核（general-purpose skeptic，两轮），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 预印本/期刊混淆（错链/过并/漏链、期刊锚到 arXiv PDF、预印本被重标）；(b) degraded fallback 空洞（非 AdapterError 异常崩溃阻塞全批、变异 adapter 污染证据锚、原证据被改）；(c) failed vs not_found 诚实性；(d) 作者/机构消歧过并或漏并、引用图是否真实；(e) 非空跑/负控制判别力 + verifier 是否从 report 而非工具现推；NOT_DEPLOYED（无网络/写/时钟/随机）。

## 第一轮：CONFIRMED_SOUND（两处最强攻击被前置硬化挡下）
- **(b) 最强攻击一**：adapter 抛**非 AdapterError**（KeyError/TypeError）会否崩溃阻塞全批？——已前置硬化：`enhance` 改为 `except Exception` 捕获，一篇的崩溃不沉全批。verifier 有对应负控制（KeyError adapter 仍保全 5 篇并记 failed）。
- **(b) 最强攻击二**：变异 adapter 篡改传入 paper 会否污染证据锚？——已前置硬化：每个 adapter 收 `copy.deepcopy(paper)` throwaway 副本，锚不可被污染。verifier 有对应负控制（vandal adapter 无法改 PAPERS/锚）。
- **(a)**：work-keying 按输入篇 index，跨篇过并**结构上不可能**；期刊 DOI 恒来自本篇已确认 Crossref 记录；确认门 load-bearing 且判别；期刊从不锚 arXiv PDF、预印本从不被重标。
- **(c)(d)(e)**：failed/not_found 正确区分、失败 adapter 不产出增强；`resolve_authors` 复用 T058 精确 alias 聚类（无模糊子串过并）；verifier 从 `RM.run_pipeline/link_works/resolve_authors` **现推**（非 report JSON），逐条判别控制；确定性、零副作用（NOT_DEPLOYED，实时 build b189d3cc0703 不变）。
- **判定**：两验收条款（预印本/期刊不混淆、增强失败不阻塞）**真成立、有 load-bearing 负控制、非空跑/作弊/错**。列 4 项**验收外的潜在过度声明**（非阻断）。

## 潜在过度声明的主动闭合（4 项）
1. **机构未真统一**（原只解析作者，机构仅附着）→ 新增 `resolve_institutions`（+ 共享 `_resolve_field`），复用 T058 跨源统一机构；verifier 加控制：MIT 跨 Crossref+OpenAlex 统一为一实体带双源 provenance、MIT≠Stanford 不过并。「机构」现**真被跨源统一**。
2. **未确认增强在增强级无标记**（只 link_works 标 unconfirmed_doi）→ `enhance` 在**增强级**计算自描述 `confirmed_publication`（00001=True/00002=False），`link_works` 改为读该 flag；缺失 flag 安全默认不链。verifier 加控制验证 flag 与链接决策一致。
3. **"引用图"过度声明**（实为 references 列表 + cited_by_count）→ 文档措辞改为「citation signals（references + cited_by_count）附着，完整图属 T065」；verifier 加控制：citation signals 作增强附着且**不泄漏进原证据**。
4. **T058 精确名过并**（同名不同人/校）→ 属 T058 固有、单一事实源**不分叉**，known_gaps 诚实披露（ORCID/ROR 强标识消歧留待部署阶段/T065），并披露 resolve_* 为**全局身份池非按篇归属**。

## 第二轮（复核 DELTA）：CONFIRMED_SOUND（hole=null, severity=none）
- **门重构行为保持**：复核者对 {has_preprint==aid / 指向别处 / None / 键缺失 / 无 doi} × {aid 有效 / None / 缺键} 做**穷尽 old-vs-new 矩阵，零分歧**；缺失 flag 安全默认 `bool(None)=False` 不链。
- **resolve_institutions 判别**：同机构跨源统一、异机构不并、子串近似（MIT vs MIT Media Lab）**不过并**——与 authors 同标准；`resolve_authors` 行为未变。
- **文档/报告**：机构真统一、引用图已缩为 signals，无实质过度声明。**无新空洞**。
- 复核者指出**一处退化非-delta 观察**：`arxiv_id=None` + Crossref `has_preprint=None` 的 `None==None` 会误判 confirmed=True（旧门同样如此，属既有，真实 arXiv 管线不出现）。

## 主动硬化（第二轮观察）
- `confirmed_publication` 加 `bool(aid) and ...` 守卫：**无 arxiv_id 的退化篇不能靠 None==None 误链期刊版本**；verifier 加负控制（无 id 篇 → confirmed=False 且无 journal 版本）。
- 模块顶部一行 intent 的 "citation graph" → "citation signals"（与正文一致，零残留过度声明）。

## 残留（诚实披露，非空洞，不阻断）
- resolve_* 为**全局跨源身份池**（非按篇作者归属）；未确认 DOI 的作者入全局池但不判给该篇、也不链为该 work 的期刊版本；按篇确认门控归属 + ORCID/ROR 强标识消歧留待 T064/T065（known_gaps 已披露）。
- 完整引用图（含 support/counter 语境）= T065 范围。

## 结论
两轮复核均 **CONFIRMED_SOUND**；两验收条款有 load-bearing 负控制、非空跑。两处最强攻击被前置硬化挡下，4 项潜在过度声明主动闭合（机构真统一、自描述确认 flag、引用 signals 措辞、退化篇硬化），均加判别控制。单一事实源被尊重（复用 T058、不分叉噪声/身份契约）。实时无回归（live build_id b189d3cc0703 == T040）。判定：**可交独立验证 / SHIP**。
