# CodexProject 主仓库

LinzeColin 的多项目源码与治理入口。根目录只保留稳定导航和公共治理边界；项目状态、运行证据与实现细节留在对应项目。多仓拆分后本仓保留治理骨架与退役项目 `WDA` 的历史。

## 📦 数据落地政策（长期有效 · 自运行分仓治理）

**本仓只存代码与治理，长期/业务/运行时数据不入本仓。** 开发中产生的任何需长期存储的数据
（原始业务数据、导出件、数据库、内容寻址对象、运行时快照、含 PII 的记录等）
一律写入私有仓 `LinzeColin/Private-Database` 对应数据区，**不要提交进本仓**：
KM 经营数据 → `Private-KMDatabase/`；Agent 会话/记忆 → `Private-AgentDatabase/`；其余项目数据 → `Private-MetaDatabase/`。
用 `private_db_client.py` 免 clone 读写（`ingest/get/list/verify`），Private-Database 禁止 `git clone`；派生/临时/可再生产物走 `.gitignore`。
**一次分清、长期自运行，不再需要人工反复迁移。**（`AGENTS.md` 已将本条列为执行契约。）

## 🧭 基础设施路牌（读这里,别乱猜)

**云服务器 / 云数据库 / 各家 API 与 token 的完整配置,不在本仓,在本机受保护目录。**
本仓是公开仓,**任何凭据、私钥、源站 IP 都不得写进来**。要接手运维,按顺序读这三份:

| 顺序 | 本机路径(不在 git 里) | 里面有什么 |
|---|---|---|
| 1 | `_protected/alpha_deploy_private/INFRA_CONFIG.md` | **总册**:服务器规格与 SSH 方式、三个 Postgres 怎么连、域名路由表、cron 清单、凭据索引、备份恢复、排障命令、已知隐患 |
| 2 | `_protected/alpha_deploy_private/HANDOVER_PROMPT_FOR_CODEX.md` | 交接手册:各服务现状、踩过的坑、改代码的正确流程 |
| 3 | `_protected/alpha_deploy_private/linze_ovh_vps1_operate_status.md` | 完整进度台账 |

上述路径相对于本机工作间根目录 `~/Documents/Codex/GithubProject/`。

### 硬性边界(违反会出事)

- **凭据只存 `_protected/`,权限 0600,永不 commit、永不上传。** 本仓、任何公开仓都不许出现 token/私钥/密码/源站 IP。
- **服务器主机名走域名,不写 IP**:站点都在 Cloudflare 后面,写出源站 IP 等于废掉源站隐藏。
- **数据库不对外**:三个 Postgres 都只在 Docker 内网,必须先 SSH 再 `docker exec`;**不要为了方便去发布端口**。
- **改运维代码的流程**见 `HANDOVER_PROMPT_FOR_CODEX.md`,不要直接在生产机改文件后不回写仓库。

### 在线只读入口(公开,不含敏感信息)

- 云平台总览(项目/主机/成本/用量/自愈/GitHub 六个二级页):<https://status.linzezhang.com>
- 运维健康探活:<https://uptime.linzezhang.com>
- 价格设置 与 GitHub 私有全量:`status.linzezhang.com/admin` 与 `/admin/github`,**仅 owner 本人可见**(Cloudflare Access + 后端 JWT 双校验,匿名 302)。

## Governance Entry

- 执行契约：[AGENTS.md](AGENTS.md)
- 治理标准：[docs/governance/STANDARD.md](docs/governance/STANDARD.md)
- 每个开发 Task 的人类记录：`governance/task_records/<Task-ID>/功能清单.md`、`开发记录.md`、`模型参数文件.md`
- 根清洁预算：[governance/root_cleanliness_budget.json](governance/root_cleanliness_budget.json)

## Projects

| Project | Path | Entry |
|---|---|---|


## Retired projects

- `WDA` 由 Owner 于 2026-07-13 退役；只保留历史，不得在无明确再激活 Task 时修改。
- 已迁出项目、目标仓库与 recovery evidence 只以 `governance/projects.yaml` 的 `migrated_projects` 为准，不在 README 复制可漂移状态表。

## 治理事实与证据边界

- 项目清单：`governance/projects.yaml`
- 不可变 ID：`governance/id_registry.json`
- 证据边界：`governance/artifact_policy.json`
- workflow 权限与供应链：`governance/workflow_policy.json`
- 大对象/archive/cache：`governance/repository_hygiene_policy.json`
- 根入口、归属、链接与上下文预算：`governance/root_cleanliness_budget.json`

每个 fact domain 只能有一个唯一写入者：canonical registry/policy 负责可编辑事实，README 与 generated view 只负责导航或展示，不能反向覆盖 canonical data。旧 manifest、attestation、review bundle 与 stage gate 仅作只读兼容；新运行只追加小于 64 KiB 的 `TSK-*.json` 紧凑收据，完整 stdout、日志和大文件只能进入临时或 CI artifact。

README 只做稳定导航，不记录短期执行状态或本机路径。Canonical facts、derived views、紧凑收据和完整 CI artifact 必须保持分层；本地 cache、WAL/SHM、session、recovery folder 不是 product source。

## Required Checks

普通变更使用只读 changed-scope gate：

```bash
python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main
python3 -B scripts/root_cleanliness_audit.py --root . --json
```

Write-mode generators are not part of the ordinary PR fast gate。仅 scheduled/manual/release evidence 可写入显式 artifact 目录：

```bash
python3 scripts/generate_governance_dashboard.py --write --changed-only --base-ref origin/main --root-artifact-dir /tmp/governance-generated-views
```

进入项目后先读其 `README.md`、`AGENTS.md` 和 Task 要求的人类记录；无明确合同时不得触碰 secrets、private/raw data、runtime DB、browser profile、cache 或无关项目。
