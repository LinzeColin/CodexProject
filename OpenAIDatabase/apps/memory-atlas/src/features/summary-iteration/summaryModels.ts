import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode, MemoryAtlas } from "../../types";
import { REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION, SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION } from "../../shared/atlas/constants";
import { DeltaStats, ReviewIterationItem, ReviewNextAction, ReviewPanelId, ReviewPeriodId, ReviewQuestionAnswer, ReviewQuestionId, ReviewSignalRow, ReviewSummaryIterationOutput, SummaryClosureChangeRow, SummaryClosureProposalCandidate, SummaryClosureSignal, SummaryIterationClosureOutput } from "../../shared/atlas/contracts";
import { buildSearch2EvidenceRefs, search2ImportanceForNode } from "../../shared/atlas/searchModels";
import { compactThemeLabel, countBy, humanCategoryLabel, humanNodeDisplayTitle, humanThemeLabel, humanizeStatement, recommendedActionForNode, topRows } from "../../shared/atlas/semanticHuman";
import { addDays, formatSigned, isNodeBetween, maxNodeDate, parseDay, toDayKey } from "../../shared/atlas/utils";



export const REVIEW_PERIOD_OPTIONS: Array<{ id: ReviewPeriodId; label: string; days: number | null }> = [
  { id: "last_30_days", label: "最近 30 天", days: 30 },
  { id: "last_90_days", label: "最近 90 天", days: 90 },
  { id: "all", label: "全部 redacted snapshot", days: null },
];



export const REVIEW_PANEL_IDS: ReviewPanelId[] = [
  "review_period_selector",
  "theme_change_panel",
  "opportunity_panel",
  "low_value_loop_panel",
  "decision_change_panel",
  "next_action_panel",
  "proposal_decision_panel",
  "iteration_backlog",
];



export function buildReviewSummaryIteration(
  atlas: MemoryAtlas,
  nodes: AtlasNode[],
  deltaStats: DeltaStats,
  periodId: ReviewPeriodId,
): ReviewSummaryIterationOutput {
  const latest = parseDay(deltaStats.latestDate) ?? parseDay(atlas.contribution.range_end) ?? maxNodeDate(nodes) ?? new Date();
  const period = REVIEW_PERIOD_OPTIONS.find((option) => option.id === periodId) ?? REVIEW_PERIOD_OPTIONS[0];
  const start = period.days === null ? parseDay(atlas.contribution.range_start) ?? maxNodeDate(nodes) ?? latest : addDays(latest, -(period.days - 1));
  const scopedNodes = period.days === null ? nodes : nodes.filter((node) => isNodeBetween(node, start, latest));
  const reviewNodes = scopedNodes.length ? scopedNodes : nodes;
  const dominant_topics = reviewTopicRows(atlas, reviewNodes, 4);
  const strengthening_topics = reviewStrengtheningRows(atlas, nodes, latest);
  const declining_topics = reviewDecliningRows(atlas, nodes, latest);
  const new_opportunities = reviewOpportunityRows(atlas, reviewNodes);
  const low_value_loops = reviewLowValueLoopRows(atlas, reviewNodes);
  const decision_changes = reviewDecisionRows(atlas, reviewNodes);
  const evidence_refs = reviewEvidenceRefs(atlas, [
    ...dominant_topics,
    ...strengthening_topics,
    ...declining_topics,
    ...new_opportunities,
    ...low_value_loops,
    ...decision_changes,
  ]);
  const next_actions = reviewNextActions(atlas, reviewNodes, evidence_refs);
  const proposalReason = low_value_loops.length
    ? `发现 ${low_value_loops[0].title}，建议生成 proposal-only update candidate，先处理低价值循环。`
    : new_opportunities.length
      ? `发现 ${new_opportunities[0].title}，可以生成 proposal-only update candidate 汇总机会。`
      : "本期没有强制写回条件，保留 review-only note 等待下一轮复盘。";
  const shouldGenerateProposal = low_value_loops.some((item) => item.count > 0) || new_opportunities.some((item) => item.count > 0);
  const iteration_backlog = reviewIterationBacklog(next_actions, low_value_loops, new_opportunities, dominant_topics);
  const review_again_at = toDayKey(addDays(latest, 7));
  const output: ReviewSummaryIterationOutput = {
    review_id: `review_${periodId}_${toDayKey(latest)}`,
    review_schema_version: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
    time_window: {
      period_id: periodId,
      label: `${period.label}（${toDayKey(start)} 至 ${toDayKey(latest)}）`,
      range_start: toDayKey(start),
      range_end: toDayKey(latest),
      node_count: reviewNodes.length,
    },
    source_scope: "redacted_atlas_snapshot",
    dominant_topics,
    strengthening_topics,
    declining_topics,
    new_opportunities,
    low_value_loops,
    decision_changes,
    next_actions,
    proposal_candidate: {
      should_generate: shouldGenerateProposal,
      proposal_decision: shouldGenerateProposal ? "generate_proposal" : "review_only",
      target_type: shouldGenerateProposal ? "memory_update_candidate" : "review_only_note",
      reason: proposalReason,
      rollback_hint: "proposal-only 交接；若人工复核不成立，丢弃 proposal 草稿即可，不会修改长期记忆。",
      requires_conflict_check: true,
      requires_agent_or_human_apply: true,
    },
    evidence_refs,
    confidence: reviewNodes.length >= 20 && evidence_refs.length >= 3 ? "high" : reviewNodes.length >= 5 ? "medium" : "low",
    iteration: {
      iteration_backlog,
      review_again_at,
      proposal_only: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
    },
    questions: [],
    panelIds: REVIEW_PANEL_IDS,
  };
  output.questions = buildReviewQuestions(output);
  return output;
}



