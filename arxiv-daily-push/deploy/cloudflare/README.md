# R6 · Cloudflare 混合部署（已上线）运维一页

部署日期：2026-07-15 · Worker：`adp-mirror` · 账户：linzezhang35@gmail.com（本机 wrangler 会话）

## 你怎么用（手机）

1. 直接打开 **https://adp.linzezhang.com**——无需钥匙。（adp.linzezhang.com 已归还给你的主页；主页上加一个链接即可跳转，例如 `<a href="https://adp.linzezhang.com">ADP 前沿学习</a>`。）
1a. **为什么云端是"镜像"而不是完整系统**：完整系统（选择引擎/FSRS/讲义生成/SQLite 主库/六主题界面）按任务包架构跑在你的 Mac 上（"重活留本机，云端做门面与镜像"）——Mac 睡眠时云端仍能看昨日内容、能评分排队，这是镜像存在的意义。想在手机上打开**一模一样的完整系统**：用 Cloudflare Tunnel 把本机 8787 端口挂到 adp.linzezhang.com（需要装官方 cloudflared，Mac 醒着才能访问）——见下方"完整系统直连（可选升级）"。
2. 云端页面：今天（讲义+四档回忆评分）/ 队列 / 系统。评分进回传队列，本机下次 `adp run`（或手动 `adp mirror pull`）时过 FSRS 生效——**云端浏览与排队不改学习状态**。
3. 断网/云端故障：本机闭环完全无感（run 内 push/pull 只降级并记 manifest）。

## 架构与数据流

```
本机 SQLite 主库 ──单向 push（每日 run 或 adp mirror push）──▶ D1 只读镜像
      ▲                                                        │
      └────── pull（每日 run 或 adp mirror pull）◀── events_inbox（云端评分队列）
Worker cron 20:30 UTC（=悉尼 06:30 AEST）：刷新到期提醒计数（失败不重试→本机心跳兜底）
```

## 访问控制（现状与代价——请知悉）

- **现状：无登录，页面公开可读**（Owner 2026-07-15 指令取消钥匙）。这意味着知道该域名的任何人都能读到讲义与学习状态（任务包盲点六提示过：这些内容构成你的兴趣画像），评分入口也公开（防滥用上限：每讲义每 UTC 日只收 1 条进队列，本机侧再过悉尼日互斥防重，最坏影响=某天某讲义的首条评分被他人抢写）。
- **想要"无钥匙且私有"的正解（推荐，约 2 分钟）**：Cloudflare Zero Trust → Access → Self-hosted App `adp.linzezhang.com`，策略=仅允许你的邮箱 One-time PIN。配置后无痕/他人访问会被 Cloudflare 登录页拦下，你自己的设备一次认证长期有效——体验同样是"直接打开"。
- 恢复钥匙模式：告诉我即可（代码保留在 git 历史 a0a79743）。

## Owner 待办（各 30 秒）

| 事项 | 步骤 | 影响 |
|---|---|---|
| 启用 R2 | Dashboard → R2 → 同意开通，然后本机 `adp mirror snapshot` | 每周快照上云（当前降级为本地 30 份滚动） |
| （可选）Access | 见上节 | 双层认证 |
| （可选）完整系统直连 | 装 cloudflared → tunnel 挂本机 8787 → adp.linzezhang.com 指向 tunnel（镜像转 fallback 子路径） | 手机打开=完整六主题系统（Mac 需在线） |

## 命令备忘

```bash
PYTHONPATH=src var/venv/bin/python -m adp mirror push      # 推镜像（含 key 哈希同步）
PYTHONPATH=src var/venv/bin/python -m adp mirror pull      # 收云端评分
PYTHONPATH=src var/venv/bin/python -m adp mirror snapshot  # 周快照（R2 启用后上云）
cd deploy/cloudflare && npx wrangler deploy                # 重新部署 Worker
```

免费额度对照（外部依赖.md）：Workers 10 万请求/日、D1 5GB——本系统日用量为个位数请求 + 几百行写入，余量巨大。
