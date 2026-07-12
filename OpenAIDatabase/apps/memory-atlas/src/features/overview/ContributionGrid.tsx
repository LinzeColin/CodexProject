import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import type { AtlasFilters, AtlasNode, MemoryAtlas } from "../../types";
import { ContributionPeriodDetail, ContributionScale, DeltaStats } from "../../shared/atlas/contracts";
import { buildContributionPeriodDetail, buildContributionPeriods, contributionTitle, defaultPeriodKeyForScale, maxActivityScore, scaleLabel } from "../../shared/atlas/contributionModels";
import { weekdayLabels } from "../../shared/atlas/runtimeConfig";
import { contributionYears, formatSigned } from "../../shared/atlas/utils";
import { DeltaStrip, InsightCard } from "../../shared/ui/primitives";
import { heatCellStyle, monthBarStyle, trendGradient, trendSegmentStyle, yearCellStyle } from "../../shared/ui/visualStyles";



export function ContributionGrid({
  atlas,
  nodes,
  filters,
  deltaStats,
  onSelectPeriod,
}: {
  atlas: MemoryAtlas;
  nodes: AtlasNode[];
  filters: AtlasFilters;
  deltaStats: DeltaStats;
  onSelectPeriod: (detail: ContributionPeriodDetail) => void;
}) {
  const [scale, setScale] = useState<ContributionScale>("day");
  const availableYears = useMemo(() => contributionYears(atlas, nodes), [atlas, nodes]);
  const [selectedYear, setSelectedYear] = useState(() => availableYears[availableYears.length - 1] ?? new Date().getUTCFullYear());
  useEffect(() => {
    if (!availableYears.length) return;
    if (!availableYears.includes(selectedYear)) {
      setSelectedYear(availableYears[availableYears.length - 1]);
    }
  }, [availableYears, selectedYear]);
  const periodData = useMemo(() => buildContributionPeriods(atlas, nodes, filters, selectedYear), [atlas, nodes, filters, selectedYear]);
  const [selectedPeriod, setSelectedPeriod] = useState("");
  const selected = periodData.periods.get(selectedPeriod) ?? periodData.defaultPeriod;
  const selectedDetail = useMemo(
    () => buildContributionPeriodDetail(scale, selected, nodes),
    [nodes, scale, selected],
  );
  const isDayOrWeek = scale === "day" || scale === "week";
  const dayWeekModeClass = scale === "week" ? "week-mode" : "day-mode";

  useEffect(() => {
    setSelectedPeriod(defaultPeriodKeyForScale(scale, periodData));
  }, [periodData, scale]);

  useEffect(() => {
    onSelectPeriod(selectedDetail);
  }, [onSelectPeriod, selectedDetail]);

  return (
    <div className="contribution-view visual-workspace">
      <div className="surface-heading compact">
        <div>
          <p className="eyebrow">使用强度 / 记忆增量 / 时间尺度对比</p>
          <h2>按日、周、月、年观察交互强度和记忆增量</h2>
        </div>
        <span>{periodData.year} 年 / 数据 {atlas.contribution.range_start || "暂无"}-{atlas.contribution.range_end || "暂无"}</span>
      </div>
      <div className="contribution-toolbar">
        <DeltaStrip stats={deltaStats} compact />
        <div className="scale-tabs" role="group" aria-label="贡献网格尺度">
          {(["day", "week", "month", "year"] as ContributionScale[]).map((item) => (
            <button className={scale === item ? "segmented active" : "segmented"} key={item} onClick={() => setScale(item)} type="button">
              {scaleLabel(item)}
            </button>
          ))}
        </div>
        <label className="year-picker">
          <span>年份</span>
          <select value={selectedYear} onChange={(event) => setSelectedYear(Number(event.target.value))}>
            {availableYears.map((yearOption) => (
              <option key={yearOption} value={yearOption}>
                {yearOption}
              </option>
            ))}
          </select>
        </label>
      </div>
      <HeatLegend />
      {isDayOrWeek ? (
        <div className={`year-heatmap-wrap ${scale === "week" ? "week-scale" : "day-scale"}`}>
          <div className="year-heatmap-body">
            <div className="weekday-label-column" aria-hidden="true">
              {weekdayLabels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div
              className={`year-heatmap ${dayWeekModeClass}`}
              style={{
                "--week-columns": periodData.weekColumns,
              } as CSSProperties}
            >
              {scale === "week"
                ? periodData.weekCells.map((cell) => {
                    const active = selectedPeriod === cell.weekKey;
                    return (
                      <button
                        className={`week-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.weekKey}
                        onClick={() => setSelectedPeriod(cell.weekKey)}
                        style={
                          {
                            ...heatCellStyle(cell, periodData.weekMaxActivityScore),
                            gridColumn: cell.weekColumn + 1,
                            gridRow: "1 / span 7",
                            "--trend-gradient": trendGradient(cell.daySlots, "180deg", periodData.dayMaxActivityScore),
                          } as CSSProperties
                        }
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <div className="cell-trend week-trend smooth-trend" aria-hidden="true">
                          {cell.daySlots.map((slot, index) => (
                            <i
                              className={`trend-segment level-${slot?.activityLevel ?? 0}${slot ? "" : " empty"}`}
                              key={slot?.date ?? index}
                              style={trendSegmentStyle(slot, periodData.dayMaxActivityScore)}
                            />
                          ))}
                        </div>
                        <span>{cell.label}</span>
                      </button>
                    );
                  })
                : periodData.dailyCells.map((cell) => {
                    const active = selectedPeriod === cell.date;
                    return (
                      <button
                        className={`heat-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                        key={cell.date}
                        onClick={() => setSelectedPeriod(cell.date)}
                        style={{ ...heatCellStyle(cell, periodData.dayMaxActivityScore), gridColumn: cell.weekColumn + 1, gridRow: cell.weekday + 1 }}
                        title={contributionTitle(cell)}
                        type="button"
                      >
                        <span>{cell.date}</span>
                      </button>
                    );
                  })}
            </div>
          </div>
          <div className="week-label-shell">
            <span aria-hidden="true" />
            <div className="week-label-row" style={{ "--week-columns": periodData.weekColumns } as CSSProperties}>
              {Array.from({ length: periodData.weekColumns }, (_, index) => (
                <span key={index}>{index % 2 === 0 ? `W${index + 1}` : ""}</span>
              ))}
            </div>
          </div>
        </div>
      ) : scale === "year" ? (
        <div className="year-trend-grid year-comparison-trend">
          {periodData.yearCells.map((cell) => {
            const periodKey = String(cell.year);
            const active = selectedPeriod === periodKey;
            return (
              <button
                aria-label={`${cell.year} 年，活动得分 ${cell.activityScore}，环比 ${formatSigned(cell.delta ?? 0)}`}
                className={`year-cell year-summary-card level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={periodKey}
                onClick={() => setSelectedPeriod(periodKey)}
                style={yearCellStyle(cell, periodData.yearMaxActivityScore)}
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="year-card-header">
                  <strong>{cell.year}</strong>
                  <span>{cell.activityScore.toLocaleString()} 分</span>
                </div>
                <div className="year-month-track" aria-hidden="true">
                  {cell.monthSlots.map((slot) => (
                    <i className={`year-month-bar level-${slot.activityLevel}`} key={slot.date} style={monthBarStyle(slot, cell.monthSlots)} />
                  ))}
                </div>
                <div className="year-month-axis" aria-hidden="true">
                  <span>Q1</span>
                  <span>Q2</span>
                  <span>Q3</span>
                  <span>Q4</span>
                </div>
                <div className="year-card-footer">
                  <span>消息 {cell.messageCount.toLocaleString()}</span>
                  <span>记忆 {cell.filteredMemoryCount.toLocaleString()}</span>
                  <span className={(cell.delta ?? 0) >= 0 ? "positive" : "negative"}>{formatSigned(cell.delta ?? 0)}</span>
                </div>
                <span>{cell.label}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="month-heatmap">
          {periodData.monthCells.map((cell) => {
            const periodKey = cell.date;
            const active = selectedPeriod === periodKey;
            const monthTrendMax = maxActivityScore(cell.daySlots);
            return (
              <button
                className={`month-cell level-${cell.activityLevel}${active ? " selected" : ""}`}
                key={cell.date}
                onClick={() => setSelectedPeriod(periodKey)}
                style={
                  {
                    ...heatCellStyle(cell, periodData.monthMaxActivityScore),
                    "--trend-gradient": trendGradient(cell.daySlots, "180deg", monthTrendMax),
                    "--month-days": cell.daySlots.length,
                  } as CSSProperties
                }
                title={contributionTitle(cell)}
                type="button"
              >
                <div className="cell-trend month-trend smooth-trend" aria-hidden="true">
                  {cell.daySlots.map((slot) => (
                    <i className={`trend-segment level-${slot.activityLevel}`} key={slot.date} style={trendSegmentStyle(slot, monthTrendMax)} />
                  ))}
                </div>
                <strong>{cell.monthLabel}</strong>
                <span>{cell.year}</span>
              </button>
            );
          })}
        </div>
      )}
      <div className="contribution-analysis">
        <InsightCard title="当前对象" value={selected.activityScore} note={`${selected.label}；活动得分`} />
        <InsightCard title="筛选记忆增量" value={selected.filteredMemoryCount} note={`当前筛选命中；决策 ${selected.filteredDecisionCount} 条`} />
        <InsightCard title="全局交互量" value={selected.messageCount} note={`对话 ${selected.conversationCount} 个；消息 ${selected.messageCount} 条`} />
        <InsightCard title="环比变化" value={selected.delta} note={`${selected.previousLabel} 对比 ${formatSigned(selected.delta)} 分`} />
      </div>
      <p className="note">
        说明：当前分析对象的真实数据范围显示在标题右侧；全年空格代表该对象当天为 0，不代表存在使用记录。层级/分类/主题筛选后的贡献增量来自当前筛选记忆节点日期聚合，避免伪造主题级消息数。
      </p>
    </div>
  );
}



export function HeatLegend() {
  return (
    <div className="heat-legend" aria-label="贡献网格热度标尺">
      <span>热度趋势</span>
      <div className="heat-legend-gradient" role="img" aria-label="热度从 0、低频、中频到高频逐步增强">
        <b>0</b>
        <i aria-hidden="true" />
        <b>高</b>
      </div>
    </div>
  );
}
