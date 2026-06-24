# 审查轨 A｜安全、代码质量、潜在 Bug、并发与可维护性

## 结论

本轨发现 **22** 项：P0=5、P1=16、P2=1、P3=0。P0 全部阻塞生产/最终集成；P1 阻塞受影响范围。

## 审查范围

审查 V7.0 包的机器合同与当前代码快照：lesson、Stage1 B1 report、runtime、state machine、storage、scheduler、scheduled execution、SMTP。

## 独立方法

先做静态边界/状态/副作用审查，再使用隔离 stub 执行可复现定向探针；本轨在完成前不采用 UI 轨的优先级判断。

## 问题总表

| ID | 问题 | 严重度 | 合并阻塞 | 证据 | 修复 Task |
|---|---|---:|---|---|---|
| `A-001` | 恢复清单允许路径穿越读取备份根目录外文件 | **P0** | `global` | dynamic_reproduced：Probe P04；stage1_runtime.py:302-337 | `S2PMT02` |
| `A-002` | 恢复先覆盖现有数据库、后验证，失败会破坏在线目标 | **P0** | `global` | dynamic_reproduced：Probe P05；stage1_runtime.py:348-367 | `S2PMT02` |
| `A-003` | SMTP 发送与持久状态之间没有事务发件箱 | **P0** | `global` | static_confirmed：smtp_delivery.py:64-99；发送完成后才返回内存报告 | `S2PMT03` |
| `A-004` | 邮件前台结论/机制/映射/行动绕过 Claim Ledger | **P0** | `scope` | dynamic_reproduced：Probe P14；lesson.py:126-156；validate_lesson_against_ledger 仅验证 sections | `S2PMT01` |
| `A-005` | 缺少不可信论文/网页内容的 Prompt Injection 与工具边界 | **P0** | `scope` | design_gap：V7.0 合同未定义 untrusted-content trust boundary | `S2PMT01` |
| `A-006` | tick 写入异常时 runtime.lock 永久残留 | **P1** | `scope` | dynamic_reproduced：Probe P01；stage1_runtime.py:103-151 | `S2PMT03` |
| `A-007` | 状态历史不验证声明的 from_state | **P1** | `scope` | dynamic_reproduced：Probe P09；state_machine.py:146-162 | `S2PMT03` |
| `A-008` | current_state 与 state_history 末态可不一致 | **P1** | `scope` | dynamic_reproduced：Probe P10；state_machine.py:77-103 | `S2PMT03` |
| `A-009` | 状态转换缺少乐观并发控制与 fencing token | **P1** | `scope` | static_confirmed：state_machine.py:106-122 只对内存副本转换 | `S2PMT03` |
| `A-010` | 报告文件在质量验证前写入正式目录 | **P1** | `scope` | dynamic_reproduced：Probe P16；stage1_b1_report.py:161-167 | `S2PMT02` |
| `A-011` | artifact_files.sha256 字段不是文件字节 SHA-256 | **P1** | `scope` | dynamic_reproduced：Probe P15；stage1_b1_report.py:517-526 | `S2PMT02` |
| `A-012` | 邮件原文链接未限制 URL scheme | **P1** | `scope` | dynamic_reproduced：Probe P17；stage1_b1_report.py:468 | `S2PMT01` |
| `A-013` | 调度模板路径未结构化转义，macOS plist 甚至不可解析 | **P1** | `scope` | dynamic_reproduced：Probe P07/P07B；stage1_runtime.py:493-525 | `S2PMT04` |
| `A-014` | 备份辅助文件同名时静默覆盖 | **P1** | `scope` | dynamic_reproduced：Probe P06；stage1_runtime.py:266-272 | `S2PMT02` |
| `A-015` | 未来时间戳被钳制为 age=0，时钟漂移可长期伪装新鲜 | **P1** | `scope` | dynamic_reproduced：Probe P03；stage1_runtime.py:563-576 | `S2PMT05` |
| `A-016` | lesson_id 只依赖 claim_id，不依赖内容/证据/模型版本 | **P1** | `scope` | dynamic_reproduced：Probe P13；lesson.py:40-43 | `S2PMT03` |
| `A-017` | SMTP delivery_id 不含正文/内容版本，且缺标准 Message-ID | **P1** | `scope` | dynamic_reproduced：Probe P11/P12；smtp_delivery.py:105-116,176-182 | `S2PMT03` |
| `A-018` | V7 要求展示 ROI，但旧邮件验证明确禁止 ROI | **P1** | `scope` | static_confirmed：stage1_b1_report.py:24-34 | `S2PAT05` |
| `A-019` | 零关键 Claim 时覆盖率被计算为 100% | **P1** | `scope` | static_confirmed：stage1_b1_report.py:289-305 | `S2PMT01` |
| `A-020` | 依赖、CI Action、SBOM 与权限最小化未形成供应链基线 | **P1** | `scope` | design_gap：V7.0 任务包无 supply-chain contract | `S2PMT01` |
| `A-021` | Roadmap 依赖为空、Stop Code 混用自由文本，机器门不可可靠执行 | **P1** | `global` | static_confirmed：roadmap_v7.yaml 多个 dependencies: []，stop_conditions 含未注册中文短语 | `S2PAT05` |
| `A-022` | SQLite 并发基础探针通过，但缺 busy_timeout、重试与高负载政策 | **P2** | `no` | dynamic_reproduced：Probe P18 120 项/24 并发通过；storage.py:86-95 未配置 busy_timeout | `S2PMT05` |

