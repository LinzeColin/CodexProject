# 运行手册

## 月度执行

1. 确认期间为 `YYYYMM`。
2. 确认输入目录只作为文件来源，不作为业务判断依据。
3. 用 `config/input_manifest.7slots.template.yml` 填写或核对 7 个输入槽位。
4. 运行登记命令：

```bash
python3 KMFA/mgmt-monthly-report-skill/scripts/mgmt_monthly_report.py \
  register \
  --period YYYYMM \
  --input-dir /path/to/inputs \
  --output-dir /path/to/outputs \
  --metadata-root KMFA/metadata/mgmt-monthly-report-skill \
  --write
```

5. 生成或刷新 Excel：`经营管理分析报表 YYYYMM.xlsx`。
6. 运行严格验收：

```bash
python3 KMFA/mgmt-monthly-report-skill/scripts/validate_deliverables.py \
  --period YYYYMM \
  --input-dir /path/to/inputs \
  --excel "/path/to/outputs/经营管理分析报表 YYYYMM.xlsx" \
  --pdf "/path/to/outputs/董事会经营分析摘要 YYYYMM.pdf" \
  --config KMFA/mgmt-monthly-report-skill/config/v6_spec.json \
  --report "KMFA/metadata/mgmt-monthly-report-skill/validation/自动验收报告 YYYYMM.json" \
  --strict
```

7. 只有 Excel 通过验收后才生成 PDF。
8. PDF 生成后再次运行验收。
9. 运行 cleanup audit，确认本机运行区只保留正式报告。

## 失败处理

- 输入缺失：停止，补齐或确认映射。
- Sheet 缺失：停止，要求提供正确源表或转换后的 `.xlsx`。
- 公式错误、乱码、禁用词、`#####`：修复后重新验收。
- PDF 期间不一致：删除错误 PDF，重新从通过验收的 Excel 生成。

