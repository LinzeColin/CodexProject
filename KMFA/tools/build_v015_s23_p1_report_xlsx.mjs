#!/usr/bin/env node
/** Build and inspect the S23-P1 authoritative XLSX with @oai/artifact-tool. */

import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const [inputPath, outputPath, previewDir] = process.argv.slice(2);
if (!inputPath || !outputPath || !previewDir) {
  throw new Error("usage: build_v015_s23_p1_report_xlsx.mjs INPUT_JSON OUTPUT_XLSX PREVIEW_DIR");
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const workbook = Workbook.create();
const summary = workbook.worksheets.add("经营摘要");
const projects = workbook.worksheets.add("项目明细");
const checks = workbook.worksheets.add("一致性检查");
workbook.comments.setSelf({ displayName: "Linze Zhang" });

const navy = "#173D57";
const teal = "#246C83";
const light = "#EDF6F9";
const line = "#D8E2E8";
const green = "#EAF6EE";
const amountFormat = '¥#,##0.00;[Red](¥#,##0.00);-';
const integerFormat = '#,##0;[Red](#,##0);-';

for (const sheet of [summary, projects, checks]) {
  sheet.showGridLines = false;
}

summary.getRange("A1:G1").merge();
summary.getRange("A1").values = [["KMFA 月度经营报告｜权威发布版本"]];
summary.getRange("A1:G1").format = {
  fill: navy,
  font: { bold: true, color: "#FFFFFF", size: 18 },
  rowHeight: 34,
  verticalAlignment: "center",
};
summary.getRange("A3:B8").values = [
  ["报告版本", payload.report_version_id],
  ["发布版本", payload.publication_version_id],
  ["公司", payload.company_name_zh],
  ["期间", payload.period.period_label_zh],
  ["数据分类", payload.data_classification],
  ["权威指纹", payload.shared_metric_fingerprint],
];
summary.getRange("A3:A8").format = { fill: light, font: { bold: true, color: navy } };
summary.getRange("B3:B8").format = { font: { color: "#008000" }, wrapText: true };
summary.getRange("A10:F10").values = [["指标编号", "指标", "整数值", "单位", "展示值", "差异"]];
summary.getRange("A10:F10").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
const metricRows = payload.metrics.map((row) => [
  row.metric_id,
  row.label_zh,
  row.value_integer,
  row.unit,
  row.display_value,
  row.difference_integer,
]);
summary.getRangeByIndexes(10, 0, metricRows.length, 6).values = metricRows;
summary.getRangeByIndexes(10, 2, metricRows.length, 1).format.numberFormat = integerFormat;
summary.getRangeByIndexes(10, 5, metricRows.length, 1).format.numberFormat = integerFormat;
summary.getRange(`A10:F${10 + metricRows.length}`).format.borders = { preset: "inside", style: "thin", color: line };
summary.getRange("A19:G19").merge();
summary.getRange("A19").values = [["说明：所有金额以整数分为权威存储单位；展示金额仅由整数分换算。"]];
summary.getRange("A19:G19").format = { fill: "#FFF8E8", font: { color: "#6B4D18" }, wrapText: true };
summary.freezePanes.freezeRows(10);
summary.getRange("A:G").format.autofitColumns();
summary.getRange("A:A").format.columnWidth = 24;
summary.getRange("B:B").format.columnWidth = 22;
summary.getRange("B3:B8").format.columnWidth = 48;

projects.getRange("A1:J1").merge();
projects.getRange("A1").values = [["项目收入、成本、毛利、回款与应收｜整数分"]];
projects.getRange("A1:J1").format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 16 }, rowHeight: 32 };
projects.getRange("A3:J3").values = [[
  "项目编号", "项目名称", "收入（分）", "成本（分）", "毛利（公式）",
  "回款（分）", "应收（公式）", "毛利率（基点）", "毛利差异", "应收差异",
]];
projects.getRange("A3:J3").format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, wrapText: true };
const projectStart = 4;
const projectEnd = projectStart + payload.projects.length - 1;
const projectInputs = payload.projects.map((row) => [
  row.project_id,
  row.project_name_zh,
  row.revenue_cents,
  row.cost_cents,
  null,
  row.collection_cents,
  null,
  null,
  null,
  null,
]);
projects.getRangeByIndexes(projectStart - 1, 0, projectInputs.length, 10).values = projectInputs;
for (let row = projectStart; row <= projectEnd; row += 1) {
  projects.getRange(`E${row}`).formulas = [[`=C${row}-D${row}`]];
  projects.getRange(`G${row}`).formulas = [[`=C${row}-F${row}`]];
  projects.getRange(`H${row}`).formulas = [[`=ROUND(E${row}*10000/C${row},0)`]];
  projects.getRange(`I${row}`).formulas = [[`=E${row}-(C${row}-D${row})`]];
  projects.getRange(`J${row}`).formulas = [[`=G${row}-(C${row}-F${row})`]];
}
const totalRow = projectEnd + 1;
projects.getRange(`A${totalRow}:B${totalRow}`).merge();
projects.getRange(`A${totalRow}`).values = [["合计"]];
for (const column of ["C", "D", "E", "F", "G", "I", "J"]) {
  projects.getRange(`${column}${totalRow}`).formulas = [[`=SUM(${column}${projectStart}:${column}${projectEnd})`]];
}
projects.getRange(`H${totalRow}`).formulas = [[`=ROUND(E${totalRow}*10000/C${totalRow},0)`]];
projects.getRange(`A${totalRow}:J${totalRow}`).format = {
  fill: light,
  font: { bold: true, color: navy },
  borders: { preset: "doubleBottom", style: "thin", color: navy },
};
projects.getRange(`C${projectStart}:J${totalRow}`).format.numberFormat = integerFormat;
projects.getRange(`A3:J${totalRow}`).format.borders = { preset: "inside", style: "thin", color: line };
projects.freezePanes.freezeRows(3);
projects.getRange("A:J").format.autofitColumns();
projects.getRange("A:A").format.columnWidth = 22;
projects.getRange("B:B").format.columnWidth = 20;
projects.getRange("C:J").format.columnWidth = 15;

