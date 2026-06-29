# S03-P2 数据源检查矩阵完成记录

更新时间: 2026-06-29

## 范围

- Stage: `S03｜原始文件导入与数据源检查矩阵`
- Phase: `S03-P2｜数据源检查矩阵`
- 任务:
  - `S3PBT01`: 按来源系统、业务板块、文件包、主体、账户、频率生成矩阵。
  - `S3PBT02`: 状态仅使用 `已就绪`、`部分/阻塞`、`失败/不适用`、`已过期`、`人工复核`。
  - `S3PBT03`: 状态变化写入 metadata，不污染原始源。

## 已完成

- 新增 `KMFA/tools/source_check_matrix.py`，从 S03-P1 文件登记 bundle 生成 source check matrix row。
- 新增 `KMFA/tests/test_source_check_matrix.py`，覆盖矩阵维度、状态枚举和 metadata-only 状态事件。
- 新增 `KMFA/metadata/sources/source_check_matrix_schema.json` 与 `source_check_matrix_policy.yaml`。
- 新增 `KMFA/metadata/sources/source_check_matrix.jsonl` 与 `source_status_events.jsonl` 协议头记录；当前不提交真实源行或真实状态事件。
- 更新 `KMFA/metadata/sources/source_registry.yaml` 与 `KMFA/metadata/protocol/directory_manifest.json`，把 S03-P2 矩阵协议纳入机器可读面。

## 非范围

- 不实现 `S03-P3｜源优先级`。
- 不固化原始上传/授权导出优先级，不处理同源不一致，不生成跨源差异队列。
- 不导入真实私有源文件，不解析业务字段，不处理金额，不生成报告。
- 不做 UI 数据源检查板，不接外部自动接口。
- 不上传 GitHub；Stage 3 必须 P1/P2/P3 全部完成、整体复审并修复后再上传。

## TDD 证据

- RED: 先写 `KMFA/tests/test_source_check_matrix.py`，运行 `python3 -m unittest KMFA.tests.test_source_check_matrix -q` 得到 `ModuleNotFoundError: No module named 'KMFA.tools.source_check_matrix'`。
- GREEN: 实现 `KMFA/tools/source_check_matrix.py` 并修复直接 CLI 入口后，同一测试通过：`Ran 4 tests ... OK`。

## 验收映射

| Roadmap 任务 | 验收点 | 证据 |
|---|---|---|
| `S3PBT01` | 矩阵行包含来源系统、业务板块、文件包、主体、账户、频率 | `KMFA/tools/source_check_matrix.py`, `KMFA/metadata/sources/source_check_matrix_schema.json` |
| `S3PBT02` | 状态枚举严格限制为五个中文状态 | `KMFA/tests/test_source_check_matrix.py`, `KMFA/metadata/sources/source_check_matrix_policy.yaml` |
| `S3PBT03` | 状态变化生成 append-only metadata event，`raw_layer_write_allowed=false` | `KMFA/tools/source_check_matrix.py`, `KMFA/metadata/sources/source_status_events.jsonl` |

## 风险与控制

| 风险 | 控制 |
|---|---|
| 数据源矩阵被误认为真实业务数据已接入 | 仅提交 schema/policy/header 和工具，不提交真实 matrix row |
| 状态枚举漂移 | `ALLOWED_STATUSES` 与 policy/schema/test 固定为五个中文状态 |
| 状态变化污染 raw 层 | `source_status_event` 固定 `target_layer=metadata` 且 `raw_layer_write_allowed=false` |
| 越界做源优先级或自动选边 | 本 Phase 明确不实现 S03-P3 |

## 下一步

继续 Stage 3 时只进入 `S03-P3｜源优先级`。S03-P3 完成后再做 Stage 3 整体复审、修复和整体上传。