## 逐项整改要求

### A-001｜恢复清单允许路径穿越读取备份根目录外文件

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** dynamic_reproduced；Probe P04；stage1_runtime.py:302-337
- **影响：** 恶意或损坏的 manifest 可让 restore 读取 ../ 指向的任意本地文件并复制到目标数据库。
- **建议修复：** 对 manifest path 做 PurePosixPath 规范化；拒绝绝对路径、..、空路径、符号链接逃逸；resolve 后必须 is_relative_to(backup_root)。
- **必须测试：** 路径 ../、绝对路径、符号链接、TOCTOU 交换均必须拒绝；合法 database 相对路径恢复通过
- **归属 Task：** `S2PMT02`

### A-002｜恢复先覆盖现有数据库、后验证，失败会破坏在线目标

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** dynamic_reproduced；Probe P05；stage1_runtime.py:348-367
- **影响：** 恢复结果 blocked 时原库已被无效数据覆盖，存在直接数据丢失。
- **建议修复：** 同目录临时文件复制→SHA/SQLite quick_check/Schema 校验→fsync→原库预备份→os.replace 原子切换；任何失败删除临时文件且保留原库。
- **必须测试：** 无效备份不得改变原库字节；断电/异常注入后只能存在旧库或完整新库，不得半文件
- **归属 Task：** `S2PMT02`

### A-003｜SMTP 发送与持久状态之间没有事务发件箱

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** global
- **证据状态：** static_confirmed；smtp_delivery.py:64-99；发送完成后才返回内存报告
- **影响：** 进程在 SMTP 接受邮件后、数据库提交前崩溃，重试会重复发送；无法做到可恢复的外部副作用。
- **建议修复：** 实现 transactional outbox：业务事务写 outbox(PENDING)+唯一 mail_key；独立 sender claim/lease；发送后记录 provider result；重启 reconciliation；明确 at-least-once + 幂等 Message-ID。
- **必须测试：** SMTP 接受后立即 kill -9，再启动不得产生不可控重复；双 sender 抢占同一 outbox 只允许一个有效发送
- **归属 Task：** `S2PMT03`

### A-004｜邮件前台结论/机制/映射/行动绕过 Claim Ledger

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P14；lesson.py:126-156；validate_lesson_against_ledger 仅验证 sections
- **影响：** 用户最先看到的关键判断可能是关键词模板推断，却被邮件描述为“关键事实已全部绑定证据”。
- **建议修复：** Frontstage 每个字段使用 typed statement：fact/inference/hypothesis/action；fact 必须 claim_ids+evidence_ids；inference 必须 premise_claim_ids+reasoning_version+confidence；禁止无标签推断。
- **必须测试：** 删除任一 frontstage 绑定后质量门失败；摘要级推断必须显示“推断/待验证”而非事实
- **归属 Task：** `S2PMT01`

### A-005｜缺少不可信论文/网页内容的 Prompt Injection 与工具边界

- **严重程度：** P0（灾难/安全/证据完整性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；V7.0 合同未定义 untrusted-content trust boundary
- **影响：** Stage2 引入全文、网页和报告后，源内容可能诱导模型泄漏提示、调用工具、改写规则或产生错误操作。
- **建议修复：** 将来源内容标记 UNTRUSTED_DATA；系统指令与数据分离；模型无仓库写权限/无密钥；工具 allowlist；输出 Schema；引用定位；注入检测只作信号，不能替代隔离。
- **必须测试：** 恶意论文含“忽略规则/发送密钥/运行命令”时仍只作为引文数据；模型输出越权工具调用被执行层拒绝
- **归属 Task：** `S2PMT01`

