import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, GaugeChart, LineChart } from "echarts/charts";
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, GaugeChart, LineChart, GridComponent, LegendComponent, TitleComponent, TooltipComponent, CanvasRenderer]);

export default function ChartPanel({ visualization }) {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current || !visualization?.echarts_option) return undefined;
    const chart = echarts.init(chartRef.current, undefined, { renderer: "canvas" });
    chart.setOption(visualization.echarts_option, true);
    const resize = () => chart.resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [visualization]);

  return (
    <section className="chart-panel" aria-label={visualization.title}>
      <div className="chart-panel__head">
        <h3>{visualization.title}</h3>
        <span>{visualization.kind}</span>
      </div>
      <div ref={chartRef} className="chart-surface" />
      <p>{visualization.description}</p>
    </section>
  );
}
