import { GitBranch } from "lucide-react";
import type { ReactNode } from "react";
import type { MemoryAtlas } from "../../types";
import { FilteredAtlasSlice } from "../atlas/contracts";



export function viewEmptyState(atlas: MemoryAtlas, slice: FilteredAtlasSlice): "empty-atlas" | "no-filtered-results" | null {
  if (slice.memoryNodes.length || slice.graphNodes.length) return null;
  if (slice.filterActive) return "no-filtered-results";
  const hasSnapshotData =
    atlas.nodes.length > 0 ||
    atlas.edges.length > 0 ||
    atlas.timeline.length > 0 ||
    atlas.overview.active_memory_count > 0;
  return hasSnapshotData ? null : "empty-atlas";
}



export function MachineFieldDetails({ title, className = "", children }: { title: string; className?: string; children: ReactNode }) {
  return (
    <details
      className={`machine-field-details${className ? ` ${className}` : ""}`}
      data-s10-p3-machine-fields="collapsed-by-default"
    >
      <summary>
        <GitBranch size={14} />
        <span>{title}</span>
      </summary>
      {children}
    </details>
  );
}



export function EvidenceRefsDetails({ refs }: { refs: string[] }) {
  return (
    <MachineFieldDetails title={`高级详情：证据字段（${refs.length.toLocaleString()} 条）`} className="inline-machine-field-details">
      <p className="machine-field-help">默认折叠。这里仅给 ChatGPT / Codex 核验证据引用，不作为首屏阅读内容。</p>
      <small>evidence_refs：{refs.join(" / ") || "none"}</small>
    </MachineFieldDetails>
  );
}
