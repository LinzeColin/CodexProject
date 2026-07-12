import { Suspense, useEffect, useState } from "react";
import { getInitialGalaxyRendererMode, persistGalaxyRendererMode, type GalaxyRendererMode } from "../../config/visualFlags";
import type { AtlasEdge, AtlasNode } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { STARFIELD_MAPPING_VERSION, type StarfieldMappingResult } from "../../models/starfieldMapping";
import { GalaxyScene } from "./lazyScenes";
import { STARFIELD_INTEGRATION_VERSION } from "../../shared/atlas/constants";
import { DeltaStats, TimelineTimeRangeSelection } from "../../shared/atlas/contracts";
import { DeltaStrip } from "../../shared/ui/primitives";



export function GalaxyView({
  graphNodes,
  graphEdges,
  memoryCount,
  selectedNode,
  sharedState,
  deltaStats,
  timelineTimeRange,
  starfieldMapping,
  onSelectNode,
}: {
  graphNodes: AtlasNode[];
  graphEdges: AtlasEdge[];
  memoryCount: number;
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  deltaStats: DeltaStats;
  timelineTimeRange: TimelineTimeRangeSelection | null;
  starfieldMapping: StarfieldMappingResult;
  onSelectNode: (node: AtlasNode) => void;
}) {
  const [galaxyRendererMode, setGalaxyRendererMode] = useState<GalaxyRendererMode>(() => getInitialGalaxyRendererMode());

  function updateGalaxyRendererMode(mode: GalaxyRendererMode) {
    setGalaxyRendererMode(mode);
    persistGalaxyRendererMode(mode);
  }

  useEffect(() => {
    window.__memoryAtlasStage4Phase3 = () => ({
      integrationVersion: STARFIELD_INTEGRATION_VERSION,
      mappingVersion: STARFIELD_MAPPING_VERSION,
      rendererMode: galaxyRendererMode,
      mappingSource: starfieldMapping.source,
      mappedParticleCount: starfieldMapping.particleCount,
      snapshotMappedCount: starfieldMapping.snapshotMappedCount,
      fallbackCount: starfieldMapping.fallbackCount,
      safety: starfieldMapping.safety,
      formulas: starfieldMapping.formulas,
    });
    return () => {
      delete window.__memoryAtlasStage4Phase3;
    };
  }, [galaxyRendererMode, starfieldMapping]);

  return (
    <div
      className="galaxy-view"
      data-stage4-phase3-integration={STARFIELD_INTEGRATION_VERSION}
      data-starfield-mapping-version={starfieldMapping.version}
      data-starfield-mapping-source={starfieldMapping.source}
      data-shared-state={sharedState.schema_version}
      data-shared-focus-node={sharedState.focus.galaxy.nodeId ?? ""}
      data-shared-cluster={sharedState.focus.galaxy.clusterId ?? ""}
    >
      <div className="surface-heading">
        <div>
          <p className="eyebrow">语义银河 / 记忆关系 / 增量观察</p>
          <h2>按主题关系探索记忆密度、局部邻域和近期增量</h2>
        </div>
        <div className="galaxy-heading-actions">
          <span>{memoryCount} 条记忆 / {graphNodes.length} 个节点 / {graphEdges.length} 条连接</span>
          {timelineTimeRange ? <span className="timeline-sync-pill">时间河选择 · {timelineTimeRange.label}</span> : null}
          <div className="galaxy-renderer-toggle" aria-label="Galaxy renderer feature flag">
            <button
              aria-pressed={galaxyRendererMode === "memory-starfield"}
              onClick={() => updateGalaxyRendererMode("memory-starfield")}
              type="button"
            >
              Flow Field
            </button>
            <button
              aria-pressed={galaxyRendererMode === "legacy"}
              onClick={() => updateGalaxyRendererMode("legacy")}
              type="button"
            >
              Legacy
            </button>
          </div>
        </div>
      </div>
      <DeltaStrip stats={deltaStats} />
      <Suspense fallback={<div className="galaxy-loading">正在载入 Three.js 银河...</div>}>
        <GalaxyScene nodes={graphNodes} edges={graphEdges} rendererMode={galaxyRendererMode} selectedNode={selectedNode} starfieldMapping={starfieldMapping} onSelectNode={onSelectNode} />
      </Suspense>
    </div>
  );
}
