import { ArrowUpRight, Database, RotateCcw, ShieldCheck, SlidersHorizontal } from "lucide-react";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";

import type {
  FormulaWhatIfPreview,
  MemoryAtlas,
  OpportunitySummary,
  ViewKey,
  VisualFacetEvent,
  VisualWorkflow,
} from "../types";
import {
  buildVisualFilterSignature,
  buildVisualWorkflowOptions,
  computeFormulaWhatIfScore,
  filterVisualFacetEvents,
  type FormulaWeightKey,
  type FormulaWeights,
  type VisualTimeFilter,
  type VisualWorkflowFilters,
} from "../visualWorkflows";

const R6_VISUAL_WORKBENCH_VERSION = "memory_atlas_visual_workflows.v1_2_r6" as const;
const DEFAULT_FILTERS: VisualWorkflowFilters = { source: "all", time: "all", project: "all", task: "all" };
const FORMULA_CONTROL_KEYS: Array<{ key: FormulaWeightKey; label: string }> = [
  { key: "time_saved_weight", label: "时间节省" },
  { key: "reuse_value_weight", label: "复用价值" },
  { key: "skill_compounding_weight", label: "长期复利" },
];

interface VisualWorkflowWorkbenchProps {
  atlas: MemoryAtlas;
  onSwitchView: (view: ViewKey) => void;
}

interface R6ChartDatum {
  id: string;
  label: string;
  secondary: string;
  value: number;
  events: VisualFacetEvent[];
}

interface EvidenceSelection {
  visualId: string;
  datumLabel: string;
  events: VisualFacetEvent[];
}

