import type { CSSProperties } from "react";
import { normalizeMemoryTier } from "../../data/atlas";
import type { AtlasNode } from "../../types";
import { SemanticInsight, SemanticMatrixCell, WordCloudItem } from "./contracts";
import { emptyHeatColor, heatLevelAnchors, heatStops } from "./runtimeConfig";
import { addDays, isNodeBetween, maxNodeDate, stableUnit, translateKind, truncate } from "./utils";



export function heatIntensityForScore(score: number, maxScore: number, fallbackLevel: number) {
  const level = Math.max(0, Math.min(5, Math.round(fallbackLevel)));
  const levelAnchor = heatLevelAnchors[level] ?? heatLevelAnchors[1];
  const rawRatio = maxScore > 0 ? Math.min(1, Math.max(0.001, score / maxScore)) : 0;
  const logRatio = maxScore > 0 ? Math.log1p(Math.max(0, score)) / Math.log1p(maxScore) : levelAnchor;
  const ratio = Math.max(levelAnchor, logRatio * 0.82 + rawRatio * 0.18);
  return Math.min(1, Math.max(0.08, 0.04 + ratio * 0.96));
}

export function heatColorForScore(score: number, maxScore: number, fallbackLevel: number) {
  if (score <= 0 && fallbackLevel <= 0) return emptyHeatColor;
  return interpolateHeatColor(heatIntensityForScore(score, maxScore, fallbackLevel));
}



export function interpolateHeatColor(value: number) {
  const bounded = Math.min(1, Math.max(0, value));
  let left = heatStops[0];
  let right = heatStops[heatStops.length - 1];
  for (let index = 1; index < heatStops.length; index += 1) {
    if (bounded <= heatStops[index].stop) {
      right = heatStops[index];
      left = heatStops[index - 1];
      break;
    }
  }
  const span = Math.max(0.001, right.stop - left.stop);
  const local = (bounded - left.stop) / span;
  const rgb = left.rgb.map((part, index) => Math.round(part + (right.rgb[index] - part) * local));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}



export function withAlpha(color: string, alpha: number) {
  const match = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
  if (!match) return color;
  return `rgba(${match[1]}, ${match[2]}, ${match[3]}, ${alpha})`;
}



export function buildSemanticInsights(nodes: AtlasNode[]): {
  topics: SemanticInsight[];
  tiers: string[];
  matrixRows: string[];
  matrix: Map<string, SemanticMatrixCell>;
  wordCloud: WordCloudItem[];
} {
  const memoryNodes = nodes.filter((node) => node.kind === "memory");
  const topicMap = new Map<string, SemanticInsight>();
  const wordMap = new Map<string, WordCloudItem>();
  const latest = maxNodeDate(memoryNodes) ?? new Date();
  const recentStart = addDays(latest, -29);

  for (const node of memoryNodes) {
    const topic = compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category);
    const current = topicMap.get(topic) ?? { label: topic, count: 0, roiScore: 0, recentCount: 0, nodes: [] };
    current.count += 1;
    current.roiScore += node.metrics?.roi?.leverage_score ?? 0;
    if (isNodeBetween(node, recentStart, latest)) current.recentCount += 1;
    current.nodes.push(node);
    topicMap.set(topic, current);

    for (const token of semanticTokensForNode(node)) {
      const row = wordMap.get(token) ?? {
        label: token,
        count: 0,
        score: 0,
        x: 8 + stableUnit(token, "word-x") * 78,
        y: 8 + stableUnit(token, "word-y") * 76,
        rotate: stableUnit(token, "word-rotate") > 0.82 ? -8 + stableUnit(token, "word-tilt") * 16 : 0,
        nodes: [],
      };
      row.count += 1;
      row.score += 1 + (node.metrics?.roi?.leverage_score ?? 0);
      row.nodes.push(node);
      wordMap.set(token, row);
    }
  }

  const topics = Array.from(topicMap.values())
    .map((topic) => ({
      ...topic,
      roiScore: topic.count ? topic.roiScore / topic.count : 0,
    }))
    .sort((a, b) => b.count - a.count || b.roiScore - a.roiScore || a.label.localeCompare(b.label, "zh-CN"));
  const tiers = ["核心画像", "一般", "临时"].filter((tier) => memoryNodes.some((node) => normalizeMemoryTier(node.memory_tier) === tier));
  const safeTiers = tiers.length ? tiers : ["未分层"];
  const matrixRows = topics.slice(0, 8).map((topic) => topic.label);
  const matrix = new Map<string, SemanticMatrixCell>();
  for (const row of matrixRows) {
    for (const tier of safeTiers) {
      const cellNodes = (topicMap.get(row)?.nodes ?? []).filter((node) => normalizeMemoryTier(node.memory_tier) === tier);
      matrix.set(`${row}::${tier}`, { topic: row, tier, count: cellNodes.length, nodes: cellNodes });
    }
  }
  const wordCloud = Array.from(wordMap.values())
    .sort((a, b) => b.score - a.score || b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, 42);

  return { topics, tiers: safeTiers, matrixRows, matrix, wordCloud };
}



