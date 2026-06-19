# FIFA Local Storage Slim Audit - 2026-06-15

生成时间：2026-06-15 AEST

## 目标

- 将 FIFA/TAB 研究系统相关必要数据资料备份到 GitHub。
- 本地只保留继续开发、运行网页平台、读取当前报告所需的必要文件。
- 删除重复交付包、缓存、临时锁文件，降低本地存储负担。

## GitHub 备份

本轮新增 GitHub 备份文件：

| 文件 | 覆盖内容 | 说明 |
| --- | --- | --- |
| `artifacts/backups/20260615/runtime_outputs_snapshot_20260615.tar.gz` | `outputs/` 当前快照，280 个条目 | 包含当前 runtime/report/provider/manual verification 等输出，排除 Python cache |
| `artifacts/backups/20260615/2026_FIFA_ledger_20260615.xlsx` | `Downloads/2026 FIFA.xlsx` | 当前 FIFA Excel 账本/赔率资料备份 |
| `artifacts/backups/20260615/fifa_world_cup_team_tables_1930_2022.xlsx` | `Downloads/fifa_world_cup_team_tables_1930_2022.xlsx` | 历史世界杯队伍表参考资料 |
| `artifacts/backups/20260615/deleted_review_packages_20260615.sha256` | 22 个旧 `FIFA_agent_review_package_*.zip` 的 SHA256 | 旧交付包为重复可再生成产物，不直接塞入 Git commit |
| `artifacts/backups/20260615/deleted_download_root_packages_20260615.sha256` | 2 个 Downloads 根目录交付 zip 的 SHA256 | 根目录 zip 可由 GitHub HEAD 重新生成 |

已推送备份 commit：

- `d925300 Back up FIFA runtime data snapshots`

## 删除内容

| 类别 | 数量 | 估算释放空间 | 处理方式 |
| --- | ---: | ---: | --- |
| 旧 `FIFA_agent_review_package_*.zip` | 22 文件 | 约 614MB | 删除本地重复包，保留 SHA256 manifest |
| Downloads 根目录交付 zip | 2 文件 | 约 59MB | 删除本地包，保留 SHA256 manifest；可由 GitHub HEAD 重新打包 |
| Excel 临时锁文件 `~$2026 FIFA.xlsx` | 1 文件 | 165B | 删除临时锁 |
| Python / pytest cache | 5 目录 | 约 4.8MB | 删除 `.pytest_cache` 与 `__pycache__` |

合计释放空间约 `678MB`。

## 本地保留

| 路径 | 当前大小 | 保留原因 |
| --- | ---: | --- |
| `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/github_sync/FIFA` | 约 96MB | Git 工作区、源码、docs、artifacts 备份、handoff |
| `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/outputs` | 约 31MB | 本地网页 runtime API 读取的最新输出 |
| `/Users/linzezhang/Downloads/FIFA Report` | 约 29MB | 用户打开的 HTML 入口与 `app_assets` |
| `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app` | 约 632KB | 用户双击入口 |
| `/Users/linzezhang/Downloads/2026 FIFA.xlsx` | 约 20KB | 用户可继续手动查看/维护的 Excel 账本 |
| `/Users/linzezhang/Downloads/fifa_world_cup_team_tables_1930_2022.xlsx` | 约 152KB | 小型参考资料，保留本地不影响存储 |
| `tab-research-pipeline/config/odds_providers.local.env` | ignored | 本机真实 provider env；不进入 Git |

## 验证

- 旧 report zip 剩余：`0`
- Downloads 根目录两个交付 zip：已删除
- Excel 临时锁：已删除
- Python cache：已删除
- GitHub 备份已推送：`d925300`
- 真实 The Odds API key tracked scan：未命中
- 本地网页必要目录未删除：HTML、`.app`、`app_assets`、`outputs` 均保留

## 边界

- 未删除 TAB 登录状态、浏览器状态、Keychain、个人文档、源码、Git 历史或 ignored provider env。
- 未运行 odds provider refresh，未消耗 API credits。
- 旧 zip 没有作为二进制大包直接写入 Git commit，避免永久膨胀仓库；如未来需要精确保留大型交付包，应使用 GitHub Release assets 或外部对象存储。