export function buildSummaryIterationClosure(review: ReviewSummaryIterationOutput): SummaryIterationClosureOutput {
  const change_comparison: SummaryClosureChangeRow[] = [
    ...review.strengthening_topics.slice(0, 3).map((row, index) =>
      summaryClosureChangeRow(row, `strengthening:${index}`, Math.max(row.count, 0), 0),
    ),
    ...review.declining_topics.slice(0, 3).map((row, index) =>
      summaryClosureChangeRow(row, `declining:${index}`, 0, Math.max(row.count, 0)),
    ),
  ];
  if (change_comparison.length < 3) {
    review.dominant_topics.slice(0, 3 - change_comparison.length).forEach((row, index) => {
      change_comparison.push(summaryClosureChangeRow(row, `dominant:${index}`, Math.max(row.count, 0), Math.max(row.count, 0)));
    });
  }

  const staleSignals = review.low_value_loops.slice(0, 2).map<SummaryClosureSignal>((row, index) => ({
    signal_id: `stale:${index}`,
    signal_type: "stale",
    severity: row.count > 0 ? "high" : "low",
    title: row.title,
    summary: row.summary,
    evidence_refs: row.evidence_refs.length ? row.evidence_refs : review.evidence_refs.slice(0, 2),
    proposal_hint: row.count > 0 ? "生成 proposal-only cleanup candidate，人工确认后再降权、合并或删除。" : "保留观察，不生成直接写回。",
    rollback_hint: "如果复核发现 stale 判断不成立，丢弃 candidate；长期记忆不会被前端修改。",
  }));
  const conflictSignals = review.decision_changes.slice(0, 2).map<SummaryClosureSignal>((row, index) => ({
    signal_id: `conflict:${index}`,
    signal_type: "conflict",
    severity: row.count > 0 ? "medium" : "low",
    title: row.title,
    summary: row.summary,
    evidence_refs: row.evidence_refs.length ? row.evidence_refs : review.evidence_refs.slice(0, 2),
    proposal_hint: "进入人工 conflict check；只有确认新决策覆盖旧背景后才生成长期记忆修改。",
    rollback_hint: "若冲突未确认，保留 review-only note，不写 proposal queue 或长期记忆。",
  }));
  const stale_conflict_signals = [...staleSignals, ...conflictSignals].slice(0, 4);

  const proposal_candidates = review.next_actions.slice(0, 3).map<SummaryClosureProposalCandidate>((action, index) => ({
    proposal_id: `summary_closure_candidate:${index + 1}`,
    title: action.title,
    target_type: review.proposal_candidate.target_type,
    reason: action.reason,
    evidence_refs: action.evidence_refs.length ? action.evidence_refs : review.evidence_refs.slice(0, 2),
    rollback_hint: "proposal-only candidate；人工或 agent 复核前不写长期记忆，回滚方式是丢弃候选。",
    requires_conflict_check: true,
    requires_agent_or_human_apply: true,
    proposal_only: true,
  }));

  return {
    closure_id: `summary_closure_${review.time_window.period_id}_${review.time_window.range_end}`,
    closure_schema_version: SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION,
    source_review_schema_version: REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION,
    source_scope: "redacted_atlas_snapshot",
    change_comparison,
    stale_conflict_signals,
    proposal_candidates,
    closure_summary: `change_comparison=${change_comparison.length}; stale_conflict_signals=${stale_conflict_signals.length}; proposal_candidates=${proposal_candidates.length}; all outputs remain proposal-only.`,
    safety: {
      proposal_only: true,
      directActiveMemoryWriteback: false,
      rawPrivateDataIncluded: false,
      proposalWrite: false,
    },
    panelIds: ["change_comparison", "stale_conflict_signals", "proposal_candidates"],
  };
}



