# KMFA 钉钉考勤 skill 交接

roadmap_progress: R6 / R6.1

status: READY_FOR_OWNER_PREVIEW_DECISION

r2_close_commit: b5b06437dfb15bfb0e302c4e735fe2978ddcd579

verification_base_commit: b5b06437dfb15bfb0e302c4e735fe2978ddcd579

canonical_name: KMFA 钉钉考勤 skill

canonical_skill_id: kmfa-dingtalk-attendance-skill

production_acceptance: NOT_EVALUATED

owner_usability_status: NOT_ACCEPTED

current_availability: NO_SEND_RUNTIME_VERIFIED

## R6.1 实际通知预览

- 已使用通过真实无发送验收的 2026-07-10 evening 与凭证绑定 final 私有结果生成一份本机私有《实际通知预览》。
- 预览按现有模板原样展示晚间暂时提醒、官方最终核对和月累计文字；未修改代码、规则、模板、时间、时区或 automation。
- 预览正文、员工明细和本机私有路径均未提交 GitHub。
- 发送状态保持 `NOT_SENT_OWNER_DISABLED`；消息数 0、目标调用数 0。
- 当前等待 owner 仅回复“能用”或指出具体不能使用的句子。

## R4.1–R4.3 独立官方原件对账

- 已冻结 2026-07-09 与 2026-07-10 两份独立官方工作簿；本轮只对这两个日期执行授权的只读钉钉/DWS 查询，未修改钉钉数据、配置、规则或人员范围。
- 企业实际报表为 49 列，不再使用预设九列替代完整官方报表。
- Owner 已裁决“部门”为可选展示字段：不参与人员匹配、异常判断、月累计、通知或官方验收；无可靠主部门时记录 `UNVERIFIED`，不得猜值。
- 正式必需字段为其余 48 列。两天官方/DWS/UserId 匹配均为 44/44/44，每天比较 2,112 格，两天合计 4,224 格。
- 最终复核达到：缺人 0、多出 0、必需列缺失 0、必需单元格缺失 0、真实值差异 0。
- 两个工作日均生成包含官方文件指纹、工作日期和聚合门槛的统一正式凭证；`final_reconciliation.py` 无转换直接读回 `PASS`。
- R4 官方考勤数据还原通过；整个 skill 仍为 `UNAVAILABLE` / `NOT_ACCEPTED`，必须等待下一阶段真实无发送运行。
- 公开脱敏一页结果：`docs/R4_OFFICIAL_RECONCILIATION_RESULT.md`。官方原件、指纹明细、员工数据和逐格差异仅保存在本机私有证据目录。
- 本轮执行了明确授权范围内的只读钉钉/DWS 查询；未发送钉钉消息，未修改 automation、schedule、time、timezone、cwd、目标或通知文案，未触碰其他 skill。

## Post-R4 真实无发送验收

- 2026-07-10 evening live DWS 按实际考勤组完成 42/42 official coverage，parity PASS，command failure 0。
- 冻结 2026-07-10 正式凭证完成 final：官方/DWS/UserId 44/44/44，48 列、2,112 格，缺人/多人/必需缺失/真实差异均为 0。
- 初次 final 暴露 manifest 未绑定凭证、monthly reader 误收旧 final 且从 run_id 推断错误 work_date；唯一修正后，月累计只接受最新有效凭证绑定 final，并使用 manifest work_date。
- 最终月累计来源为本次凭证绑定 final 的 42 条 2026-07-10 正式记录；旧 final、legacy、morning、evening 均排除。
- evening/final receipt 均为 `NOT_SENT_OWNER_DISABLED`，消息 0、目标调用 0。
- 未修改 automation、schedule、time、timezone、cwd、发送目标或通知文案；未触碰其他 skill。

next_action: owner decides whether and when to evaluate any delivery-enabled stage

## R3.3 撤回与证据判定

- `R3.2 真实工作日验收已完成` 声明正式撤回。
- R3.2 的 fresh DWS official-report query 与内部 parity 只能证明 DWS 读取链自洽，不能替代独立钉钉官方导出原件。
- R3.3 当时仅找到 2 份对应 2026-07-10 的 DWS raw；其内部一致不构成独立官方证据。
- R4 已取得可独立冻结的 2026-07-10 钉钉官方 XLSX 导出原件，并以企业实际 49 列执行逐员工逐字段对账。
- 完整对账列应包含员工唯一键、工作日、考勤结果、应出勤天数、出勤天数、休息天数、迟到次数、早退次数、上班缺卡次数、下班缺卡次数和旷工天数；当前只能确认 DWS 侧字段，不能伪造官方导出列映射。
- 官方原件、预期结果和对账标准均未创建、修改或替换。
- 因 `EVIDENCE_MISSING`，本轮未进入唯一一次代码修正，也未消耗唯一一次复核。
- 未运行新 live DWS、未发送、未修改 schedule/time/timezone、未修改 automation、未触碰其他 skill。

