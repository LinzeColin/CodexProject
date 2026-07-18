# 域名 → 仓库 → 运行承载 (linzezhang.com, 只读发现 2026-07-18)

| 子域 | 仓库/嵌套 | 承载方式 |
|---|---|---|
| home | LinzeHomeHub | Cloudflare (Pages/Workers) |
| memoryatlas | AgentDatabase/MemoryAtlas | Cloudflare Pages |
| adp | MetaDatabase/ADP | Cloudflare Tunnel |
| eei | MetaDatabase/EEI | Cloudflare 代理(承载方式待更广只读 token 确认) |
| nab | Archive/nab | Cloudflare 代理(同上) |
| send | (NitroSend 邮件) | MX + SPF + DKIM + DMARC |
| **account** (本次新建) | 自建 | 自托管 Keycloak @ OVH VPS-1 (Traefik+LE) |
| **status** (本次新建) | 自建 | 自托管 Gatus @ OVH VPS-1 |

## 结论
- 现有线上站均由 Cloudflare(Pages/Tunnel/代理)承载,不在任何自有服务器 → 迁移不中断
- account/server 子域此前不存在;account 已由本工程新建上线
