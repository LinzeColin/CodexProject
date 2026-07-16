# airM2 macdata HANDOFF

更新时间：2026-07-16（Australia/Sydney）

## 当前目标

执行 `TSK.OpenAIDatabase.CLEAN1.0001`：把 airM2/proM2 最新受控快照迁入 `main`，退役长期 `macdata-*` 生产分支，并将后续生产者改为 Automation C 短命 PR 事务。

## 当前状态

- airM2 最新分支快照的 17 个文件已原样迁入本地 `main` 工作树；本地聚合 SHA256 为 `9f0484dccd4a9e1ee684541fe59804425cda3a93a5049c0e552c4f5967bada15`。
- 生产者已改为：锁定 `main` → 唯一短命 `automation-c/macdata-airM2-*` 分支 → 非 draft PR → trusted Project Governance/Settlement → 精确哈希复核 → 事务分支删除。
- 禁止 direct-push `main`、重建 `macdata-airM2`、创建 Issue 或删除其他事务对象。
- 单元测试与本地事务模拟通过；模拟不调用 `git`/`gh`，远端写入为 0。
- GitHub 正式迁移、旧分支删除和 `PR/Issue/non-main=0/0/0` 验收尚未执行，原因是总任务约束要求 37 个 Task 全部完成后统一发布。

## 关键决策

- `main` 是唯一持久分支；`macdata-airM2` 仅作为待退役 legacy 输入，不再是生产目标。
- 发布前后必须满足 `PR/Issue/non-main branch=0/0/0`；任何门禁失败均 fail closed。
- 只发布配置声明的四个设备快照目录；提交前扫描高风险凭证模式。
- Time Machine、iCloud、凭证、Keychain、shell history、完整环境变量和 `.env` 原文仍不采集。
- 本任务不扩展电脑级缓存清理；仅保留原有 macdata 自身保留策略。

## 验证

- `python3 -m unittest OpenAIDatabase.macdata.tests.test_automation_c OpenAIDatabase.macdata.airM2.tests.test_macdata_package OpenAIDatabase.macdata.proM2.tests.test_macdata_package -q`：25 tests OK。
- `python3 -B -m py_compile ...`：通过。
- airM2 `--simulate-transaction`：`ok=true`、`mode=LOCAL_SIMULATION_NO_REMOTE_WRITE`、17 files、90,278 bytes。
- 正式远端验收：PENDING，禁止在全包统一发布前执行。

## 下一步

保持当前本地提交不推送；全 37 Task 完成后统一发布并执行旧分支删除、Settlement 与最终 `0/0/0` 验收。