export function semanticTokensForNode(node: AtlasNode): string[] {
  const themeTokens = humanThemeLabel(node)
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean);
  const categoryTokens = [humanCategoryLabel(node.category), normalizeMemoryTier(node.memory_tier)].filter(Boolean);
  const textTokens = `${node.label} ${node.statement ?? ""}`
    .match(/[A-Za-z][A-Za-z0-9+_-]{2,}|[\u4e00-\u9fff]{2,8}/g)
    ?.map((token) => token.trim())
    .filter((token) => token.length >= 2 && !semanticStopwords.has(token.toLowerCase()))
    .slice(0, 8) ?? [];
  return Array.from(new Set([...themeTokens, ...categoryTokens, ...textTokens]))
    .map((token) => truncate(token.replace(/^(核心画像|一般|临时)\s*·\s*/, ""), 16))
    .filter((token) => token && !semanticStopwords.has(token.toLowerCase()));
}



export const semanticStopwords = new Set([
  "静态图谱低敏摘要",
  "层级",
  "分类",
  "重要性",
  "有效期",
  "主题",
  "unknown",
  "memory",
  "一般短期",
  "重要中长期",
]);



export function selectRepresentativeNode(nodes: AtlasNode[]): AtlasNode | null {
  return [...nodes].sort((a, b) => {
    const roi = (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0);
    if (roi !== 0) return roi;
    if ((b.importance === "高") !== (a.importance === "高")) return b.importance === "高" ? -1 : 1;
    return (b.date ?? "").localeCompare(a.date ?? "");
  })[0] ?? null;
}



export function semanticHeatStyle(count: number, maxCount: number): CSSProperties {
  const level = count <= 0 ? 0 : Math.max(1, Math.min(5, Math.ceil((count / Math.max(1, maxCount)) * 5)));
  const color = heatColorForScore(count, maxCount, level);
  return {
    "--semantic-bg": count ? `linear-gradient(145deg, ${withAlpha(color, 0.72)}, ${color})` : "rgba(15, 17, 22, 0.9)",
    "--semantic-border": count ? withAlpha(color, 0.72) : "rgba(244, 241, 232, 0.08)",
  } as CSSProperties;
}



export function semanticColor(index: number): string {
  const palette = ["#7ee8d4", "#8fd3ff", "#48c7e8", "#f48fb1", "#c7a7ff", "#6ea8ff", "#94a3b8"];
  return palette[index % palette.length];
}



export function wordCloudStyle(item: WordCloudItem, maxScore: number): CSSProperties {
  const ratio = Math.min(1, Math.max(0.12, item.score / Math.max(1, maxScore)));
  const size = 11 + Math.sqrt(ratio) * 23;
  return {
    "--word-x": `${item.x}%`,
    "--word-y": `${item.y}%`,
    "--word-rotate": `${item.rotate}deg`,
    "--word-size": `${size}px`,
    "--word-color": heatColorForScore(item.score, maxScore, Math.ceil(ratio * 5)),
  } as CSSProperties;
}



