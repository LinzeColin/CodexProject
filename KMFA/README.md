# KMFA｜经营分析系统

KMFA 是面向 C-level management / board 的经营分析系统。当前优先级是文件型项目成本分析 MVP：先建立项目治理、数据治理、金额精度、零差异、差异队列、人工处理事件、重跑链路和可追溯经营报告基础。

## 当前状态

| 项目 | 内容 |
|---|---|
| project_id | `KMFA` |
| 当前版本 | `0.1.0-s03p3` |
| 当前 Stage | `S03｜原始文件导入与数据源检查矩阵` |
| 当前 Phase | `S03-P3｜源优先级` |
| 当前 Task | `S3PCT01-S3PCT03` |
| 风险等级 | `T3`，涉及经营数据、金额、税务、隐私和公开仓库边界 |
| GitHub 目录 | `LinzeColin/CodexProject/KMFA` |
| 当前基线 | `KMFA/taskpack/v1_2`，源包 SHA256 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66` |
| Stage 上传规则 | 中间 Phase 不上传 GitHub；Stage 3 复审已通过，待整体上传 GitHub |

## 双平面结构

### 人类可读面

| 文件 | 用途 |
|---|---|
| `README.md` | 项目入口、范围、状态、运行边界 |
| `功能清单.md` | 面向 owner 的功能、限制、证据和下一任务 |
| `开发记录.md` | Stage -> Phase -> Task 开发记录、验收、风险、回滚 |
| `模型参数文件.md` | 模型、公式、参数、质量门禁和验证状态 |
| `HANDOFF.md` | 跨线程交接摘要 |

### 机器可读面

| 文件/目录 | 用途 |
|---|---|
| `docs/governance/project.yaml` | Lean v2 项目事实 |
| `docs/governance/roadmap.yaml` | Lean v2 Roadmap 事实 |
| `docs/governance/events.jsonl` | Lean v2 事件 |
| `docs/governance/*` | v1 兼容治理文件 |
| `metadata/project/project.yaml` | KMFA 内部项目配置草案 |
| `metadata/stage_status.jsonl` | Stage/Phase/Task 状态登记草案 |
| `metadata/model_registry.yaml` | KMFA 内部模型参数机器镜像草案 |
| `metadata/imports/file_import_policy.yaml` | S03-P1 文件型导入登记、安全解包、WPS/OLE 提示和公开仓库禁止项 |
| `metadata/sources/source_check_matrix_policy.yaml` | S03-P2 数据源检查矩阵维度、状态枚举和 metadata-only 状态事件策略 |
| `metadata/sources/source_priority_policy.yaml` | S03-P3 原始/授权/处理后数据优先级、同源失效重跑和跨源差异队列策略 |
| `metadata/baseline/source_package_v1_2.json` | v1.2 完整任务包机器清单、源包 hash、复制/排除策略 |
| `metadata/baseline/html_acceptance_samples_v1_2.json` | 45 个 HTML 样板与 7 个核心样板的机器清单 |
| `metadata/traceability/requirements.csv` | 完整需求追溯矩阵，P0/P1 绑定任务、验收、测试、证据 |
| `tools/no_omission_check.py` | 正式防遗漏检查脚本，可在 CI/本地运行 |
| `tools/check_required_html.py` | v1.2 HTML/UIUX/报告样板强制门禁 |
| `tools/file_import_register.py` | S03-P1 文件登记、hash/manifest、私有 storage ref 和 zip 安全解包工具 |
| `tools/source_check_matrix.py` | S03-P2 数据源检查矩阵 row 和状态事件生成工具 |
| `tools/source_priority.py` | S03-P3 源优先级、同源不一致事件和跨源差异队列 metadata 工具 |
| `taskpack/v1_2/` | v1.2 FULL_HTML_NO_OMISSION 可提交基线 |
| `stage_artifacts/` | Stage/Phase 证据包 |

## P0 MVP 边界

P0 是文件型项目成本分析 MVP，目标链路如下：

```text
上传/登记权威项目成本资料
-> 原始文件hash与manifest
-> 字段映射
-> A0黄金基准
-> 金额整数分标准化
-> 零差异校验
-> 差异队列
-> 人工处理事件
-> 重跑派生链路
-> 项目成本报告
-> 经营总览摘要
```

当前 `S03-P3` 已建立源优先级协议和工具：`raw_upload`、`authorized_export` 优先于 `raw_extracted_value`、`staging_structured_row`、`canonical_fact`、`derived_metric`、`report_reference`、`frontend_display` 和泛化 `processed_data`；同源不同引用不一致时只追加 metadata event，要求失效派生缓存并重跑；跨源冲突进入差异队列，显式禁止自动选边。仍不解析业务字段、不生成项目成本事实、不处理金额、不生成报告。

## 禁止事项

- 不提交原始敏感数据到公开 GitHub。
- 不自动付款、报税、开票、发工资或发奖金。
- 不对外发送完整经营报告。
- 不在金额计算中使用 float。
- 不把缺数据报告伪装成完整报告。
- 不自动选择 PDF 或 Excel 冲突的一边。
- 不用工具化、营销化、非真实软件感的前端或报告文案。

## 验证命令

当前 S03-P3 最小验证:

```bash
python3 -m unittest KMFA.tests.test_source_priority -q
python3 -m unittest KMFA.tests.test_source_check_matrix -q
python3 -m unittest KMFA.tests.test_file_import_register -q
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- KMFA
```
