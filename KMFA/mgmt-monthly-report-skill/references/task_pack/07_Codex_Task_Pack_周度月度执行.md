# 07_Codex Task Pack｜经营管理分析报表周度/月度执行

## 0. 任务目标

从用户提供的 6 个业务输入包，稳定生成：

1. `经营管理分析报表 YYYYMM.xlsx`
2. `董事会经营分析摘要 YYYYMM.pdf`

必须复现 v6 基准结构和样式。

## 1. Codex 执行模式

必须按以下阶段执行：

| 阶段 | 模式 | 目标 |
|---|---|---|
| 1 | read-only | 列出输入文件、基准文件、配置文件，不修改任何文件 |
| 2 | plan | 输出将读取的文件、将更新的 Sheet、关键公式、校验方式 |
| 3 | execute | 生成 Excel 和 PDF |
| 4 | verify | 运行自动验收脚本，生成 JSON 验收报告 |
| 5 | deliver | 只交付验收通过的 Excel/PDF；失败则交付问题清单 |

## 2. Read-only 阶段必须输出

- 本期期间 YYYYMM。
- 输入目录文件列表。
- 6 个业务输入包映射结果。
- 开票纳税资金汇总表是否包含 3 个必需 Sheet。
- 基准文件是否存在：`golden/经营管理分析报表 v6基准.xlsx`。
- 输出路径。

如果缺失，停止，不进入 execute。

## 3. Plan 阶段必须输出

- 将读取的源文件和 Sheet。
- 将刷新的 Excel Sheet。
- 将保留的 Sheet 顺序。
- 资金总流入、资金总流出、累计资金净流量公式策略。
- 图表更新策略。
- PDF 页结构。
- 验收命令。
- 回滚方案：保留上一个已验收版本，不覆盖。

## 4. Execute 阶段规则

- 从 v6 基准文件复制并刷新。
- 不重建空白样式。
- 不新增可见 Sheet。
- 不写测试数据。
- 不覆盖公式为值。
- 不生成静态图表图片。
- 所有文本完整显示。
- 所有百分比两位小数。
- 输出文件名：`经营管理分析报表 YYYYMM.xlsx`、`董事会经营分析摘要 YYYYMM.pdf`。

## 5. Verify 阶段命令

```bash
python scripts/validate_deliverables.py   --period YYYYMM   --input-dir ./inputs   --excel "./outputs/经营管理分析报表 YYYYMM.xlsx"   --pdf "./outputs/董事会经营分析摘要 YYYYMM.pdf"   --config ./config/v6_spec.json   --report "./outputs/自动验收报告 YYYYMM.json"   --strict
```

## 6. 验收失败处理

- 不得交付正式结果。
- 输出 `自动验收报告 YYYYMM.json`。
- 输出问题摘要：失败项、影响 Sheet、影响指标、修复建议。
- 修复后重新运行验收。
- 最多自动修复 2 轮；仍失败则停止并请求用户确认。

## 7. 数据准确性红线

以下情况必须停止：

- 缺失必需输入包。
- 开票纳税资金汇总表缺少指定 Sheet。
- 资金总流入/资金总流出/累计资金净流量不是公式。
- Sheet 顺序错。
- 出现 Series1/Series2。
- 出现乱码或 `#####`。
- 使用测试数据。
- PDF 与 Excel 期间不一致。

## 8. 文件归档

输出目录建议：

```text
outputs/YYYYMM/
  经营管理分析报表 YYYYMM.xlsx
  董事会经营分析摘要 YYYYMM.pdf
  自动验收报告 YYYYMM.json
  生成日志 YYYYMM.md
```

不得覆盖历史月份文件。

## 9. 交付摘要模板

交付时只写：

- 文件链接。
- 验收结果：通过 / 未通过。
- 如果未通过，列出失败项。
- 不要解释无关技术细节。