export function buildHumanNodeSummary(node: AtlasNode, edgeCount: number) {
  const theme = humanThemeLabel(node);
  const categoryLabel = humanCategoryLabel(node.category);
  const tier = normalizeMemoryTier(node.memory_tier);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const topics = splitHumanTopics(theme);
  const memoryType = tier !== "未分层" ? `${tier} / ${categoryLabel}` : categoryLabel;
  const status = humanMemoryStatus(node);
  return {
    title,
    subtitle: buildHumanNodeSubtitle(node, theme, continuityMemory),
    scope: `人类视图 · ${tier !== "未分层" ? tier : categoryLabel}`,
    meaning: buildMeaningBullets(node, theme, continuityMemory),
    impact: buildHumanImpact(node, edgeCount, continuityMemory),
    futureUse: buildFutureUseItems(node, continuityMemory),
    topics,
    statusRows: [
      { label: "记忆类型", value: memoryType },
      { label: "适用对象", value: continuityMemory ? "ChatGPT / Codex / 任意 Agent" : humanApplicableScope(node) },
      { label: "首次记录", value: node.date || "未知" },
      { label: "当前状态", value: status },
      { label: "关联数量", value: edgeCount.toLocaleString() },
      { label: "可信度", value: node.confidence || "未知" },
    ],
    agentMemory: buildAgentMemoryLine(node, title, continuityMemory),
    agentMeta: buildAgentMetaLine(node, theme, status),
  };
}



export function recommendedActionForNode(node: AtlasNode): string {
  if (node.category === "answering_rule") return "作为未来回答和验收标准，执行前先检查。";
  if (node.category === "decision") return "作为已做出的选择，后续方案默认继承并记录影响。";
  if (node.category === "project_context") return "用于恢复项目背景，继续任务前先读关联项目和下一步。";
  if (node.category === "workflow") return "沉淀成可复用流程、Skill 或自动化检查。";
  if (node.category === "security_boundary") return "作为硬边界处理，涉及外部写入、交易、secret 时先确认。";
  if (node.category === "deprecated_info") return "保留历史轨迹，但回答时标明可能过时，避免当成当前事实。";
  if (node.category === "temporary_or_sensitive") return "低权重召回，只在当前任务相关时读取，不要污染长期画像。";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "优先进入 personalization，影响所有 agent 的默认行为。";
  if (tier === "一般") return "保留为一般上下文，用于项目连续性和决策复盘。";
  return "作为背景资料保留，必要时再展开。";
}



export function isMemoryContinuityNode(node: AtlasNode, theme: string): boolean {
  const text = `${node.label} ${node.statement ?? ""} ${theme} ${node.visual?.cluster ?? ""}`.toLowerCase();
  return (
    text.includes("memory-rag-continuity") ||
    text.includes("长期记忆") ||
    text.includes("memory atlas") ||
    text.includes("openaidatabase") ||
    text.includes("rag") ||
    text.includes("personalization") ||
    text.includes("agent continuity")
  );
}



export function humanNodeTitle(node: AtlasNode, theme?: string, continuityMemory = false): string {
  const compactTheme = compactThemeLabel(theme ?? humanThemeLabel(node));
  if (continuityMemory && node.category === "answering_rule") {
    return `回答规则：${compactTheme || "长期记忆库"}先于执行`;
  }
  if (node.category === "answering_rule") return `回答规则：${compactTheme || "交付标准"}`;
  if (node.category === "decision") return `决策：${compactTheme || "重要选择"}`;
  if (node.category === "project_context") return `项目背景：${compactTheme || "上下文"}`;
  if (node.category === "workflow") return `工作流：${compactTheme || "可复用流程"}`;
  if (node.category === "preference") return `偏好：${compactTheme || "判断标准"}`;
  if (node.category === "security_boundary") return `安全边界：${compactTheme || "高风险动作"}`;
  if (node.category === "deprecated_info") return `历史信息：${compactTheme || "默认低权重"}`;
  return node.label
    .replace(/^(核心画像|一般|临时|重要中长期|一般短期)\s*·\s*/, "")
    .replace(/\s*·\s*/g, " / ")
    .slice(0, 72);
}



