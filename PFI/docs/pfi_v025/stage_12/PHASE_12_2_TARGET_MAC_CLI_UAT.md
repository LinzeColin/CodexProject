# PFI v0.2.5 Stage 12 Phase 12.2：目标 Mac CLI/App UAT

## 唯一目标

完成 `S12-P2-T1..T4` 的目标 Mac 安装、生命周期、磁盘/备份恢复和人类任务协议；严格遵守用户最新指令，不执行 Finder、LaunchServices、`open` 或 GUI 文件操作。

## Acceptance target

- Acceptance ID：`ACC-PFI-V025-S12-P122-TARGET-MAC-CLI-UAT`
- 结果上限：`candidate_pass`
- 仍需：Phase 12.3 状态统一与 release freeze、Stage 12 整阶段独立审查和绑定最终 release/evidence 的用户明确验收

## Finder requirement override

Roadmap 原始 `S12-P2-T1` 写明 Finder 启动；用户在当前任务明确禁止任何 Finder 操作。本 Phase 将入口证明改为：CLI 原子安装 canonical `/Applications/PFI.app`，然后直接执行 bundle 内原生 executable，并验证 plist、launcher query、backend manifest、frontend manifest 和 asset hash 为同一 build。该 override 只改变启动表面，不豁免技术门、真实数据门或最终人类验收。

## 真实运行边界

- 安装前保存 owner-only 的旧 bundle 私有归档；staged App 编译、ad-hoc sign、严格 codesign 校验后在 `/Applications` 同文件系统原子替换，失败自动恢复。
- App runtime 使用本 Phase 私有临时 HOME、data、runtime、cache、browser state 和 loopback ports；不写 canonical 私有 DB。
- 4 个真实 Alipay Git objects 进入已安装 App 的上传、预览、确认、一条复核与账本流程；隔离 SQLite 重启后仍保持 8,808 条 ledger 与已完成复核状态。
- `SRC-HOLDINGS` 仍为 `not_loaded`：持仓编辑保持 `not_run`，只验收真实阻断、无 fixture/fallback 和无假零。
- 报告继续保持当前真实覆盖状态：5 份报告中 3 blocked、2 partial；公式/参数/来源/Interconnection 下钻可见。

## 生命周期与恢复

- 覆盖 start、3 次 repeated start、browser close、stop、restart、浏览器 offline/recovery。
- 不触发真实内核 sleep/wake；仅对本 run 已证明归属的独立进程组执行 `SIGSTOP/SIGCONT`，明确记录为服务暂停/恢复代理和 P2 限制。
- canonical 私有 SQLite 仅执行 query-only + Online Backup API；restore、故障注入和自动 rollback 均在隔离副本。
- 磁盘压力仅使用 `hdiutil -nobrowse` 临时 HFS sparse image 制造真实 `SQLITE_FULL`，清理 partial backup 后恢复成功；主机卷不被填满。

## 明确不做

- 不进入 Phase 12.3，不更新最终 VERSION，不生成最终 `human_acceptance.json`。
- 不 push，不冻结 release，不声明 production accepted 或 final human acceptance。
- 不修改 Desktop/Downloads 入口；只做 CLI census 并记录不一致数量。

## Evidence

权威机器证据位于 `reports/pfi_v025/stage_12/phase_12_2/`，包括 App 安装、entry census、release identity、生命周期、浏览器 UAT、隔离 DB before/after、真实 backup/restore、真实磁盘压力、缺陷登记、Phase contract、trace、截图、privacy scan 和 artifact manifest。
