# PFI 测试/样例/模拟数据审计

日期：2026-06-28 Australia/Sydney

用户最新约束：PFI 正式交付和运行依据只允许使用真实上传/导入的数据；不再新增 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收基础。真实原始数据统一进入 `CodexProject/MetaDatabase`，PFI 只读取或派生。

## 当前扫描结果

扫描范围：`PFI/`

扫描词：`demo`、`sample`、`synthetic`、`fixture`、`mock`、`fake`、`测试样例`

结果：175 个文件、604 处命中。

高命中路径示例：

| 命中数 | 路径 | 当前判断 |
| ---: | --- | --- |
| 41 | `PFI/src/pfi_os/application/pfi008_portfolio_acceptance.py` | legacy acceptance / synthetic fixture，不能作为 PFI 正式产品验收依据。 |
| 34 | `PFI/src/pfi_os/application/pfi009_strategy_acceptance.py` | legacy strategy acceptance，不能作为真实财务数据验收依据。 |
| 24 | `PFI/src/pfi_os/application/pfi004_truth_golden.py` | legacy golden fixture，需隔离为历史测试或移除产品路径影响。 |
| 17 | `PFI/docs/pfi_os_legacy/docs/Handbook.md` | legacy docs，不得污染正式运行页面。 |
| 16 | `PFI/systems/industry_research/source/tests/test_entity_registry.py` | 子系统测试，不得作为 PFI 用户财务验收依据。 |
| 15 | `PFI/systems/finance_ledger/source/tests/test_validate_outputs.py` | 子系统测试，不得作为 PFI 用户财务验收依据。 |
| 15 | `PFI/模型参数文件.md` | 历史记录中仍提到旧测试口径，需要后续中文清理或明确 legacy。 |
| 12 | `PFI/开发记录.md` | 历史记录中仍提到旧测试口径，需要后续中文清理或明确 legacy。 |
| 9 | `PFI/src/pfi_os/app/streamlit_app.py` | 需由前端/UI thread 继续核查是否影响正式页面。 |
| 5 | `PFI/src/pfi_v02/stage6_e2e_stabilization.py` | Stage 6 历史 synthetic/read-only E2E，不得继续作为当前 PFI 正式验收依据。 |

## 当前影响判断

- 正式 8501 抽样可见文本未命中 `demo/sample/synthetic/fixture/mock/fake/测试样例`。
- 最新真实浏览器矩阵 `/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json` 继续显示桌面和移动正式页面禁用可见词 0 命中，且消费搜索结果来自 `MetaDatabase` 真实支付宝流水，不来自测试/样例/模拟数据。
- 代码、测试、legacy docs 中仍大量存在测试/样例/模拟口径。
- 因此，本轮起完整 `pytest tests` 只能作为 legacy regression 信号，不能单独作为“PFI 产品交付通过”证据。
- 后续 Stage 复审和 closeout 必须优先使用真实 `MetaDatabase` 数据、真实空状态、schema/contract 检查，或经用户确认的脱敏真实最小子集。

## 已采取的纠偏

- `PFI/tests/test_v022_stage5_ledger_taxonomy.py` 不再构造虚构财务流水作为 Stage 5 验收输入；改为空记录/合同口径验证。
- Stage 5 本轮 closeout 暂停为正式交付通过；等待 UI thread 修复真实入口阻断，并等待后续测试数据隔离策略落地。

## 后续处理原则

- 不新增任何虚构账单、虚构交易、虚构持仓、demo records、synthetic records、fixture CSV/JSON。
- 如必须保留极小构造对象用于单元测试，必须先向用户说明并等待确认。
- 对 legacy sample/fixture 模块分三类处理：正式运行路径移除或隔离；历史测试改为空状态/schema/contract；确需留存的旧资料标记为 legacy archive，不用于验收。