export function buildHumanNodeSubtitle(node: AtlasNode, theme: string, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "这条记忆的重点不是数据库字段，而是让未来任何 agent 先理解你的画像、偏好、项目历史、决策标准和回答规则，再开始工作。";
  }
  if (node.kind !== "memory") {
    return "这是一个导航节点，用来把相关主题、项目、决策、时间线和记忆连接起来，帮助你从全局理解历史轨迹。";
  }
  if (node.category === "answering_rule") return "这是一条会影响未来回答方式和交付验收标准的长期规则。";
  if (node.category === "decision") return "这记录了一个已做出的选择，后续规划和 agent 执行应默认继承。";
  if (node.category === "project_context") return "这保存项目背景，目的是降低换线程、换 agent 或隔一段时间后继续工作的成本。";
  if (node.category === "preference") return "这记录你的偏好、taste 或判断标准，未来 personalization 应优先使用。";
  return `这条记忆和「${theme}」有关，适合用于复盘、搜索、上下文恢复和未来 agent 个性化。`;
}



export function buildMeaningBullets(node: AtlasNode, theme: string, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "你不希望 AI 只记住设置页里很短的 personalization，而是要有完整、长期、可追溯的记忆数据库。",
      "ChatGPT、Codex 和未来任意 agent 都应能读取同一套画像、偏好、历史项目、决策标准和回答规则。",
      "前端默认展示人类能理解的结论、机会、建议和待办；完整原文和高敏内容只给授权 agent 读取。",
    ];
  }
  if (node.kind !== "memory") {
    return [
      `它把「${theme}」相关的记忆集中到同一个导航对象。`,
      "点击它的价值是快速找到相关历史、项目、决策和行为模式。",
    ];
  }
  if (node.category === "decision") {
    return [
      "这里记录的是已经做出的选择，不应在未来任务中反复重新讨论。",
      "后续 agent 应把它作为默认背景，并在新证据出现时再提出修改建议。",
    ];
  }
  if (node.category === "answering_rule") {
    return [
      "这里记录的是未来回答和交付方式需要遵守的规则。",
      "它的用途是提高回答稳定性，减少你重复纠正同类问题的次数。",
    ];
  }
  if (node.category === "project_context") {
    return [
      "这里保存的是项目背景、历史进展或上下文，不是一次性的聊天片段。",
      "它能帮助新线程、新 agent 或未来的你快速恢复任务状态。",
    ];
  }
  const cleanStatement = humanizeStatement(node.statement);
  return [
    cleanStatement || `这是一条关于「${theme}」的记忆，适合用于搜索、复盘和上下文恢复。`,
    recommendedActionForNode(node),
  ];
}



export function buildHumanImpact(node: AtlasNode, edgeCount: number, continuityMemory: boolean): string {
  if (continuityMemory) {
    return "它直接影响所有未来 AI 协作质量：减少重复解释、降低上下文成本、提高项目接续能力，并让 agent 更接近长期了解你的工作伙伴。";
  }
  if (node.category === "answering_rule") return "它能减少重复纠错，让不同 agent 在回答风格、验收标准和执行边界上更一致。";
  if (node.category === "decision") return "它能避免重复决策，让后续计划沿着既定方向推进，同时保留未来修正的证据入口。";
  if (node.category === "project_context") return "它能降低项目切换成本，让历史背景、当前状态和下一步行动更容易被恢复。";
  if (node.category === "preference") return "它会影响未来 personalization，让回答更贴近你的 taste、偏好、风险边界和决策方式。";
  if (node.category === "security_boundary") return "它属于硬边界信息，能防止 agent 在外部写入、隐私、交易或 secret 场景里越权。";
  const connectionText = edgeCount ? `当前有 ${edgeCount.toLocaleString()} 个关联，` : "";
  return `${connectionText}它的价值在于帮助你看清反复出现的主题、行为习惯和潜在机会，而不是只作为后台索引。`;
}



