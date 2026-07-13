import { useEffect, useMemo, useState } from "react";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { REVIEW_PERIOD_OPTIONS, buildReviewSummaryIteration, buildSummaryIterationClosure, reviewQuestionAnswerById } from "./summaryModels";
import { REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION, REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION, SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION, SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION } from "../../shared/atlas/constants";
import { DeltaStats, ReviewPeriodId } from "../../shared/atlas/contracts";
import { dedupeRecommendationItems, humanizeRecommendationTitle, humanizeStatement, recommendationMeta } from "../../shared/atlas/semanticHuman";
import { buildIterationHighlights, formatSigned, formatUpdatedAt } from "../../shared/atlas/utils";
import { EvidenceRefsDetails, MachineFieldDetails } from "../../shared/ui/display";
import { DeltaStrip, HumanOverviewPanel } from "../../shared/ui/primitives";



export function SummaryIterationView({
  atlas,
  nodes,
  deltaStats,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  deltaStats: DeltaStats;
}) {
  const recommendations = atlas.agent_recommendations;
  const updatedAt = formatUpdatedAt(recommendations?.generated_at || atlas.overview.generated_at);
  const highlights = useMemo(() => buildIterationHighlights(nodes, deltaStats), [nodes, deltaStats]);
  const [reviewPeriod, setReviewPeriod] = useState<ReviewPeriodId>("last_30_days");
  const reviewSummary = useMemo(
    () => buildReviewSummaryIteration(atlas, nodes, deltaStats, reviewPeriod),
    [atlas, nodes, deltaStats, reviewPeriod],
  );
  const summaryClosure = useMemo(() => buildSummaryIterationClosure(reviewSummary), [reviewSummary]);
  const dominantAnswer = reviewQuestionAnswerById(reviewSummary, "dominant_topics");
  const strengtheningAnswer = reviewQuestionAnswerById(reviewSummary, "strengthening_topics");
  const decliningAnswer = reviewQuestionAnswerById(reviewSummary, "declining_topics");
  const opportunityAnswer = reviewQuestionAnswerById(reviewSummary, "new_opportunities");
  const lowValueAnswer = reviewQuestionAnswerById(reviewSummary, "low_value_loops");
  const decisionAnswer = reviewQuestionAnswerById(reviewSummary, "decision_changes");
  const nextActionAnswer = reviewQuestionAnswerById(reviewSummary, "next_actions");
  const proposalAnswer = reviewQuestionAnswerById(reviewSummary, "proposal_decision");
  const schemaQuestionLine = reviewSummary.questions.map((item) => item.question).join(" / ");

  useEffect(() => {
    window.__memoryAtlasStage7Phase2 = () => ({
      runtimeVersion: REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION,
      reviewSchemaVersion: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
      questionCount: reviewSummary.questions.length,
      panelIds: reviewSummary.panelIds,
      iterationItemCount: reviewSummary.iteration.iteration_backlog.length,
      proposalCandidate: reviewSummary.proposal_candidate.should_generate,
      hasEvidenceRefs: reviewSummary.evidence_refs.length > 0,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    });
    return () => {
      delete window.__memoryAtlasStage7Phase2;
    };
  }, [reviewSummary]);

  useEffect(() => {
    window.__memoryAtlasStage8Phase1 = () => ({
      runtimeVersion: SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION,
      closureSchemaVersion: SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION,
      sourceReviewSchemaVersion: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
      panelIds: summaryClosure.panelIds,
      changeComparisonCount: summaryClosure.change_comparison.length,
      staleConflictSignalCount: summaryClosure.stale_conflict_signals.length,
      proposalCandidateCount: summaryClosure.proposal_candidates.length,
      proposalOnly: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
      proposalWrite: false,
    });
    return () => {
      delete window.__memoryAtlasStage8Phase1;
    };
  }, [summaryClosure]);

  return (
    <div
      className="summary-iteration-view visual-workspace review-summary-runtime"
      data-review-summary-iteration-runtime={REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION}
      data-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">总结与迭代</p>
          <h2>把当前记忆切片转成可更新的 Personalization、Agents.md 和 Memory 建议</h2>
        </div>
        <span>更新时间：{updatedAt}</span>
      </div>
      <section className="review-period-selector" data-review-period-selector="true" data-review-panel="review_period_selector">
        <label>
          <span>复盘窗口</span>
          <select value={reviewPeriod} onChange={(event) => setReviewPeriod(event.target.value as ReviewPeriodId)}>
            {REVIEW_PERIOD_OPTIONS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <p>{reviewSummary.time_window.label} · {reviewSummary.time_window.node_count.toLocaleString()} 条 redacted 节点</p>
      </section>
      <section
        className="review-session-output"
        data-review-output-schema={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
        data-proposal-candidate={String(reviewSummary.proposal_candidate.should_generate)}
        data-evidence-ref={reviewSummary.evidence_refs.join(",")}
      >
        <div className="panel-title-row">
          <h3>复盘会话输出</h3>
          <span>置信度：{reviewSummary.confidence}</span>
        </div>
        <p>默认层只回答八个复盘问题；schema、panel id 和 evidence refs 已收进高级详情。</p>
        <MachineFieldDetails title="高级详情：复盘 schema 与字段" className="review-machine-details">
          <p className="machine-field-help">
            review_schema_version={reviewSummary.review_schema_version}; dominant_topics; strengthening_topics;
            declining_topics; new_opportunities; low_value_loops; decision_changes; next_actions; proposal_candidate;
            evidence_refs; iteration_backlog. Questions: {schemaQuestionLine}
          </p>
          <div className="review-output-grid">
            <span>review_id：{reviewSummary.review_id}</span>
            <span>source_scope：{reviewSummary.source_scope}</span>
            <span>proposal_decision：{reviewSummary.proposal_candidate.proposal_decision}</span>
            <span>panels：{reviewSummary.panelIds.join(", ")}</span>
          </div>
        </MachineFieldDetails>
      </section>
      <DeltaStrip stats={deltaStats} compact />
      <div className="summary-signal-grid" aria-label="总结与迭代关键结论">
        {highlights.map((item) => (
          <SummarySignalCard key={item.label} label={item.label} value={item.value} note={item.note} />
        ))}
      </div>
      <section className="review-question-grid" aria-label="Review / Summary / Iteration 八个问题">
        <article className="review-question-card" data-review-question="dominant_topics" data-review-panel="theme_change_panel">
          <strong>{dominantAnswer.question}</strong>
          <p>{dominantAnswer.answer}</p>
          <EvidenceRefsDetails refs={dominantAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="strengthening_topics" data-review-panel="theme_change_panel">
          <strong>{strengtheningAnswer.question}</strong>
          <p>{strengtheningAnswer.answer}</p>
          <EvidenceRefsDetails refs={strengtheningAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="declining_topics" data-review-panel="theme_change_panel">
          <strong>{decliningAnswer.question}</strong>
          <p>{decliningAnswer.answer}</p>
          <EvidenceRefsDetails refs={decliningAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="new_opportunities" data-review-panel="opportunity_panel">
          <strong>{opportunityAnswer.question}</strong>
          <p>{opportunityAnswer.answer}</p>
          <EvidenceRefsDetails refs={opportunityAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="low_value_loops" data-review-panel="low_value_loop_panel">
          <strong>{lowValueAnswer.question}</strong>
          <p>{lowValueAnswer.answer}</p>
          <EvidenceRefsDetails refs={lowValueAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="decision_changes" data-review-panel="decision_change_panel">
          <strong>{decisionAnswer.question}</strong>
          <p>{decisionAnswer.answer}</p>
          <EvidenceRefsDetails refs={decisionAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="next_actions" data-review-panel="next_action_panel">
          <strong>{nextActionAnswer.question}</strong>
          <p>{nextActionAnswer.answer}</p>
          <EvidenceRefsDetails refs={nextActionAnswer.evidence_refs} />
        </article>
        <article className="review-question-card" data-review-question="proposal_decision" data-review-panel="proposal_decision_panel">
          <strong>{proposalAnswer.question}</strong>
          <p>{proposalAnswer.answer}</p>
          <EvidenceRefsDetails refs={proposalAnswer.evidence_refs} />
        </article>
      </section>
      <section className="review-runtime-panels" aria-label="Review / Summary / Iteration 运行面板">
        <article className="proposal-decision-panel" data-review-panel="proposal_decision_panel">
          <div className="panel-title-row">
            <h3>提案判断</h3>
            <span>{reviewSummary.proposal_candidate.target_type}</span>
          </div>
          <strong>{reviewSummary.proposal_candidate.should_generate ? "建议生成提案" : "暂不生成提案"}</strong>
          <p>{reviewSummary.proposal_candidate.reason}</p>
          <small>{reviewSummary.proposal_candidate.rollback_hint}</small>
        </article>
        <article className="iteration-backlog" data-review-panel="iteration_backlog">
          <div className="panel-title-row">
            <h3>迭代待办</h3>
            <span>{reviewSummary.iteration.review_again_at}</span>
          </div>
          <ol>
            {reviewSummary.iteration.iteration_backlog.map((item) => (
              <li key={item.item_id}>
                <strong>{item.title}</strong>
                <p>{item.why_it_matters}</p>
                <small>{item.next_step} · {item.acceptance_hint}</small>
              </li>
            ))}
          </ol>
        </article>
      </section>
      <section
        className="summary-closure-runtime"
        data-summary-iteration-closure-runtime={SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION}
        data-summary-closure-schema-version={SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION}
        data-source-review-schema-version={REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION}
      >
        <div className="panel-title-row">
          <h3>总结与迭代闭环</h3>
          <span>仅生成提案</span>
        </div>
        <p className="summary-closure-schema-line">默认显示变化、冲突和提案候选的中文解释；schema 与机器字段在高级详情中核验。</p>
        <MachineFieldDetails title="高级详情：闭环 schema 与机器字段" className="summary-closure-machine-details">
          <p className="machine-field-help">
            closure_schema_version={summaryClosure.closure_schema_version}; source_review_schema_version={summaryClosure.source_review_schema_version};
            change_comparison; stale_conflict_signals; proposal_candidates; requires_conflict_check; requires_agent_or_human_apply.
            {summaryClosure.closure_summary}
          </p>
        </MachineFieldDetails>
        <div className="summary-closure-grid">
          <article className="summary-closure-card" data-summary-closure-panel="change_comparison">
            <div className="panel-title-row">
              <h4>变化对比</h4>
              <span>{summaryClosure.change_comparison.length} 条信号</span>
            </div>
            <ol>
              {summaryClosure.change_comparison.map((item) => (
                <li key={item.signal_id}>
                  <strong>{item.title}</strong>
                  <p>{formatSigned(item.delta)} · 当前 {item.current_count} / 上期 {item.previous_count}</p>
                  <small>{item.summary}</small>
                  <EvidenceRefsDetails refs={item.evidence_refs} />
                </li>
              ))}
            </ol>
          </article>
          <article className="summary-closure-card" data-summary-closure-panel="stale_conflict_signals">
            <div className="panel-title-row">
              <h4>过期与冲突信号</h4>
              <span>{summaryClosure.stale_conflict_signals.length} 条检查</span>
            </div>
            <ol>
              {summaryClosure.stale_conflict_signals.map((item) => (
                <li key={item.signal_id} data-summary-signal-type={item.signal_type}>
                  <strong>{item.signal_type}:{item.severity} · {item.title}</strong>
                  <p>{item.summary}</p>
                  <small>{item.proposal_hint} · {item.rollback_hint}</small>
                </li>
              ))}
            </ol>
          </article>
        </div>
        <article className="summary-closure-proposals" data-summary-closure-panel="proposal_candidates">
          <div className="panel-title-row">
            <h4>提案候选</h4>
            <span>{summaryClosure.proposal_candidates.length} 个候选</span>
          </div>
          <div>
            {summaryClosure.proposal_candidates.map((item) => (
              <section key={item.proposal_id}>
                <strong>{item.title}</strong>
                <p>{item.reason}</p>
                <small>需要冲突检查：{item.requires_conflict_check ? "是" : "否"}；应用方式：人工或受控代理；证据引用 {item.evidence_refs.length.toLocaleString()} 条</small>
                <MachineFieldDetails title="高级详情：提案候选字段" className="inline-machine-field-details">
                  <p className="machine-field-help">
                    proposal_id={item.proposal_id}; target_type={item.target_type}; requires_conflict_check={String(item.requires_conflict_check)};
                    requires_agent_or_human_apply={String(item.requires_agent_or_human_apply)}; evidence_refs={item.evidence_refs.join(" / ")}
                  </p>
                </MachineFieldDetails>
              </section>
            ))}
          </div>
        </article>
        <div className="summary-closure-safety">
          <span>仅生成提案：是</span>
          <span>直接写长期记忆：否</span>
          <span>包含 raw 私有数据：否</span>
          <span>前端写入 proposal：否</span>
        </div>
      </section>
      <HumanOverviewPanel nodes={nodes} deltaStats={deltaStats} />
      <section className="iteration-panels" aria-label="给 ChatGPT 和 Codex 使用的更新建议">
        <AgentRecommendationsPanel atlas={atlas} />
        <ConfigMemoryPanel atlas={atlas} updatedAt={updatedAt} />
      </section>
    </div>
  );
}



export function SummarySignalCard({ label, value, note }: { label: string; value: string | number; note: string }) {
  return (
    <article className="summary-signal-card">
      <span>{label}</span>
      <strong>{typeof value === "number" ? value.toLocaleString() : value}</strong>
      <p>{note}</p>
    </article>
  );
}



export function AgentRecommendationsPanel({ atlas }: { atlas: MemoryAtlas }) {
  const recommendations = atlas.agent_recommendations;
  if (!recommendations) {
    return null;
  }
  return (
    <section className="agent-recommendations" aria-label="建议写入 ChatGPT 与 Codex 的内容">
      <div className="panel-title-row">
        <h3>Personalization / Agents.md 建议</h3>
        <span>{formatUpdatedAt(recommendations.generated_at)}</span>
      </div>
      <div className="recommendation-columns">
        <RecommendationBucket title="Memory / Personalization" section={recommendations.memory} />
        <RecommendationBucket title="Agents.md / 执行规则" section={recommendations.meta_data} />
      </div>
    </section>
  );
}



export function ConfigMemoryPanel({ atlas, updatedAt }: { atlas: MemoryAtlas; updatedAt: string }) {
  const recommendations = atlas.agent_recommendations;
  const memoryCurrent = recommendations?.memory.current ?? [];
  const metaCurrent = recommendations?.meta_data.current ?? [];
  const configItems = [
    {
      title: "config.toml",
      statement: "保留中文优先、真实验证、低上下文成本、每轮输出进度/风险/下一步；写库必须走提案与版本回滚。",
      count: metaCurrent.length,
    },
    {
      title: "Memory",
      statement: "优先装载核心画像、长期偏好、项目历史、决策日志和回答规则；短期信息保留但低权重召回。",
      count: memoryCurrent.length,
    },
    {
      title: "新增/删除/修改",
      statement: `新增 ${recommendations?.memory.added.length ?? 0} / 修改 ${recommendations?.memory.modified.length ?? 0} / 降权 ${recommendations?.memory.deleted.length ?? 0}；Meta 同步显示在上方。`,
      count: (recommendations?.memory.added.length ?? 0) + (recommendations?.memory.modified.length ?? 0) + (recommendations?.memory.deleted.length ?? 0),
    },
  ];
  return (
    <section className="config-memory-panel" aria-label="config.toml 和 Memory 建议">
      <div className="panel-title-row">
        <h3>config.toml / Memory</h3>
        <span>更新时间：{updatedAt}</span>
      </div>
      <div className="config-memory-grid">
        {configItems.map((item) => (
          <article key={item.title}>
            <strong>{item.title}</strong>
            <p>{item.statement}</p>
            <small>{item.count.toLocaleString()} 条相关建议</small>
          </article>
        ))}
      </div>
    </section>
  );
}



export function RecommendationBucket({
  title,
  section,
}: {
  title: string;
  section: NonNullable<MemoryAtlas["agent_recommendations"]>["memory"];
}) {
  return (
    <article className="recommendation-bucket">
      <strong>{title}</strong>
      <RecommendationList label="新增" items={section.added} />
      <RecommendationList label="修改" items={section.modified.map((item) => item.after)} />
      <RecommendationList label="降权/不再默认使用" items={section.deleted} />
      <RecommendationList label="当前有效" items={section.current} limit={6} />
    </article>
  );
}



export function RecommendationList({
  label,
  items,
  limit = 4,
}: {
  label: string;
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>;
  limit?: number;
}) {
  const displayItems = useMemo(() => dedupeRecommendationItems(items).slice(0, limit), [items, limit]);
  return (
    <div className="recommendation-list">
      <span>{label}</span>
      {displayItems.length ? (
        <ul>
          {displayItems.map(({ item, duplicateCount }) => (
            <li key={`${label}-${item.id}`}>
              <b>{humanizeRecommendationTitle(item.title)}</b>
              <small>{humanizeStatement(item.statement)}</small>
              <em>{recommendationMeta(item, duplicateCount)}</em>
            </li>
          ))}
        </ul>
      ) : (
        <p>暂无</p>
      )}
    </div>
  );
}