export function summaryClosureChangeRow(
  row: ReviewSignalRow,
  signalId: string,
  currentCount: number,
  previousCount: number,
): SummaryClosureChangeRow {
  return {
    signal_id: signalId,
    title: row.title,
    summary: row.summary,
    current_count: currentCount,
    previous_count: previousCount,
    delta: currentCount - previousCount,
    evidence_refs: row.evidence_refs,
  };
}



export function reviewQuestionAnswerById(output: ReviewSummaryIterationOutput, questionId: ReviewQuestionId): ReviewQuestionAnswer {
  return output.questions.find((item) => item.question_id === questionId) ?? {
    question_id: questionId,
    panel_id: "theme_change_panel",
    question: "本期主导主题是什么",
    answer: "当前 review 输出尚未生成足够证据，保持观察。",
    evidence_refs: output.evidence_refs.slice(0, 2),
  };
}



export function buildReviewQuestions(output: ReviewSummaryIterationOutput): ReviewQuestionAnswer[] {
  return [
    {
      question_id: "dominant_topics",
      panel_id: "theme_change_panel",
      question: "本期主导主题是什么",
      answer: reviewRowSentence(output.dominant_topics, "主导主题"),
      evidence_refs: output.dominant_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "strengthening_topics",
      panel_id: "theme_change_panel",
      question: "哪些主题增强",
      answer: reviewRowSentence(output.strengthening_topics, "增强主题"),
      evidence_refs: output.strengthening_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "declining_topics",
      panel_id: "theme_change_panel",
      question: "哪些主题衰退",
      answer: reviewRowSentence(output.declining_topics, "衰退主题"),
      evidence_refs: output.declining_topics[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "new_opportunities",
      panel_id: "opportunity_panel",
      question: "哪些新机会出现",
      answer: reviewRowSentence(output.new_opportunities, "新机会"),
      evidence_refs: output.new_opportunities[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "low_value_loops",
      panel_id: "low_value_loop_panel",
      question: "哪些低价值循环出现",
      answer: reviewRowSentence(output.low_value_loops, "低价值循环"),
      evidence_refs: output.low_value_loops[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "decision_changes",
      panel_id: "decision_change_panel",
      question: "哪些决策变化",
      answer: reviewRowSentence(output.decision_changes, "决策变化"),
      evidence_refs: output.decision_changes[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "next_actions",
      panel_id: "next_action_panel",
      question: "下一步动作是什么",
      answer: output.next_actions.map((item) => `${item.title}：${item.reason}`).slice(0, 3).join("；"),
      evidence_refs: output.next_actions[0]?.evidence_refs ?? output.evidence_refs.slice(0, 2),
    },
    {
      question_id: "proposal_decision",
      panel_id: "proposal_decision_panel",
      question: "是否需要生成 proposal",
      answer: `${output.proposal_candidate.proposal_decision}；${output.proposal_candidate.reason}`,
      evidence_refs: output.evidence_refs.slice(0, 3),
    },
  ];
}



export function reviewTopicRows(atlas: MemoryAtlas, nodes: AtlasNode[], limit: number): ReviewSignalRow[] {
  const rows = topRows(countBy(nodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), limit);
  return rows.map((row) => {
    const topicNodes = nodes.filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.label);
    return reviewSignalRow(atlas, row.label, `${row.label} 在当前窗口内出现 ${row.count.toLocaleString()} 次，是复盘优先入口。`, row.count, topicNodes);
  });
}



export function reviewStrengtheningRows(atlas: MemoryAtlas, nodes: AtlasNode[], latest: Date): ReviewSignalRow[] {
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const rows = Object.keys(recentCounts)
    .map((title) => ({ title, count: recentCounts[title] - (previousCounts[title] ?? 0) }))
    .filter((row) => row.count > 0)
    .sort((left, right) => right.count - left.count || left.title.localeCompare(right.title, "zh-CN"))
    .slice(0, 3);
  const fallback = rows.length ? rows : topRows(recentCounts, 3).map((row) => ({ title: row.label, count: row.count }));
  return fallback.map((row) => {
    const topicNodes = recentNodes.filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.title);
    return reviewSignalRow(atlas, row.title, `${row.title} 近 30 天净增 ${formatSigned(row.count)} 条，优先检查是否进入下一轮任务。`, row.count, topicNodes);
  });
}



export function reviewDecliningRows(atlas: MemoryAtlas, nodes: AtlasNode[], latest: Date): ReviewSignalRow[] {
  const recentStart = addDays(latest, -29);
  const previousStart = addDays(latest, -59);
  const previousEnd = addDays(latest, -30);
  const recentNodes = nodes.filter((node) => isNodeBetween(node, recentStart, latest));
  const previousNodes = nodes.filter((node) => isNodeBetween(node, previousStart, previousEnd));
  const recentCounts = countBy(recentNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const previousCounts = countBy(previousNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category));
  const rows = Object.keys(previousCounts)
    .map((title) => ({ title, count: previousCounts[title] - (recentCounts[title] ?? 0) }))
    .filter((row) => row.count > 0)
    .sort((left, right) => right.count - left.count || left.title.localeCompare(right.title, "zh-CN"))
    .slice(0, 3);
  const staleNodes = nodes.filter((node) => node.category === "deprecated_info" || node.metrics?.roi?.staleness_status);
  const fallback = rows.length
    ? rows
    : topRows(countBy(staleNodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), 3).map((row) => ({
        title: row.label,
        count: row.count,
      }));
  return fallback.map((row) => {
    const topicNodes = previousNodes.concat(staleNodes).filter((node) => (compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)) === row.title);
    return reviewSignalRow(atlas, row.title, `${row.title} 当前动能下降或带有 stale 信号，需要降权、合并或标注时效。`, row.count, topicNodes);
  });
}



export function reviewOpportunityRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const opportunityNodes = nodes
    .filter((node) => /机会|opportunity|下一步|继续|action|proposal|优化|扩展/i.test(`${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`))
    .sort(reviewNodeSort);
  const rows = opportunityNodes.slice(0, 3).map((node) =>
    reviewSignalRow(atlas, humanNodeDisplayTitle(node), recommendedActionForNode(node), 1, [node]),
  );
  if (rows.length) return rows;
  return reviewTopicRows(atlas, nodes, 1).map((row) => ({
    ...row,
    title: `机会待确认：${row.title}`,
    summary: "当前窗口没有明显机会信号，先从主导主题里人工确认是否值得推进。",
    count: 0,
  }));
}



