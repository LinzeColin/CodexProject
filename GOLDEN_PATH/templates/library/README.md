# library / non-runtime 模板
库、数据集、归档、CLI、macOS-only 项目**不部署**(不造空服务),按 STAGE-14.4 例外处理:
1. 不建 Coolify 资源、不申请子域名
2. 在 home 卡片用 `fallbackUrl` 指向 GitHub 源,`deploymentStatus: "Non-runtime"`
3. 在 `GOLDEN_PATH/exception_policy.yaml` 登记原因(library/data/archive/macos-only/blocked)
