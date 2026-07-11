roadmap_progress: R2 / R2.1

status: READY_FOR_EXTERNAL_REVIEW

previous_completed_stage: R1

canonical_name: KMFA 钉钉考勤 skill

canonical_skill_id: kmfa-dingtalk-attendance-skill

occurrence_summary:
  - inventory_baseline_commit: 5b41a243cb52ae53a062fe98d31db0859b0e2194
  - method: 在上述 baseline、重写本 handoff 之前，对 118 个指定 tracked 文件和两个本机考勤 automation 的 prompt、config、memory 做大小写不敏感、非重叠旧编号 token 匹配；另计 tracked 文件路径中的旧编号。本 handoff 为避免自引用不计入新增引用，私有归档和预存 untracked 文件未扫描。
  - tracked_content_matches: 476
  - tracked_path_matches: 1
  - local_automation_matches: 10
  - total_matches: 487
  - A_current_human_visible_name: 51
  - B_current_machine_identifier: 42
  - C_current_runtime_or_storage_protocol: 112
  - D_historical_public_document: 279
  - E_private_history_or_archive: 3
  - category_total_check: 51 + 42 + 112 + 279 + 3 = 487
  - private_archive_note: E 类计数只包含两个本机 automation memory 中的 3 个可审计匹配；私有归档文件未读取、未列名、未计数。

migration_inventory:

