roadmap_progress: R2 / R2.2

status: IMPLEMENTED_PENDING_EXTERNAL_REVIEW

base_commit: 2c91c22f3d334f82aa111245e452f8a35ac51cc6

implementation_commit: commit containing this handoff file

canonical_name: KMFA 钉钉考勤 skill

canonical_skill_id: kmfa-dingtalk-attendance-skill

active_legacy_matches: 0

allowed_legacy_matches:
  historical_identifier: 79
  legacy_read_only: 23
  deprecated_compatibility: 4
  counting_method: case-insensitive non-overlapping content occurrences plus the retained deprecated wrapper path

new_writer_contract:
  - 新运行只写 `skill_id: kmfa-dingtalk-attendance-skill`。
  - 新 run ID、archive 文件名和 seed 只使用 `dingtalk_attendance_` 语义前缀。
  - 新 writer 不写旧身份字段、旧阶段值或旧文件名前缀。

legacy_reader_contract:
  - archive、monthly rollup、ledger、replay 和 send-latest 通过集中式 identity compatibility 定义双读新旧 manifest、run ID、archive glob 与 seed。
  - 旧身份仅作 `legacy_read_only` 输入；新旧身份同时存在且冲突时 fail closed。
  - 既有公开历史、私有旧归档和 automation memory 不移动、不重命名、不改写。

environment_key_migration:
  - 当前授权、browser policy 路径和 timeout 均使用 `KMFA_DINGTALK_ATTENDANCE_*` 命名。
  - deprecated key 仅作只读 fallback；新旧 key 值冲突时 fail closed。
  - 未读取、修改或暴露本机授权值、policy 内容、credential 或 secret。

checker_migration:
  - 正式入口为 `check_dingtalk_attendance.py` 和 `validate_dingtalk_attendance_files`。
  - 保留一个 `deprecated_compatibility` 薄 wrapper，仅转发到正式实现；当前文档、prompt 与正式 required-file contract 不调用它。
  - 回归测试证明 wrapper 与正式函数为同一对象，不含第二套验证逻辑。

repo_prompt_hashes:
  morning_sha256: 32bba4910dcb29b8baa2c21eaaa770572d37b9dcabc78c885072fd7243508b41
  evening_sha256: 02fff9a42201a08b7d622ec433e19b688ed937d53f3085ce11d976dbc2f7300f
  normalization: exactly one trailing newline

live_prompt_readback:
  - repo push 成功后才允许仅更新两个 live prompt。
  - 实际 readback hash 和 repo mirror 一致性由本轮最终返回提供，并留给 R2.3 外部复核。

validation_performed:
  focused_attendance_tests: PASS, 97 tests
  current_checker: PASS
  skill_package_validator: PASS
  sensitive_data_validator: PASS
  git_diff_check: PASS
  changed_path_audit: PASS
  prompt_mirror_check: PASS
  source_manifest_and_checksums: PASS

unchanged_business_contract:
  - 未修改考勤业务规则、通知模板、发送目标、晨报/晚报产品规则、automation schedule、时间或 timezone。
  - 未运行 live DWS，未触发 automation，未发送任何钉钉消息。
  - 未读取或修改另外三个 KMFA skill。

blockers:
  - 私有旧归档数量保持 UNKNOWN；本轮按边界不读取、不枚举、不移动或重命名私有历史归档。
  - 新命名的生产自然触发证据属于后续验收，不由离线测试或 prompt readback 代替。

next_action: R2.3 external verification