export function buildFutureUseItems(node: AtlasNode, continuityMemory: boolean): string[] {
  if (continuityMemory) {
    return [
      "新 agent 启动前先读取 Memory Atlas / OpenAIDatabase，再生成适配你的 profile、preference 和项目上下文。",
      "回答时优先遵守你的长期偏好、交付标准、历史决策和安全边界。",
      "发现新偏好、新规则或新项目决策时，先生成可审查、可回滚的 memory update candidate。",
    ];
  }
  if (node.category === "security_boundary") {
    return ["涉及外部写入、交易、secret、隐私或权限时先停下来确认。", "把它作为 agent 执行前的硬性检查项。"];
  }
  if (node.category === "workflow") {
    return ["把它沉淀成可复用 skill、Task Pack 或自动化检查。", "未来相似任务先套用这套流程，再根据新证据调整。"];
  }
  if (node.category === "deprecated_info") {
    return ["保留历史轨迹，但回答时明确它可能过时。", "如果新资料冲突，应以更新证据为准并生成修改提案。"];
  }
  return [recommendedActionForNode(node), "如果这条记忆影响未来回答，建议在下方写回提案里补充更清晰的人类结论。"];
}



export function humanNodeDisplayTitle(node: AtlasNode): string {
  const theme = humanThemeLabel(node);
  return humanNodeTitle(node, theme, isMemoryContinuityNode(node, theme));
}



export function buildSearchResultPreview(node: AtlasNode, duplicateCount: number): { title: string; summary: string; meta: string } {
  const theme = humanThemeLabel(node);
  const continuityMemory = isMemoryContinuityNode(node, theme);
  const title = humanNodeTitle(node, theme, continuityMemory);
  const summary = humanizeStatement(node.statement) || buildHumanNodeSubtitle(node, theme, continuityMemory);
  const meta = [
    normalizeMemoryTier(node.memory_tier),
    humanCategoryLabel(node.category),
    node.date || "未知日期",
    duplicateCount > 1 ? `已合并 ${duplicateCount.toLocaleString()} 条同类记录` : "",
  ].filter(Boolean).join(" / ");
  return { title, summary, meta };
}



