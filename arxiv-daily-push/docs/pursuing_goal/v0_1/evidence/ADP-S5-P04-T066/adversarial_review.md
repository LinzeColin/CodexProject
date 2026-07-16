# Adversarial review · ADP-S5-P04-T066｜Watchlist + Change-only Digest

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。

## 攻击向量
(a) 去重/重跑（键是否足以防重复、跨周期同内容、A→B→A 回退、两 watch 同条目、state 是否原地改）；(b) 无变化不打扰（是否真由 T026 content_hash 驱动、自造 noise-only 再渲染是否 0 通知、facet-only 变更是否被漏报）；(c) 可定位（locator 是否解析到真实变更版本、错版本/缺条目是否被拒、是否 stub）；(d) silence（有变化不发/无变化才发）；(e) 非空跑/负控制（每条款有判别控制、verifier 从工具而非 report 现推）；NOT_DEPLOYED（无网络/写/时钟/随机）。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
- **(a) 去重/重跑**：跨周期同内容→0 新（键不含 period，正确）；state 复制非原地改；两 watch 同条目→**独立键各自通知**；**A→B→A 回退**→回到旧 hash 键已 seen→抑制（完整性 gap，非验收违反）。
- **(b) 无变化不打扰**：复核者自造 footer/share/engagement/相对时间/utm+spm 追踪参数等 noise-only 再渲染→**全 0 通知**，content_hash 稳定，**真由 T026 驱动**；facet-only 变更（body 同、agency/doc_number 改）→hash 同→不通知（完整性 gap，非验收违反）。
- **(c) 可定位**：`notification_is_locatable` 对同条目 True、**改版本 False、缺条目 False**——**真判别非 stub**。
- **(d) silence**：匹配但全已见→no_change 静默（准确）；匹配无→静默；均正确。
- **(e)**：verifier 从**工具+fixture 现推**（不读 report JSON）；每条款判别控制齐（stateless re-emit 6 vs 去重 0；noise-only h1==h2 vs 真变 g1!=g2；locator 错版本 False）。确定性、无网络/时钟/随机/写。
- **判定**：三验收条款（重跑不重复 / 无变化不打扰 / 每条可定位）**均单向成立、有 load-bearing 判别控制、非空跑/作弊/错**。验收为单向（"无变化→不通知"、"通知→可定位"），**不声称"每变化→必通知"**，故漏报回退/facet-only 不违反验收。列 3 项**非致命 latent**。

## latent 的主动闭合（3 项）
1. **content_hash 键漏报 A→B→A 回退 + facet-only 变更**：与内容态去重设计一致——**已在 known_gaps 诚实披露**（"通知去重键"条 + "实质变化定义"条：回退/纯 facet 元数据重分类不触发，复用 T026 单一定义不分叉；若需另计属 T026 契约范围）。
2. **可定位控制只喂同周期、无法抓 stub 的 always-True**：**已加显式 always-False 负控制**——错版本 hash（sha256:deadbeef）与缺 canonical_id 均须被 `notification_is_locatable` 拒（实测双拒），证明第 3 条款控制**非 stub**。
3. **daily/weekly 共享 seen-set 会使 weekly 重跑变空**：**已在 known_gaps 披露**——daily 与 weekly 应各用独立 seen-set（或 weekly=daily 通知 rollup），分 cadence 落地由部署阶段负责；本任务单 seen-set 仅证幂等。

## 结论
复核 **CONFIRMED_SOUND**；三验收条款有判别负控制、非空跑，verifier 从工具现推。3 项非致命 latent 主动闭合（回退/facet 漏报披露、可定位 always-False 负控制、daily/weekly 分 cadence 披露）。复用 T026 单一"实质变化"定义不分叉。确定性、零副作用、不读时钟。实时无回归（live build_id b189d3cc0703 == T040）。**开启 S5-P04**。判定：**可交独立验证 / SHIP**。