r3_3_initial_reconciliation:

- independent_official_export: MISSING
- dws_raw_count: 2
- dws_employee_set_match: PASS
- dws_employee_count: 42
- dws_official_field_count: 9
- dws_cell_comparison_count: 378
- dws_internal_difference_count: 0
- official_export_vs_dws: NOT_RUN_EVIDENCE_MISSING
- code_correction: NOT_RUN
- review: NOT_RUN
- production_acceptance: NOT_EVALUATED
- owner_usability_status: NOT_ACCEPTED

r3_3_validation:

- package_validator: PASS
- sensitive_data_validator: PASS
- git_whitespace_validation: PASS
- changed_path_audit: PASS
- live_dws_run: NO
- dingtalk_send: NO
- automation_change: NO

## R3.2 实施结果

- 晨间和晚间结果已固定为 `TEMPORARY_REMINDER`，不再表示当日最终结论。
- 新增 completed prior work date 的 `OFFICIAL_FINAL_RECONCILIATION`；exact official parity 通过后生成 aggregate-only 一页结果。
- 新月累计只读取 canonical `final` archive。legacy、morning、evening archive 均为 audit-only，不进入新累计。
- production 和 resend entry 的发送保持关闭，固定返回 `NOT_SENT_OWNER_DISABLED`，不解析目标、不调用 sender。
- 两个 automation 只更新 prompt；scheduler、time、timezone、automation ID、cwd 和发送目标均未修改。
- 已对一个真实工作日执行 fresh live DingTalk official report 核对：parity PASS，morning/evening evidence 均存在，但历史提醒为 legacy 且 parity UNKNOWN，因此页面诚实标为 `UNVERIFIED_REMINDER`。
- 真实完成依据不是 synthetic fixture；fixture 仅用于回归测试。
- production acceptance 仍为 `NOT_EVALUATED`，owner usability 仍为 `NOT_ACCEPTED`，整体保持 `UNAVAILABLE`。

real_work_date_evidence:

- work_date: 2026-07-10
- source: DWS_INTERNAL_CHECK_ONLY
- official_final_parity: WITHDRAWN
- reminder_binding: LEGACY_UNVERIFIED
- notification_status: NOT_SENT_OWNER_DISABLED
- one_page_result: PRIVATE_ARCHIVE_ONLY

validation_performed:

- focused_attendance_tests: 101/101 PASS
- attendance_checker: PASS
- skill_package_validator: PASS
- sensitive_data_validator: PASS
- git_whitespace_validation: PASS
- prompt_mirror_and_live_readback: PASS
- real_monthly_source_check: FINAL_ONLY / LEGACY_FALSE / TEMPORARY_FALSE

## R3.1 结论

- 当前代码已经实现 official-report-only、完整覆盖 parity 和 fail-closed delivery gate，但现有私有历史归档不能证明这些新门禁在自然生产运行中成功执行。
- 六日窗口可关联到 20 个证据项：13 个 archive artifact 和 7 个 automation task。证据项之间可能重叠，当前不能把它们声明为 20 个唯一运行。
- 13 个 archive artifact 的 raw hash 均可复核且报告文件存在；但全部使用 legacy identity，全部缺少 official parity 字段，raw 中也没有 official-report evidence row。
- 11 个旧 receipt 记录为 `SENT`，但 `SENT` 只证明旧 sender receipt 状态；它不证明取数正确、官方一致、客户端可见或 owner 接受。
- 当前自然月累计代码明确双读 current 与 legacy archive。若同一 user-day 有 official row，代码优先 official；若没有 official row，legacy row 仍可进入累计。因此“会读取 legacy archive”为 FACT，“是否已污染最终累计数值”为 UNKNOWN。
- R3.1 不定义晨报、晚报、累计或发送的新产品规则。需要 owner 决定的事项列在下方。

## 当前代码实际执行链

