# Known gaps · ADP-S5-P03-T063

- **fixture-backed adapters（非实时网络）**：本任务是 **NOT_DEPLOYED 只读增强库**，`make_crossref_adapter`/`make_openalex_adapter` 由**确定性 fixture 索引**驱动，不打真实 Crossref/OpenAlex（本机环境亦不可靠达该 API）。真实网络调用、API key/配额、速率限制、缓存与重试由**部署阶段**接入（各自的门）；本任务提供其确定性契约与 degraded-fallback 骨架。
- **作者/机构统一=精确 alias 全局池（T058）**：`resolve_authors` 与 `resolve_institutions` 复用 T058 `entity_resolver.resolve`，按**共享精确 alias** 聚类、逐源 provenance、**不做模糊子串合并**（防过并）。二者是**全局跨源身份池**（作者/机构身份本就是全局的），**非按论文归属**——即把 Crossref+OpenAlex 中同名作者/机构统一为一实体，而非"把此增强的作者判给此篇 arXiv"。因此**同名不同人**（如两位 "J. Smith"）或同名不同校若无更强标识会被并为一实体；真实系统应以 **ORCID / OpenAlex author id / ROR** 作强标识消歧——fixtures 已带 orcid/ror 字段，强标识消歧留待部署阶段 / T065。反之不同拼写的同一人（无共享 alias）暂不自动统一。
- **未确认增强的作者入全局池**：未确认发表关系的 Crossref 增强（`confirmed_publication=False`，见 `enhance` 在增强级打的自描述标记）其作者仍进入全局作者池——因为该池**不做按篇归属**，故不会误把其作者判给此 arXiv 篇（`link_works` 也不把未确认 DOI 链为本 work 的期刊版本）。**按篇、确认门控的作者归属**（只把已确认发表的作者判给该 work）留待 T064/T065。
- **预印本→期刊链接信号**：链接仅在 Crossref 记录 `has_preprint_arxiv_id == 本 arxiv_id`（即 Crossref 的 preprint 关系明确指向本预印本）时成立——**证据驱动、非凭标题猜测**。未确认的 DOI 只作 `unconfirmed_doi` 附着、**不**链为期刊版本（防混淆）。可扩展的更强信号（DOI 双向 relation、arXiv `journal_ref`、版本链 v1/v2）留待后续。
- **引用图**：OpenAlex `references`/`cited_by_count` 作**增强字段附着**（带来源），非原始证据；构建完整跨库引用图（含 support/counter 语境）是 **T065**（引用支持/反驳/关系证据）的范围。
- **增强附加不改原证据**：`enhance` 对原始论文 deepcopy 为证据锚、adapter 只收 throwaway 副本、任何 adapter 异常（含非 AdapterError）记 failed 而不阻塞——保证「增强失败不阻塞原始论文」在真实多样失败模式下**鲁棒**。代价：adapter 内的真实 bug 会被记为 failed 而非高声崩溃（生产可用性优先，failed 状态供可观测）。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。后继 T064（Research Set/筛选/结构化比较）、T065（引用支持/反驳/关系证据）在本增强层之上扩展。
