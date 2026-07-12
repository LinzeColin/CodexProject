import { CalendarDays, Crosshair, FilterX, Orbit, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { uniqueSorted } from "../../data/atlas";
import type { AtlasFilters, AtlasNode, MemoryAtlas, ViewKey } from "../../types";
import { SEARCH_2_0_RUNTIME_VERSION, SEARCH_2_0_SESSION_SUMMARY_VERSION } from "../../shared/atlas/constants";
import { DeltaStats, Search2Filters, Search2ImportanceFilter, Search2RecencyFilter, Search2Result, Search2TierFilter } from "../../shared/atlas/contracts";
import { buildSearch2Results, buildSearch2SessionSummary, search2FilterStateLabel } from "../../shared/atlas/searchModels";
import { buildSearchVisualRows, humanThemeLabel } from "../../shared/atlas/semanticHuman";
import { MachineFieldDetails } from "../../shared/ui/display";
import { DeltaStrip, HumanOverviewPanel, MiniBarList } from "../../shared/ui/primitives";



export function SearchReview({
  atlas,
  filters,
  nodes,
  deltaStats,
  onSelectNode,
  onSwitchView,
}: {
  atlas: MemoryAtlas;
  filters: AtlasFilters;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
  onSwitchView: (view: ViewKey) => void;
}) {
  const [searchFilters, setSearchFilters] = useState<Search2Filters>(() => ({
    query: filters.query,
    tier: "all",
    topic: "all",
    recency: "all",
    importance: "all",
    evidenceOnly: true,
  }));
  useEffect(() => {
    setSearchFilters((current) => (
      current.query === filters.query ? current : { ...current, query: filters.query }
    ));
  }, [filters.query]);
  const searchVisualRows = useMemo(() => buildSearchVisualRows(nodes), [nodes]);
  const topicOptions = useMemo(() => uniqueSorted(nodes.map((node) => humanThemeLabel(node))).slice(0, 24), [nodes]);
  const searchResults = useMemo(() => buildSearch2Results(atlas, nodes, searchFilters), [atlas, nodes, searchFilters]);
  const sessionSummary = useMemo(() => buildSearch2SessionSummary(searchResults, searchFilters.query), [searchFilters.query, searchResults]);
  const visibleResults = searchResults.slice(0, 50);

  useEffect(() => {
    window.__memoryAtlasStage7Phase1 = () => ({
      runtimeVersion: SEARCH_2_0_RUNTIME_VERSION,
      sessionSummaryVersion: SEARCH_2_0_SESSION_SUMMARY_VERSION,
      query: searchFilters.query,
      resultCount: searchResults.length,
      hasMatchedReason: searchResults.some((result) => result.matched_reason.length > 0),
      hasEvidenceRefs: searchResults.some((result) => result.evidence_refs.length > 0),
      jumpActions: ["starfield", "river", "inspector"],
      zeroResultRecoveryVisible: searchResults.length === 0,
      proposalCandidateCount: searchResults.filter((result) => result.proposal_candidate).length,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage7Phase1;
    };
  }, [searchFilters.query, searchResults]);

  function updateSearchFilter(patch: Partial<Search2Filters>) {
    setSearchFilters((current) => ({ ...current, ...patch }));
  }

  function resetSearchFilters() {
    setSearchFilters({
      query: "",
      tier: "all",
      topic: "all",
      recency: "all",
      importance: "all",
      evidenceOnly: true,
    });
  }

  function jumpToSearchTarget(result: Search2Result, target: "starfield" | "river" | "inspector") {
    onSelectNode(result.node);
    if (target === "starfield") onSwitchView("galaxy");
    if (target === "river") onSwitchView("timeline");
  }

  return (
    <div className="search-review search-2-runtime" data-search-2-0-runtime={SEARCH_2_0_RUNTIME_VERSION}>
      <DeltaStrip stats={deltaStats} compact />
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="search-2-controls" aria-label="Search 2.0 query_input">
        <label className="search-2-query">
          <span>query_input</span>
          <div className="search-2-input-frame">
            <Search size={16} />
            <input
              data-search-query-input="true"
              value={searchFilters.query}
              onChange={(event) => updateSearchFilter({ query: event.target.value })}
              placeholder="搜索主题、层级、行动、证据"
            />
          </div>
        </label>
        <div className="search-2-filter-grid">
          <label>
            <span>tier</span>
            <select value={searchFilters.tier} onChange={(event) => updateSearchFilter({ tier: event.target.value as Search2TierFilter })}>
              <option value="all">all</option>
              <option value="core_profile">core_profile</option>
              <option value="project">project</option>
              <option value="decision">decision</option>
              <option value="workflow">workflow</option>
              <option value="knowledge">knowledge</option>
              <option value="opportunity">opportunity</option>
              <option value="stale">stale</option>
            </select>
          </label>
          <label>
            <span>topic</span>
            <select value={searchFilters.topic} onChange={(event) => updateSearchFilter({ topic: event.target.value })}>
              <option value="all">all</option>
              {topicOptions.map((topic) => (
                <option key={topic} value={topic}>{topic}</option>
              ))}
            </select>
        </label>
        <label>
            <span>时效</span>
            <select value={searchFilters.recency} onChange={(event) => updateSearchFilter({ recency: event.target.value as Search2RecencyFilter })}>
              <option value="all">全部</option>
              <option value="recent">近期</option>
              <option value="active">活跃</option>
              <option value="stale">过期</option>
              <option value="archival">归档</option>
            </select>
          </label>
          <label>
            <span>重要性</span>
            <select value={searchFilters.importance} onChange={(event) => updateSearchFilter({ importance: event.target.value as Search2ImportanceFilter })}>
              <option value="all">全部</option>
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">关键</option>
            </select>
          </label>
          <label className="search-2-checkbox">
            <input
              type="checkbox"
              checked={searchFilters.evidenceOnly}
              onChange={(event) => updateSearchFilter({ evidenceOnly: event.target.checked })}
            />
            <span>仅看有证据结果</span>
          </label>
          <button className="search-2-reset" onClick={resetSearchFilters} type="button">
            <FilterX size={14} />
            <span>重置</span>
          </button>
        </div>
        <div
          className="search-2-filter-state"
          data-search-filter-state="search_2_0"
          data-result-count={searchResults.length}
          data-evidence-only={String(searchFilters.evidenceOnly)}
        >
          <span>筛选状态</span>
          <b>{searchResults.length.toLocaleString()} 条结果</b>
          <small>{search2FilterStateLabel(searchFilters)}</small>
        </div>
      </section>
      <section className="search-visual-summary" aria-label="搜索结果视觉摘要">
        <div className="panel-title-row">
          <h3>当前结果分布</h3>
          <span>{searchResults.length.toLocaleString()} 条</span>
        </div>
        <div className="search-topic-bars">
          <MiniBarList title="高频主题" rows={searchVisualRows.topics} />
          <MiniBarList title="记忆层级" rows={searchVisualRows.tiers} />
          <MiniBarList title="近期/决策" rows={searchVisualRows.signals} />
        </div>
      </section>
      <section
        className="search-2-session-summary"
        data-search-session-summary={SEARCH_2_0_SESSION_SUMMARY_VERSION}
        data-proposal-candidate={String(sessionSummary.proposal_candidate)}
      >
        <div className="panel-title-row">
          <h3>搜索会话摘要</h3>
          <span>{sessionSummary.result_count.toLocaleString()} 条结果</span>
        </div>
        <p>默认只看结果数量、分布和下一步；会话字段已收进高级详情。</p>
        <MachineFieldDetails title="高级详情：搜索会话字段" className="search-machine-details">
          <p className="machine-field-help">默认折叠。这里给 agent 核验 query、dominant topics、missing evidence 和 proposal candidate，不作为默认阅读层。</p>
          <dl>
            <div><dt>query / 查询词</dt><dd>{sessionSummary.query || "all redacted memory"}</dd></div>
            <div><dt>dominant_topics / 主导主题</dt><dd>{sessionSummary.dominant_topics.join(" / ") || "none"}</dd></div>
            <div><dt>high_importance_hits / 高重要命中</dt><dd>{sessionSummary.high_importance_hits.join(" / ") || "none"}</dd></div>
            <div><dt>stale_or_black_hole_hits / 过期或低价值命中</dt><dd>{sessionSummary.stale_or_black_hole_hits.join(" / ") || "none"}</dd></div>
            <div><dt>missing_evidence / 缺证据项</dt><dd>{sessionSummary.missing_evidence.join(" / ") || "none"}</dd></div>
            <div><dt>next_step / 下一步</dt><dd>{sessionSummary.next_step}</dd></div>
            <div><dt>proposal_candidate / 提案候选</dt><dd>{sessionSummary.proposal_candidate ? "true" : "false"}</dd></div>
          </dl>
        </MachineFieldDetails>
      </section>
      <div className="writeback-banner">
        <strong>写回策略</strong>
        <span>Search 2.0 只产生 proposal_candidate 判断和 Inspector 跳转；任何改动仍必须走 proposal-only handoff，不直接写长期记忆。</span>
      </div>
      {visibleResults.length ? (
        <section className="search-2-result-list" aria-label="Search 2.0 result_list">
          {visibleResults.map((result) => (
            <article
              className="search-2-result-card"
              data-search-result="true"
              data-result-id={result.result_id}
              data-result-tier={result.tier}
              data-result-topic={result.topic}
              data-result-recency={result.recency}
              data-result-importance={result.importance}
              data-matched-reason={result.matched_reason}
              data-evidence-ref={result.evidence_refs.join(",")}
              data-proposal-candidate={String(result.proposal_candidate)}
              key={result.result_id}
            >
              <header>
                <div>
                  <strong>{result.title}</strong>
                  <span>{result.source} / {result.tier} / {result.topic}</span>
                </div>
                <b>{result.importance}</b>
              </header>
              <p>{result.summary}</p>
              <MachineFieldDetails title="高级详情：结果字段" className="search-2-result-schema inline-machine-field-details">
                <dl>
                  <div><dt>matched_reason / 匹配原因</dt><dd>{result.matched_reason}</dd></div>
                  <div><dt>evidence_refs / 证据引用</dt><dd>{result.evidence_refs.join(" / ")}</dd></div>
                  <div><dt>proposal_candidate / 提案候选</dt><dd>{result.proposal_candidate ? "true" : "false"}</dd></div>
                </dl>
              </MachineFieldDetails>
              <div className="search-2-result-actions" aria-label="搜索结果操作">
                <button
                  data-search-jump="starfield"
                  data-starfield-target={result.jump_to_starfield}
                  onClick={() => jumpToSearchTarget(result, "starfield")}
                  type="button"
                >
                  <Orbit size={14} />
                  <span>跳到星图</span>
                </button>
                <button
                  data-search-jump="river"
                  data-river-target={result.jump_to_river}
                  onClick={() => jumpToSearchTarget(result, "river")}
                  type="button"
                >
                  <CalendarDays size={14} />
                  <span>跳到时间河</span>
                </button>
                <button
                  data-search-jump="inspector"
                  data-inspector-target={result.open_inspector}
                  onClick={() => jumpToSearchTarget(result, "inspector")}
                  type="button"
                >
                  <Crosshair size={14} />
                  <span>同步详情</span>
                </button>
              </div>
            </article>
          ))}
        </section>
      ) : (
        <section className="search-2-zero-recovery" data-zero-result-recovery="search_2_0">
          <div className="panel-title-row">
            <h3>无结果恢复</h3>
            <span>0 条</span>
          </div>
          <ul>
            <li>扩大查询：减少关键词或改用主题词。</li>
            <li>移除筛选：放宽层级、主题、时效、重要性或仅证据限制。</li>
            <li>相关主题：回到全部主题后查看相邻主题。</li>
            <li>过期/归档：切换过期或归档记忆查找历史线索。</li>
            <li>后续复盘提示：总结与迭代只作为复盘入口，本 phase 不执行提案应用。</li>
          </ul>
        </section>
      )}
    </div>
  );
}
