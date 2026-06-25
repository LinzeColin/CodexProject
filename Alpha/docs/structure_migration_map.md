# Alpha S4PBT01 中文结构验收报告

- 任务：`S4PBT01`
- 验收：`ACC-S4PBT01`
- 结论：中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。

## 用户可读结论

Alpha 的 S4PBT01 只把历史输出和重建交接资料从主动项目根目录中分离出去。源码、测试、配置、私密样例数据路径和自动循环行为都没有改变。Owner 需要判断当前边界时，只看本节即可：`Alpha/outputs/**` 和旧 `HANDOFF.md` 属于历史/归档层，`Alpha/data/sample_prices.csv` 保持原位并继续作为 owner 复核私密路径。

## 中文验收标准

- 两分钟内能看出当前任务、验收 ID、影响路径、停止条件和回滚方式。
- 中文说明优先，英文路径和 ID 只作为不可翻译的技术标识保留。
- 不把治理整改 Roadmap 写进产品开发记录，不新增第二套事实源。

## 停止条件与结果

- Alpha 自动循环行为被改变：`false`
- Alpha 源码 import 路径被改变：`false`
- 私密 `Alpha/data/sample_prices.csv` 被移动或归档：`false`
- live-trading readiness 被提升：`false`

## 回滚

优先用 git revert 回退 S4PBT01 任务提交。若必须手工恢复，从 `governance/archive/other8_wave1_pending/Alpha/` 按旧路径还原，并用 `governance/stage_gates/s4pa/wave1_archive_manifest.sha256` 校验。

## 下一步

S4/S5 后续 gate 只能复用本报告中的中文边界，不得把 `outputs/**` 重新当作主动源码。

---

## 原技术记录

# Alpha S4PBT01 Structure Migration Map

Task: `S4PBT01`
Acceptance: `ACC-S4PBT01`
Date: 2026-06-25

## Scope

This map records the reversible structure simplification for Alpha. It moves
historical outputs and the reconstructed handoff out of the active Alpha project
root while keeping source code, tests, configs, and the private sample data path
unchanged.

## Old To New Paths

| Old path | New path | Status |
|---|---|---|
| `Alpha/HANDOFF.md` | `governance/archive/other8_wave1_pending/Alpha/HANDOFF.md` | archived |
| `Alpha/outputs/**` | `governance/archive/other8_wave1_pending/Alpha/outputs/**` | archived |
| `Alpha/data/sample_prices.csv` | `Alpha/data/sample_prices.csv` | unchanged; PRIVATE owner-review path |

## Compatibility Notes

- Source imports, test paths, configs, launcher scripts, and runtime state paths
  are unchanged.
- The old `Alpha/outputs/**` files were historical patch bundles and
  repository-local launchers; no active source or test reference consumed them
  at S4PBT01 implementation time.
- Future runtime or local output under `Alpha/outputs/` is ignored by
  `.gitignore` and should not become a tracked daily-development surface.
- The archived files remain checksum-bound by
  `governance/stage_gates/s4pa/wave1_archive_manifest.sha256`.
- If a migrated file's current checkout byte form differs from the S4PAT02
  historical checksum entry, the S4PBT01 run manifest records a reconciliation
  entry with both the historical checksum and the archived worktree checksum.

## Rollback

Rollback is a git revert of the S4PBT01 task commit. If manual restoration is
needed, restore each archived path from
`governance/archive/other8_wave1_pending/Alpha/` to its old `Alpha/` path and
verify checksums against `governance/stage_gates/s4pa/wave1_archive_manifest.sha256`.

## Stop Conditions Preserved

- Alpha automatic loop behavior changed: no.
- Alpha source import path changed: no.
- PRIVATE `Alpha/data/sample_prices.csv` moved or archived: no.
- Live-trading readiness promoted: no.
