# 政策系统 Data Trust Layer

## 目标

Data Trust Layer 用于回答一个问题：当前政策系统里的来源、文件、运行记录、外部参考、报告和控制文件，哪些已经可作为证据链使用，哪些只能作为候选线索，哪些必须人工复核或拒绝。

该层只做本地只读审计，不触发政策抓取，不调用搜索 API，不读取或输出 API key、cookie、session、账号密码。

## 运行命令

```bash
PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite data-trust-audit \
  --content-db data/policy_documents.sqlite \
  --report-dir reports \
  --output-dir reports/system_audit \
  --as-of 2026-06-06
```

输出文件：

- `reports/system_audit/data_trust_audit_<date>.json`
- `reports/system_audit/data_trust_audit_<date>.csv`
- `reports/system_audit/data_trust_audit_<date>.md`
- `reports/system_audit/data_trust_audit_<date>.pdf`

## 信任状态

| 状态 | 含义 | 使用边界 |
|---|---|---|
| `RAW_IMPORTED` | 已发现但未完成解析或验证 | 只能作为线索 |
| `PARSED_CANDIDATE` | 已解析但还缺少完整复核证据 | 只能进入观察或待复核 |
| `NEEDS_REVIEW` | 有缺口、授权不足、待人工确认或证据不足 | 不得升级为高置信结论 |
| `USER_CONFIRMED` | 已有人为确认 | 可进入证据链，但仍需保留确认记录 |
| `RECONCILED` | 已和数据库、报告、运行记录形成闭环 | 可作为当前系统证据 |
| `ARCHIVED` | 已归档或忽略 | 仅保留审计痕迹 |
| `REJECTED` | 失败、拒绝或明确不可用 | 阻断对应结论 |

## 证据分类

| 分类 | 含义 |
|---|---|
| `FACT` | 文件、数据库行、报告产物、运行状态等可直接验证事实 |
| `OBSERVATION` | 外部参考、缺口、候选任务等观察线索 |
| `INFERENCE` | 系统分析、模型推断或自动摘要 |
| `OPINION` | 人工观点或主观判断；当前审计不主动生成 |

## 结论等级

| 等级 | 含义 |
|---|---|
| `Actionable` | 可进入政策证据链，不代表交易、投资或执行建议 |
| `Watch` | 需要继续观察或补证 |
| `Observe` | 已归档，仅作背景 |
| `Reject` | 明确不可用或阻断 |

## 审计范围

- 控制文件：`AGENTS.md`、`HANDOFF.md`、`PLANS.md`、`CODEX_TASK_PACK.md`、`CODEX_PROMPTS.md`、`README.md`、`pyproject.toml`
- 配置和脚本：`config/seed_sources.json`、`config/interpretation_sources.json`、`config/platform_parsers.json`、`rules/quality_gates.json`、`scripts/run_policy_report.sh`
- 来源库：`data/source_registry.sqlite`
- 内容库：`data/policy_documents.sqlite`
- 报告目录：`reports/`

## 验收标准

- CLI 可以生成 JSON、CSV、Markdown 和 PDF。
- 缺失控制文件必须显示为 `NEEDS_REVIEW`。
- 失败运行必须显示为 `REJECTED`。
- pending 外部参考缺口必须显示为 `NEEDS_REVIEW`。
- 报告、数据库、配置和控制文件必须带 `content_hash` 或稳定 hash，便于追溯。
- 所有审计输出不得包含 API key、cookie、session、账号密码或完整敏感路径。
