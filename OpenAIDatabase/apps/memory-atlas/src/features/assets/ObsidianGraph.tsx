import { Suspense } from "react";
import type { AtlasEdge, AtlasNode } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { ObsidianGraphScene } from "./lazyScenes";
import { DeltaStats } from "../../shared/atlas/contracts";



export function ObsidianGraph({
  nodes,
  edges,
  selectedNode,
  sharedState,
  deltaStats,
  onSelectNode,
}: {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  selectedNode: AtlasNode | null;
  sharedState: SharedAtlasState;
  deltaStats: DeltaStats;
  onSelectNode: (node: AtlasNode) => void;
}) {
  return (
    <Suspense fallback={<div className="galaxy-loading">正在载入 Obsidian 动态图谱...</div>}>
      <ObsidianGraphScene nodes={nodes} edges={edges} selectedNode={selectedNode} sharedFocus={sharedState.focus} deltaStats={deltaStats} onSelectNode={onSelectNode} />
    </Suspense>
  );
}