export function dedupeNodesForDisplay(nodes: AtlasNode[]): Array<{ node: AtlasNode; duplicateCount: number }> {
  const rows = new Map<string, { node: AtlasNode; duplicateCount: number }>();
  for (const node of nodes) {
    const title = humanNodeDisplayTitle(node);
    const theme = humanThemeLabel(node);
    const summary = humanizeStatement(node.statement);
    const keySource = node.category === "answering_rule"
      ? `${node.kind}|${node.category}|${normalizeMemoryTier(node.memory_tier)}|${theme}`
      : `${node.kind}|${node.category}|${title}|${summary || node.label}`;
    const key = normalizeDisplayKey(keySource);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
    } else {
      rows.set(key, { node, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}



export function dedupeRecommendationItems(
  items: Array<{ id: string; title: string; statement: string; evidence_count?: number; reason?: string }>,
): Array<{ item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }> {
  const rows = new Map<string, { item: { id: string; title: string; statement: string; evidence_count?: number; reason?: string }; duplicateCount: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(`${humanizeRecommendationTitle(item.title)}|${humanizeStatement(item.statement)}`);
    const current = rows.get(key);
    if (current) {
      current.duplicateCount += 1;
      current.item.evidence_count = Math.max(current.item.evidence_count ?? 0, item.evidence_count ?? 0);
    } else {
      rows.set(key, { item, duplicateCount: 1 });
    }
  }
  return [...rows.values()];
}



export function dedupeDisplayItems(items: string[], limit: number): string[] {
  const rows = new Map<string, { text: string; count: number }>();
  for (const item of items) {
    const key = normalizeDisplayKey(item);
    const current = rows.get(key);
    if (current) {
      current.count += 1;
    } else {
      rows.set(key, { text: item, count: 1 });
    }
  }
  return [...rows.values()].slice(0, limit).map((row) => (
    row.count > 1 ? `${row.text}（另有 ${row.count - 1} 条同类记录）` : row.text
  ));
}



export function humanizeRecommendationTitle(value: string): string {
  return truncate(value
    .replace(/^(Memory|Meta Data)\s*·\s*/i, "")
    .replace(/answering_rule/g, "回答规则")
    .replace(/project_context/g, "项目上下文")
    .replace(/security_boundary/g, "安全边界")
    .replace(/temporary_or_sensitive/g, "短期/敏感背景")
    .replace(/\s*·\s*/g, " / "), 72);
}



export function recommendationMeta(
  item: { evidence_count?: number },
  duplicateCount: number,
): string {
  const parts = [`证据 ${item.evidence_count ?? 0}`];
  if (duplicateCount > 1) parts.push(`合并 ${duplicateCount.toLocaleString()} 条同类`);
  return parts.join(" / ");
}



export function splitHumanTopics(theme: string): string[] {
  return theme
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 8);
}



export function humanMemoryStatus(node: AtlasNode): string {
  if (node.category === "deprecated_info") return "保留历史，默认不作为当前事实";
  if (node.validity === "临时") return "临时有效";
  if (node.validity === "项目结束前") return "项目期内有效";
  return "有效";
}



export function humanApplicableScope(node: AtlasNode): string {
  if (node.category === "answering_rule") return "所有未来回答";
  if (node.category === "preference") return "Personalization / Profile";
  if (node.category === "project_context") return "相关项目和接续任务";
  if (node.category === "workflow") return "Codex / Agent 工作流";
  if (node.category === "security_boundary") return "所有高风险动作";
  return "搜索 / 复盘 / 相关 Agent";
}



export function buildAgentMemoryLine(node: AtlasNode, title: string, continuityMemory: boolean): string {
  const prefix = continuityMemory ? "核心 personalization" : humanCategoryLabel(node.category);
  return `${prefix}：${title}。未来 agent 应把这条记忆用于画像、偏好、历史上下文或回答规则恢复；新增/修改/删除需走下方写回提案。`;
}



export function buildAgentMetaLine(node: AtlasNode, theme: string, status: string): string {
  return [
    `层级=${normalizeMemoryTier(node.memory_tier)}`,
    `分类=${node.category || "未知"}`,
    `重要性=${node.importance || "未知"}`,
    `有效期=${node.validity || "未知"}`,
    `状态=${status}`,
    `主题=${theme}`,
  ].join("；");
}



export function humanizeStatement(value: string | undefined): string {
  if (!value) return "";
  const withoutPrefix = value
    .replace(/^静态图谱低敏摘要[：:]\s*/, "")
    .replace(/层级=/g, "层级是")
    .replace(/分类=/g, "分类是")
    .replace(/重要性=/g, "重要性是")
    .replace(/有效期=/g, "有效期是")
    .replace(/主题=/g, "主题是");
  return truncate(withoutPrefix, 150);
}



export function compactThemeLabel(value: string): string {
  return value
    .replace(/agent continuity/gi, "Agent 连续性")
    .replace(/agent/gi, "Agent")
    .replace(/workflow/gi, "工作流")
    .replace(/token/gi, "Token")
    .replace(/dashboard/gi, "仪表盘")
    .split("/")
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2)
    .join(" / ")
    .slice(0, 38);
}



export function normalizeDisplayKey(value: string): string {
  return value
    .toLowerCase()
    .replace(/\s+/g, "")
    .replace(/[，。；：、/|·:;,.()[\]（）【】「」]/g, "")
    .trim();
}



export function humanThemeLabel(node: AtlasNode): string {
  const cluster = node.visual?.cluster;
  if (cluster) return themeLabelFromCluster(cluster);
  const parts = node.label.split("·").map((part) => part.trim()).filter(Boolean);
  return parts[2] || node.category || normalizeMemoryTier(node.memory_tier) || translateKind(node.kind);
}



export function themeLabelFromCluster(cluster: string): string {
  const labels: Record<string, string> = {
    "memory-rag-continuity": "长期记忆库 / RAG / Agent 连续性",
    "codex-agent-workflow": "Codex / Agent 工作流 / Token ROI",
    "learning-notion-nitrosend": "学习系统 / Notion / 仪表盘",
    "rotary-kiln-industrial": "回转窑 / 工业服务 / 动态测量调整",
    "finance-trading-probability": "金融 / 交易 / FIFA / 概率决策",
    "course-reporting": "课程 / 公司报告 / 可持续报告",
    "ai-era-growth": "AI 时代 / 社会影响 / 个人能力突破",
    "formal-engineering-delivery": "EVA OS / 系统开发 / Task Pack",
    uncategorized: "其他待人工归类主题",
  };
  return labels[cluster] ?? cluster;
}



export function humanCategoryLabel(value: string | undefined): string {
  const labels: Record<string, string> = {
    answering_rule: "回答规则",
    codex_agent_metadata: "Codex agent 元数据",
    codex_development_record: "Codex 开发记录",
    codex_personalization: "Codex 个性化上下文",
    codex_usage_record: "Codex 使用记录",
    decision: "重要决策",
    deprecated_info: "历史/可能过时信息",
    fact: "事实资料",
    preference: "个人偏好",
    project_context: "项目上下文",
    security_boundary: "安全边界",
    temporary_or_sensitive: "短期/敏感背景",
    workflow: "工作流",
  };
  return labels[value ?? ""] ?? value ?? "未分类";
}



export function countBy<T>(items: T[], getKey: (item: T) => string): Record<string, number> {
  return items.reduce<Record<string, number>>((acc, item) => {
    const key = getKey(item) || "未分类";
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});
}



export function remapValues(values: Record<string, number>, mapKey: (key: string) => string): Record<string, number> {
  return Object.entries(values).reduce<Record<string, number>>((acc, [key, count]) => {
    const label = mapKey(key) || "未分类";
    acc[label] = (acc[label] ?? 0) + count;
    return acc;
  }, {});
}



export function topRows(values: Record<string, number>, limit: number): Array<{ label: string; count: number }> {
  const rows = Object.entries(values)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "zh-CN"))
    .slice(0, limit);
  return rows.length ? rows : [{ label: "暂无数据", count: 0 }];
}



export function buildSearchVisualRows(nodes: AtlasNode[]): {
  topics: Array<{ label: string; count: number }>;
  tiers: Array<{ label: string; count: number }>;
  signals: Array<{ label: string; count: number }>;
} {
  const latest = maxNodeDate(nodes) ?? new Date();
  const recentStart = addDays(latest, -29);
  return {
    topics: topRows(countBy(nodes, (node) => compactThemeLabel(humanThemeLabel(node)) || humanCategoryLabel(node.category)), 7),
    tiers: topRows(countBy(nodes, (node) => normalizeMemoryTier(node.memory_tier)), 4),
    signals: [
      { label: "近 30 天", count: nodes.filter((node) => isNodeBetween(node, recentStart, latest)).length },
      { label: "决策", count: nodes.filter((node) => node.category === "decision").length },
      { label: "核心画像", count: nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像").length },
      { label: "待行动", count: nodes.filter((node) => /todo|action|执行|继续|需要|下一步/i.test(`${node.label} ${node.statement ?? ""}`)).length },
    ],
  };
}
