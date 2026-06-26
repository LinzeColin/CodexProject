# PFI S5PCT01 中文结构验收报告

- 任务：`S5PCT01`
- 验收：`ACC-S5PCT01`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

PFI/QBVS 的主动运行和算法代码仍在 `PFI/modules/qbvs_lab/qbvs/`。`config/` 是输入配置层，`tests/` 是验证层，根合同和 handoff 只描述 QuantLab read-only 互操作与恢复，`tools/` 下日期脚本只是报告/交接生成器，`runs/` 与 `reports/` 是输出证据层。本任务不移动文件、不改算法、不让输出反向成为源码事实。

## 中文验收标准

- Owner 能直接判断 active qbvs、config、tests、root contracts、dated tools、runs/reports 的职责。
- 必须明确 PFI/Serenity 运行路径不得因结构迁移触发外部副作用。
- 技术 ID 和路径可保留英文，但结论、风险、停止条件和回滚必须中文可读。

## 停止条件与结果

- PFI date-stamped script integration 改变算法：`未触发`
- root contracts 被当作 active algorithm source：`未触发`
- `runs/` 或 `reports/` 被默认 import 为 source truth：`未触发`
- `qbvs/` active runtime path 被改变：`未触发`
- archive written 或 files moved：`未触发`

## 回滚

回滚仅限文档和治理证据：移除 S5PCT01 报告、合同、smoke log、run manifest、README/AGENTS 边界说明和治理测试。因为没有移动 runtime 或输出文件，git restore 足够。

## 下一步

S5PCT03 只能汇总本中文边界和 Wave2 checksum，不得重新计算或移动 PFI 输出历史。

---

## 原技术记录

# PFI S5PCT01 结构报告

task_id: `S5PCT01`
acceptance_id: `ACC-S5PCT01`
project_id: `PFI_BIG_DATA_SIMULATOR`
mode: `BOUNDARY_ONLY_NO_ALGORITHM_CHANGE`

## Owner 摘要

S5PCT01 把当前 PFI/QBVS 结构绑定为明确层级：

- Active QBVS package: `PFI/modules/qbvs_lab/qbvs/`
- Config layer: `PFI/modules/qbvs_lab/config/`
- Test layer: `PFI/modules/qbvs_lab/tests/`
- Root contracts and handoff：`QUANTLAB_INTEGRATION_CONTRACT.json`,
  `HANDSHAKE_PROTOCOL.json`, `HANDOFF.md`, `BACKUP_MANIFEST.md`
- Date-stamped generator scripts：`PFI/modules/qbvs_lab/tools/`
- Output/evidence layers：`PFI/modules/qbvs_lab/runs/` and
  `PFI/modules/qbvs_lab/reports/`

S5PCT01 不移动文件。现有 Wave 2 manifest 记录 42 个 PFI archive/merge candidates：40 个 `ARCHIVE` 和 2 个 `MERGE`。这些候选继续由 `governance/stage_gates/s5pa/wave2_archive_manifest.json` checksum-bound。

## 边界决策

- `qbvs/` 仍是唯一默认 active runtime package。
- `config/` 可以供 `qbvs/` 命令使用，但不包含 runtime algorithms。
- `tests/` 验证 lifecycle 和 active runtime 行为。
- Root contracts 描述 QuantLab read-only 互操作和恢复。
- Date-stamped tools 是报告或 handoff 生成器；S5PCT01 不重写其逻辑，也不把它们变成默认 runtime 入口。
- `runs/` 和 `reports/` 是 output/evidence layers，不是 strategy、backtest、cache、warehouse 或 adapter algorithms 的 source truth。

## Smoke 证据

- `python -B -m pytest "PFI/modules/qbvs_lab/tests" -q`：`未运行`，本地 Python 环境不包含 `pytest`。
- `python -B -m unittest tests.test_s3pct02_lifecycle -q`：`通过`，1 个测试通过。
- Active `qbvs/` direct smoke：`通过`，生成 240 个 strategy specs，运行 backtest/buy-hold，并创建或刷新一个 OHLCV cache index。

结果：`可用 smoke 通过，pytest 环境阻塞已记录`。

## 停止条件结果

- PFI date-stamped script integration 改变算法：`未触发`
- Root contracts 被当作 active algorithm source：`未触发`
- `runs/` 或 `reports/` 被默认 import 为 source truth：`未触发`
- `qbvs/` active runtime path 被改变：`未触发`
- Archive written 或 files moved：`未触发`

## 回滚方式

回滚仅限文档和治理层：移除 S5PCT01 report、contract、smoke log、run manifest、README/AGENTS 边界说明和 S5PCT01 governance test。由于没有移动 runtime files、generated outputs 或 PFI artifacts，git restore 足够。