export function reviewLowValueLoopRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const lowValueNodes = nodes.filter((node) => {
    const tier = normalizeMemoryTier(node.memory_tier);
    return (
      tier === "临时" ||
      node.category === "temporary_or_sensitive" ||
      node.category === "deprecated_info" ||
      /临时|过期|stale|低权重|重复|噪音/i.test(`${node.label} ${node.statement ?? ""} ${node.validity ?? ""} ${node.metrics?.roi?.staleness_status ?? ""}`)
    );
  });
  const rows = topRows(countBy(lowValueNodes, (node) => humanCategoryLabel(node.category) || normalizeMemoryTier(node.memory_tier)), 3)
    .filter((row) => row.count > 0)
    .map((row) => {
      const rowNodes = lowValueNodes.filter((node) => (humanCategoryLabel(node.category) || normalizeMemoryTier(node.memory_tier)) === row.label);
      return reviewSignalRow(atlas, row.label, `${row.label} 出现 ${row.count.toLocaleString()} 次；建议压缩、降权或转成有时效标记的背景。`, row.count, rowNodes);
    });
  return rows.length
    ? rows
    : [reviewSignalRow(atlas, "低价值循环未显著出现", "当前窗口没有明显短期噪音或过期信息，可先保持观察。", 0, nodes.slice(0, 1))];
}



