# R6 · Cloudflare 部署（完整系统直连 + 镜像兜底）运维一页

部署日期：2026-07-15 · Worker：`adp-mirror` · Tunnel：`adp`（3bc9d50e） · 账户：linzezhang35@gmail.com（本机 wrangler 会话）

## 你怎么用（手机）

1. 直接打开 **https://adp.linzezhang.com**——无需钥匙。（home.linzezhang.com 已归还给你的主页；主页上加一个链接即可跳转，例如 `<a href="https://adp.linzezhang.com">ADP 前沿学习</a>`。）
2. **Mac 在线时**：打开的就是完整系统本体（六主题界面、今天/队列/雷达/证据/系统/试运行全部页面）——Worker 把请求经 Cloudflare Tunnel 反向代理到本机 127.0.0.1:8787，评分即时过 FSRS。（直连已于 2026-07-15 端到端实测：`adp-origin.linzezhang.com` 回源记录经你确认后由 cloudflared 创建，云端打开完整系统 183ms，远程守卫 403 生效。）
2a. **你的主页**：https://home.linzezhang.com 由你自己的 `linze-home-hub` Worker 提供（Owner 独立维护，不在本仓库）。曾一度被本项目的 Worker 误占，2026-07-15 已把 custom_domain 归还给 `linze-home-hub` 并删除误建的 Worker；本仓库不再放任何主页代码。想从主页跳到 ADP，在你的主页里加 `<a href="https://adp.linzezhang.com">ADP 前沿学习</a>` 即可。
3. **Mac 睡眠/断网时**：自动回落只读镜像（页脚会标明"镜像兜底页"）——仍可看讲义、评分进回传队列，本机下次 `adp run`（或 `adp mirror pull`）时过 FSRS 生效。
4. 断网/云端故障：本机闭环完全无感（run 内 push/pull 只降级并记 manifest）。

## 架构与数据流

```
手机 ─▶ adp.linzezhang.com（Worker）
          │ 首选：反代 adp-origin.linzezhang.com ─▶ Tunnel ─▶ 本机 127.0.0.1:8787（完整系统）
          │ 兜底：本机离线/隧道断 ─▶ D1 只读镜像 + events_inbox 回传队列
本机 SQLite 主库 ──单向 push（每日 run 或 adp mirror push）──▶ D1 镜像
      └────── pull（每日 run 或 adp mirror pull）◀── events_inbox（兜底页评分队列）
Worker cron 20:30 UTC（=悉尼 06:30 AEST）：刷新到期提醒计数（失败不重试→本机心跳兜底）
```

常驻（LaunchAgents，模板在 `deploy/cloudflare/launchd/`，已安装到 `~/Library/LaunchAgents/`）：

- `com.linze.adp.web` —— 完整系统网页（uvicorn，127.0.0.1:8787），日志 `var/log/adp-web.log`
- `com.linze.adp.tunnel` —— cloudflared connector（`--no-autoupdate` 防漂移；令牌 `~/.cloudflared/adp-tunnel-token`，0600 不入库），日志 `var/log/adp-tunnel.log`

已知边界（如实披露）：两个 LaunchAgent 是 gui 域——**重启后要登录一次 Mac 才会拉起**（FileVault 下本来也无法更早）；plist 里的路径绑定在当前 worktree（`main_worktree/CodexProject/adp`），若仓库拆分迁走这个目录，需改 plist 路径后重新 `launchctl bootstrap`（venv、数据库、日志都随目录走）。

## 访问控制（现状与代价——请知悉）

- **现状：无登录，页面公开可读**（Owner 2026-07-15 指令取消钥匙）。知道域名的任何人都能读讲义与学习状态（任务包盲点六：兴趣画像）。
- **写操作分级**：本机 webapp 对隧道来访（带 CF 头，无法伪造——外部流量必经 Cloudflare 边缘）只放行「浏览 + 主动回忆评分」；上板/试点决策/状态编辑/纠错/撤销/迁移等 Owner 决策类 POST 远程一律 403，仅限本机亲手执行（`webapp.remote_guard`，有保护测试）。兜底镜像的 /grade 仍有每讲义每 UTC 日 1 条防重上限。
- **想要"无钥匙且私有"的正解（推荐，约 2 分钟）**：Cloudflare Zero Trust → Access → Self-hosted App `adp.linzezhang.com`，策略=仅允许你的邮箱 One-time PIN。你的设备一次认证长期有效，外人被拦。
- 恢复钥匙模式：告诉我即可（代码保留在 git 历史 a0a79743）。

## Owner 待办（各 30 秒）

| 事项 | 步骤 | 影响 |
|---|---|---|
| ~~确认 DNS 回源记录~~ | 已完成（2026-07-15 你点授权后自动创建，直连已实测） | — |
| 启用 R2 | Dashboard → R2 → 同意开通，然后本机 `adp mirror snapshot` | 每周快照上云（当前降级为本地 30 份滚动） |
| （可选）Access | 见上节 | 私有化入口 |
| （可选）自托管 RSSHub | Docker 跑 `diygod/rsshub` 后改 boards_v0_3.yaml 里的 feed_url | 板块三「国务院政策文件库」路由从限流降级恢复直连 |

## 命令备忘

```bash
PYTHONPATH=src var/venv/bin/python -m adp mirror push      # 推镜像（兜底数据）
PYTHONPATH=src var/venv/bin/python -m adp mirror pull      # 收兜底页评分
PYTHONPATH=src var/venv/bin/python -m adp mirror snapshot  # 周快照（R2 启用后上云）
cd deploy/cloudflare && npx wrangler deploy                # 重新部署镜像/代理 Worker（adp-mirror）
cd deploy/cloudflare/home && npx wrangler deploy           # 重新部署主页 Worker（home）
launchctl kickstart -k gui/$UID/com.linze.adp.web          # 重启本机网页
launchctl kickstart -k gui/$UID/com.linze.adp.tunnel       # 重启隧道 connector
tail -f var/log/adp-tunnel.log                             # 看隧道状态
```

免费额度对照（外部依赖.md）：Workers 10 万请求/日、D1 5GB、Tunnel 免费——本系统日用量为个位数请求 + 几百行写入，余量巨大。
