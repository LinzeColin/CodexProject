# PFI v0.2.1.1 交付阻断复核记录

日期：2026-06-29

## 结论

本轮复核针对用户指出的正式可见 UI 汇率格式残留、真实支付宝数据同步、GitHub main 同步、本机 app 入口和真实浏览器验收阻断项。

当前正式汇率徽标统一为：

`AUD/CNY=4.69（2026/06/28 06:00）`

当前通用展示格式统一为：

`AUD/CNY=4.69（YYYY/MM/DD HH:MM）`

旧 CNY/AUD 口径、紧凑日期和双连字符时间口径不得作为正式 UI、静态页、参数中心、报告页或 Interconnection 页展示格式。历史文档如提及旧口径，只能作为历史记录，不得被正式页面读取展示。

## 真实数据同步状态

真实支付宝数据以 `MetaDatabase/PFI/alipay_daily` 为 canonical 原始与标准化归档：

| 项目 | 状态 |
|---|---|
| 原始 CSV | 4 个真实支付宝导出文件 |
| 原始归档 | `MetaDatabase/PFI/alipay_daily/raw/` |
| 标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |
| 导入 manifest | `MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json` |
| 私有运行导入 | `~/.pfi/runtime/imports/alipay_daily/` |
| 标准化记录数 | 8815 |
| 待复核记录数 | 406 |
| 日期范围 | 2022-06-06 至 2026-06-03 |

正式消费趋势读模型读取 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`。账户与投资模块缺少真实持仓或账户快照时，必须显示中文真实空态，不得伪造收益、净值或持仓。

## Git 与工作树边界

本轮只允许修改 `PFI/` 范围内的文档、合同和前端可见格式相关文件，不触碰 EEI、ADP、Alpha、Serenity、OpenAIDatabase 或用户真实数据。

canonical 本机 checkout 当前存在历史混合分支与未提交状态，因此本轮采取：

1. 在干净临时 worktree 基于 `origin/main` 修复与验证。
2. 提交并推送到 GitHub `main`。
3. 回到 canonical checkout 只按 PFI 相关路径同步本轮文件。
4. 不执行整仓 reset，不删除其他 worktree，不删除真实数据库和 MetaDatabase。

## 验收要求

本轮 closeout 必须同时提供：

- GitHub `main` 最新 commit hash。
- canonical checkout 当前 HEAD/branch 与 `origin/main` 的关系。
- `/Applications/PFI.app`、`~/Downloads/PFI.app`、Desktop link 的 PFI root 指向。
- 8501 与 8766 health，PID cwd 指向 canonical PFI。
- 真实浏览器桌面端与移动端验收矩阵。
- 正式可见页面旧汇率格式扫描结果。
- 真实支付宝数据 manifest、记录数、read model 读取状态。
- worktree、branch、PR/issue 检查结果。
