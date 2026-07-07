# 经营管理月报 Skill

`mgmt-monthly-report-skill` 是经营管理分析月报的可持续运行包。它把任务包里的
Markdown 规范、v6 Excel 结构、PDF 要求、验收脚本和数据治理规则固化下来，避免每月
重新靠人工记忆操作。

## 目录

```text
KMFA/mgmt-monthly-report-skill/
  SKILL.md
  功能清单.md
  规则清单.md
  agents/openai.yaml
  config/
  references/
  scripts/
  schemas/
  tests/
  tools/
```

对应 metadata：

```text
KMFA/metadata/mgmt-monthly-report-skill/
  backup_registry/
  cleanup/
  config/
  database/
  logs/
  public_reports/
  raw_index/
  run_manifests/
  validation/
```

## 基本流程

1. 把本期输入文件放到受控输入目录。
2. 用 `config/input_manifest.7slots.template.yml` 填好或自动生成本期映射。
3. 先运行 `scripts/mgmt_monthly_report.py register`，登记 hash、sheet、输出状态。
4. 生成 `经营管理分析报表 YYYYMM.xlsx`。
5. 运行 `scripts/validate_deliverables.py`。
6. Excel 通过后生成 `董事会经营分析摘要 YYYYMM.pdf`。
7. 再次登记 backup、validation、cleanup 状态。
8. 本机运行区只保留最终报告；临时缓存、运行数据库和日志要清理或只保留在 GitHub
   metadata 的 public-safe 形态。

## 重要限制

KMFA 仓库契约禁止提交原始敏感经营数据、合同、银行、税务、工资、token 或明文报告正文。
因此本 skill 默认只把 hash、manifest、schema、验收摘要、日志摘要和备份登记提交到
GitHub。真实原始 Excel 和含敏感明文的报告文件留在本机报告目录或用户指定的私有介质。