### A-006｜tick 写入异常时 runtime.lock 永久残留

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P01；stage1_runtime.py:103-151
- **影响：** 一次磁盘/权限错误即可阻塞后续自动运行，watchdog 只报告不恢复。
- **建议修复：** 锁封装为 context manager + finally；锁中加入 owner_id/host/pid/lease_until/fencing_token；续租与安全接管。
- **必须测试：** heartbeat/checkpoint 任一步异常后无残锁；模拟死进程后仅新 fencing token 可接管
- **归属 Task：** `S2PMT03`

### A-007｜状态历史不验证声明的 from_state

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P09；state_machine.py:146-162
- **影响：** 被篡改的历史记录仍可通过，审计链不可信。
- **建议修复：** 每条 history.from_state 必须等于上一条 to_state；首条严格固定；所有字段完整。
- **必须测试：** 篡改 from_state 必须失败；缺 reason/at 或时间倒序必须失败
- **归属 Task：** `S2PMT03`

### A-008｜current_state 与 state_history 末态可不一致

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P10；state_machine.py:77-103
- **影响：** 控制台、恢复逻辑和审计可能读取不同状态。
- **建议修复：** 验证 last(history).to_state == current_state；status 与状态映射一致；记录 schema_version/row_version。
- **必须测试：** 末态不一致和 status 不一致均失败
- **归属 Task：** `S2PMT03`

### A-009｜状态转换缺少乐观并发控制与 fencing token

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** static_confirmed；state_machine.py:106-122 只对内存副本转换
- **影响：** 两个 worker 可同时从同一旧状态成功，后写覆盖先写，造成重复处理或丢状态。
- **建议修复：** 数据库 UPDATE ... WHERE id=? AND row_version=?；受影响行必须为 1；作业 claim 使用 lease + fencing token；事件 append-only。
- **必须测试：** 100 个并发 claimant 仅一个获得同一任务；过期 worker 的写入被 fencing token 拒绝
- **归属 Task：** `S2PMT03`

### A-010｜报告文件在质量验证前写入正式目录

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P16；stage1_b1_report.py:161-167
- **影响：** 最终返回 blocked，正式目录仍残留 5 个看似有效产物，后续发送/索引可能误用。
- **建议修复：** 先纯内存构建与验证；通过后写 staging 目录；逐文件 fsync；manifest 完整后原子发布目录/指针；失败清理。
- **必须测试：** 强制验证失败时正式目录 0 新文件；中途异常后无半发布 package
- **归属 Task：** `S2PMT02`

### A-011｜artifact_files.sha256 字段不是文件字节 SHA-256

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P15；stage1_b1_report.py:517-526
- **影响：** 审计者按标准 SHA256 校验会失败，完整性字段语义错误。
- **建议修复：** 使用 hashlib.sha256(path.read_bytes()) 或流式哈希；如保留 canonical content hash，改名 content_hash 并同时保存 file_sha256。
- **必须测试：** 每个 artifact manifest SHA 与 sha256sum 完全相同
- **归属 Task：** `S2PMT02`

### A-012｜邮件原文链接未限制 URL scheme

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P17；stage1_b1_report.py:468
- **影响：** 被污染的 canonical_url 可生成 javascript: 等危险链接。
- **建议修复：** urlsplit；仅允许 https（必要时 http）；拒绝 userinfo、控制字符、非 allowlist host；纯文本也标识来源域。
- **必须测试：** javascript/data/file/带凭据 URL 均拒绝或降级为无链接文本
- **归属 Task：** `S2PMT01`

### A-013｜调度模板路径未结构化转义，macOS plist 甚至不可解析

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P07/P07B；stage1_runtime.py:493-525
- **影响：** 带空格/分号路径会破坏命令，可能命令注入；launchd XML 中 && 未转义导致安装失败。
- **建议修复：** 不拼 shell 字符串；launchd ProgramArguments 每参数一个 string 且 XML 库生成；systemd 使用结构化 unit/EnvironmentFile；PowerShell 参数数组；路径验证。
- **必须测试：** 空格、中文、分号、& 路径均安全；plistlib/systemd-analyze/PowerShell parser 通过
- **归属 Task：** `S2PMT04`

### A-014｜备份辅助文件同名时静默覆盖

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P06；stage1_runtime.py:266-272
- **影响：** 两份不同配置/状态文件在备份中共享 files/same.txt，manifest 重复路径，恢复证据失真。
- **建议修复：** 保存相对来源路径或 source_path_hash/filename；拒绝重复目标；manifest 路径唯一约束。
- **必须测试：** 不同目录同名文件均可完整恢复，manifest path 无重复
- **归属 Task：** `S2PMT02`

