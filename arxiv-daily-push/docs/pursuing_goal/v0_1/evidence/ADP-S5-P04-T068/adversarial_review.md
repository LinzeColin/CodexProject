# Adversarial review · ADP-S5-P04-T068｜Knowledge Validity + 131 项收益对齐回归

独立对抗复核（general-purpose skeptic），职责是**证伪**验收（找空洞/作弊/误导），非确认。**特别要求复核 131 项 registry 的诚实性**（虚标/填充即为空洞）。

## 攻击向量
(a) validity clock（是否哈希驱动非时钟、噪声不churn、实质变→needs_review、删→invalid、revalidate重绑新哈希、A→B→A回退、是否原地改）；(b) 131 计数 + 无 unknown/no-owner（独立计数、closed vocab、_owner_ok 边界）；(c) **131 诚实性/是否填充**（真实竞品收益？delivered 是否虚标未建功能？逐项对照被引任务）；(d) 证据要求（delivered/partial 带 evidence、planned/na 带 note）；(e) 非空跑（gate 移除即失败的负控制、verifier 从工具现推）；NOT_DEPLOYED。

## 复核结论：CONFIRMED_SOUND（hole=null, severity=none）
- **(a) validity**：确认**哈希驱动非时钟**；噪声再渲染共享 v1 content_hash（strip_noise 去「责任编辑：张三」）→ 保 valid **无 churn**；实质 body 变→needs_review+reason；删→invalid；revalidate 重绑 **v2 新哈希**；**A→B→A 回退正确回 valid**（无状态哈希比较）；check_validity **不原地改**调用方。
- **(b) 计数**：独立求和 16+11+14+15+14+13+9+16+23=**131**，0 重复 benefit 文本，131 distinct (competitor,benefit)；全状态 closed vocab 无 unknown；`_owner_ok` 对 'No-Owner'/'UNKNOWN'/'  unassigned '/''/'   '/None **全拒**；`clean` 需三条全净。
- **(c) 诚实性**：抽查被引工具——T064 抽 method/sample/result 带源 span、T065 support/counter/mention 由上下文非标题、T063 增强/去重/预印本-期刊、T066 change-only digest、T067 library provenance、T060/T061 检索、T057-T059 事件/实体/关系——**每个被引任务都真实存在（工具 + 证据目录）**；状态**保守降级** partial/planned 反映 NOT_DEPLOYED。
- **(d)(e)**：delivered/partial 强制 evidence_ref；verifier 从 `build_registry()` 现推（非 emitted JSON），负控制注入 unknown-status/no-owner/blank-owner/bad-token **全被抓**，含噪声无 churn + 哈希判别。确认工具无网络/写/时钟/随机；两次运行字节一致；emitted JSON == build_registry()。
- **判定**：两验收条款**真成立、非空跑/作弊/错、131 registry 诚实非填充**。列 3 项**非致命**。

## latent 的主动闭合（复核前 5 项 + 复核后 3 项）
- **诚实降级（共 7 项 delivered→partial）**：复核前已降 5 项（相似图 Graph of similar papers、seed-map Build/Citation map from a seed、topic timeline、as-of map——substrate[T065/T062]存在但非该具体收益）；**复核后再降 2 项**（Litmaps「Email/weekly digest」——digest 已算但**无邮件投递**属生产；General「Cost/benefit quantified」——**成本已量化、收益为枚举非量化**）。现 by_status = delivered 92 / partial 21 / planned 15 / not_applicable 3，**更诚实**。
- **gate 加强（note 要求）**：复核指出 parity_report 只强制 delivered/partial 带 evidence、未强制 planned/not_applicable 带 note——**已加 `planned_or_na_missing_note` 检查并入 clean**；verifier 加控制（note-less planned 被抓）。
- **emitted 工件防陈旧**：复核指出 verifier 从 build_registry 现推、忽略 emitted parity_registry_131.json（正确金标准，但陈旧工件不被抓）——**已加 verifier 检查 emitted JSON == build_registry()**（陈旧即失败）。

## 结论
复核 **CONFIRMED_SOUND**；两验收条款（源变自动失效/重学、131 项无未知/无人负责）有 load-bearing 判别负控制（注入 unknown/no-owner/blank/bad-token/note-less 全抓）、非空跑，verifier 从工具现推。**131 registry 经复核诚实非填充**；共 7 项过度 delivered 主动降级 partial，gate 加 note 要求 + emitted 防陈旧。复用 T026 content_hash 单一实质变化定义。确定性、零副作用、不读时钟。实时无回归（live build_id b189d3cc0703 == T040）。**收尾 S5-P04 与整个 Stage S5**。判定：**可交独立验证 / SHIP**。
