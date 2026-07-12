import { X } from "lucide-react";
import type { TierAssetDetail } from "../shared/atlas/contracts";

export type { TierAssetDetail } from "../shared/atlas/contracts";

interface AssetDetailPanelProps {
  asset: TierAssetDetail | null;
  onClose: () => void;
  onOpenTarget: (asset: TierAssetDetail) => void;
}

export function AssetDetailPanel({ asset, onClose, onOpenTarget }: AssetDetailPanelProps) {
  if (!asset) return null;

  return (
    <aside
      aria-label="层级资产明细"
      className="asset-detail-panel"
      data-active-memory-mutation="false"
      data-asset-detail-panel={asset.asset_id}
      data-proposal-only="true"
    >
      <div className="asset-detail-panel-heading">
        <div>
          <span>{asset.asset_tier} / {asset.priority}</span>
          <h4>{asset.title}</h4>
        </div>
        <button aria-label="关闭层级资产明细" onClick={onClose} type="button">
          <X size={16} />
        </button>
      </div>

      <p>{asset.summary}</p>

      <dl className="asset-detail-panel-grid">
        <div><dt>theme</dt><dd>{asset.theme}</dd></div>
        <div><dt>value_score</dt><dd>{formatAssetScore(asset.value_score)}</dd></div>
        <div><dt>importance</dt><dd>{asset.importance}</dd></div>
        <div><dt>priority</dt><dd>{asset.priority}</dd></div>
        <div><dt>confidence</dt><dd>{formatAssetScore(asset.confidence)}</dd></div>
        <div><dt>staleness_status</dt><dd>{asset.staleness_status}</dd></div>
        <div><dt>updated_at</dt><dd>{asset.updated_at}</dd></div>
        <div><dt>last_seen_range</dt><dd>{asset.last_seen_range}</dd></div>
        <div><dt>source_scope</dt><dd>{asset.source_scope}</dd></div>
        <div><dt>evidence_count</dt><dd>{asset.evidence_count.toLocaleString()}</dd></div>
      </dl>

      <section className="asset-detail-section" aria-label="建议资产动作">
        <span>recommended_asset_action</span>
        <p>{asset.recommended_asset_action}</p>
      </section>

      <section className="asset-detail-section" aria-label="关联动作与主题">
        <span>linked_action_ids / linked_topic_ids</span>
        <p>{joinOrEmpty(asset.linked_action_ids)} / {joinOrEmpty(asset.linked_topic_ids)}</p>
      </section>

      <section className="asset-detail-section" aria-label="证据引用">
        <span>evidence_refs</span>
        <ul className="asset-detail-evidence-list">
          {asset.evidence_refs.map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>

      <div className="asset-detail-safety-strip" aria-label="proposal-only asset safety contract">
        <span>{asset.proposal_hint}</span>
        <span>{asset.rollback_hint}</span>
        <span>proposal_only: {String(asset.proposal_only)}</span>
      </div>

      <button className="asset-detail-open-target" onClick={() => onOpenTarget(asset)} type="button">
        打开关联上下文
      </button>
    </aside>
  );
}

function formatAssetScore(value: number): string {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

function joinOrEmpty(values: string[]): string {
  return values.length ? values.join(", ") : "none";
}
