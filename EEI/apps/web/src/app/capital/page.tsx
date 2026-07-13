"use client";

import {
  AlertTriangle,
  ArrowRight,
  Database,
  FileSearch,
  Filter,
  RefreshCw,
  RotateCcw
} from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";

import {
  amountBucketKey,
  buildCapitalEventQuery,
  loadCapitalRiver,
  type CapitalEventFilters,
  type CapitalEventRecord,
  type CapitalRiverSyncResult,
  type EventAmountBucket
} from "../capital-events-client";
import {
  loadEvidenceDetail,
  type EvidenceDetailRecord
} from "../production-data-client";
import { WorkspaceNavigationRail } from "../workspace-navigation";
import type { WorkspaceModuleId } from "../workspace-context";

const EMPTY_FILTERS: CapitalEventFilters = {
  entity: "",
  from: "",
  to: "",
  eventType: "",
  currency: "",
  amountKind: ""
};

type LoadState = "idle" | "loading" | "hydrated" | "error" | "api_required";
type EvidenceState = "idle" | "loading" | "hydrated" | "error";

export default function CapitalRiverPage() {
  const [filters, setFilters] = useState<CapitalEventFilters>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<CapitalEventFilters>(EMPTY_FILTERS);
  const [result, setResult] = useState<CapitalRiverSyncResult | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [loadReason, setLoadReason] = useState("initializing");
  const [selectedEvent, setSelectedEvent] = useState<CapitalEventRecord | null>(null);
  const [evidence, setEvidence] = useState<EvidenceDetailRecord | null>(null);
  const [evidenceState, setEvidenceState] = useState<EvidenceState>("idle");
  const [evidenceReason, setEvidenceReason] = useState("select_event");

  const events = result?.status === "hydrated" ? result.events : [];
  const summary = result?.status === "hydrated" ? result.summary : null;
  const eventsByBucket = useMemo(() => groupEventsByBucket(events), [events]);
  const unreportedEvents = useMemo(
    () => events.filter((event) => event.amount_semantics.state === "unreported"),
    [events]
  );
  const unclassifiedEvents = useMemo(
    () => events.filter((event) => event.amount_semantics.state === "reported_unclassified"),
    [events]
  );

  useEffect(() => {
    const initialFilters = readFiltersFromLocation();
    setFilters(initialFilters);
    setAppliedFilters(initialFilters);
    void hydrateCapitalRiver(initialFilters);
  }, []);

  async function hydrateCapitalRiver(nextFilters: CapitalEventFilters) {
    setLoadState("loading");
    setLoadReason("requesting_events_and_summary");
    setSelectedEvent(null);
    setEvidence(null);
    setEvidenceState("idle");
    const nextResult = await loadCapitalRiver(nextFilters);
    setResult(nextResult);
    if (nextResult.status === "hydrated") {
      setLoadState("hydrated");
      setLoadReason("server_hydrated");
      return;
    }
    if (nextResult.status === "api_required") {
      setLoadState("api_required");
      setLoadReason(nextResult.reason);
      return;
    }
    setLoadState("error");
    setLoadReason(nextResult.reason);
  }

  function updateFilter(key: keyof CapitalEventFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = { ...filters, currency: filters.currency.trim().toUpperCase() };
    setFilters(normalized);
    setAppliedFilters(normalized);
    window.history.replaceState(null, "", `/capital?${buildCapitalEventQuery(normalized)}`);
    void hydrateCapitalRiver(normalized);
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS);
    setAppliedFilters(EMPTY_FILTERS);
    window.history.replaceState(null, "", "/capital");
    void hydrateCapitalRiver(EMPTY_FILTERS);
  }

  async function openEventEvidence(event: CapitalEventRecord) {
    setSelectedEvent(event);
    setEvidence(null);
    setEvidenceState("loading");
    setEvidenceReason("requesting_event_evidence");
    const evidenceResult = await loadEvidenceDetail({
      objectType: "event",
      objectId: event.id,
      limit: 20
    });
    if (evidenceResult.status === "hydrated") {
      setEvidence(evidenceResult.record);
      setEvidenceState("hydrated");
      setEvidenceReason("server_hydrated");
      return;
    }
    setEvidenceState("error");
    setEvidenceReason(evidenceResult.reason);
  }

  function navigateToLens(lens: string, _moduleId: WorkspaceModuleId) {
    window.location.assign(`/?lens=${encodeURIComponent(lens)}`);
  }

  function navigateToSection(sectionTestId: string, _moduleId: WorkspaceModuleId) {
    window.location.assign(`/#${encodeURIComponent(sectionTestId)}`);
  }

  return (
    <div
      className="capitalWorkspace"
      data-acceptance-ids="A108,A109,A110"
      data-amount-semantics-version={summary?.schema_version ?? "pending"}
      data-cross-bucket-summation={summary?.cross_bucket_summation_performed ?? false}
      data-load-state={loadState}
      data-testid="capital-river-shell"
    >
      <WorkspaceNavigationRail
        activeLens="capital_transactions"
        activeModuleId="capital_network"
        onLensTarget={navigateToLens}
        onSectionTarget={navigateToSection}
      />

      <main className="capitalMain">
        <header className="capitalHeader">
          <div>
            <p className="eyebrow">Capital, financing and M&amp;A</p>
            <h1>资金河流</h1>
            <p>
              事件金额按币种、金额类型与期间分 lane；跨 lane 不合计，未披露金额不映射为零。
            </p>
          </div>
          <div className="capitalHeaderStatus" data-testid="capital-sync-status">
            <Database size={16} aria-hidden="true" />
            <span>{loadState}</span>
            <small>{loadReason}</small>
          </div>
        </header>

        <form className="capitalFilters" data-testid="capital-filters" onSubmit={applyFilters}>
          <label>
            <span>主体 UUID</span>
            <input
              data-testid="capital-filter-entity"
              onChange={(event) => updateFilter("entity", event.target.value)}
              placeholder="entity id"
              type="text"
              value={filters.entity}
            />
          </label>
          <label>
            <span>起始日期</span>
            <input
              data-testid="capital-filter-from"
              onChange={(event) => updateFilter("from", event.target.value)}
              type="date"
              value={filters.from}
            />
          </label>
          <label>
            <span>结束日期</span>
            <input
              data-testid="capital-filter-to"
              onChange={(event) => updateFilter("to", event.target.value)}
              type="date"
              value={filters.to}
            />
          </label>
          <label>
            <span>事件类型</span>
            <input
              data-testid="capital-filter-event-type"
              onChange={(event) => updateFilter("eventType", event.target.value)}
              placeholder="capital_expenditure"
              type="text"
              value={filters.eventType}
            />
          </label>
          <label>
            <span>币种</span>
            <input
              data-testid="capital-filter-currency"
              maxLength={3}
              minLength={3}
              onChange={(event) => updateFilter("currency", event.target.value)}
              placeholder="USD"
              type="text"
              value={filters.currency}
            />
          </label>
          <label>
            <span>金额类型</span>
            <input
              data-testid="capital-filter-amount-kind"
              onChange={(event) => updateFilter("amountKind", event.target.value)}
              placeholder="period_capex"
              type="text"
              value={filters.amountKind}
            />
          </label>
          <div className="capitalFilterActions">
            <button data-testid="capital-filter-apply" type="submit">
              <Filter size={16} aria-hidden="true" />
              应用
            </button>
            <button data-testid="capital-filter-reset" onClick={resetFilters} type="button">
              <RotateCcw size={16} aria-hidden="true" />
              重置
            </button>
          </div>
        </form>

        {loadState === "api_required" ? (
          <section className="capitalEmptyState" data-testid="capital-api-required">
            <AlertTriangle size={20} aria-hidden="true" />
            <div>
              <strong>需要生产 API</strong>
              <p>配置 `NEXT_PUBLIC_EEI_API_BASE_URL` 或本地 API base 后加载事件与证据。</p>
            </div>
          </section>
        ) : null}

        {summary ? (
          <section
            className="capitalSummaryBand"
            data-bucket-count={summary.bucket_count}
            data-comparable-total-available={summary.comparable_reported_total_available}
            data-cross-bucket-summation={summary.cross_bucket_summation_performed}
            data-testid="capital-amount-summary"
          >
            <div>
              <span>事件</span>
              <strong>{summary.event_count}</strong>
            </div>
            <div>
              <span>可比分桶</span>
              <strong>{summary.bucket_count}</strong>
            </div>
            <div>
              <span>金额未披露</span>
              <strong>{summary.unreported_event_count}</strong>
            </div>
            <div>
              <span>跨桶总额</span>
              <strong data-testid="capital-cross-bucket-total">
                {summary.comparable_reported_total_available
                  ? formatAmount(summary.comparable_reported_total, summary.buckets[0]?.currency)
                  : "禁用"}
              </strong>
            </div>
            <div>
              <span>不可比维度</span>
              <strong>{summary.incomparable_dimensions.join(" / ") || "无"}</strong>
            </div>
          </section>
        ) : null}

        <div className="capitalBody">
          <section className="capitalRiver" aria-label="资金事件流" data-testid="capital-river">
            <header>
              <div>
                <p className="eyebrow">Comparable lanes</p>
                <h2>事件流</h2>
              </div>
              <button
                aria-label="刷新资金事件"
                className="iconButton"
                data-testid="capital-refresh"
                onClick={() => void hydrateCapitalRiver(appliedFilters)}
                title="刷新资金事件"
                type="button"
              >
                <RefreshCw size={17} aria-hidden="true" />
              </button>
            </header>

            {summary?.buckets.map((bucket) => (
              <ComparableLane
                bucket={bucket}
                events={eventsByBucket.get(amountBucketKey(bucket)) ?? []}
                key={amountBucketKey(bucket)}
                onOpenEvidence={openEventEvidence}
              />
            ))}

            {unreportedEvents.length ? (
              <SemanticExceptionLane
                events={unreportedEvents}
                kind="unreported"
                onOpenEvidence={openEventEvidence}
              />
            ) : null}
            {unclassifiedEvents.length ? (
              <SemanticExceptionLane
                events={unclassifiedEvents}
                kind="unclassified"
                onOpenEvidence={openEventEvidence}
              />
            ) : null}

            {loadState === "hydrated" && events.length === 0 ? (
              <div className="capitalNoResults" data-testid="capital-no-results">
                当前筛选没有带证据的事件。
              </div>
            ) : null}
          </section>

          <aside
            className="capitalEvidence"
            data-evidence-state={evidenceState}
            data-selected-event-id={selectedEvent?.id ?? "none"}
            data-testid="capital-event-evidence"
          >
            <header>
              <div>
                <p className="eyebrow">Event evidence</p>
                <h2>事件证据</h2>
              </div>
              <FileSearch size={19} aria-hidden="true" />
            </header>
            {!selectedEvent ? <p className="capitalEvidenceHint">选择事件查看来源与原文片段。</p> : null}
            {selectedEvent ? (
              <section className="capitalSelectedEvent">
                <strong>{selectedEvent.title}</strong>
                <span>{selectedEvent.event_type}</span>
                <small>{selectedEvent.id}</small>
              </section>
            ) : null}
            <div className="capitalEvidenceState" data-testid="capital-evidence-status">
              {evidenceState} / {evidenceReason}
            </div>
            {evidence ? (
              <div className="capitalEvidenceContent">
                <dl>
                  <div>
                    <dt>来源</dt>
                    <dd data-testid="capital-evidence-count">{evidence.evidence_count}</dd>
                  </div>
                  <div>
                    <dt>文档</dt>
                    <dd>{evidence.source_document_count}</dd>
                  </div>
                </dl>
                <ol data-testid="capital-evidence-list">
                  {evidence.evidence.map((item) => (
                    <li key={item.evidence_id}>
                      <div>
                        <strong>{item.title || item.publisher || "Untitled source"}</strong>
                        <span>
                          {item.publisher || "Unknown publisher"} / Tier {item.source_tier} / {item.role}
                        </span>
                      </div>
                      <p>{item.snippet.text || "No excerpt supplied."}</p>
                      {item.url ? (
                        <a href={item.url} rel="noreferrer" target="_blank">
                          打开来源 <ArrowRight size={14} aria-hidden="true" />
                        </a>
                      ) : null}
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}
          </aside>
        </div>
      </main>
    </div>
  );
}

function ComparableLane({
  bucket,
  events,
  onOpenEvidence
}: {
  bucket: EventAmountBucket;
  events: CapitalEventRecord[];
  onOpenEvidence: (event: CapitalEventRecord) => void;
}) {
  const key = amountBucketKey(bucket);
  return (
    <section
      className="capitalLane"
      data-aggregation-key={key}
      data-testid={`capital-lane-${safeTestId(key)}`}
    >
      <header>
        <div>
          <strong>{bucket.amount_kind}</strong>
          <span>{bucket.currency} / {formatPeriod(bucket.period_start, bucket.period_end)}</span>
        </div>
        <div>
          <small>Lane total</small>
          <strong>{formatAmount(bucket.total_amount, bucket.currency)}</strong>
        </div>
      </header>
      <div className="capitalLaneEvents">
        {events.map((event) => {
          const share = bucket.visual_weight_total
            ? Math.max(8, (Number(event.amount_semantics.visual_weight) / bucket.visual_weight_total) * 100)
            : 8;
          return (
            <article
              className="capitalEventRow"
              data-amount-kind={event.amount_kind ?? "unknown"}
              data-event-id={event.id}
              data-has-flow-width="true"
              data-testid={`capital-event-${event.id}`}
              key={event.id}
            >
              <ParticipantColumn event={event} direction="out" />
              <div className="capitalFlowColumn">
                <div className="capitalFlowTrack" aria-hidden="true">
                  <span style={{ width: `${share}%` }} />
                </div>
                <div className="capitalEventTitle">
                  <strong>{event.title}</strong>
                  <span>{formatAmount(event.amount_semantics.display_amount, bucket.currency)}</span>
                </div>
                <button
                  data-testid={`capital-open-evidence-${event.id}`}
                  onClick={() => void onOpenEvidence(event)}
                  type="button"
                >
                  <FileSearch size={15} aria-hidden="true" />
                  {event.evidence_count} 条证据
                </button>
              </div>
              <ParticipantColumn event={event} direction="in" />
            </article>
          );
        })}
      </div>
    </section>
  );
}

function SemanticExceptionLane({
  events,
  kind,
  onOpenEvidence
}: {
  events: CapitalEventRecord[];
  kind: "unreported" | "unclassified";
  onOpenEvidence: (event: CapitalEventRecord) => void;
}) {
  return (
    <section className="capitalLane exception" data-testid={`capital-lane-${kind}`}>
      <header>
        <div>
          <strong>{kind === "unreported" ? "金额未披露" : "金额语义未分类"}</strong>
          <span>{kind === "unreported" ? "不显示零值或流量宽度" : "不参与聚合或宽度映射"}</span>
        </div>
        <small>{events.length} events</small>
      </header>
      <div className="capitalExceptionEvents">
        {events.map((event) => (
          <article
            data-event-id={event.id}
            data-has-flow-width="false"
            data-testid={`capital-event-${event.id}`}
            key={event.id}
          >
            <div>
              <strong>{event.title}</strong>
              <span>{event.event_type} / {event.amount_semantics.non_aggregation_reason}</span>
            </div>
            <span className="unknownAmount">
              {kind === "unreported"
                ? "未披露"
                : `${formatAmount(event.amount_semantics.display_amount, event.currency)} / 不可聚合`}
            </span>
            <button
              data-testid={`capital-open-evidence-${event.id}`}
              onClick={() => void onOpenEvidence(event)}
              type="button"
            >
              <FileSearch size={15} aria-hidden="true" />
              {event.evidence_count} 条证据
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

function ParticipantColumn({
  event,
  direction
}: {
  event: CapitalEventRecord;
  direction: "in" | "out";
}) {
  const participants = event.participants.filter((participant) => participant.direction === direction);
  return (
    <div className="capitalParticipants" data-direction={direction}>
      {participants.length ? (
        participants.map((participant) => (
          <span key={`${participant.entity_id}:${participant.role}`}>
            <strong>{participant.role}</strong>
            <small>{shortId(participant.entity_id)}</small>
          </span>
        ))
      ) : (
        <span>
          <strong>{direction === "out" ? "source" : "destination"}</strong>
          <small>not reported</small>
        </span>
      )}
    </div>
  );
}

function groupEventsByBucket(events: CapitalEventRecord[]) {
  const grouped = new Map<string, CapitalEventRecord[]>();
  for (const event of events) {
    const key = event.amount_semantics.aggregation_key;
    if (!key) continue;
    const normalizedKey = amountBucketKey(key);
    grouped.set(normalizedKey, [...(grouped.get(normalizedKey) ?? []), event]);
  }
  return grouped;
}

function readFiltersFromLocation(): CapitalEventFilters {
  const query = new URLSearchParams(window.location.search);
  return {
    entity: query.get("entity") ?? "",
    from: (query.get("from") ?? "").slice(0, 10),
    to: (query.get("to") ?? "").slice(0, 10),
    eventType: query.get("event_type") ?? "",
    currency: query.get("currency") ?? "",
    amountKind: query.get("amount_kind") ?? ""
  };
}

function formatAmount(amount: number | null, currency?: string | null) {
  if (amount === null) return "未披露";
  return new Intl.NumberFormat("zh-CN", {
    style: currency ? "currency" : "decimal",
    currency: currency || undefined,
    notation: "compact",
    maximumFractionDigits: 1
  }).format(amount);
}

function formatPeriod(start: string | null, end: string | null) {
  if (!start && !end) return "open period";
  return `${start ?? "open"} - ${end ?? "open"}`;
}

function shortId(value: string) {
  return `${value.slice(0, 8)}...${value.slice(-4)}`;
}

function safeTestId(value: string) {
  return value.replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase();
}