checks.getRange("A1:G1").merge();
checks.getRange("A1").values = [["一致性检查｜差异必须为 0"]];
checks.getRange("A1:G1").format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 16 }, rowHeight: 32 };
checks.getRange("A3:G3").values = [["检查", "实际", "期望", "差异", "容差", "状态", "修复位置"]];
checks.getRange("A3:G3").format = { fill: teal, font: { bold: true, color: "#FFFFFF" } };
const expected = payload.headline;
const checkDefs = [
  ["项目收入合计", `='项目明细'!C${totalRow}`, expected.revenue_cents, "项目明细"],
  ["项目成本合计", `='项目明细'!D${totalRow}`, expected.cost_cents, "项目明细"],
  ["项目毛利合计", `='项目明细'!E${totalRow}`, expected.gross_profit_cents, "项目明细"],
  ["项目回款合计", `='项目明细'!F${totalRow}`, expected.collection_cents, "项目明细"],
  ["项目应收合计", `='项目明细'!G${totalRow}`, expected.receivable_cents, "项目明细"],
  ["项目毛利率", `='项目明细'!H${totalRow}`, expected.gross_margin_bps, "项目明细"],
];
for (let index = 0; index < checkDefs.length; index += 1) {
  const row = 4 + index;
  const [label, actualFormula, expectedValue, location] = checkDefs[index];
  checks.getRange(`A${row}:G${row}`).values = [[label, null, expectedValue, null, 0, null, location]];
  checks.getRange(`B${row}`).formulas = [[actualFormula]];
  checks.getRange(`D${row}`).formulas = [[`=B${row}-C${row}`]];
  checks.getRange(`F${row}`).formulas = [[`=IF(ABS(D${row})<=E${row},"PASS","FAIL")`]];
}
const statusRow = 11;
checks.getRange(`A${statusRow}:E${statusRow}`).merge();
checks.getRange(`A${statusRow}`).values = [["MODEL STATUS"]];
checks.getRange(`F${statusRow}`).formulas = [[`=IF(COUNTIF(F4:F9,"FAIL")=0,"PASS","FAIL")`]];
checks.getRange(`A${statusRow}:G${statusRow}`).format = { fill: green, font: { bold: true, color: "#17623A" } };
checks.getRange("B4:E9").format.numberFormat = integerFormat;
checks.getRange("A3:G11").format.borders = { preset: "inside", style: "thin", color: line };
checks.getRange("A:G").format.autofitColumns();
checks.getRange("A:A").format.columnWidth = 22;
checks.getRange("G:G").format.columnWidth = 18;

await fs.mkdir(previewDir, { recursive: true });
const previews = [];
for (const sheetName of ["经营摘要", "项目明细", "一致性检查"]) {
  const blob = await workbook.render({ sheetName, autoCrop: "all", scale: 1.5, format: "png" });
  const previewPath = path.join(previewDir, `${sheetName}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await blob.arrayBuffer()));
  previews.push(previewPath);
}

const summaryInspect = await workbook.inspect({
  kind: "table",
  range: `经营摘要!A1:F${10 + metricRows.length}`,
  include: "values,formulas",
  tableMaxRows: 24,
  tableMaxCols: 10,
  maxChars: 12000,
});
const projectInspect = await workbook.inspect({
  kind: "table",
  range: `项目明细!A3:J${totalRow}`,
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 12,
  maxChars: 12000,
});
const errorInspect = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "S23-P1 final formula error scan",
});

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const metricValues = summary.getRange(`C11:C${10 + metricRows.length}`).values.map((row) => Number(row[0]));
const projectValues = projects.getRange(`A${projectStart}:J${projectEnd}`).values;
const numericValues = {};
payload.metrics.forEach((row, index) => { numericValues[row.metric_id] = metricValues[index]; });
payload.projects.forEach((row, index) => {
  const values = projectValues[index];
  numericValues[`${row.project_id}:revenue_cents`] = Number(values[2]);
  numericValues[`${row.project_id}:cost_cents`] = Number(values[3]);
  numericValues[`${row.project_id}:gross_profit_cents`] = Number(values[4]);
  numericValues[`${row.project_id}:collection_cents`] = Number(values[5]);
  numericValues[`${row.project_id}:receivable_cents`] = Number(values[6]);
});
const checkStatus = String(checks.getRange(`F${statusRow}`).values[0][0]);
const formulaErrorFree = !/(#REF!|#DIV\/0!|#VALUE!|#NAME\?|#N\/A)/.test(errorInspect.ndjson || "");
console.log(JSON.stringify({
  status: checkStatus === "PASS" && formulaErrorFree ? "PASS" : "FAIL",
  check_status: checkStatus,
  formula_error_free: formulaErrorFree,
  numeric_values: numericValues,
  preview_paths: previews,
  inspected_summary: Boolean(summaryInspect.ndjson),
  inspected_projects: Boolean(projectInspect.ndjson),
  output_path: outputPath,
}));