export function reviewDecisionRows(atlas: MemoryAtlas, nodes: AtlasNode[]): ReviewSignalRow[] {
  const decisionNodes = nodes
    .filter((node) => node.category === "decision" || node.kind === "decision" || /决策|决定|选择|批准|停止/i.test(`${node.label} ${node.statement ?? ""}`))
    .sort(reviewNodeSort);
  const rows = decisionNodes.slice(0, 3).map((node) =>
    reviewSignalRow(atlas, humanNodeDisplayTitle(node), humanizeStatement(node.statement) || recommendedActionForNode(node), 1, [node]),
  );
  return rows.length
    ? rows
    : [reviewSignalRow(atlas, "决策变化未显著出现", "当前窗口没有新的 decision 类节点；后续若出现新证据再生成修改 proposal。", 0, nodes.slice(0, 1))];
}



export function reviewNextActions(atlas: MemoryAtlas, nodes: AtlasNode[], evidenceRefs: string[]): ReviewNextAction[] {
  const recommendationItems = atlas.agent_recommendations
    ? [
        ...atlas.agent_recommendations.memory.added,
        ...atlas.agent_recommendations.memory.modified.map((item) => item.after),
        ...atlas.agent_recommendations.meta_data.added,
        ...atlas.agent_recommendations.meta_data.modified.map((item) => item.after),
      ]
    : [];
  const recommendationActions = recommendationItems.slice(0, 3).map<ReviewNextAction>((item, index) => ({
    action_id: `agent_recommendation:${item.id || index}`,
    title: item.title,
    reason: item.reason || item.statement,
    priority: item.importance === "high" ? "high" : "medium",
    source_scope: "agent_recommendations_redacted",
    evidence_refs: item.source ? [`recommendation:${item.source}`] : evidenceRefs.slice(0, 2),
    acceptance_hint: "人工确认后进入 proposal-only handoff，不由前端直接写长期记忆。",
  }));
  if (recommendationActions.length) return recommendationActions;

  return [...nodes]
    .sort((left, right) => (right.metrics?.roi?.leverage_score ?? 0) - (left.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 3)
    .map<ReviewNextAction>((node, index) => ({
      action_id: `review_action:${node.id || index}`,
      title: humanNodeDisplayTitle(node),
      reason: recommendedActionForNode(node),
      priority: search2ImportanceForNode(node) === "critical" ? "high" : "medium",
      source_scope: "redacted_atlas_snapshot",
      evidence_refs: buildSearch2EvidenceRefs(atlas, node),
      acceptance_hint: "进入下一阶段前需要可审查记录、回滚提示和 validator 证明。",
    }));
}



export function reviewIterationBacklog(
  nextActions: ReviewNextAction[],
  lowValueLoops: ReviewSignalRow[],
  opportunities: ReviewSignalRow[],
  dominantTopics: ReviewSignalRow[],
): ReviewIterationItem[] {
  const items: ReviewIterationItem[] = [
    {
      item_id: "iteration_backlog:proposal_triage",
      title: "Proposal triage",
      why_it_matters: nextActions[0]?.reason || "需要把本期结论转成可审查、可回滚的候选更新。",
      next_step: nextActions[0]?.title || "选择最高价值 review action",
      acceptance_hint: "生成 proposal-only 候选，不直接写长期记忆。",
      priority: nextActions[0]?.priority || "medium",
    },
    {
      item_id: "iteration_backlog:low_value_loop",
      title: "Low-value loop cleanup",
      why_it_matters: lowValueLoops[0]?.summary || "低价值循环会污染长期召回，需要周期性压缩或降权。",
      next_step: lowValueLoops[0]?.title || "复核低价值循环",
      acceptance_hint: "保留证据 refs，人工确认后再修改记忆权重。",
      priority: lowValueLoops[0]?.count ? "high" : "low",
    },
    {
      item_id: "iteration_backlog:opportunity_capture",
      title: "Opportunity capture",
      why_it_matters: opportunities[0]?.summary || dominantTopics[0]?.summary || "主导主题需要被转成下一步动作，否则只停留在可视化层。",
      next_step: opportunities[0]?.title || dominantTopics[0]?.title || "复核主导主题",
      acceptance_hint: "下一轮 validator 应能看到 evidence_refs 和 decision/proposal 边界。",
      priority: opportunities[0]?.count ? "high" : "medium",
    },
  ];
  return items;
}



export function reviewSignalRow(
  atlas: MemoryAtlas,
  title: string,
  summary: string,
  count: number,
  nodes: AtlasNode[],
): ReviewSignalRow {
  return {
    title,
    summary,
    count,
    evidence_refs: reviewNodeEvidenceRefs(atlas, nodes),
  };
}



export function reviewNodeEvidenceRefs(atlas: MemoryAtlas, nodes: AtlasNode[]): string[] {
  const refs = nodes.flatMap((node) => buildSearch2EvidenceRefs(atlas, node));
  return Array.from(new Set(refs.length ? refs : ["source:redacted_atlas_snapshot"])).slice(0, 4);
}



export function reviewEvidenceRefs(atlas: MemoryAtlas, rows: ReviewSignalRow[]): string[] {
  const refs = rows.flatMap((row) => row.evidence_refs);
  return Array.from(new Set(refs.length ? refs : [`source:${atlas.source_contract.export_profile}`])).slice(0, 8);
}



export function reviewRowSentence(rows: ReviewSignalRow[], fallbackLabel: string): string {
  const activeRows = rows.filter((row) => row.count > 0);
  const displayRows = activeRows.length ? activeRows : rows;
  return displayRows.length
    ? displayRows.slice(0, 3).map((row) => `${row.title}（${row.count.toLocaleString()}）：${row.summary}`).join("；")
    : `${fallbackLabel} 暂无足够证据，保持观察。`;
}



export function reviewNodeSort(left: AtlasNode, right: AtlasNode): number {
  const scoreDelta = (right.metrics?.roi?.leverage_score ?? 0) - (left.metrics?.roi?.leverage_score ?? 0);
  if (scoreDelta) return scoreDelta;
  return (right.date ?? "").localeCompare(left.date ?? "") || humanNodeDisplayTitle(left).localeCompare(humanNodeDisplayTitle(right), "zh-CN");
}
