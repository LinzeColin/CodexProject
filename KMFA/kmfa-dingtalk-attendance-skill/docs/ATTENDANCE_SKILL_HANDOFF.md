name: KMFA 钉钉考勤 skill

roadmap_progress: R1 / R1.3

status: READY_FOR_EXTERNAL_REVIEW

main_base_commit: d90e82adc75a71f4d9b05dcee68d080d46331d9e

owner_policy:
  - main-only
  - no branch
  - no PR
  - 经 owner 批准的变更直接提交并推送 main。
  - 每阶段结束确认本任务没有遗留 branch，且开放 PR 数量为零。
  - 不触碰无关现有分支。

scope:
  - 本步骤只建立考勤 skill 的 GitHub 单一协作通道并清理当前命名。
  - 本步骤只新增公开安全交接文件并同步既有 package manifest 与 checksum。
  - 本步骤不定义或修改考勤业务规则，不编写通知内容。

verified_facts:
  - GitHub source of truth 是 LinzeColin/CodexProject，当前工作基线来自最新 origin/main。
  - 两个本机考勤 automation 均为 ACTIVE，并指向 CodexProject 仓库工作区。
  - morning automation 当前使用本机墙钟 10:45，evening automation 当前使用本机墙钟 20:00。
  - 两个本机考勤 automation 的 schedule 均不包含 timezone、TZID 或 DTSTART 字段。
  - 两个 live automation prompt 在规范化末尾换行后均与考勤 skill 内 prompt mirror 一致。
  - 当前代码将用户可见统计路由到当前考勤组成员和官方考勤报表字段，并在覆盖、日期、字段或状态不完整时 fail closed。
  - 历史 test、manifest、dispatch 与 readback 的 PASS 不能单独作为 production acceptance。
  - 已审计的十九份历史 run manifest 均未保存 official-report parity evidence；随后一次自然 evening task 在生成 manifest 或发送前中断。

contradictions:
  - live morning automation 是 10:45，而考勤 skill、runbook 和 focused test 仍包含 10:35。
  - live automation prompt 与考勤 skill 内 prompt mirror 对齐，但与独立 metadata prompt mirror 不一致。
  - 历史归档使用过与当前官方报表 collector 不同的人员范围和推断路径。
  - 历史 PASS 与 SENT 证据存在未保存 official-report parity evidence 的情况。
  - 当前 main 基线包含缩短后的 official-only collector，但尚无完成的自然 automation run 对该基线进行端到端验证。
  - evening automation memory 未记录最近一次中断的自然 task，与 task history 不一致。
  - synthetic test parity 验证代码契约和 fail-closed，不验证与 owner 同时点、同筛选范围的独立官方报告完全一致。

unknowns:
  - 多数历史归档没有保存其精确 source commit 和 prompt version。
  - 多数历史运行没有可用的精确触发时点官方快照。
  - 当前 main 基线尚未获得 morning 与 evening 自然运行的同时间官方证据验收。
  - morning 与 evening 产品语义以及最终 production acceptance 仍需 owner 在后续独立步骤决定。

blockers:
  - 当前 main 基线的自然运行稳定性和同时间官方一致性尚未验收。
  - 历史归档缺少完整版本、prompt 和官方快照关联，不能补写为已验证事实。
  - R1.3 不授权解决业务、automation、schedule、timezone、live DWS 或发送问题。

changes_in_this_commit:
  - 新增本公开安全交接文件。
  - 同步 source_manifest.txt 与 source_checksums.sha256。
  - 不修改考勤业务代码、test、automation、schedule、timezone 或通知内容。

validation_performed:
  - skill package validator: PASS
  - public repository sensitive-data validator: PASS
  - Git whitespace validation: PASS
  - changed-path audit: PASS

next_action:
  - 对 main 中的本交接文件进行 external review。
  - 未经 owner 单独指令，不进入 R2。

public_safety_statement:
  - 本文件只包含公开安全的仓库、调度、聚合状态和契约信息。
  - 本文件不包含员工明文、raw attendance 数据、报告正文、DWS ID、token、webhook、secret、SQLite、私有归档绝对路径或本机 session 原文。
  - 本步骤未运行 live DWS，未发送钉钉消息，未修改本机 automation，也未读取或修改其他 KMFA skill。