1. Codex automation prompt 要求进入 canonical repo，依次运行 preflight、runtime inspection、offline validation、month gate 和 config-only healthcheck。
2. `run_attendance.py` 解析 slot/work date，生成 `skill_id` 与 current run/file prefix 的 run plan。
3. `dws_auth_guard.py` 检查 DWS allow key 与 browser policy；缺授权或新旧 key 冲突时在 collector 前 fail closed。
4. `collect_official_org_attendance` 读取组织映射、当前考勤组范围、官方列定义，并按目标业务日查询 official report。
5. collector 要求考勤组成员、返回人员、日期、精确列和状态全部可解释；任何缺口进入 `OFFICIAL_ATTENDANCE_PARITY_FAILED`。
6. parity 通过后，production rows 只由 official report 生成；逐人 record/summary sweep 被标记为 diagnostic skipped。
7. `write_private_outputs` 才写 raw、两类私有报告、manifest 与 cleanup audit。新 manifest 只写 canonical `skill_id`。
8. 写通知前，`build_stats_with_rest_required_people` 调用 `_monthly_attendance_records`；后者通过集中 identity module 同时 glob current 和 legacy raw archive。
9. `dispatch_reports_to_targets` 再次执行 official delivery gate，按默认 `all` 目标路由发送；指定日期 personal-only 只在显式参数下启用。
10. notification 之后执行 cleanup 并写 audit；CLI exit code 另行把 auth、unavailable、partial、notification failure 与 success 区分。
11. 私有 SQLite ledger 是单独的 replay/index 流程，不由 `run_attendance` 自动同步，也不构成当前生产结果真值。

## 两个 automation 的当前活动配置

| automation | 状态 | 实际本机时间 | scheduler timezone 字段 | cwd | current prompt | 当前事实 |
|---|---|---:|---|---|---|---|
| morning (`kmfa`) | ACTIVE | 10:45 | 无 | canonical repo | SHA `32bba4910dcb29b8baa2c21eaaa770572d37b9dcabc78c885072fd7243508b41`，与 repo mirror 一致 | active prompt 调用 runner 默认 `target_filter=all`；prompt/代码/metadata 写 10:35，与实际 scheduler 10:45 冲突；最新自然 task 因未获 DWS 授权 fail closed，未运行 entry、未发送 |
| evening (`kmfa-3`) | ACTIVE | 20:00 | 无 | canonical repo | SHA `02fff9a42201a08b7d622ec433e19b688ed937d53f3085ce11d976dbc2f7300f`，与 repo mirror 一致 | active prompt 调用 runner 默认 `target_filter=all`；当前 TOML prompt 已使用 canonical identity；最近可读 task snapshot 是旧 prompt 的历史快照，且该 task 在 live collection 阶段失败并未发送 |

说明：实际 recipient resolution 属于私有 runtime，不在公开报告展开。两个 automation 的 memory 均只记录为 `EXPECTED_MUTABLE_RUNTIME_STATE`，没有覆盖 prompt、schedule、timezone、cwd、automation ID 或发送目标；本轮 non-prompt automation configuration unchanged。

## 当前契约冲突

| ID | 冲突 | 已验证事实 | 当前分类 |
|---|---|---|---|
| C01 | morning 文档/prompt/代码/metadata 为 10:35，live scheduler 为 10:45 | 两侧均已只读回读；prompt hash 相等不能消除时间冲突 | OWNER_DECISION_REQUIRED |
| C02 | current code 要求 official parity；六日 13 个 archive artifact 全部没有 parity 字段或 official evidence row | artifact 完整不等于 official consistency | FACT |
| C03 | 旧 receipt 可为 `SENT`，同时同一 artifact 的 command failure 大于 0 | 至少 3 个 evidence item 存在不一致的 collection/send 状态信号；缺少历史版本契约绑定，业务正确性仍未知 | FACT / UNKNOWN |
| C04 | public repair ledger 记录两个日期的 read-only official probe PASS；现有 archive 无法把这些 probe 绑定到对应生产发送 | probe 只能证明当时 collector/readback，不证明 historical notification 正确 | UNKNOWN |
| C05 | 97 项 focused tests PASS；测试 official parity 主要使用 deterministic synthetic fixture | test PASS 不提供 live official report、自然触发或客户端送达证据 | FACT |
| C06 | current live prompt 已 canonical；最近 evening task snapshot 仍显示旧 prompt | task snapshot 是 immutable history，不是 current automation config | FACT |
| C07 | metadata manifest 和 checker 锁定 morning 10:35，但 automation config 实际为 10:45 | checker 没有读取 live scheduler，因此其 PASS 不覆盖该冲突 | FACT |
| C08 | 19 个可见 private manifest 全部是 legacy identity；current writer 尚无可见 production archive proof | 身份迁移通过测试，但生产落盘未验收 | EVIDENCE_MISSING |