export function VisualWorkflowWorkbench({ atlas, onSwitchView }: VisualWorkflowWorkbenchProps) {
  const registry = atlas.visual_workflows;
  const formula = atlas.formula_what_if;
  const behavior = atlas.behavior_intelligence;
  const allEvents = useMemo(() => behavior?.facet_events ?? [], [behavior?.facet_events]);
  const options = useMemo(() => buildVisualWorkflowOptions(allEvents), [allEvents]);
  const [filters, setFilters] = useState<VisualWorkflowFilters>(DEFAULT_FILTERS);
  const filteredEvents = useMemo(() => filterVisualFacetEvents(allEvents, filters), [allEvents, filters]);
  const filterSignature = useMemo(() => buildVisualFilterSignature(allEvents, filters), [allEvents, filters]);
  const [selection, setSelection] = useState<EvidenceSelection>(() => ({
    visualId: registry?.visuals[0]?.id ?? "cluster_tree",
    datumLabel: "当前筛选",
    events: allEvents.slice(0, 3),
  }));
  const opportunities = behavior?.opportunities ?? [];
  const [selectedOpportunityId, setSelectedOpportunityId] = useState(opportunities[0]?.opportunity_id ?? "");
  const [formulaWeights, setFormulaWeights] = useState<Partial<FormulaWeights>>(() => ({ ...(formula?.default_weights ?? {}) }));

  useEffect(() => {
    setSelection((current) => ({ ...current, events: filteredEvents.slice(0, 3) }));
  }, [filterSignature, filteredEvents]);

  useEffect(() => {
    if (formula) setFormulaWeights({ ...formula.default_weights });
  }, [formula?.schema_version]);

  useEffect(() => {
    if (!opportunities.some((item) => item.opportunity_id === selectedOpportunityId)) {
      setSelectedOpportunityId(opportunities[0]?.opportunity_id ?? "");
    }
  }, [opportunities, selectedOpportunityId]);

  const selectedWorkflow = registry?.visuals.find((item) => item.id === selection.visualId)
    ?? registry?.visuals[0]
    ?? null;
  const selectedOpportunity = opportunities.find((item) => item.opportunity_id === selectedOpportunityId)
    ?? opportunities[0]
    ?? null;
  const formulaResult = useMemo(
    () => formula ? computeFormulaWhatIfScore(formula, formulaWeights) : null,
    [formula, formulaWeights],
  );
  const filterSummary = visualFilterSummary(filters);

  if (!registry || registry.p0_visual_count !== 12) {
    return (
      <section className="r6-visual-workbench r6-visual-workbench-error" aria-live="polite">
        <strong>决策视图尚未就绪</strong>
        <p>当前快照缺少完整的 12 项可视化注册表，请重新生成 Memory Atlas 数据。</p>
      </section>
    );
  }

  function updateFilter<Key extends keyof VisualWorkflowFilters>(key: Key, value: VisualWorkflowFilters[Key]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function selectDatum(workflow: VisualWorkflow, datum: R6ChartDatum) {
    setSelection({ visualId: workflow.id, datumLabel: datum.label, events: datum.events.slice(0, 4) });
  }

  function selectOpportunity(workflow: VisualWorkflow, opportunity: OpportunitySummary) {
    setSelectedOpportunityId(opportunity.opportunity_id);
    setSelection({
      visualId: workflow.id,
      datumLabel: opportunity.label_zh || opportunity.opportunity_type,
      events: filteredEvents.slice(0, 4),
    });
  }

  function selectFormula(workflow: VisualWorkflow) {
    setSelection({ visualId: workflow.id, datumLabel: "当前参数组合", events: filteredEvents.slice(0, 4) });
  }

  return (
    <section
      className="r6-visual-workbench"
      aria-labelledby="r6-visual-workbench-title"
      data-r6-filtered-event-count={filteredEvents.length}
      data-r6-visual-workbench={R6_VISUAL_WORKBENCH_VERSION}
    >
      <div className="r6-workbench-heading">
        <div>
          <span>行为与决策</span>
          <h2 id="r6-visual-workbench-title">从记录看清投入、摩擦与机会</h2>
          <p>让每张图回答一个真实问题，并保留可追溯证据。</p>
        </div>
        <div className="r6-workbench-totals" aria-label="可视化工作台摘要">
          <strong>{filteredEvents.length.toLocaleString()}</strong>
          <span>条匹配事件</span>
          <small>{registry.p0_visual_count} 个决策视图</small>
        </div>
      </div>

      <div className="r6-filter-bar" aria-label="决策视图过滤">
        <label>
          <span>来源</span>
          <select data-r6-visual-filter="source" value={filters.source} onChange={(event) => updateFilter("source", event.target.value)}>
            <option value="all">全部来源</option>
            {options.sources.map((source) => <option key={source} value={source}>{source}</option>)}
          </select>
        </label>
        <label>
          <span>时间</span>
          <select data-r6-visual-filter="time" value={filters.time} onChange={(event) => updateFilter("time", event.target.value as VisualTimeFilter)}>
            {options.times.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
          </select>
        </label>
        <label>
          <span>项目</span>
          <select data-r6-visual-filter="project" value={filters.project} onChange={(event) => updateFilter("project", event.target.value)}>
            <option value="all">全部项目</option>
            {options.projects.map((project) => <option key={project} value={project}>{project}</option>)}
          </select>
        </label>
        <label>
          <span>任务</span>
          <select data-r6-visual-filter="task" value={filters.task} onChange={(event) => updateFilter("task", event.target.value)}>
            <option value="all">全部任务</option>
            {options.tasks.map((task) => <option key={task} value={task}>{humanFacetLabel(task)}</option>)}
          </select>
        </label>
        <button
          className="r6-filter-reset"
          data-r6-visual-filter-reset
          onClick={() => setFilters(DEFAULT_FILTERS)}
          title="重置决策视图过滤"
          type="button"
        >
          <RotateCcw size={17} />
          <span className="sr-only">重置决策视图过滤</span>
        </button>
      </div>

      <div className="r6-filter-status">
        <span data-r6-visual-event-count data-r6-count={filteredEvents.length}>{filterSummary}</span>
        <span data-r6-visual-filter-signature data-r6-signature={filterSignature}>基于 {filteredEvents.length.toLocaleString()} 条事件重算</span>
        {filteredEvents.length === 0 ? <strong>没有匹配事件，请放宽一个过滤条件。</strong> : null}
      </div>

      <div className="r6-workbench-layout">
        <div className="r6-visual-grid">
          {registry.visuals.map((workflow) => {
            if (workflow.id === "opportunity_radar") {
              return (
                <OpportunityVisualCard
                  key={workflow.id}
                  opportunities={opportunities}
                  selectedOpportunityId={selectedOpportunity?.opportunity_id ?? ""}
                  workflow={workflow}
                  onSelect={(opportunity) => selectOpportunity(workflow, opportunity)}
                />
              );
            }
            if (workflow.id === "formula_explorer") {
              return (
                <FormulaVisualCard
                  key={workflow.id}
                  formula={formula}
                  formulaResult={formulaResult}
                  weights={formulaWeights}
                  workflow={workflow}
                  onReset={() => setFormulaWeights({ ...(formula?.default_weights ?? {}) })}
                  onSelect={() => selectFormula(workflow)}
                  onWeightChange={(key, value) => setFormulaWeights((current) => ({ ...current, [key]: value }))}
                />
              );
            }
            const data = buildVisualData(workflow.id, filteredEvents);
            return (
              <EventVisualCard
                data={data}
                key={workflow.id}
                workflow={workflow}
                onSelect={(datum) => selectDatum(workflow, datum)}
              />
            );
          })}
        </div>

        <aside
          className="r6-evidence-workspace"
          data-r6-selected-visual={selectedWorkflow?.id ?? ""}
          data-r6-visual-evidence
        >
          <div className="r6-evidence-heading">
            <span>证据工作区</span>
            <strong>{selectedWorkflow ? displayWorkflowTitle(selectedWorkflow) : "选择一个图中数据"}</strong>
            <small>{selection.datumLabel}</small>
          </div>
          <dl className="r6-evidence-decision">
            <div>
              <dt>要回答的问题</dt>
              <dd data-r6-human-question>{selectedWorkflow?.human_question_zh ?? "当前数据能支持什么判断？"}</dd>
            </div>
            <div>
              <dt>行动价值</dt>
              <dd data-r6-action-value>{selectedWorkflow ? productActionValue(selectedWorkflow.action_value_zh) : "先检查证据，再决定下一步。"}</dd>
            </div>
          </dl>
          <div className="r6-evidence-list" aria-label="选中数据的证据">
            {selection.events.length ? selection.events.map((event) => (
              <article data-r6-evidence-ref key={event.event_id}>
                <span>{event.source_id} · {humanDate(event.occurred_at)}</span>
                <strong>{event.topic || "未命名主题"}</strong>
                <small>{event.project} · {humanFacetLabel(event.task_type)} · {humanFacetLabel(event.evidence_refs[0]?.evidence_level || "派生证据")}</small>
                <details>
                  <summary>证据引用</summary>
                  {event.evidence_refs.map((ref) => <code key={ref.ref_id}>{ref.ref_id} · {ref.ref_type || "reference"} · {ref.path || "无公开路径"}</code>)}
                </details>
              </article>
            )) : (
              <article className="r6-evidence-empty"><strong>当前过滤没有可展示证据</strong><small>放宽来源、时间、项目或任务条件。</small></article>
            )}
          </div>
          <button
            className="r6-next-action"
            data-r6-next-action
            onClick={() => onSwitchView(targetViewForVisual(selectedWorkflow?.id ?? "cluster_tree"))}
            type="button"
          >
            <span>{selectedWorkflow ? productActionValue(selectedWorkflow.action_value_zh) : "打开相关视图"}</span>
            <ArrowUpRight size={16} />
          </button>
          <details data-r6-machine-details className="r6-machine-details">
            <summary><Database size={14} /> 数据合同</summary>
            <code>{registry.schema_version}</code>
            <code>{filterSignature}</code>
            <code>{formula?.formula_source || "formula source unavailable"}</code>
          </details>
        </aside>
      </div>

      <OpportunityDetail opportunity={selectedOpportunity} />
    </section>
  );
}

function EventVisualCard({
  data,
  workflow,
  onSelect,
}: {
  data: R6ChartDatum[];
  workflow: VisualWorkflow;
  onSelect: (datum: R6ChartDatum) => void;
}) {
  const maximum = Math.max(1, ...data.map((datum) => datum.value));
  return (
    <article className={`r6-visual-card r6-family-${safeCssToken(workflow.family)}`} data-r6-visual-id={workflow.id}>
      <VisualCardHeading workflow={workflow} />
      <div className={`r6-chart r6-chart-${workflow.id}`} aria-label={workflow.title_zh}>
        {data.map((datum, index) => (
          <button
            className="r6-chart-datum"
            data-r6-visual-datum={datum.id}
            key={datum.id}
            onClick={() => onSelect(datum)}
            style={{ "--r6-ratio": `${Math.max(8, Math.round((datum.value / maximum) * 100))}%`, "--r6-rank": index } as CSSProperties}
            type="button"
          >
            <span className="r6-chart-mark" aria-hidden="true" />
            <span className="r6-chart-copy">
              <strong>{datum.label}</strong>
              <small>{datum.secondary}</small>
            </span>
            <b>{datum.value.toLocaleString()}</b>
          </button>
        ))}
      </div>
    </article>
  );
}

function OpportunityVisualCard({
  opportunities,
  selectedOpportunityId,
  workflow,
  onSelect,
}: {
  opportunities: OpportunitySummary[];
  selectedOpportunityId: string;
  workflow: VisualWorkflow;
  onSelect: (opportunity: OpportunitySummary) => void;
}) {
  return (
    <article className="r6-visual-card r6-family-economic" data-r6-visual-id={workflow.id}>
      <VisualCardHeading workflow={workflow} />
      <div className="r6-opportunity-list">
        {opportunities.slice(0, 5).map((opportunity) => (
          <button
            className={selectedOpportunityId === opportunity.opportunity_id ? "active" : ""}
            data-r6-opportunity-id={opportunity.opportunity_id}
            data-r6-visual-datum={opportunity.opportunity_id}
            key={opportunity.opportunity_id}
            onClick={() => onSelect(opportunity)}
            type="button"
          >
            <span>{opportunity.label_zh || opportunity.opportunity_type}</span>
            <strong>{Math.round(opportunity.score)}</strong>
            <small>{opportunity.opportunity_half_life_days ?? 0} 天窗口</small>
          </button>
        ))}
      </div>
    </article>
  );
}

function FormulaVisualCard({
  formula,
  formulaResult,
  weights,
  workflow,
  onReset,
  onSelect,
  onWeightChange,
}: {
  formula: FormulaWhatIfPreview | undefined;
  formulaResult: ReturnType<typeof computeFormulaWhatIfScore> | null;
  weights: Partial<FormulaWeights>;
  workflow: VisualWorkflow;
  onReset: () => void;
  onSelect: () => void;
  onWeightChange: (key: FormulaWeightKey, value: number) => void;
}) {
  return (
    <article className="r6-visual-card r6-formula-card r6-family-workflow" data-r6-visual-id={workflow.id}>
      <VisualCardHeading workflow={workflow} />
      <button className="r6-formula-score" data-r6-formula-score data-r6-score={formulaResult?.score ?? 0} data-r6-visual-datum="formula-score" onClick={onSelect} type="button">
        <span>当前 proxy 分</span>
        <strong>{formulaResult?.score ?? "--"}</strong>
        <small>{formulaResult ? `${formulaResult.delta >= 0 ? "+" : ""}${formulaResult.delta} 相对经济基线` : "公式快照不可用"}</small>
      </button>
      <div className="r6-formula-controls">
        {FORMULA_CONTROL_KEYS.map(({ key, label }) => {
          const bounds = formula?.adjustable_weight_bounds[key] ?? { min: 0.25, max: 2, step: 0.05 };
          const value = weights[key] ?? formula?.default_weights[key] ?? 1;
          return (
            <label key={key}>
              <span>{label}<strong>{Number(value).toFixed(2)}</strong></span>
              <input
                data-r6-formula-weight={key}
                max={bounds.max}
                min={bounds.min}
                onChange={(event) => onWeightChange(key, Number(event.target.value))}
                step={bounds.step}
                type="range"
                value={value}
              />
            </label>
          );
        })}
      </div>
      <div className="r6-formula-footer">
        <span data-r6-formula-safety><ShieldCheck size={14} /> 内部 proxy，仅用于方向比较；不是收入预测，也不是财务建议。</span>
        <button data-r6-formula-reset onClick={onReset} title="重置公式参数" type="button"><RotateCcw size={15} /><span className="sr-only">重置公式参数</span></button>
      </div>
      <details className="formula-technical-details r6-formula-machine-details">
        <summary><SlidersHorizontal size={14} /> 查看公式来源</summary>
        <code>data/derived/economic_proxy/formula_what_if_preview.json</code>
        <code>{formula?.formula_source || "formula source unavailable"}</code>
      </details>
    </article>
  );
}

function VisualCardHeading({ workflow }: { workflow: VisualWorkflow }) {
  return (
    <header className="r6-visual-card-heading">
      <span>{humanFamilyLabel(workflow.family)}</span>
      <h3>{displayWorkflowTitle(workflow)}</h3>
      <strong>{workflow.insight_header_zh}</strong>
      <p data-r6-card-question>{workflow.human_question_zh}</p>
      <small data-r6-card-action>{productActionValue(workflow.action_value_zh)}</small>
    </header>
  );
}

function OpportunityDetail({ opportunity }: { opportunity: OpportunitySummary | null }) {
  if (!opportunity) return null;
  const reason = opportunity.defer_reason_zh
    || opportunity.why_not_now_card?.reason_zh
    || opportunity.why_not_now_card?.defer_until_signal_zh
    || "当前证据不足，暂不扩大投入。";
  return (
    <section className="r6-opportunity-detail" data-r6-opportunity-detail aria-label="选中机会详情">
      <div>
        <span>机会详情</span>
        <h3>{opportunity.label_zh || opportunity.opportunity_type}</h3>
        <p>{opportunity.summary_zh}</p>
      </div>
      <dl>
        <div><dt>下一步</dt><dd data-r6-opportunity-next-step>{productActionValue(opportunity.next_step_zh || "先补充最小证据。")}</dd></div>
        <div><dt>机会半衰期</dt><dd data-r6-opportunity-half-life>{opportunity.opportunity_half_life_days ?? 0} 天</dd></div>
        <div><dt>Why Not Now</dt><dd data-r6-opportunity-defer-reason>{reason}</dd></div>
        <div><dt>压力边界</dt><dd data-r6-opportunity-not-pressure>{opportunity.why_not_now_card?.not_pressure_list ? "不进入压力清单；等触发信号后再评估。" : "由人工确认是否进入行动清单。"}</dd></div>
      </dl>
      <div className="r6-opportunity-evidence-list" aria-label="机会证据">
        {opportunity.evidence_refs.map((ref) => (
          <span data-r6-opportunity-evidence key={ref.ref_id}>{ref.source_id || "derived"} · {ref.evidence_level || ref.ref_type || "evidence"}</span>
        ))}
      </div>
    </section>
  );
}

function buildVisualData(visualId: string, events: VisualFacetEvent[]): R6ChartDatum[] {
  if (visualId === "evidence_timeline") {
    const timeline = [...events]
      .filter((event) => Number.isFinite(Date.parse(event.occurred_at)))
      .sort((left, right) => Date.parse(right.occurred_at) - Date.parse(left.occurred_at))
      .slice(0, 6)
      .map((event, index) => ({
        id: event.event_id,
        label: humanDate(event.occurred_at),
        secondary: compactLabel(event.topic),
        value: Math.max(1, 6 - index),
        events: [event],
      }));
    return timeline.length ? timeline : emptyDatum();
  }

  const labelsForEvent = (event: VisualFacetEvent): string[] => {
    if (visualId === "cluster_tree" || visualId === "topic_cluster_explorer") return [compactLabel(event.topic)];
    if (visualId === "bubble_map" || visualId === "roi_scatter") return [event.project];
    if (visualId === "task_treemap") return [humanFacetLabel(event.task_type)];
    if (visualId === "automation_vs_augmentation" || visualId === "latent_radar") {
      return event.value_signal.length ? event.value_signal.map(humanFacetLabel) : ["待识别价值"];
    }
    if (visualId === "agent_decision_sankey") return [`${event.source_id} → ${humanFacetLabel(event.intent)}`];
    if (visualId === "friction_heatmap") return event.friction.length ? event.friction.map(humanFacetLabel) : ["无显著摩擦"];
    return [event.project];
  };
  const groups = new Map<string, VisualFacetEvent[]>();
  for (const event of events) {
    for (const label of new Set(labelsForEvent(event).filter(Boolean))) {
      groups.set(label, [...(groups.get(label) ?? []), event]);
    }
  }
  const rows = Array.from(groups, ([label, groupedEvents]) => ({
    id: `${safeCssToken(label)}-${groupedEvents[0]?.event_id ?? "empty"}`,
    label,
    secondary: visualDatumSecondary(visualId, groupedEvents),
    value: groupedEvents.length,
    events: groupedEvents,
  }))
    .sort((left, right) => right.value - left.value || left.label.localeCompare(right.label, "zh-CN"))
    .slice(0, 6);
  return rows.length ? rows : emptyDatum();
}

function visualDatumSecondary(visualId: string, events: VisualFacetEvent[]): string {
  const sourceCount = new Set(events.map((event) => event.source_id)).size;
  const evidenceCount = events.reduce((total, event) => total + event.evidence_refs.length, 0);
  if (visualId === "roi_scatter") {
    const valueCount = events.reduce((total, event) => total + event.value_signal.length, 0);
    const frictionCount = events.reduce((total, event) => total + event.friction.length, 0);
    return `${valueCount} 个价值信号 · ${frictionCount} 个摩擦`;
  }
  if (visualId === "agent_decision_sankey") return `${evidenceCount} 条证据流`;
  if (visualId === "friction_heatmap") return `${sourceCount} 个来源 · ${evidenceCount} 条证据`;
  return `${events.length} 条事件 · ${sourceCount} 个来源`;
}

function emptyDatum(): R6ChartDatum[] {
  return [{ id: "empty", label: "暂无匹配事件", secondary: "请放宽过滤条件", value: 0, events: [] }];
}

function visualFilterSummary(filters: VisualWorkflowFilters): string {
  const source = filters.source === "all" ? "全部来源" : filters.source;
  const time = filters.time === "all" ? "全部时间" : filters.time === "365d" ? "近 1 年" : `近 ${filters.time.replace("d", "")} 天`;
  const project = filters.project === "all" ? "全部项目" : filters.project;
  const task = filters.task === "all" ? "全部任务" : humanFacetLabel(filters.task);
  return `${source} · ${time} · ${project} · ${task}`;
}

function targetViewForVisual(visualId: string): ViewKey {
  if (["cluster_tree", "bubble_map"].includes(visualId)) return "galaxy";
  if (["topic_cluster_explorer", "friction_heatmap"].includes(visualId)) return "search";
  if (["agent_decision_sankey", "latent_radar"].includes(visualId)) return "summary";
  if (visualId === "evidence_timeline") return "timeline";
  return "roi";
}

function humanFamilyLabel(value: string): string {
  if (value.includes("clio")) return "主题与语义";
  if (value.includes("economic")) return "投入与机会";
  return "工作流与治理";
}

function displayWorkflowTitle(workflow: VisualWorkflow): string {
  const titles: Record<string, string> = {
    agent_decision_sankey: "Agent 决策流",
    automation_vs_augmentation: "自动化与增强",
    bubble_map: "主题气泡分布",
    cluster_tree: "层级簇树",
    evidence_timeline: "证据时间线",
    formula_explorer: "公式与参数",
    friction_heatmap: "摩擦热区",
    latent_radar: "潜在线索雷达",
    opportunity_radar: "机会雷达",
    roi_scatter: "投入回报分布",
    task_treemap: "任务构成",
    topic_cluster_explorer: "主题簇探索",
  };
  return titles[workflow.id] ?? workflow.title_zh;
}

function productActionValue(value: string): string {
  return value
    .replace(/\s*S(?:0[1-9]|1[0-4])(?:\s*\/\s*S(?:0[1-9]|1[0-4]))?/g, "后续治理流程")
    .replace(/\s*proposal-only\s*/gi, "“只提案、不直接写入”")
    .replace(/\s*proposal\s*/gi, "提案")
    .replace(/\s*run contract\s*/gi, "执行合同")
    .replace(/\s*validator\s*/gi, "验收门禁")
    .replace(/\s*dry-run\s*/gi, "只读试运行")
    .replace(/\s*badge\s*/gi, "标记");
}

function humanFacetLabel(value: string): string {
  const labels: Record<string, string> = {
    analysis: "分析",
    automation: "自动化",
    data: "数据",
    decision_support: "决策支持",
    design: "设计",
    engineering: "工程",
    execution: "执行",
    governance: "治理",
    implementation: "实施",
    processed_manifest: "已处理清单",
    product: "产品",
    research: "研究",
    reusable_asset: "可复用资产",
    scope_creep: "范围扩张",
    time_saved: "节省时间",
    unknown: "未标注",
    writing: "写作",
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

function humanDate(value: string): string {
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return "日期未标注";
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" }).format(timestamp);
}

function compactLabel(value: string): string {
  const normalized = value.trim() || "未标注主题";
  return normalized.length > 30 ? `${normalized.slice(0, 29)}…` : normalized;
}

function safeCssToken(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "") || "item";
}
