# PFI V0.2 Stage 5 Advice, Reports, And Alpha Read-Only Export

更新时间：2026-06-27 Australia/Sydney

## 目标

Stage 5 将 PFI 从“能分析”推进到“能给出可复盘建议并生成报告”。建议必须有证据、预期效果、代价、动作和 owner decision；报告必须可复现导出；Alpha 只允许消费 PFI 只读 context snapshot。

## 范围

- 新增本地 Stage 5 delivery model：`src/pfi_v02/stage5_advice_report_alpha.py`。
- 新增合同测试：`tests/test_stage5_advice_report_alpha.py`。
- Web shell 首页、建议与复盘、报告与洞察接入 Stage 5。
- 生成 `pfi_context_snapshot_v1` 只读 context schema。
- 保留 Stage 3/4 read-model 作为 Stage 5 输入。
- 保留 Stage 4 投资/消费分析、Stage 3 首页/账户/账本、PFI 策略实验室、策略回测、盘感训练和大数据模拟器；QBVS 保持 `CodexProject/QBVS` 顶层独立系统。

## 非范围

- 不修改 Alpha repository。
- 不新增 Alpha、Ralpha、System 或 Development 一级入口。
- 不接入真实交易密码。
- 不提交券商订单。
- 不提交支付动作。
- 不声明自动实盘投资建议。
- 不修改 EEI、ADP、Serenity 或其它项目。

## Phase / Task 验收矩阵

| Task ID | Phase | 任务 | Acceptance Criteria | Stop Condition | Validation | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| S5PAT01 | 5A | Recommendation model | 每条建议包含 domain、evidence、expected effect、tradeoff、action、decision | 无证据建议 | model test | `recommendations` |
| S5PAT02 | 5A | Review lifecycle | 支持 accept、reject、snooze、review、effect measurement | 建议无法复盘 | lifecycle test | `review_lifecycle` |
| S5PAT03 | 5A | 投资建议 | 覆盖 concentration、trading frequency、cash position、strategy pause/launch | 不能解释原因 | investment rec test | `recommendation_type` |
| S5PAT04 | 5A | 消费建议 | 覆盖 budget、subscription、anomaly、cost saving 且有 savings target | 无节省目标 | consumption rec test | `savings_target_aud` |
| S5PAT05 | 5A | Top N ranking | 首页只显示最重要建议，其余留在 lifecycle | 首页噪音过多 | ranking test | `top_recommendations` |
| S5PBT01 | 5B | 月度报告 | 覆盖净资产、现金流、消费、投资、建议复盘 | 报告缺证据链 | report test | `reports.monthly_report` |
| S5PBT02 | 5B | 投资报告 | 覆盖收益、风险、归因、持仓、行为 | 数据不足却输出精确结论 | report test | `reports.investment_report` |
| S5PBT03 | 5B | 消费报告 | 覆盖分类、预算、订阅、异常、节省金额 | 无节省金额 | report test | `reports.consumption_report` |
| S5PBT04 | 5B | 数据质量报告 | 覆盖同步状态、缺失区间、对账差异、parser 错误 | 数据质量不可定位 | report test | `reports.data_quality_report` |
| S5PBT05 | 5B | 导出中心 | Markdown、JSON、CSV 可复现，保留 checksum | 导出不可复现 | export test | `export_center` |
| S5PCT01 | 5C | Context schema | 输出 `pfi_context_snapshot_v1` | schema 不稳定 | schema test | `alpha_context_export.schema` |
| S5PCT02 | 5C | Context exporter fields | 输出净资产、可投资现金、组合配置、风险预算、现金流压力、行为标签、数据新鲜度 | 字段缺失 | exporter test | `alpha_context_export` |
| S5PCT03 | 5C | Alpha independent doc | PFI 只写只读出口边界，不修改 Alpha repo | 修改 Alpha repo | independence test | `alpha_independence` |
| S5PCT04 | 5C | Constraint fields | `trading_password_available=false`、`live_trade_submission_authorized=false` | 出现实盘授权 | constraint test | `alpha_context_export.constraints` |
| S5PZT01 | 5Z | Stage 5 closeout | 合同、UI、治理、入口、缓存、GitHub 同步完成 | 未通过目标验证 | closeout validation | 本文件 + `HANDOFF.md` |

## Stop Condition Checks

| 检查项 | 结果 |
| --- | --- |
| 无证据建议 | PASS：全部 `recommendations` 均有 `evidence_refs` |
| 建议无法复盘 | PASS：`review_lifecycle` 支持 decision record 和 effect measurement |
| 投资建议不能解释原因 | PASS：投资建议覆盖集中度、交易频率、现金仓位、策略 gate，均有 tradeoff 和 action |
| 消费建议无节省目标 | PASS：budget、subscription、anomaly、cost saving 均有 `savings_target_aud` |
| 首页噪音过多 | PASS：首页只显示 `top_recommendations`，完整建议留在 lifecycle |
| 报告缺证据链 | PASS：四类报告均有 `evidence_refs` 和 `has_evidence_chain=true` |
| 导出不可复现 | PASS：Markdown、JSON、CSV 均有 content sha256 和 reproducibility key |
| schema 不稳定 | PASS：context schema 固定为 `pfi_context_snapshot_v1` |
| 修改 Alpha repo | PASS：Stage 5 只修改 PFI；`alpha_repo_modified=false` |
| 新增 Alpha/Ralpha/System 一级入口 | PASS：Web shell 仍为 8 个一级入口，没有 Alpha/Ralpha/System workspace |
| 出现实盘授权 | PASS：`trading_password_available=false`，`live_trade_submission_authorized=false`，无券商订单或支付提交 |
| 丢失旧 PFI 能力 | PASS：Stage 3/4 read-model、PFI 策略回测、盘感训练和大数据模拟器均保留；QBVS 作为顶层独立系统 smoke 验证，不作为 PFI 所属入口 |

## Validation

目标验证命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha -q
cd ../QBVS && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
python3 -B -m unittest tests.governance.test_human_entry_markdown_contract -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
git diff --check -- PFI
```

当前本地结果：

- Stage 5 focused contract：`Ran 14 tests / OK`
- Stage 1+2+3+4+5 full contracts：`Ran 89 tests / OK`
- Top-level QBVS lifecycle smoke：`Ran 1 test / OK`
- Python compile：`OK`
- Web shell syntax：`node --check OK`
- Project governance validation：`errors 0 / warnings 0`
- Human-entry Markdown contract：`Ran 2 tests / OK`
- `git diff --check -- PFI`：`OK`
- PFI.app entry refresh：`/Applications/PFI.app`、`~/Downloads/PFI.app`、`~/Desktop/PFI.app` installed and bound to canonical `CodexProject/PFI`
- macOS app acceptance lite：`29 pass / 0 fail / 2 info`
- Browser validation：Stage 5 labels visible, 建议与复盘 and 报告与洞察 workspace switches pass, screenshot `/tmp/pfi-stage5-browser-verified.png`, console errors `0`

## 当前边界

Stage 5 完成的是本地只读建议、报告和 Alpha context export MVP。真实账户联通、真实凭证、自动调度、支付提交、券商下单、报告正式发布、Alpha 独立消费验证和生产运行仍需后续单独 gate。
