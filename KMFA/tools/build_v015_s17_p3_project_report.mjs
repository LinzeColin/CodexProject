#!/usr/bin/env node
/* Build the S17-P3 project-cost workbook with @oai/artifact-tool. */

import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [inputPath, outputPath, previewDir, inspectionPath] = process.argv.slice(2);
if (!inputPath || !outputPath || !previewDir || !inspectionPath) {
  throw new Error("usage: build_v015_s17_p3_project_report.mjs input.json output.xlsx preview_dir inspection.json");
}

const report = JSON.parse(await fs.readFile(inputPath, "utf8"));
const workbook = Workbook.create();
const navy = "#173D57";
const blue = "#2F7AA4";
const paleBlue = "#EEF7FB";
const paleGreen = "#F1FAF5";
const green = "#246040";
const paleGold = "#FFF8E8";
const line = "#D8E2E8";
const text = "#263B49";
const muted = "#607684";
const moneyFormat = "#,##0.00;[Red]-#,##0.00;0.00";
const integerFormat = "0";

const styleTitle = (sheet, range, title) => {
  sheet.mergeCells(range);
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[title]];
  cell.format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 18 }, verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 34;
};

const styleSection = (range) => {
  range.format = { fill: paleBlue, font: { bold: true, color: navy }, borders: { preset: "all", style: "thin", color: line } };
};

const styleHeader = (range) => {
  range.format = { fill: blue, font: { bold: true, color: "#FFFFFF" }, borders: { preset: "all", style: "thin", color: line }, wrapText: true, verticalAlignment: "center" };
};

const styleBody = (range) => {
  range.format = { font: { color: text }, borders: { preset: "all", style: "thin", color: line }, verticalAlignment: "top" };
};

const setWidths = (sheet, widths) => {
  widths.forEach(([range, width]) => { sheet.getRange(range).format.columnWidth = width; });
};

// 项目摘要
const summary = workbook.worksheets.add("项目摘要");
summary.showGridLines = false;
styleTitle(summary, "A1:F1", report.report_name_zh);
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [[`${report.project.project_name_zh} · ${report.project.project_id} · ${report.project.period} · ${report.report_version}`]];
summary.getRange("A2:F2").format = { fill: "#F4F7F9", font: { color: muted, italic: true }, wrapText: true };
summary.getRange("A4:B4").values = [["项目", "结果"]];
styleHeader(summary.getRange("A4:B4"));
summary.getRange("A5:A13").values = [
  ["确认收入（元）"], ["确认成本（元）"], ["毛利（元）"], ["毛利率"], ["预算基准（元）"], ["成本差异（元）"], ["未归集成本（元）"], ["页面与报告差异（元）"], ["核对结果"],
];
summary.getRange("B5").values = [[report.summary.revenue_cents / 100]];
summary.getRange("B6").formulas = [["=ROUND(SUM('成本明细'!B5:B15),2)"]];
summary.getRange("B7").formulas = [["=ROUND(B5-B6,2)"]];
summary.getRange("B8").formulas = [["=IF(B5=0,0,B7/B5)"]];
summary.getRange("B9").formulas = [["=ROUND(SUM('成本明细'!C5:C15),2)"]];
summary.getRange("B10").formulas = [["=ROUND(B6-B9,2)"]];
summary.getRange("B11").formulas = [["='成本明细'!B15"]];
summary.getRange("B12").formulas = [[`=ROUND(B6-${report.summary.cost_cents / 100},2)`]];
summary.getRange("B13").formulas = [["=IF(AND(B12=0,'校验与来源'!B8=0,'校验与来源'!B9=0),\"通过：允许差异 0 分\",\"失败：请复核\")"]];
styleBody(summary.getRange("A5:B13"));
summary.getRange("B5:B7").format.numberFormat = moneyFormat;
summary.getRange("B8").format.numberFormat = "0.00%";
summary.getRange("B9:B12").format.numberFormat = moneyFormat;
summary.getRange("B13").format = { fill: paleGreen, font: { bold: true, color: green }, borders: { preset: "all", style: "thin", color: line } };
summary.getRange("D4:F4").merge();
summary.getRange("D4").values = [["使用说明"]];
styleSection(summary.getRange("D4:F4"));
summary.getRange("D5:F10").merge();
summary.getRange("D5").values = [["这是一份公开合成的项目成本附表。金额来自同一份处理投影；处理记录只追加、可撤销，不修改源数据。成本明细和项目摘要中的汇总均由公式计算，便于复核。"]];
summary.getRange("D5:F10").format = { fill: "#FAFCFD", font: { color: text }, borders: { preset: "all", style: "thin", color: line }, wrapText: true, verticalAlignment: "top" };
summary.getRange("D12:F12").merge();
summary.getRange("D12").values = [["报告状态"]];
styleSection(summary.getRange("D12:F12"));
summary.getRange("D13:F13").merge();
summary.getRange("D13").values = [[report.checks.report_sync_status === "PASS" ? "页面与专题报告已同步" : "等待重新计算"]];
summary.getRange("D13:F13").format = { fill: paleGreen, font: { bold: true, color: green }, borders: { preset: "all", style: "thin", color: line } };
setWidths(summary, [["A:A", 19], ["B:B", 23], ["C:C", 3], ["D:F", 17]]);
summary.freezePanes.freezeRows(3);