| 类别 | 当前值 | 所在文件或本机 automation | 用途及依赖 | 建议新值 | 修改时必须同步 | 旧值临时只读兼容 | 删除兼容层的明确条件 | 风险 | R2.2 |
|---|---|---|---|---|---|---|---|---|---|
| A | legacy human labels: `KMFA S19 DingTalk attendance`、`S19` | package README、SKILL、runbook、configuration、module/CLI descriptions、metadata README | 被人类文档、CLI 帮助和 prompt 文本依赖；不是 canonical skill ID | `KMFA 钉钉考勤 skill` 或 `考勤 skill` | 当前 package 文档、metadata README、tool docstring/CLI description、prompt mirrors | 当前身份不保留；历史记录按 D 类处理 | 所有当前入口和新输出均只显示 canonical_name | 中 | 是 |
| A | live prompt 中的旧人类名称 | local automation `kmfa`、`kmfa-3`；package 与 metadata prompt mirrors | 被两个 automation prompt 直接依赖 | canonical_name；skill 调用继续使用 canonical_skill_id | 两个 live prompt、package morning/evening mirrors、metadata morning/evening/manual mirrors、prompt contract tests | 不保留旧当前名称；变更必须原子同步 | live readback、repo mirrors 和 prompt hash contract 全部一致 | 高 | 是 |
| B | `kmfa-dingtalk-attendance-skill` | SKILL frontmatter、prompt invocation、agent metadata | skill resolver、automation prompt 和 package validator 依赖 | 不变 | 无命名迁移；仅验证引用未漂移 | 不需要 | 不适用 | 低 | 否 |
| B | `STAGE_ID = "S19"` | `tools/dingtalk_attendance/__init__.py`、healthcheck、runner imports | 被代码、测试和输出字段依赖 | `SKILL_ID = "kmfa-dingtalk-attendance-skill"` | imports、healthcheck、runner、tests、metadata schemas/manifests | 仅旧 manifest reader 接受旧值；新写入不再生成 | 所有写端使用 SKILL_ID，所有 reader 完成双读，旧归档仍可重放 | 高 | 是 |
| C | output field `stage_id`，值为 `S19` 或 `KMFA-S19` | run plan、healthcheck、manifest writer、metadata JSON/YAML、tests | 被运行输出、manifest、tests、归档 reader 依赖 | `skill_id: kmfa-dingtalk-attendance-skill` | writer、reader、schema、metadata manifests、tests、report/dispatch consumers | reader 临时接受旧 `stage_id`；不得回写或改名旧归档 | retained legacy archive 全部可由 `skill_id`/legacy fallback 读取，且新 manifest 连续一个自然月不再写旧字段 | 高 | 是 |
| C | run-id prefix `s19_` | runner、tests、archive parser、automation memory | 被 run_id 生成、日期解析、排序、manifest/report 文件关系依赖 | `dingtalk_attendance_` | runner、parsers、sort key、tests、fixtures、prompt examples、ledger sync | 新写端只写新前缀；reader 双读旧前缀 | 所有 retained legacy run_id 均可通过已验证 fallback 读取；若仍保留旧归档则兼容层不得删除 | 高 | 是 |
| C | archive globs `s19_*.manifest.json`、`s19_*.raw.jsonl(.gz)`、`s19_*_*.manifest.json` | runner monthly rollup、send-latest、ledger sync、package replay scripts | 被归档发现、月累计、重放、ledger 和 resend 查找依赖 | 对应 `dingtalk_attendance_*` globs | 所有 archive readers、replay scripts、tests、fixtures | 必须双 glob 只读旧文件；禁止移动或重命名旧归档 | retained legacy archive 数量为零，或独立索引证明无需文件名 glob 且全量 replay/ledger 验证通过 | 极高 | 是 |
| C | seed prefix `s19_seed_` | archive inspection、raw replay、package docs/tests | 被 seed 隔离和无 manifest 例外逻辑依赖 | `dingtalk_attendance_seed_` | inspector、replay builder、fixtures、tests、migration docs | 双读旧 seed prefix | retained legacy seed 已过保留期或全量 replay 证明无旧 seed 依赖 | 高 | 是 |
| B | `KMFA_S19_ALLOW_DWS_COMMANDS` | auth guard、SKILL、runbook、configuration、env template、prompts、tests、local automation prompt | live DWS 授权门禁；被代码、环境配置、测试和 prompt 依赖 | `KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS` | guard、templates、docs、tests、package validator、两个 live prompt | 新 key 优先、旧 key 只读 fallback，禁止双 key 冲突时 fail open | 本机配置和两个 live prompt 均使用新 key，两个自然运行窗口验证无旧 key 读取 | 极高 | 是 |
| B | `KMFA_S19_DWS_BROWSER_POLICY_PATH` | auth guard、configuration、env template、tests | DWS browser policy 文件定位；被代码、环境配置和测试依赖 | `KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH` | guard、templates、docs、tests、live prompt 如有引用 | 新 key 优先、旧 key 只读 fallback | config-only healthcheck 与两个自然运行窗口均证明只使用新 key | 高 | 是 |
| B | `KMFA_S19_DWS_TIMEOUT_SECONDS` | DWS runner、tests、模型参数文件 | DWS command timeout；被代码、测试和公开参数登记依赖 | `KMFA_DINGTALK_ATTENDANCE_DWS_TIMEOUT_SECONDS` | DWS runner、tests、模型参数文件、env 文档 | 新 key 优先、旧 key 只读 fallback | focused timeout tests 与自然运行证明无旧 key 读取 | 中 | 是 |
| B | `check_s19_dingtalk_attendance.py`、`validate_s19_files` 及同名 module/test symbols | checker 文件、runbook、startup prompt、root docs、focused tests | 被 CLI、import、required-file contract、测试和文档依赖 | `check_dingtalk_attendance.py`、`validate_dingtalk_attendance_files` | checker、imports、required tool list、tests、runbook、startup prompt、root current references | 可保留一个只转发到新入口的 deprecated wrapper；不得保留双实现 | 连续两次完整 inventory 无调用旧入口，CI/automation/docs 全部使用新入口 | 高 | 是 |
| B/C | tests、fixtures、assertions 中的旧 machine values 和 run-id examples | `tests/test_dingtalk_attendance.py`、package replay tests/fixtures | 验证 stage/skill identity、run-id、archive glob、checker import 和 legacy replay | 新 machine values；另建明确标注 `legacy_read_only` 的兼容 fixtures | production code、schemas、fixtures、expected values、test names | 仅 legacy-reader tests 保留旧输入，不得作为新 writer expected value | 新 writer tests 全部只期望新值，legacy tests 只验证只读兼容 | 高 | 是 |
| A/C | metadata manifests 与 prompt mirrors 中的旧名称、`stage_id` 和旧 machine references | `metadata/dingtalk_attendance/**` | 被公开配置、prompt contract、storage/report policy 和 tests 依赖 | canonical_name、canonical_skill_id、new machine values | metadata JSON/YAML、package mirrors、tests、source checksums | reader 对旧 manifest 只读；当前 metadata 不保留旧身份 | metadata validators、prompt hash readback、focused tests 全部通过 | 高 | 是 |
| D | package 历史公开文档中的旧编号 | package `docs/**`、migration checklist、decision-impact | 历史设计、交付和迁移记录依赖；不应伪造历史 | 保留历史原文并增加明确 `historical_identifier` 说明；当前标题与 next action 使用 canonical_name | 涉及当前身份的摘要、索引、next action；source checksums | 是，历史内容只读 | 仅当文档被正式废止且有等价不可变历史证据时才可移除 | 中 | 部分 |
| D | KMFA 根级 HANDOFF、功能清单、开发记录、模型参数文件中的 274 个匹配 | KMFA 根级四个公开文件的考勤相关段落 | 历史审计、功能登记、开发记录、参数键和当前摘要依赖 | 当前摘要改用 canonical_name；历史事件与旧参数键标记为 historical/legacy | 四个根级文件的当前索引、交叉引用和 machine-key 清单 | 是，历史事件和旧参数键只读 | 不删除历史；仅在新的 canonical 索引可追溯并通过治理复核后停止主动展示旧键 | 高 | 部分 |
| E | local automation memory 中 3 个旧编号匹配 | `kmfa`、`kmfa-3` memory | 私有历史运行记录依赖 | 不重写历史；后续新 memory 条目只使用 canonical_name/new run-id | memory writer 行为及后续新条目 | 永久只读保留既有历史 | 不删除历史兼容；仅停止新增旧值 | 中 | 否 |
| E/C | 私有历史归档可能使用旧 run-id/file prefix | private monthly archive；本步骤未扫描或列名 | archive replay、ledger、月累计和审计可能依赖 | 不重命名文件；由 reader 双读旧/新协议 | archive readers、ledger sync、replay、send-latest、tests | 必须保留只读兼容 | 所有 retained legacy archive 已按 retention 正常退出，或独立索引与全量 replay 证明旧 glob 不再需要 | 极高 | 仅改 reader，不改归档 |
| B | `source_manifest.txt` 与 `source_checksums.sha256` | package root | package 完整性和内容校验依赖；当前文件本身没有旧编号匹配 | 文件名不变 | 每个 R2.2 package 文件改名/改内容后同步 manifest 与 checksum | 不需要旧编号兼容 | package validator 通过 | 中 | 是 |

