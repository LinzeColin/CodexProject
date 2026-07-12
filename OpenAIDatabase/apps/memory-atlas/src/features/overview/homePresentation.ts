import { HOME_LEVEL_ASSET_GROUPS, HOME_THEME_CATEGORY_STATES } from "../../shared/atlas/constants";
import { HomeAction, HomeActionDetail, HomeTierAsset, HomeTopicDetail, TierAssetDetail, TopicClassificationDetail } from "../../shared/atlas/contracts";



export function buildHomeActionStatusChips(actions: HomeAction[]): Array<{ id: HomeActionDetail["status"]; label: string; count: number }> {
  const statuses: HomeActionDetail["status"][] = ["proposed", "review", "blocked", "done_safe"];
  return statuses.map((status) => ({
    count: actions.filter((action) => action.status === status).length,
    id: status,
    label: humanActionStatusLabel(status),
  }));
}



export function humanPriorityLabel(priority?: string): string {
  return ({ P0: "立即判断", P1: "优先处理", P2: "随后处理", P3: "持续观察" } as Record<string, string>)[priority ?? ""] ?? "待判断";
}



export function humanActionStatusLabel(status: HomeActionDetail["status"]): string {
  return ({ proposed: "待判断", review: "待复核", blocked: "受阻", done_safe: "已安全完成" } as Record<HomeActionDetail["status"], string>)[status];
}



export function humanEffortLabel(effort: HomeActionDetail["effort_cost"]): string {
  return ({ low: "低投入", medium: "中等投入", high: "高投入" } as Record<HomeActionDetail["effort_cost"], string>)[effort];
}



export function humanUrgencyLabel(urgency: HomeActionDetail["urgency"]): string {
  return ({ low: "低紧迫", medium: "中等紧迫", high: "高紧迫" } as Record<HomeActionDetail["urgency"], string>)[urgency];
}



export type HomeLevelAssetGroupId = (typeof HOME_LEVEL_ASSET_GROUPS)[number]["id"];


export type HomeThemeCategoryStateId = (typeof HOME_THEME_CATEGORY_STATES)[number]["id"];



export function buildLevelAssetGroupChips(assets: HomeTierAsset[]): Array<{ id: HomeLevelAssetGroupId; label: string; count: number }> {
  return HOME_LEVEL_ASSET_GROUPS.map((group) => ({
    count: assets.filter((asset) => homeLevelAssetGroupFor(asset) === group.id).length,
    id: group.id,
    label: group.label,
  }));
}



export function homeLevelAssetGroupFor(asset: TierAssetDetail): HomeLevelAssetGroupId {
  if (asset.asset_tier === "core_profile") return "core_profile";
  if (asset.asset_tier === "project") return "project";
  if (asset.asset_tier === "decision") return "decision";
  if (asset.asset_tier === "stale" || asset.staleness_status === "stale") return "stale";
  return "temporary";
}



export function buildThemeCategoryChips(topics: HomeTopicDetail[]): Array<{ id: HomeThemeCategoryStateId; label: string; count: number }> {
  return HOME_THEME_CATEGORY_STATES.map((state) => ({
    count: topics.filter((topic) => homeThemeCategoryFor(topic) === state.id).length,
    id: state.id,
    label: state.label,
  }));
}



export function homeThemeCategoryFor(topic: TopicClassificationDetail): HomeThemeCategoryStateId {
  if (topic.topic_state === "rising") return "rising";
  if (topic.topic_state === "declining" || topic.topic_state === "stale" || topic.topic_state === "black_hole") return "declining";
  if (topic.topic_state === "conflict") return "conflict";
  if (topic.topic_state === "emerging" || (topic.roi_score >= 0.58 && topic.trend !== "down")) return "opportunity";
  return "stable";
}
