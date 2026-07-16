# PFI v0.2.5 Stage 2 Phase 2.1 实施合同

## 唯一目标

- Contract：`PFI-V025-STAGE2-PHASE21-DATA-ROOT-SOURCE-MANIFEST`
- Acceptance：`ACC-PFI-V025-S2-P21-DATA-ROOT-SOURCE-MANIFEST`
- Acceptance 来源：项目治理分配；Roadmap/Task Pack 未提供 `ACC-*` ID。
- Tasks：`S2-P1-T1..T4`
- 风险层级：`T3_PRIVACY`

本 Phase 只交付候选根目录清单、canonical/alias 决策、Source Manifest 和指标可计算性矩阵。Stage 2 保持 `in_progress`；不实现 Phase 2.2/2.3，不计算财务指标，不 push，不安装 App，不使用 Finder。

## 读取与写入边界

- 固定候选根：`MetaDatabase/PFI`、`PFI/MetaDatabase`、`$PFI_DATA_HOME`、`~/.pfi`。
- 真实来源只读；不复制、移动、合并、删除或修复原始数据。
- Git Evidence 只保留固定 alias、hash、计数、coverage、as-of、状态及脱敏原因。
- 禁止保存绝对私有路径、原始文件名、table 名、row、账户标识、金额或 credential。
- SQLite 只在 lexical root 与各级组件非 symlink、private root 位于 public Git 外、默认 alias 无冲突、operational directory 可遍历、固定 DB 为唯一 regular file、无 `pfi.sqlite-*` sidecar 且 header 为 rollback-journal `1/1` 时探测；使用 `mode=ro` 共享只读事务、`query_only=ON`、deny-write authorizer、固定 schema allowlist，并复核前后 sidecar、目录、候选集与 DB 完整指纹。
- SQLite source-level record count、coverage 和 as-of 无明确语义时保持 `null`；不能用数据库文件存在或空表推导财务零值。

## 实施步骤

1. 以 RED 测试锁定固定根、唯一 canonical private root、双层 schema、SQLite fail-closed、路径脱敏和 no-false-zero。
2. 新增 v0.2.5 专用 inventory 模块与薄 CLI；不复用会输出绝对路径或可写连接的旧审计器。
3. 从当前 Git object 的 import manifest 投影安全元数据，并对 `mode + path + oid + size + blob` 做 length-framed `sha256`；不输出 object path 或内容。
4. 对 canonical operational SQLite 只做完整性与 schema presence 元数据探测；不读财务行，不动态遍历表求总行数。
5. 生成四项交付物及 Phase Evidence；同步 canonical governance 与中文 human entries。
6. 运行 focused tests、CLI、privacy、source before/after、项目治理、changed-scope governance 和 diff 检查。

## Stop Conditions

- candidate roots 冲突且不能基于当前运行合同判定 canonical；
- source bytes、inode、size、mtime/ctime、hash 或 sidecar 集合在探测中变化；
- 输出需要包含绝对私有路径、原始文件名、账户/交易行、金额或密钥；
- SQLite 存在 symlink、非 regular candidate、不可遍历目录、WAL header、sidecar、多个候选、权限失败或 `quick_check != ok`；
- 任一 missing/partial source 被转换为财务 `0` 或 fake fixture pass。

## 回滚

只撤销本 Phase 的代码、schema、registry、Evidence 和治理提交。原始数据没有被修改，因此禁止对原始数据执行回滚、迁移或清理。
