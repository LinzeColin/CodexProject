# TASK_REPORT · ADP-S5-P03-T063｜接入 DOI/Crossref/OpenAlex 等研究元数据增强

## 唯一目标（达成）
用 DOI/Crossref/OpenAlex 研究元数据**增强** arXiv 论文的身份、作者、机构、版本与引用图，**同时始终以原始论文（arXiv）为证据锚**。增强是**附加、带来源**的，**绝不替换或阻塞**原始论文。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：metadata adapters（crossref/openalex）+ dedup（预印本/期刊不混淆）+ degraded fallback（增强失败不阻塞原始论文）。
2. **允许修改文件**：`tools/research_metadata.py`（新）+ `evidence/ADP-S5-P03-T063/*` + 治理同步。**不改 worker/生产/registry/VERSION**。复用 T058 `entity_resolver`（作者/机构统一）。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。增强为附加只读层。
4. **基线**：main `f3f1db73`（T062 已合入）；fixture-backed adapters（无实时网络，本环境亦不可靠达 Crossref/OpenAlex）。
5. **验收**：预印本/期刊不混淆（含负控制：未确认 DOI 不得链为期刊版本；同题不得凭题合并）；增强失败不阻塞原始论文（含负控制：丢弃式管线会掉论文；原始证据零变更；非 AdapterError 崩溃亦不阻塞；变异 adapter 不能污染锚）。
6. **回滚**：`git revert <sha>`（只读增强库，生产未变更）。

## 交付物
- `tools/research_metadata.py` —— `make_crossref_adapter`/`make_openalex_adapter`（fixture-backed，返回增强 / None[未找到] / 抛 AdapterError[瞬时失败]）+ `enhance`（附加带来源增强；原始论文 deepcopy 为证据锚**永不变更**；任何 adapter 异常记为 failed 而**不阻塞**；adapter 收到 throwaway 副本，**不能污染锚**）+ `run_pipeline`（degraded fallback：失败不掉论文）+ `link_works`（预印本→期刊仅在 Crossref `has_preprint_arxiv_id==本 arxiv_id` 时链接，两版本**类型/证据各自独立不混淆**，未确认 DOI 不链）+ `resolve_authors`（复用 T058 跨 Crossref/OpenAlex 统一作者带来源）。
- `evidence/…/build_research_metadata.py`（fixtures：确认发表/未确认 DOI/同题诱饵/两处 adapter 失败）+ `research_metadata_report.json` + `test-results/{t063_verify.py, research_metadata_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/research_metadata_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 预印本/期刊不混淆**：确认发表的 work（arXiv 2401.00001）恰含**两个不同版本**——preprint（证据源=arxiv）+ journal（证据源=crossref，DOI 10.1038/…），二者**同 work_id 链接但证据 id 不同**；**preprint 从不被重标为 journal，journal 从不锚到 arXiv PDF**。**负控制**：未确认 DOI（2401.00002 的 `has_preprint`→别处）**不加**期刊版本（仅 preprint，DOI 作 unconfirmed 附着）；**判别力**：把该 DOI 改为确认→control 立即产生 journal 版本（证明确认门 load-bearing）；同题两篇（00001/00003）**不凭题合并**（不同 work）。
- **② 增强失败不阻塞原始论文**：5 篇入 → **5 篇出，blocked=0**（crossref 对 00004 瞬时失败、openalex 对 00005 失败）；每篇原始论文**逐字节未变更**、无增强泄漏进原证据、证据锚恒为 arXiv；失败被**如实记为 failed**（非静默 not_found），失败 adapter **不产出**任何增强。**负控制**：丢弃式管线只会留 2/5（证明保数非平凡）。**鲁棒性**：adapter 抛 **KeyError（非 AdapterError）**仍保全 5 篇并记 failed；**变异 adapter**（篡改 title/arxiv_id）**无法污染** PAPERS 或证据锚。
- **③ 作者/机构统一（复用 T058）**：Alice Chen 在 Crossref+OpenAlex 均现→统一为**一个实体带双源 provenance**；Alice/Bob/Carol **三位不同作者不混**。**机构同样统一**（`resolve_institutions`）：MIT 在 Crossref+OpenAlex 均现→**一个机构实体带双源 provenance**，MIT/Stanford 不混（「机构」是**真被跨源统一**，非仅附着）。**自描述确认标记**：`enhance` 在增强级打 `confirmed_publication`（00001=True/00002=False），`link_works` 依此链接。**引用信号**=OpenAlex references(2 条)+cited_by_count 作增强**附着**（非原证据），完整引用图属 T065。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 5 arXiv 原文 + Crossref/OpenAlex fixture 索引（确认/未确认/失败/同题诱饵）。Performance = 实时无回归。无 UI 改动；六主题保留（增强为库层，供研究集合视图 T064 消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**证据锚定的研究元数据增强**——论文身份/作者/机构/版本/引用图更完善，且**原始论文始终为证据**；预印本与期刊版本清晰区分不混淆；任一元数据源失败都不阻塞论文流。对齐 Elicit/Consensus/Scite 的研究元数据收益而不牺牲证据性。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = adapters + fixtures + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED；真实 Crossref/OpenAlex 调用成本由部署阶段门控）。

## Known gaps
见 `known_gaps.md`：fixture-backed（真实 Crossref/OpenAlex 调用/配额/速率由部署阶段接入）；作者消歧为精确 alias（同名不同人需 ORCID 强标识，已备注）；链接信号=Crossref preprint 关系（可扩展 DOI 双向/版本链）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = research_metadata_report.json。`benchmarks` = N/A（非性能任务）。

## 完成声明
```text
Task: ADP-S5-P03-T063
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/research_metadata.py(新) + T063 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: research_metadata_tests.txt —— 预印本/期刊不混淆(确认发表→preprint+journal双版本各自证据;未确认DOI不链;确认control产journal证判别;同题不合并);增强失败不阻塞(5入5出blocked=0;原证据零变更;KeyError不阻塞;变异adapter不污染;丢弃式管线只留2/5);作者跨源统一不混;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: DOI/Crossref/OpenAlex 研究元数据增强 + 预印本/期刊区分 + degraded fallback
Data/Performance/Visual: Data=5原文+Crossref/OpenAlex fixtures；Perf=实时无回归；Visual=六主题保留
Value: 证据锚定的研究元数据增强,原始论文始终为证据,预印本/期刊不混淆,失败不阻塞
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读增强库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
