import { Pause, Play, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import type { CSSProperties, PointerEvent, WheelEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { normalizeMemoryTier } from "../../data/atlas";
import { DEFAULT_TIMELINE_RENDERER_MODE, getInitialTimelineRendererMode, persistTimelineRendererMode, TIMELINE_RENDERER_FEATURE_FLAG_VERSION, type TimelineRendererMode } from "../../config/visualFlags";
import type { AtlasNode } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { DeltaStats, TimelineBrushDraft, TimelineDisplayEvent, TimelineEvent, TimelineFeedbackSettings, TimelineInteractionMode, TimelinePanDraft, TimelineTimeRangeSelection } from "../../shared/atlas/contracts";
import { buildMemoryRiverLayout } from "../../shared/atlas/memoryRiverModels";
import { MEMORY_RIVER_WIDTH } from "../../shared/atlas/runtimeConfig";
import { humanCategoryLabel, humanThemeLabel, humanizeStatement } from "../../shared/atlas/semanticHuman";
import { buildMemoryRiverDraftOverlay, buildMemoryRiverRangeOverlay, buildTimelineLayout, buildTimelineRangeSelection, clampMemoryRiverX, emitTimelineFeedback, getInitialTimelineFeedbackSettings, memoryRiverPointerX, memoryRiverXToRatio, persistTimelineFeedbackSettings } from "../../shared/atlas/timelineInteraction";
import { isActivationKey } from "../../shared/atlas/utils";
import { DeltaStrip } from "../../shared/ui/primitives";



export function TimelineView({
  timeline,
  nodeMap,
  selectedNode,
  sharedState,
  selectedTimelineRange,
  deltaStats,
  onSelectNode,
  onSelectTimelineRange,
  onClearTimelineRange,
}: {
  timeline: TimelineEvent[];
  nodeMap: Map<string, AtlasNode>;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  selectedTimelineRange: TimelineTimeRangeSelection | null;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
  onSelectTimelineRange: (range: TimelineTimeRangeSelection) => void;
  onClearTimelineRange: () => void;
}) {
  const [timelineZoom, setTimelineZoom] = useState(1);
  const [timelineCenter, setTimelineCenter] = useState(0.5);
  const [timelineCursor, setTimelineCursor] = useState(1);
  const [timelinePlaying, setTimelinePlaying] = useState(false);
  const [hoveredEventId, setHoveredEventId] = useState<string | null>(null);
  const [lockedEventId, setLockedEventId] = useState<string | null>(null);
  const [interactionMode, setInteractionMode] = useState<TimelineInteractionMode>("pan");
  const [brushDraft, setBrushDraft] = useState<TimelineBrushDraft | null>(null);
  const [panDraft, setPanDraft] = useState<TimelinePanDraft | null>(null);
  const [feedbackSettings, setFeedbackSettings] = useState<TimelineFeedbackSettings>(() => getInitialTimelineFeedbackSettings());
  const [timelineRendererMode, setTimelineRendererMode] = useState<TimelineRendererMode>(() => getInitialTimelineRendererMode());
  const display = useMemo(
    () => buildTimelineLayout(timeline, nodeMap, { zoom: timelineZoom, center: timelineCenter, cursor: timelineCursor }),
    [timeline, nodeMap, timelineCenter, timelineCursor, timelineZoom],
  );
  const riverDisplay = useMemo(() => buildMemoryRiverLayout(display.events, display.cursorX), [display.cursorX, display.events]);
  const selectedRangeOverlay = useMemo(() => buildMemoryRiverRangeOverlay(selectedTimelineRange, display), [display, selectedTimelineRange]);
  const brushDraftOverlay = brushDraft ? buildMemoryRiverDraftOverlay(brushDraft) : null;
  const lockedEvent = useMemo(() => display.events.find((event) => event.id === lockedEventId) ?? null, [display.events, lockedEventId]);
  const hoveredRiverEvent = useMemo(() => display.events.find((event) => event.id === hoveredEventId) ?? null, [display.events, hoveredEventId]);
  const hoveredEvent = useMemo(
    () => hoveredRiverEvent ?? display.events.find((event) => event.source.node_id === selectedNode?.id) ?? display.events[display.events.length - 1] ?? null,
    [display.events, hoveredRiverEvent, selectedNode?.id],
  );
  const activeRiverEvent = lockedEvent ?? hoveredRiverEvent;

  useEffect(() => {
    window.__memoryAtlasStage5Phase3 = () => ({
      integrationVersion: TIMELINE_RENDERER_FEATURE_FLAG_VERSION,
      rendererMode: timelineRendererMode,
      defaultRendererMode: DEFAULT_TIMELINE_RENDERER_MODE,
      legacyRollbackEnabled: true,
      visibleEventCount: display.visibleCount,
      totalEventCount: display.totalCount,
      selectedRangeActive: Boolean(selectedTimelineRange),
      selectedRange: selectedTimelineRange,
      evidenceLayers: [...riverDisplay.evidenceLayers.map((layer) => layer.kind), "roi-gradient"],
      levelCounts: riverDisplay.levelCounts,
      feedback: {
        reducedMotion: feedbackSettings.reducedMotion,
        pseudoHaptic: feedbackSettings.pseudoHaptic,
        audio: feedbackSettings.audio,
      },
      safety: {
        rawPrivateDataIncluded: false,
        directActiveMemoryWriteback: false,
        proposalWrite: false,
      },
    });
    return () => {
      delete window.__memoryAtlasStage5Phase3;
    };
  }, [
    display.totalCount,
    display.visibleCount,
    feedbackSettings.audio,
    feedbackSettings.pseudoHaptic,
    feedbackSettings.reducedMotion,
    riverDisplay.evidenceLayers,
    riverDisplay.levelCounts,
    selectedTimelineRange,
    timelineRendererMode,
  ]);

  useEffect(() => {
    setTimelinePlaying(false);
    setTimelineCursor(1);
  }, [timeline.length]);

  useEffect(() => {
    if (!timelinePlaying || feedbackSettings.reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      setTimelineCursor((current) => {
        if (current >= 0.995) {
          setTimelinePlaying(false);
          return 1;
        }
        return Math.min(1, current + 0.012);
      });
    }, 180);
    return () => window.clearInterval(timer);
  }, [feedbackSettings.reducedMotion, timelinePlaying]);

  useEffect(() => {
    if (feedbackSettings.reducedMotion) setTimelinePlaying(false);
    persistTimelineFeedbackSettings(feedbackSettings);
  }, [feedbackSettings]);

  const clampTimelineCenter = useCallback((value: number) => {
    setTimelineCenter(Math.min(1, Math.max(0, value)));
  }, []);
  const clampTimelineZoom = useCallback((value: number) => {
    setTimelineZoom(Math.min(8, Math.max(1, Number(value.toFixed(2)))));
  }, []);
  const handleTimelineWheel = useCallback((event: WheelEvent<SVGSVGElement>) => {
    event.preventDefault();
    clampTimelineZoom(timelineZoom + (event.deltaY < 0 ? 0.45 : -0.45));
  }, [clampTimelineZoom, timelineZoom]);
  const handleMemoryRiverPointerDown = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    event.preventDefault();
    const x = memoryRiverPointerX(event);
    setTimelinePlaying(false);
    if (interactionMode === "brush") {
      setBrushDraft({ pointerId: event.pointerId, startX: x, endX: x });
    } else {
      setPanDraft({ pointerId: event.pointerId, startX: x, startCenter: timelineCenter });
    }
    event.currentTarget.setPointerCapture(event.pointerId);
  }, [interactionMode, timelineCenter, timelineRendererMode]);
  const handleMemoryRiverPointerMove = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    const x = memoryRiverPointerX(event);
    if (brushDraft && event.pointerId === brushDraft.pointerId) {
      event.preventDefault();
      setBrushDraft({ ...brushDraft, endX: x });
      return;
    }
    if (panDraft && event.pointerId === panDraft.pointerId) {
      event.preventDefault();
      const deltaRatio = (x - panDraft.startX) / MEMORY_RIVER_WIDTH / Math.max(1, timelineZoom);
      clampTimelineCenter(panDraft.startCenter - deltaRatio);
    }
  }, [brushDraft, clampTimelineCenter, panDraft, timelineRendererMode, timelineZoom]);
  const handleMemoryRiverPointerUp = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (timelineRendererMode !== "memory-river") return;
    if (brushDraft && event.pointerId === brushDraft.pointerId) {
      event.preventDefault();
      const endX = memoryRiverPointerX(event);
      const nextDraft = { ...brushDraft, endX };
      const selection = buildTimelineRangeSelection(display, nextDraft.startX, nextDraft.endX);
      if (selection) {
        onSelectTimelineRange(selection);
        setTimelineCursor(memoryRiverXToRatio((clampMemoryRiverX(nextDraft.startX) + clampMemoryRiverX(nextDraft.endX)) / 2));
        emitTimelineFeedback(feedbackSettings, "brush");
      }
      setBrushDraft(null);
      event.currentTarget.releasePointerCapture(event.pointerId);
      return;
    }
    if (panDraft && event.pointerId === panDraft.pointerId) {
      event.preventDefault();
      setPanDraft(null);
      emitTimelineFeedback(feedbackSettings, "pan");
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }, [brushDraft, display, feedbackSettings, onSelectTimelineRange, panDraft, timelineRendererMode]);
  const handleMemoryRiverPointerCancel = useCallback((event: PointerEvent<SVGSVGElement>) => {
    if (brushDraft?.pointerId === event.pointerId) setBrushDraft(null);
    if (panDraft?.pointerId === event.pointerId) setPanDraft(null);
  }, [brushDraft?.pointerId, panDraft?.pointerId]);

  function resetTimelineView() {
    setTimelineZoom(1);
    setTimelineCenter(0.5);
    setTimelineCursor(1);
    setTimelinePlaying(false);
    setBrushDraft(null);
    setPanDraft(null);
    setLockedEventId(null);
    onClearTimelineRange();
  }

  function updateTimelineRendererMode(mode: TimelineRendererMode) {
    setTimelineRendererMode(mode);
    persistTimelineRendererMode(mode);
  }

  function updateFeedbackSettings(patch: Partial<TimelineFeedbackSettings>) {
    setFeedbackSettings((current) => {
      const next = { ...current, ...patch };
      if (next.reducedMotion) setTimelinePlaying(false);
      return next;
    });
  }

  function lockMemoryRiverEvent(event: TimelineDisplayEvent) {
    setLockedEventId(event.id);
    setHoveredEventId(event.id);
    if (event.node) onSelectNode(event.node);
    emitTimelineFeedback(feedbackSettings, "event");
  }

  return (
    <div
      className="visual-workspace timeline-map"
      data-timeline-renderer={timelineRendererMode}
      data-default-timeline-renderer={DEFAULT_TIMELINE_RENDERER_MODE}
      data-stage5-phase3-integration={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.timeline.nodeId ?? ""}
      data-shared-time-range={sharedState.focus.timeline.timeRangeId ?? ""}
    >
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">{timelineRendererMode === "memory-river" ? "记忆时间河 / UTC Time Scale / Theme Lanes" : "时间轴 / 动态窗口 / 事件密度"}</p>
          <h2>{timelineRendererMode === "memory-river" ? "按 Macro / Meso / Micro 河道观察主题、项目和记忆如何增强、衰退和迁移" : "按真实日期播放、缩放和定位记忆、决策、项目事件"}</h2>
        </div>
        <span>{display.visibleCount} / {display.totalCount} 个事件 · {display.rangeLabel}</span>
      </div>
      <DeltaStrip stats={deltaStats} compact />
      <div className="timeline-control-bar" aria-label="时间轴控制">
        <div className="timeline-renderer-toggle" aria-label="Timeline renderer feature flag">
          <button
            aria-pressed={timelineRendererMode === "memory-river"}
            onClick={() => updateTimelineRendererMode("memory-river")}
            type="button"
          >
            Memory River
          </button>
          <button
            aria-pressed={timelineRendererMode === "legacy"}
            onClick={() => updateTimelineRendererMode("legacy")}
            type="button"
          >
            Legacy
          </button>
        </div>
        <button aria-label={timelinePlaying ? "暂停时间轴播放" : "播放时间轴"} className="icon-control" onClick={() => setTimelinePlaying((value) => !value)} disabled={feedbackSettings.reducedMotion} type="button">
          {timelinePlaying ? <Pause size={15} /> : <Play size={15} />}
        </button>
        <button aria-label="缩小时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom - 0.5)} disabled={timelineZoom <= 1} type="button">
          <ZoomOut size={15} />
        </button>
        <button aria-label="放大时间窗口" className="icon-control" onClick={() => clampTimelineZoom(timelineZoom + 0.5)} disabled={timelineZoom >= 8} type="button">
          <ZoomIn size={15} />
        </button>
        <label className="timeline-range-control">
          <span>窗口</span>
          <input aria-label="时间窗口中心" max="1" min="0" onChange={(event) => clampTimelineCenter(Number(event.target.value))} step="0.01" type="range" value={timelineCenter} />
        </label>
        <label className="timeline-range-control">
          <span>游标</span>
          <input aria-label="时间播放游标" max="1" min="0" onChange={(event) => setTimelineCursor(Number(event.target.value))} step="0.01" type="range" value={timelineCursor} />
        </label>
        <button className="segmented" onClick={resetTimelineView} type="button">
          <RotateCcw size={14} />
          重置
        </button>
        <span className="timeline-zoom-readout">{timelineZoom.toFixed(1)}x · {display.cursorLabel}</span>
      </div>
      <div
        className="memory-river-interaction-bar"
        data-interaction-mode={interactionMode}
        data-reduced-motion={feedbackSettings.reducedMotion ? "true" : "false"}
        data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}
        data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}
        data-feedback-defaults={feedbackSettings.pseudoHaptic || feedbackSettings.audio ? "opted-in" : "silent-by-default"}
        aria-label="记忆时间河交互设置"
      >
        <div className="river-mode-tabs" role="group" aria-label="记忆时间河交互模式">
          <button aria-pressed={interactionMode === "pan"} onClick={() => setInteractionMode("pan")} type="button">
            Pan
          </button>
          <button aria-pressed={interactionMode === "brush"} onClick={() => setInteractionMode("brush")} type="button">
            Brush
          </button>
        </div>
        <span className="timeline-range-readout">
          {selectedTimelineRange
            ? `${selectedTimelineRange.label} · ${selectedTimelineRange.eventCount.toLocaleString()} 事件 · ${selectedTimelineRange.topTheme}`
            : interactionMode === "brush"
              ? "拖拽选择时间段；选择会同步到首页、星系和交互焦点"
              : "在河道区域横向拖拽平移；滚轮缩放，选择不会丢失"}
        </span>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.reducedMotion}
            onChange={(event) => updateFeedbackSettings({ reducedMotion: event.target.checked })}
            type="checkbox"
          />
          <span>Reduced Motion</span>
        </label>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.pseudoHaptic}
            onChange={(event) => updateFeedbackSettings({ pseudoHaptic: event.target.checked })}
            type="checkbox"
          />
          <span>伪触感</span>
        </label>
        <label className="feedback-toggle">
          <input
            checked={feedbackSettings.audio}
            onChange={(event) => updateFeedbackSettings({ audio: event.target.checked })}
            type="checkbox"
          />
          <span>音频</span>
        </label>
        <button className="segmented" disabled={!selectedTimelineRange} onClick={onClearTimelineRange} type="button">
          清除区间
        </button>
      </div>
      <div className="timeline-summary-grid" aria-label="时间轴摘要">
        <div><span>窗口事件</span><strong>{display.visibleCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Macro 河道" : "高重要/决策"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Macro.toLocaleString() : display.importantCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Meso 河道" : "核心画像"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Meso.toLocaleString() : display.coreCount.toLocaleString()}</strong></div>
        <div><span>{timelineRendererMode === "memory-river" ? "Micro 河道" : "密度峰值"}</span><strong>{timelineRendererMode === "memory-river" ? riverDisplay.levelCounts.Micro.toLocaleString() : display.peakDensity.toLocaleString()}</strong></div>
      </div>
      <div className="timeline-density-track" aria-label="时间密度轨">
        {display.densityBands.map((band) => (
          <button
            aria-label={`${band.label} · ${band.count} 个事件`}
            className={band.active ? "timeline-density-band active" : "timeline-density-band"}
            key={band.key}
            onClick={() => clampTimelineCenter(band.center)}
            style={{ "--band-height": `${Math.max(8, band.intensity * 100)}%` } as CSSProperties}
            title={`${band.label} · ${band.count} 个事件`}
            type="button"
          />
        ))}
      </div>
      {timelineRendererMode === "memory-river" ? (
        <svg
          className="memory-river-canvas timeline-canvas"
          data-stage5-phase3-memory-river={TIMELINE_RENDERER_FEATURE_FLAG_VERSION}
          data-legacy-rollback="timelineRenderer=legacy"
          data-utc-time-scale="true"
          data-interaction-mode={interactionMode}
          data-selected-time-range={selectedTimelineRange ? "true" : "false"}
          data-feedback-reduced-motion={feedbackSettings.reducedMotion ? "true" : "false"}
          data-feedback-pseudo-haptic={feedbackSettings.pseudoHaptic ? "enabled" : "disabled"}
          data-feedback-audio={feedbackSettings.audio ? "enabled" : "disabled"}
          data-evidence-layers="black-hole-lifecycle proto-star-lifecycle stale-deprecated roi-gradient"
          data-roi-gradient="capability-growth"
          viewBox="0 0 1000 640"
          role="img"
          aria-label="记忆时间河 Macro Meso Micro UTC 河道"
          onPointerCancel={handleMemoryRiverPointerCancel}
          onPointerDown={handleMemoryRiverPointerDown}
          onPointerMove={handleMemoryRiverPointerMove}
          onPointerUp={handleMemoryRiverPointerUp}
          onWheel={handleTimelineWheel}
        >
          <defs>
            <filter id="memoryRiverGlow">
              <feGaussianBlur stdDeviation="4.4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {riverDisplay.lanes.map((lane) => (
              <linearGradient id={lane.gradientId} key={lane.gradientId} x1="0%" x2="100%" y1="0%" y2="0%">
                <stop offset="0%" stopColor={lane.color} stopOpacity="0.16" />
                <stop offset="45%" stopColor={lane.color} stopOpacity="0.72" />
                <stop offset="100%" stopColor={lane.color} stopOpacity="0.28" />
              </linearGradient>
            ))}
          </defs>
          {display.densityBars.map((band) => (
            <rect className="timeline-density-backdrop" height={band.height} key={band.key} width={band.width} x={band.x} y={band.y} />
          ))}
          <g className="memory-river-roi-gradient" data-roi-gradient="capability-growth">
            <title>{`${riverDisplay.roiGradient.label} · ${riverDisplay.roiGradient.signal}`}</title>
            {riverDisplay.roiGradient.bands.map((band) => (
              <rect
                data-roi-gradient-band={band.id}
                fill={band.color}
                height={band.height}
                key={band.id}
                width={band.width}
                x={band.x}
                y={band.y}
              >
                <title>{band.label}</title>
              </rect>
            ))}
            <text x="82" y="92">{riverDisplay.roiGradient.label}</text>
            <text x="82" y="108">{riverDisplay.roiGradient.signal}</text>
          </g>
          {display.ticks.map((tick) => (
            <g key={tick.label}>
              <line x1={tick.x} x2={tick.x} y1="58" y2="552" stroke="rgba(244,241,232,0.08)" />
              <text x={tick.x} y="574" textAnchor="middle" className="axis-label">{tick.label}</text>
            </g>
          ))}
          {riverDisplay.levels.map((level) => (
            <g className="memory-river-level" key={level.level}>
              <text x="30" y={level.y - 18} className="memory-river-level-label">{level.level}</text>
              <text x="30" y={level.y} className="memory-river-level-note">{level.note}</text>
              <line x1="80" x2="960" y1={level.y + 12} y2={level.y + 12} />
            </g>
          ))}
          {riverDisplay.lanes.map((lane) => (
            <g className={`memory-river-lane level-${lane.level.toLowerCase()}`} key={lane.id}>
              <title>{`${lane.level} · ${lane.label} · ${lane.count} 个事件 · UTC scale`}</title>
              <path className="memory-river-lane-shadow" d={lane.path} strokeWidth={lane.strokeWidth + 10} />
              <path className="memory-river-lane-flow" d={lane.path} stroke={`url(#${lane.gradientId})`} strokeWidth={lane.strokeWidth} />
              <text x={lane.labelX} y={lane.labelY} className="memory-river-lane-label">{lane.label}</text>
            </g>
          ))}
          {riverDisplay.evidenceLayers.map((layer) => (
            <g className={`memory-river-evidence-layer ${layer.kind}`} data-evidence-layer={layer.kind} key={layer.id}>
              <title>{`${layer.label} · ${layer.count} 个 redacted derived signals · ${layer.detail}`}</title>
              {layer.segments.map((segment) => (
                <rect
                  data-evidence-segment={layer.kind}
                  height={segment.height}
                  key={segment.id}
                  rx="8"
                  width={segment.width}
                  x={segment.x}
                  y={segment.y}
                >
                  <title>{segment.label}</title>
                </rect>
              ))}
              {layer.path ? <path d={layer.path} /> : null}
              {layer.points.map((point) => (
                <circle cx={point.x} cy={point.y} key={point.id} r={point.radius}>
                  <title>{point.label}</title>
                </circle>
              ))}
              <text x={layer.labelX} y={layer.labelY}>{layer.label}</text>
            </g>
          ))}
          {selectedRangeOverlay ? (
            <g className="memory-river-selected-range" data-selected-time-range="active">
              <rect x={selectedRangeOverlay.x} y="64" width={selectedRangeOverlay.width} height="486" />
              <text x={selectedRangeOverlay.labelX} y="86" textAnchor="middle">{selectedRangeOverlay.label}</text>
            </g>
          ) : null}
          {brushDraftOverlay ? (
            <g className="memory-river-brush-draft" data-brush-range="draft">
              <rect x={brushDraftOverlay.x} y="64" width={brushDraftOverlay.width} height="486" />
            </g>
          ) : null}
          {display.eventTicks.map((tick) => (
            <g className="event-date-tick memory-river-date-tick" key={tick.date}>
              <title>{`${tick.date} UTC · ${tick.count} 个真实事件`}</title>
              <line x1={tick.x} x2={tick.x} y1="528" y2="552" />
              <text x={tick.x} y={tick.stagger ? 612 : 594} textAnchor="middle" className="event-axis-label">{tick.label}</text>
            </g>
          ))}
          {riverDisplay.markers.map((marker) => (
            <g
              className={`memory-river-marker ${marker.kind}${marker.event.id === lockedEventId ? " locked" : ""}`}
              key={marker.id}
              role="button"
              tabIndex={marker.event.node ? 0 : -1}
              onClick={(event) => {
                event.stopPropagation();
                lockMemoryRiverEvent(marker.event);
              }}
              onKeyDown={(keyboardEvent) => {
                if (marker.event.node && isActivationKey(keyboardEvent)) lockMemoryRiverEvent(marker.event);
              }}
              onPointerDown={(event) => event.stopPropagation()}
              onPointerEnter={() => setHoveredEventId(marker.event.id)}
              onPointerLeave={() => {
                if (marker.event.id !== lockedEventId) setHoveredEventId(null);
              }}
            >
              <title>{marker.title}</title>
              <circle cx={marker.x} cy={marker.y} r={marker.radius + 6} />
              <circle cx={marker.x} cy={marker.y} r={marker.radius} />
            </g>
          ))}
          <g className="timeline-cursor memory-river-cursor">
            <line x1={display.cursorX} x2={display.cursorX} y1="58" y2="552" />
            <text x={display.cursorX} y="50" textAnchor="middle">UTC {display.cursorLabel}</text>
          </g>
        </svg>
      ) : (
        <svg className="timeline-canvas" viewBox="0 0 1000 640" role="img" aria-label="动态记忆时间轴" onWheel={handleTimelineWheel}>
          <defs>
            <filter id="softGlow">
              <feGaussianBlur stdDeviation="3.2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {display.densityBars.map((band) => (
            <rect className="timeline-density-backdrop" height={band.height} key={band.key} width={band.width} x={band.x} y={band.y} />
          ))}
          <line x1="80" x2="960" y1="540" y2="540" stroke="rgba(244,241,232,0.28)" strokeWidth="2" />
          {display.ticks.map((tick) => (
            <g key={tick.label}>
              <line x1={tick.x} x2={tick.x} y1="70" y2="548" stroke="rgba(244,241,232,0.08)" />
              <text x={tick.x} y="570" textAnchor="middle" className="axis-label">{tick.label}</text>
            </g>
          ))}
          {display.eventTicks.map((tick) => (
            <g className="event-date-tick" key={tick.date}>
              <title>{`${tick.date} · ${tick.count} 个真实事件`}</title>
              <line x1={tick.x} x2={tick.x} y1="528" y2="552" />
              <text x={tick.x} y={tick.stagger ? 612 : 594} textAnchor="middle" className="event-axis-label">{tick.label}</text>
            </g>
          ))}
          {display.lanes.map((lane) => (
            <g key={lane.key}>
              <line x1="80" x2="960" y1={lane.y} y2={lane.y} stroke={lane.color} opacity="0.2" />
              <text x="28" y={lane.y + 4} className="lane-label">{lane.label}</text>
            </g>
          ))}
          <g className="timeline-cursor">
            <line x1={display.cursorX} x2={display.cursorX} y1="58" y2="552" />
            <text x={display.cursorX} y="50" textAnchor="middle">{display.cursorLabel}</text>
          </g>
          {display.events.map((event) => {
            const node = event.node;
            const selected = event.source.node_id === selectedNode?.id;
            const hovered = event.id === hoveredEventId;
            const statusClass = event.future ? "future" : "past";
            return (
              <g
                className={`timeline-event ${statusClass}${selected ? " selected" : ""}${hovered ? " hovered" : ""}`}
                aria-label={`${event.source.date} · ${normalizeMemoryTier(event.source.memory_tier)} · ${event.source.label}`}
                key={event.id}
                role="button"
                tabIndex={node ? 0 : -1}
                onClick={() => {
                  if (node) onSelectNode(node);
                }}
                onMouseEnter={() => setHoveredEventId(event.id)}
                onMouseLeave={() => setHoveredEventId(null)}
                onKeyDown={(keyboardEvent) => {
                  if (node && isActivationKey(keyboardEvent)) onSelectNode(node);
                }}
              >
                <line x1={event.x} x2={event.x} y1={event.y} y2="540" stroke={event.color} opacity="0.28" />
                <circle cx={event.x} cy={event.y} r={event.radius} fill={event.color} filter="url(#softGlow)" />
                {(event.major || selected || hovered) ? (
                  <text x={Math.min(930, event.x + 10)} y={event.y - 10} className="timeline-point-label">{event.shortLabel}</text>
                ) : null}
              </g>
            );
          })}
        </svg>
      )}
      {timelineRendererMode === "memory-river" && activeRiverEvent ? (
        <div className={`memory-river-event-card${lockedEvent ? " locked" : ""}`} data-event-card={lockedEvent ? "locked" : "hover"}>
          <div>
            <span>{activeRiverEvent.utcDate} UTC · {normalizeMemoryTier(activeRiverEvent.source.memory_tier)} · {humanCategoryLabel(activeRiverEvent.source.category)}</span>
            <strong>{humanizeStatement(activeRiverEvent.node?.statement) || activeRiverEvent.source.label}</strong>
            <small>redacted derived event · {activeRiverEvent.source.importance || "普通"} · {activeRiverEvent.node ? humanThemeLabel(activeRiverEvent.node) : "未连接节点"}</small>
          </div>
          <div className="event-card-actions">
            <button disabled={!activeRiverEvent.node} onClick={() => activeRiverEvent.node && onSelectNode(activeRiverEvent.node)} type="button">
              同步 Inspector
            </button>
            <button onClick={() => lockedEvent ? setLockedEventId(null) : lockMemoryRiverEvent(activeRiverEvent)} type="button">
              {lockedEvent ? "解除锁定" : "锁定事件"}
            </button>
          </div>
        </div>
      ) : null}
      <div className="timeline-event-detail-strip" aria-label="时间轴事件详情">
        {hoveredEvent ? (
          <>
            <div>
              <span>{hoveredEvent.source.date} · {normalizeMemoryTier(hoveredEvent.source.memory_tier)} · {humanCategoryLabel(hoveredEvent.source.category)}</span>
              <strong>{humanizeStatement(hoveredEvent.node?.statement) || hoveredEvent.source.label}</strong>
            </div>
            <button disabled={!hoveredEvent.node} onClick={() => hoveredEvent.node && onSelectNode(hoveredEvent.node)} type="button">
              同步详情
            </button>
          </>
        ) : (
          <p>移动到事件点查看内容；点击事件同步右侧详情。滚轮缩放，窗口滑块定位年份内局部阶段。</p>
        )}
      </div>
    </div>
  );
}
