# PFI S5PCT01 中文结构验收报告

- 任务：`S5PCT01`
- 验收：`ACC-S5PCT01`
- 结论：中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。

## 用户可读结论

PFI/QBVS 的主动运行和算法代码仍在 `PFI/大数据模拟器/qbvs/`。`config/` 是输入配置层，`tests/` 是验证层，根合同和 handoff 只描述 QuantLab read-only 互操作与恢复，`tools/` 下日期脚本只是报告/交接生成器，`runs/` 与 `reports/` 是输出证据层。本任务不移动文件、不改算法、不让输出反向成为源码事实。

## 中文验收标准

- Owner 能直接判断 active qbvs、config、tests、root contracts、dated tools、runs/reports 的职责。
- 必须明确 PFI/Serenity 运行路径不得因结构迁移触发外部副作用。
- 技术 ID 和路径可保留英文，但结论、风险、停止条件和回滚必须中文可读。

## 停止条件与结果

- PFI date-stamped script integration 改变算法：`false`
- root contracts 被当作 active algorithm source：`false`
- `runs/` 或 `reports/` 被默认 import 为 source truth：`false`
- `qbvs/` active runtime path 被改变：`false`
- archive written 或 files moved：`false`

## 回滚

回滚仅限文档和治理证据：移除 S5PCT01 报告、合同、smoke log、run manifest、README/AGENTS 边界说明和治理测试。因为没有移动 runtime 或输出文件，git restore 足够。

## 下一步

S5PCT03 只能汇总本中文边界和 Wave2 checksum，不得重新计算或移动 PFI 输出历史。

---

## 原技术记录

# PFI S5PCT01 Structure Report

task_id: `S5PCT01`
acceptance_id: `ACC-S5PCT01`
project_id: `PFI_BIG_DATA_SIMULATOR`
mode: `BOUNDARY_ONLY_NO_ALGORITHM_CHANGE`

## Owner Summary

S5PCT01 binds the current PFI/QBVS structure into explicit layers:

- Active QBVS package: `PFI/大数据模拟器/qbvs/`
- Config layer: `PFI/大数据模拟器/config/`
- Test layer: `PFI/大数据模拟器/tests/`
- Root contracts and handoff: `QUANTLAB_INTEGRATION_CONTRACT.json`,
  `HANDSHAKE_PROTOCOL.json`, `HANDOFF.md`, `BACKUP_MANIFEST.md`
- Date-stamped generator scripts: `PFI/大数据模拟器/tools/`
- Output/evidence layers: `PFI/大数据模拟器/runs/` and
  `PFI/大数据模拟器/reports/`

No files are moved in S5PCT01. The existing Wave 2 manifest records 42 PFI
archive/merge candidates: 40 `ARCHIVE` and 2 `MERGE`. Those candidates remain
checksum-bound by `governance/stage_gates/s5pa/wave2_archive_manifest.json`.

## Boundary Decisions

- `qbvs/` remains the only default active runtime package.
- `config/` may feed `qbvs/` commands, but does not contain runtime algorithms.
- `tests/` verifies lifecycle and active runtime behavior.
- Root contracts describe QuantLab read-only interoperability and recovery.
- Date-stamped tools are report or handoff generators; S5PCT01 does not rewrite
  their logic and does not make them default runtime entries.
- `runs/` and `reports/` are output/evidence layers and are not source truth
  for strategy, backtest, cache, warehouse, or adapter algorithms.

## Smoke Evidence

- `python -B -m pytest "PFI/大数据模拟器/tests" -q`: `NOT_RUN`, local Python
  environments do not include `pytest`.
- `python -B -m unittest tests.test_s3pct02_lifecycle -q`: `PASS`, 1 test OK.
- Active `qbvs/` direct smoke: `PASS`, generated 240 strategy specs, ran
  backtest/buy-hold, and created/refreshed one OHLCV cache index.

Result: `PASS_WITH_PYTEST_ENV_BLOCKER_RECORDED`.

## Stop Conditions

- PFI date-stamped script integration changes algorithm: `false`
- Root contracts used as active algorithm source: `false`
- `runs/` or `reports/` imported as source truth by default: `false`
- `qbvs/` active runtime path changed: `false`
- Archive written or files moved: `false`

## Rollback

Rollback is documentation/governance-only: remove the S5PCT01 report, contract,
smoke log, run manifest, README/AGENTS boundary text, and S5PCT01 governance
test. Because no runtime files, generated outputs, or PFI artifacts are moved,
git restore is sufficient.
