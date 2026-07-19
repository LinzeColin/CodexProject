# Linze Operate — Owner 交接手册

> 目标:你**只需要看两个网址**,其余全自动。

## 一、你的入口

| 用途 | 网址 | 怎么进 |
|---|---|---|
| **项目总入口** | https://home.linzezhang.com | 直接打开;所有上线项目的跳转卡片 |
| **账号中心** | https://account.linzezhang.com | 邮箱密码 / Google / GitHub / Cloudflare 四选一 |
| 服务器控制台 | https://server.linzezhang.com | Coolify 登录(仅你) |
| 运行状态 | https://status.linzezhang.com | 各服务健康看板 |
| KMFA 财务面板 | https://kmfa.linzezhang.com | Cloudflare Access:输邮箱收验证码 |

**你的账号**:`linzezhang35@gmail.com`,已是全部 9 个仓库的最高权限 + 身份系统管理员。

## 二、日常你不用做的事(已全自动)
- **新版本上线**:任何仓 push 到 main → 自动检查(密钥扫描/测试/构建)→ 自动部署 → 自动冒烟 → 自动更新 home 卡片。失败会**拦住不上线**,不会把坏版本推到线上。
- **备份**:每天凌晨自动备份控制面+身份库,加密后传到服务器外(Oracle 对象存储)。已实测能恢复。
- **安全更新**:系统补丁自动装;镜像基底补丁已固化进构建。
- **崩溃自愈**:容器进程挂掉会自动拉起(已实测)。
- **死链巡检**:每天检查 home 上所有链接是否还活着。
- **成本熔断**:Cloudflare 免费席位接近上限(45/50)会自动停用快捷登录,不会产生费用。

## 三、你偶尔需要做的事
| 场景 | 做什么 |
|---|---|
| 想上线一个新项目 | 跟开发线程说一句;他跑 `tools/bootstrap_new_project.py` 即可,不用你操作 |
| 收到 Access 验证码邮件 | 那是你自己在登录 kmfa 面板,输码即可 |
| 某个站打不开 | 先看 status.linzezhang.com;多数情况会自愈,不用管 |

## 四、出事了怎么办(不用命令行)
1. 打开 https://status.linzezhang.com 看哪个红了
2. 打开 https://server.linzezhang.com → 找到该应用 → 点 **Redeploy**
3. 还不行 → 点 **Rollback** 回上一个版本
4. 仍不行 → 找开发线程,给他看 status 截图

## 五、钱
- 唯一付费:OVH VPS-1 新加坡,约 **A$7.4/月**
- 其余全部免费额度内:Cloudflare(免费版)、Coolify(自建免费)、Oracle 对象存储(Always Free)、NitroSend(免费档)
- 已设熔断:免费额度接近上限会自动降级,不会自动扣费

## 六、关键凭据在哪
全部在你本机 `_protected/alpha_deploy_private/`(**永不上传 GitHub**),索引见同目录 `CREDENTIAL_SLOTS.md`。
备份恢复密钥 `backup_enc.key` 是**离机恢复的唯一钥匙**,建议再复制一份到密码管理器。
