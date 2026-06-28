# v0.2.2 Stage 11 复审并解决

日期：2026-06-28
范围：本轮只复审解决 Stage 11 - 测试与验证。
非范围：不修改 v0.2.1 Web Shell UIUX 基线，不重装 app 入口，不同步 GitHub，不实现 Stage 12/13 新功能。

## 复审结论

Stage 11 原验收口径存在阻断：金融逻辑测试、跨板块一致性和图表性能门仍保留构造金额与替代记录思路，不能作为 PFI 正式运行上线条件。已改为真实金融逻辑验证：只读取 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`、真实 read model、本地参数 hash 和中文真实空态。

## 已解决问题

- 投资入金：当前没有真实 CBA -> Moomoo 双边转账或入金分组时，保留中文真实空态，不构造入金金额。
- 基金申购：读取真实支付宝基金申购 `21` 条、`CNY 4,120.00`，计入消费总流出，不计入生活消费；没有真实持仓快照时不伪造持仓增加。
- 退款抵消：读取真实退款 `250` 条、抵消金额 `CNY 132,707.90`，不伪造收入或投资收益。
- 信用卡还款：当前没有真实信用卡还款事件时，保留中文真实空态，不构造还款链路。
- 现金流：可追溯真实账本事件；没有真实计划事件时保留中文真实空态。
- 图表性能：使用真实 `8815` 条标准化流水记录检查 `compute time` 与 `cache status`，不得使用模拟记录作为正式验收依据。

## 变更文件

- `PFI/src/pfi_v02/stage_v022_test_validation.py`
- `PFI/tests/test_v022_stage11_test_validation.py`
- `PFI/tests/test_v022_review_stage11.py`
- `PFI/docs/pfi_v022/STAGE11_TEST_VALIDATION.md`
- `PFI/docs/pfi_v022/ROADMAP_LOCK.md`
- `PFI/config/pfi_parameters.yaml`
- `PFI/config/parameter_changelog.md`
- `PFI/模型参数文件.md`
- `PFI/功能清单.md`
- `PFI/开发记录.md`
- `PFI/HANDOFF.md`

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage11_test_validation.py tests/test_v022_review_stage11.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_review_stage10.py tests/test_v022_stage11_test_validation.py tests/test_v022_review_stage11.py -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
curl -fsS http://127.0.0.1:8501/_stcore/health
```

## 当前验证状态

- Stage 11 目标 + 复审测试：`11 passed, 15 subtests passed`。
- Stage 0-11 v0.2.2 相关回归：`104 passed, 363 subtests passed`。
- Web shell 语法检查：`node --check web/app/shell.js` 通过。
- 项目治理检查：`python3 scripts/validate_project_governance.py --project PFI` 返回 `errors: 0`、`warnings: 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`curl -fsS http://127.0.0.1:8501/_stcore/health` 返回 `ok`。
- 真实 8501 浏览器矩阵：`/tmp/pfi_stage11_review_recheck/summary.json` 通过；桌面和移动端均验证 `PFI`、`首页总览`、`数据源与上传`、`建议与复盘`、`报告与洞察`、`AUD/CNY` 可见，7 个首页 workflow 卡片可见，`.workflow-meta=0`，一级入口和首页真实按钮可点击，全局搜索 `406/8815` 可用，禁用词 `0`，console/page errors `0`，水平溢出 `0px`。
- 浏览器截图：`/tmp/pfi_stage11_review_recheck/desktop.png`、`/tmp/pfi_stage11_review_recheck/mobile.png`。

## 剩余风险

- PFI legacy 目录中仍存在历史 `fixture` / `synthetic` / `demo` 词汇和早期只读验收记录；这些只能作为 legacy regression 背景，不得作为 PFI 正式页面、报告、图表、首页或建议的产品数据源。
- GitHub 同步、app 入口重装和全局缓存清理按当前整体 goal 在 Stage 1-13 复审解决与整体复审完成后执行。
