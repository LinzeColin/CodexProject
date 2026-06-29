# S04-P1 Amount Tools Completion Record

## Scope

- stage: `S04`
- phase: `S04-P1`
- tasks: `S4PAT01-S4PAT03`
- version: `0.1.0-s04p1`
- status: `completed_validated_local_only`

## Completed

- `S4PAT01`: 新增 `normalize_amount_to_cents`，支持元、万元、千元、千分位、负数和括号负数，输出整数分。
- `S4PAT02`: 新增 `KMFA/tools/check_no_float_money.py`，检查 KMFA Python 文件中的 float literal、`float()` 调用和 float 标注。
- `S4PAT03`: 空白、横杠、井号、异常文本和不能整分表示的金额均抛出错误，不静默转 0。

## Files Added Or Updated

- `KMFA/tools/amount_tools.py`
- `KMFA/tools/check_no_float_money.py`
- `KMFA/tests/test_amount_tools.py`
- `KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md`
- `KMFA/stage_artifacts/S04_P1_amount_tools/human/test_results.md`
- `KMFA/stage_artifacts/S04_P1_amount_tools/machine/s04_p1_manifest.json`
- `KMFA/metadata/stage_status.jsonl`
- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/HANDOFF.md`
- `KMFA/docs/governance/*`

## Non Scope

- 不实现 S04-P2 字段标准化。
- 不实现 S04-P3 工具函数测试报告总包。
- 不建立 A0 黄金基准、zero-delta 正式校验、事实层、报告、UI 或外部接口。
- 不读取或提交原始敏感经营数据。
- 不上传 GitHub；Stage 4 完整复审并修复前不得上传。

## Rollback

删除 `KMFA/tools/amount_tools.py`、`KMFA/tools/check_no_float_money.py`、`KMFA/tests/test_amount_tools.py` 和 `KMFA/stage_artifacts/S04_P1_amount_tools/`，并恢复本次同步的 KMFA 状态/治理/中文入口文件。
