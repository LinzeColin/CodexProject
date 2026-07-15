# RUNBOOK —— 交付后怎样使用和维护

## A. 日常使用

见 `01_PRD/用户手册.md`（每天 10 分钟 + 控制权 + 数据安全）。本手册面向部署、升级与恢复。

## B. 本地部署（主运行位置）

1. 环境：macOS · Python ≥3.10 · `pip install -r requirements.txt`（fsrs==6.3.1、feedparser、pyalex、semanticscholar、fastapi、jinja2、sqlite-utils）。
2. 初始化：`adp init` 建库（WAL+FTS5）→ 迁移旧数据（见 02_系统架构/数据模型.md 迁移规则）。
3. 定时：安装 launchd plist（模板在 deploy/，含错过补跑与时区注释）；心跳文件超时会在系统页亮「失败」行。
4. 网页：`adp web` 绑定 127.0.0.1:8787；开机自启同由 launchd 管理。
5. 密钥：全部走 Keychain/env；仓库、日志、导出包里永远没有密钥。

## C. Cloudflare 混合部署（R6 可选，home.linzezhang.com）

1. Pages：`deploy/pages/` 静态前端 → 绑定子域；Access 策略只允许你的邮箱登录。
2. D1：`wrangler d1 create adp-mirror` → 本机每日 `adp mirror push`（增量，SQLite 语法直迁）。
3. R2：每周快照桶 `adp-snapshots`，保留 12 份滚动。
4. Worker：`deploy/wrangler.toml` 定时触发（UTC 表达式，注意换算；免费档失败不自动重试——本机心跳负责兜底补跑）。
5. 免费额度核对（2026-06）：Workers 10 万请求/日、D1 5GB、R2 10GB——本系统日用量约几百行写入，余量充足。

## D. 升级与回滚

- 依赖升级：pin 版本 → 回放 30 天 → 无差异异常再合入；fsrs 大版本升级尤其注意参数数变化（5→6 曾 19→21）。
- 配置回滚：`adp config rollback <版本>`（一切配置变更有回执与历史版本）。
- 代码回滚：git revert 上一可用标签；数据事件只增不删，回滚代码不丢数据。

## E. 备份与恢复

- 每日自动备份至 data/backups/（30 份滚动）；每周快照至异地/R2。
- 恢复演练（每季一次，进运维记录）：从最近快照 `adp restore <快照>` → 校验行数与最近 7 天事件一致。
- 一键导出：系统页「数据永不丢失」卡片 → 通用格式（JSONL+CSV）。

## F. 安全检查清单（每月）

无密钥入库（扫描）· 授权凭证未过期即在用、过期即撤 · Access 策略仅 Owner · 来源政策快照在有效期 · 备份可恢复演练通过。