compatibility_requirements:
  - 所有新 writer 只生成 canonical_skill_id、`skill_id` 和新的 attendance 语义前缀。
  - 所有 archive、manifest、ledger 和 replay reader 在迁移期必须双读新旧字段、run-id prefix 和 glob，并保持 fail closed。
  - 旧环境变量只允许作为只读 fallback；新旧 key 同时存在且值冲突时必须阻断，不得静默选边。
  - 不重写既有 automation memory、历史公开事件或私有历史归档。
  - checker 兼容层只能是薄 wrapper，不得形成两套业务实现。
  - source_manifest 与 source_checksums 必须随每次 package 路径或内容变更同步。

prohibited_changes:
  - 不修改考勤业务规则、晨报、晚报、时间或 timezone。
  - 不修改通知模板或发送目标。
  - 不运行 live DWS，不发送钉钉消息。
  - 不修改本机 automation。
  - 不移动、重命名、读取或枚举私有历史归档。
  - 不修改业务代码或测试逻辑。
  - 不读取或修改其他 KMFA skill。
  - 不创建 branch、worktree、PR 或 Draft PR。
  - 不触碰 5 个预存无关 untracked 文件。

validation_performed:
  - skill package validator: PASS
  - public repository sensitive-data validator: PASS
  - git diff --check: PASS
  - changed-path audit: PASS
  - task branch count: 0
  - open PR count: 0
  - pre-existing untracked count: 5, unchanged

blockers:
  - R2.2 尚未获得 external review 后的实施授权。
  - 私有归档的实际旧文件数量按边界保持 UNKNOWN；本表只锁定兼容协议，不据此声称完成归档迁移。
  - machine identifier、environment key、writer、reader、tests、prompts 和 metadata 必须作为一个受控变更集迁移，不能分散产生混合写入。

next_action: R2.2 implementation after external review
