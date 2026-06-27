# PFI MetaDatabase 指针

PFI 的用户上传原始数据不再分散存放在临时运行目录。

当前 GitHub 可见根目录：

- `LinzeColin/CodexProject/MetaDatabase`
- 本机路径：`/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject/MetaDatabase`

当前已登记：

- 支付宝日常账单原始 CSV：`MetaDatabase/PFI/alipay_daily/raw/`
- 支付宝标准化导入 manifest 和流水：`MetaDatabase/PFI/alipay_daily/processed/`

PFI 运行时仍可读取本机缓存 `~/.pfi/runtime/imports/`，但验收、备份和 GitHub 检查以顶层 `MetaDatabase/` 为准。
