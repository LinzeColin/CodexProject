# Alpha S4PBT01 中文结构验收报告

- 任务：`S4PBT01`
- 验收：`ACC-S4PBT01`
- 结论：用户可读优先，中文 owner 可读验收通过；本报告先给人类可读结论，再保留原技术记录。
- 验收状态：`通过`

## 用户可读结论

Alpha 的 S4PBT01 只把历史输出和重建交接资料从主动项目根目录中分离出去。源码、测试、配置、私密样例数据路径和自动循环行为都没有改变。Owner 需要判断当前边界时，只看本节即可：`Alpha/outputs/**` 和旧 `HANDOFF.md` 属于历史/归档层，`Alpha/data/sample_prices.csv` 保持原位并继续作为 owner 复核私密路径。

## 中文验收标准

- 两分钟内能看出当前任务、验收 ID、影响路径、停止条件和回滚方式。
- 中文说明优先，英文路径和 ID 只作为不可翻译的技术标识保留。
- 不把治理整改 Roadmap 写进产品开发记录，不新增第二套事实源。

## 停止条件与结果

- Alpha 自动循环行为被改变：`未触发`
- Alpha 源码 import 路径被改变：`未触发`
- 私密 `Alpha/data/sample_prices.csv` 被移动或归档：`未触发`
- live-trading readiness 被提升：`未触发`

## 回滚

优先用 git revert 回退 S4PBT01 任务提交。若必须手工恢复，从 `governance/archive/other8_wave1_pending/Alpha/` 按旧路径还原，并用 `governance/stage_gates/s4pa/wave1_archive_manifest.sha256` 校验。

## 下一步

S4/S5 后续 gate 只能复用本报告中的中文边界，不得把 `outputs/**` 重新当作主动源码。

---

## 原技术记录

# Alpha S4PBT01 结构迁移记录

任务：`S4PBT01`
验收：`ACC-S4PBT01`
日期：2026-06-25

## 范围

本记录描述 Alpha 可回滚的结构瘦身：历史输出和重建交接资料从主动项目根目录移出，源码、测试、配置和私密样例数据路径保持不变。

## 旧路径到新路径

| 旧路径 | 新路径 | 状态 |
|---|---|---|
| `Alpha/HANDOFF.md` | `governance/archive/other8_wave1_pending/Alpha/HANDOFF.md` | 已归档 |
| `Alpha/outputs/**` | `governance/archive/other8_wave1_pending/Alpha/outputs/**` | 已归档 |
| `Alpha/data/sample_prices.csv` | `Alpha/data/sample_prices.csv` | 未改变；私密 owner 复核路径 |

## 兼容说明

- 源码 import、测试路径、配置、启动脚本和运行状态路径均未改变。
- 旧 `Alpha/outputs/**` 文件是历史 patch 包和仓库本地启动器；S4PBT01 实施时没有主动源码或测试引用它们。
- 未来 `Alpha/outputs/` 下的运行输出或本地输出由 `.gitignore` 忽略，不应重新成为日常开发 tracked 表面。
- 已归档文件继续由 `governance/stage_gates/s4pa/wave1_archive_manifest.sha256` 绑定校验和。
- 如果迁移文件当前 checkout 字节与 S4PAT02 历史 checksum 不一致，S4PBT01 run manifest 同时记录历史 checksum 和归档 worktree checksum。

## 回滚方式

回滚优先使用 git revert 回退 S4PBT01 任务提交。若必须手工恢复，把每个归档路径从 `governance/archive/other8_wave1_pending/Alpha/` 还原到旧 `Alpha/` 路径，并用 `governance/stage_gates/s4pa/wave1_archive_manifest.sha256` 校验。

## 停止条件保持情况

- Alpha 自动循环行为被改变：未触发。
- Alpha 源码 import 路径被改变：未触发。
- 私密 `Alpha/data/sample_prices.csv` 被移动或归档：未触发。
- live-trading readiness 被提升：未触发。