// 成本明细
const costs = workbook.worksheets.add("成本明细");
costs.showGridLines = false;
styleTitle(costs, "A1:F1", "成本明细与预算差异");
costs.getRange("A2:F2").merge();
costs.getRange("A2").values = [["金额单位：元；实际、预算和差异均可追溯到公开合成来源。"]];
costs.getRange("A2:F2").format = { fill: "#F4F7F9", font: { color: muted }, wrapText: true };
costs.getRange("A4:F4").values = [["成本分类", "实际", "预算", "差异", "来源编号", "核对"]];
styleHeader(costs.getRange("A4:F4"));
const costRows = report.cost_rows;
costs.getRange(`A5:A${4 + costRows.length}`).values = costRows.map((row) => [row.category_zh]);
costs.getRange(`B5:B${4 + costRows.length}`).values = costRows.map((row) => [row.actual_cents / 100]);
costs.getRange(`C5:C${4 + costRows.length}`).values = costRows.map((row) => [row.budget_cents / 100]);
costs.getRange("D5").formulas = [["=ROUND(B5-C5,2)"]];
costs.getRange(`D5:D${4 + costRows.length}`).fillDown();
costs.getRange(`E5:E${4 + costRows.length}`).values = costRows.map((row) => [row.source_ref]);
costs.getRange("F5").formulas = [["=IF(D5=ROUND(B5-C5,2),\"通过\",\"失败\")"]];
costs.getRange(`F5:F${4 + costRows.length}`).fillDown();
styleBody(costs.getRange(`A5:F${4 + costRows.length}`));
costs.getRange(`B5:D${4 + costRows.length}`).format.numberFormat = moneyFormat;
const totalRow = 5 + costRows.length;
costs.getRange(`A${totalRow}:F${totalRow}`).values = [["合计", null, null, null, "页面成本核对", null]];
costs.getRange(`B${totalRow}`).formulas = [[`=ROUND(SUM(B5:B${totalRow - 1}),2)`]];
costs.getRange(`C${totalRow}`).formulas = [[`=ROUND(SUM(C5:C${totalRow - 1}),2)`]];
costs.getRange(`D${totalRow}`).formulas = [[`=ROUND(B${totalRow}-C${totalRow},2)`]];
costs.getRange(`F${totalRow}`).formulas = [[`=IF(B${totalRow}='项目摘要'!B6,\"通过\",\"失败\")`]];
costs.getRange(`A${totalRow}:F${totalRow}`).format = { fill: paleGold, font: { bold: true, color: navy }, borders: { preset: "doubleBottom", style: "medium", color: blue } };
costs.getRange(`B${totalRow}:D${totalRow}`).format.numberFormat = moneyFormat;
setWidths(costs, [["A:A", 18], ["B:D", 17], ["E:E", 46], ["F:F", 12]]);
costs.getRange(`E5:E${totalRow}`).format.wrapText = true;
costs.freezePanes.freezeRows(4);
const chart = costs.charts.add("bar", costs.getRange(`A4:C${totalRow - 1}`));
chart.title = "分类成本：实际与预算";
chart.hasLegend = true;
chart.setPosition("H4", "O22");

// 处理记录
const events = workbook.worksheets.add("处理记录");
events.showGridLines = false;
styleTitle(events, "A1:G1", "处理记录（只追加、可撤销）");
events.getRange("A2:G2").merge();
events.getRange("A2").values = [["有效记录参与当前投影；历史与辅助记录仍保留，便于还原处理过程。"]];
events.getRange("A2:G2").format = { fill: "#F4F7F9", font: { color: muted }, wrapText: true };
events.getRange("A4:G4").values = [["顺序", "事件编号", "处理类型", "时间", "原因", "当前有效", "内容校验码"]];
styleHeader(events.getRange("A4:G4"));
const eventRows = report.processing_events;
if (eventRows.length) {
  events.getRange(`A5:G${4 + eventRows.length}`).values = eventRows.map((row) => [row.event_sequence, row.event_id, row.event_type_zh, row.event_time, row.reason_zh, row.active ? "是" : "否", row.content_hash]);
  styleBody(events.getRange(`A5:G${4 + eventRows.length}`));
  events.getRange(`D5:D${4 + eventRows.length}`).format.numberFormat = "yyyy-mm-dd hh:mm:ss";
}
setWidths(events, [["A:A", 8], ["B:B", 31], ["C:C", 28], ["D:D", 24], ["E:E", 38], ["F:F", 12], ["G:G", 50]]);
events.getRange(`B5:G${Math.max(5, 4 + eventRows.length)}`).format.wrapText = true;
events.freezePanes.freezeRows(4);