## 六日 20 个运行证据项矩阵

窗口：2026-07-06 至 2026-07-11。`Axx` 为 private archive artifact 的脱敏索引；`Txx` 为 automation task 的脱敏索引。它们是证据项，不保证一一对应到唯一运行。

| ID | 日期 | slot | 来源 | machine/artifact 事实 | 通知证据 | official consistency | owner accepted | 当前状态 |
|---|---|---|---|---|---|---|---|---|
| A01 | 07-07 | evening | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN：无 parity/evidence row | 否 | UNKNOWN |
| A02 | 07-08 | evening | archive | hash/report 完整，command failure=67 | receipt `FAILED` | UNKNOWN | 否 | FACT：collection errors present 且通知失败 |
| A03 | 07-10 | evening | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A04 | 07-06 | morning | archive | hash/report 完整，command failure=3 | receipt `SENT` | UNKNOWN | 否 | FACT：状态信号不一致；生产可用性 UNKNOWN |
| A05 | 07-07 | morning | archive | hash/report 完整，command failure=44 | receipt `SENT` | UNKNOWN | 否 | FACT：状态信号不一致；生产可用性 UNKNOWN |
| A06 | 07-07 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A07 | 07-07 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A08 | 07-07 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A09 | 07-07 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A10 | 07-08 | morning | archive | hash/report 完整，command failure=1 | receipt `SENT` | UNKNOWN | 否 | FACT：状态信号不一致；生产可用性 UNKNOWN |
| A11 | 07-10 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| A12 | 07-11 | morning | archive | hash/report 完整，command failure=0 | receipt 缺失 | UNKNOWN | 否 | UNKNOWN |
| A13 | 07-11 | morning | archive | hash/report 完整，command failure=0 | receipt `SENT` | UNKNOWN | 否 | UNKNOWN |
| T01 | 07-08 | morning | automation task | task final 缺少可判定状态 | 无可绑定证据 | UNKNOWN | 否 | EVIDENCE_MISSING |
| T02 | 07-09 | morning | automation task | task final 缺少可判定状态 | 无可绑定证据 | UNKNOWN | 否 | EVIDENCE_MISSING |
| T03 | 07-09 | morning | automation task | task final 缺少可判定状态 | 无可绑定证据 | UNKNOWN | 否 | EVIDENCE_MISSING |
| T04 | 07-10 | evening | automation task | task final 标记 `passed` | 无独立可绑定送达证据 | UNKNOWN | 否 | UNKNOWN |
| T05 | 07-10 | morning | automation task | final 出现 `DWS_AUTH_REQUIRED` | 无发送证明 | UNKNOWN | 否 | FACT：fail-closed |
| T06 | 07-11 | evening | automation task | final `failed`，live collection 被中断 | 明确未发送 | UNKNOWN | 否 | FACT：失败 |
| T07 | 07-11 | morning | automation task | task final 标记 `passed` | 无独立可绑定送达证据 | UNKNOWN | 否 | UNKNOWN |

### 矩阵边界

- 20 个证据项中有 archive/task 重叠的可能；缺 run-to-task stable key，不能声称 20 个唯一运行。
- archive manifest 没有 code commit、prompt hash 或 automation task id，无法逐项证明使用了哪一版代码/prompt。
- receipt `SENT` 是 sender 返回状态，不是客户端可见、已读、官方一致或 owner 接受证明。
- `passed` 是 task final 状态，不是 official parity、通知成功或 owner acceptance 的替代字段。

## 月累计与 legacy archive

verified_code_path: `_monthly_attendance_records -> archive_raw_paths -> CURRENT_RAW_GLOBS + LEGACY_RAW_GLOBS`

current_facts:

- FACT：当前每次成功 collection 在发送前都会读取目标月目录内 current 与 legacy gzip raw。
- FACT：六日窗口内 13 个 archive artifact 均为 legacy，且 raw 文件存在并通过 manifest hash。
- FACT：canonicalization 对同一 user-day 优先 latest official row；没有 official row 时 legacy row 仍参与异常、有效出勤、连续异常和休息累计。
- UNKNOWN：当前实际通知中的月累计具体有多少来自 legacy row。本轮不读取或输出员工级明细，也没有可绑定的全月 official baseline。
- RISK：在建立 cutover/rebuild policy 前，旧错误 work_date、旧人员范围和旧推断规则可能继续影响没有 official replacement 的日期。