### A-015｜未来时间戳被钳制为 age=0，时钟漂移可长期伪装新鲜

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P03；stage1_runtime.py:563-576
- **影响：** 未来 heartbeat/lock 不会被识别为异常，可能阻塞恢复或错误显示健康。
- **建议修复：** 允许小容差；超过 clock_skew_tolerance 直接 CLOCK-TIMEZONE-FAIL；内部租约使用单调时钟，持久审计使用 UTC。
- **必须测试：** 未来 5 分钟以上 heartbeat 阻塞；DST 不影响 lease 计算
- **归属 Task：** `S2PMT05`

### A-016｜lesson_id 只依赖 claim_id，不依赖内容/证据/模型版本

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P13；lesson.py:40-43
- **影响：** Claim 文本或证据变更仍得到同一 lesson_id，缓存和审计可能返回旧内容。
- **建议修复：** 区分 stable lesson_key 与 immutable lesson_revision_id；revision hash 包含 claim statement/evidence hash/analysis model/prompt contract/language。
- **必须测试：** 任一证据或内容变更导致 revision 变化，stable key 不变
- **归属 Task：** `S2PMT03`

### A-017｜SMTP delivery_id 不含正文/内容版本，且缺标准 Message-ID

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** dynamic_reproduced；Probe P11/P12；smtp_delivery.py:105-116,176-182
- **影响：** 不同正文可共享同一 delivery_id；邮件客户端去重与系统修订追踪不明确。
- **建议修复：** 定义 mail_key(cycle_id, product_id, recipient) 与 immutable content_revision_id；Message-ID 由 mail_key+revision+受控域生成；重发策略明确。
- **必须测试：** 同 revision 重试 Message-ID 不变；内容修订 revision 变化且需显式 supersede/resend
- **归属 Task：** `S2PMT03`

### A-018｜V7 要求展示 ROI，但旧邮件验证明确禁止 ROI

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** static_confirmed；stage1_b1_report.py:24-34
- **影响：** 新产品合同与当前代码互相冲突，Stage1 回灌会被旧质量门阻断。
- **建议修复：** 迁移为 Expected ROI / Actual ROI typed schema；禁止的是无假设保证收益，不是 ROI 字段本身；加入版本兼容测试。
- **必须测试：** V7.1 合法 ROI 可发布；无成本/概率/证据的收益声明被拒绝
- **归属 Task：** `S2PAT05`

### A-019｜零关键 Claim 时覆盖率被计算为 100%

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** static_confirmed；stage1_b1_report.py:289-305
- **影响：** 没有任何关键 Claim 也会“100% 证据覆盖”，形成空集真值误导。
- **建议修复：** 关键 Claim 数必须达到板块最低要求；0 项返回 not_applicable/blocked，不得显示 100%。
- **必须测试：** 0 critical claim 不能通过关键证据门
- **归属 Task：** `S2PMT01`

### A-020｜依赖、CI Action、SBOM 与权限最小化未形成供应链基线

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** scope
- **证据状态：** design_gap；V7.0 任务包无 supply-chain contract
- **影响：** 依赖漂移、恶意包、未固定 Action 或过宽 token 权限可能破坏生产链。
- **建议修复：** 锁定依赖 hash；生成 SBOM；pip-audit/OSV；GitHub Actions 固定 commit SHA；最小 permissions；制品 provenance；secret scanning。
- **必须测试：** CI 自动审计依赖和 Action 引用；高危漏洞按例外审批流程阻断
- **归属 Task：** `S2PMT01`

### A-021｜Roadmap 依赖为空、Stop Code 混用自由文本，机器门不可可靠执行

- **严重程度：** P1（高风险功能/可靠性级）
- **是否阻塞合并：** global
- **证据状态：** static_confirmed；roadmap_v7.yaml 多个 dependencies: []，stop_conditions 含未注册中文短语
- **影响：** 不同 agent 可跳过前置任务；CI 无法判定 Stop Gate；交接连续性不稳定。
- **建议修复：** V7.1 将 task_ids 数组化、依赖显式化、自由文本移入 stop_notes，stop_conditions 只允许注册代码。
- **必须测试：** 任务图无缺失引用/环；所有 stop condition 均在 registry
- **归属 Task：** `S2PAT05`

### A-022｜SQLite 并发基础探针通过，但缺 busy_timeout、重试与高负载政策

- **严重程度：** P2（中风险质量/维护性级）
- **是否阻塞合并：** no
- **证据状态：** dynamic_reproduced；Probe P18 120 项/24 并发通过；storage.py:86-95 未配置 busy_timeout
- **影响：** 简单探针通过不代表长事务、备份、FTS 和多进程下稳定，仍可能 database is locked。
- **建议修复：** 显式 busy_timeout；短事务；写入队列或单 writer；锁等待指标；指数退避；WAL checkpoint 政策。
- **必须测试：** 多进程写+备份+FTS soak；锁等待 P95/P99 指标满足预算
- **归属 Task：** `S2PMT05`