// 差异分析
const variance = workbook.worksheets.add("差异分析");
variance.showGridLines = false;
styleTitle(variance, "A1:F1", "项目差异分析");
variance.getRange("A2:F2").merge();
variance.getRange("A2").values = [["实际、基准和形成原因并排显示；当前报告口径已经重算。"]];
variance.getRange("A2:F2").format = { fill: "#F4F7F9", font: { color: muted }, wrapText: true };
variance.getRange("A4:F4").values = [["差异项目", "实际", "基准", "差异", "解释", "校验"]];
styleHeader(variance.getRange("A4:F4"));
const varianceRows = report.variance_rows;
variance.getRange(`A5:A${4 + varianceRows.length}`).values = varianceRows.map((row) => [row.label_zh]);
variance.getRange(`B5:B${4 + varianceRows.length}`).values = varianceRows.map((row) => [row.actual_cents / 100]);
variance.getRange(`C5:C${4 + varianceRows.length}`).values = varianceRows.map((row) => [row.baseline_cents / 100]);
variance.getRange("D5").formulas = [["=ROUND(B5-C5,2)"]];
variance.getRange(`D5:D${4 + varianceRows.length}`).fillDown();
variance.getRange(`E5:E${4 + varianceRows.length}`).values = varianceRows.map((row) => [row.explanation_zh]);
variance.getRange("F5").formulas = [["=IF(D5=ROUND(B5-C5,2),\"通过\",\"失败\")"]];
variance.getRange(`F5:F${4 + varianceRows.length}`).fillDown();
styleBody(variance.getRange(`A5:F${4 + varianceRows.length}`));
variance.getRange(`B5:D${4 + varianceRows.length}`).format.numberFormat = moneyFormat;
variance.getRange(`E5:E${4 + varianceRows.length}`).format.wrapText = true;
setWidths(variance, [["A:A", 18], ["B:D", 17], ["E:E", 50], ["F:F", 12]]);
variance.freezePanes.freezeRows(4);

// 校验与来源
const evidence = workbook.worksheets.add("校验与来源");
evidence.showGridLines = false;
styleTitle(evidence, "A1:D1", "校验与证据索引");
evidence.getRange("A3:B3").values = [["核对项", "结果（分）"]];
styleHeader(evidence.getRange("A3:B3"));
evidence.getRange("A4:A10").values = [["页面成本"], ["黄金基准成本"], ["分类成本合计"], ["允许差异"], ["页面－黄金基准"], ["分类－页面"], ["报告同步状态"]];
evidence.getRange("B4:B10").values = [[report.checks.page_cost_cents], [report.checks.golden_cost_cents], [report.checks.category_total_cents], [report.checks.money_tolerance_cents], [report.checks.page_golden_difference_cents], [report.checks.category_page_difference_cents], [report.checks.report_sync_status]];
styleBody(evidence.getRange("A4:B10"));
evidence.getRange("B4:B9").format.numberFormat = integerFormat;
evidence.getRange("D3").values = [["报告指纹"]];
styleSection(evidence.getRange("D3"));
evidence.getRange("D4").values = [[report.report_fingerprint]];
evidence.getRange("D4").format = { borders: { preset: "all", style: "thin", color: line }, wrapText: true, font: { color: text } };
let cursor = 12;
for (const [label, key] of [["事实来源", "source_facts"], ["处理记录", "processing_event_refs"], ["计算依据", "calculation_refs"], ["报告格式", "report_refs"]]) {
  evidence.getRange(`A${cursor}:D${cursor}`).merge();
  evidence.getRange(`A${cursor}`).values = [[label]];
  styleSection(evidence.getRange(`A${cursor}:D${cursor}`));
  cursor += 1;
  const rows = report.evidence_index[key];
  evidence.getRange(`A${cursor}:D${cursor + rows.length - 1}`).merge(true);
  evidence.getRange(`A${cursor}:A${cursor + rows.length - 1}`).values = rows.map((value) => [value]);
  evidence.getRange(`A${cursor}:D${cursor + rows.length - 1}`).format = { borders: { preset: "all", style: "thin", color: line }, font: { color: text }, wrapText: true };
  cursor += rows.length + 1;
}
setWidths(evidence, [["A:A", 31], ["B:B", 23], ["C:C", 4], ["D:D", 55]]);
evidence.freezePanes.freezeRows(2);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(path.dirname(inspectionPath), { recursive: true });

const inspection = {};
inspection.summary = JSON.parse((await workbook.inspect({ kind: "table", range: "项目摘要!A1:F13", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 8 })).ndjson);
inspection.costs = JSON.parse((await workbook.inspect({ kind: "table", range: `成本明细!A1:F${totalRow}`, include: "values,formulas", tableMaxRows: 25, tableMaxCols: 8 })).ndjson);
inspection.errors = (await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" })).ndjson;

for (const sheetName of ["项目摘要", "成本明细", "处理记录", "差异分析", "校验与来源"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1.25, format: "png" });
  await fs.writeFile(path.join(previewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.writeFile(inspectionPath, JSON.stringify(inspection, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ status: "PASS", outputPath, sheetCount: 5, previewCount: 5 }));