## 已验证事实

1. canonical identity、current writer、双读 compatibility、新环境变量和正式 checker 的 R2 迁移已完成。
2. current production collector 的代码路径是 official-report-only，完整性不足时在 archive/send 前 fail closed。
3. repo 与 live morning/evening prompt 内容各自完全一致。
4. morning 实际 scheduler 时间与 current repo contract 冲突；evening 20:00 无 scheduler timezone 字段。
5. 六日 13 个 archive artifact 全部是 legacy identity，均无 official parity/evidence row。
6. 97 项 focused tests PASS；它们证明离线契约和 synthetic regression，不证明 production acceptance。
7. 本轮未运行 live DWS、未触发 automation、未发送钉钉消息。

## 仍缺证据

- 20 个证据项到 20 个唯一运行的一对一映射。
- 每个 historical run 的 code commit、prompt hash、准确触发来源与官方报告绑定。
- 六日每个 work date 的同范围 official report snapshot 与可复算 parity。
- current identity writer 在自然 morning/evening run 的成功 archive proof。
- receipt `SENT` 到客户端可见/已读的独立证明。
- legacy archive 对当前月累计的逐人逐日影响量；只能确认读取路径存在。
- owner 对晨报、晚报、累计和发送验收口径的明确决定。

## 必须由 owner 决定

1. OWNER_DECISION_REQUIRED：morning 永久时间采用 live 10:45，还是 repo 10:35；本轮不替 owner 改时间。
2. OWNER_DECISION_REQUIRED：晨报与晚报各自何时、以哪些 official fields 构成产品级完成口径。
3. OWNER_DECISION_REQUIRED：月累计是否允许保留 legacy-only 日期；若不允许，需要 owner 批准 cutover date 与重建范围。
4. OWNER_DECISION_REQUIRED：生产发送验收是 sender receipt、客户端可见、已读回执还是 owner 人工确认。
5. OWNER_DECISION_REQUIRED：历史错误/不可证运行是否需要撤回、补发、标记废止或仅保留审计。

## 五种状态严格区分

| 状态 | 只证明 | 明确不证明 |
|---|---|---|
| TEST_PASS | 当前离线代码/fixture 满足断言 | live DWS、自然触发、official parity、发送、owner 接受 |
| RUN_COMPLETED | task/process 到达其完成状态 | 数据正确、通知成功、official parity、owner 接受 |
| NOTIFICATION_SENT | sender/receipt 返回 `SENT` | 消息内容正确、客户端可见/已读、official parity、owner 接受 |
| OFFICIAL_CONSISTENT | 同 work date、同人员范围、同官方字段完成可复算 parity | automation 稳定、消息送达、owner 接受 |
| OWNER_ACCEPTED | owner 按明确产品验收标准确认可用 | 不自动推广到其他日期、slot 或未来运行 |

## 公开安全证据索引

- E01：`KMFA/tools/dingtalk_attendance/run_attendance.py` — auth/parity/archive/monthly/dispatch/cleanup 主链。
- E02：`KMFA/tools/dingtalk_attendance/dws_attendance.py` — official group/report collector 与 official-only rows。
- E03：`KMFA/tools/dingtalk_attendance/identity.py` — current/legacy 双读协议。
- E04：`KMFA/tools/dingtalk_attendance/notification_template.py` 与 `notification_targets.py` — delivery gate 和 target dispatch。
- E05：`KMFA/tests/test_dingtalk_attendance.py` — 97 项 focused synthetic/regression contract。
- E06：package/metadata automation prompt mirrors 与两个 live prompt SHA readback。
- E07：public automation bug log 中的历史 repair/probe 摘要；只作公开历史索引，不替代 private run binding。
- E08：private archive 脱敏统计：19 个 manifest 可见；六日窗口 13 个；不提交路径、文件名、员工、raw 或报告正文。
- E09：Codex automation task 脱敏统计：六日窗口 7 个 exact attendance task evidence item；不提交 task/session id 或原文。

## R3.1 安全声明

- 未修改考勤业务代码、测试逻辑、通知模板或 automation。
- 未修改 schedule、time、timezone、automation ID、cwd 或发送目标。
- 未运行 live DWS，未触发 automation，未发送钉钉消息。
- 未读取或修改另外三个 skill。
- 未提交员工明文、原始考勤、private path、DWS ID、SQLite、secret、automation memory 正文或报告正文。
- R3.1 只建立事实基线；不进入 R3.2 或 R4。

next_action: OWNER_DECISION_REQUIRED before R3.2
