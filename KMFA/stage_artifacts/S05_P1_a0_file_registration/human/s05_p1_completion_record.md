# S05-P1 A0 文件登记完成记录

## 范围

- Stage/Phase: `S05-P1`
- Task: `S5PAT01-S5PAT03`
- 目标: 登记销售绩效考核 A0 输入文件，生成 A0 文件清单和项目候选清单，标记 Q3/Q4 状态。

## 已完成

- 新增 `KMFA/tools/a0_file_register.py`，从 v1.2 public-safe inventory 生成 A0 文件登记 metadata。
- 新增 `KMFA/tools/check_a0_file_registration.py`，验证 A0 文件数量、文件类型、质量状态和公开仓库安全边界。
- 新增 `KMFA/metadata/baseline/a0_file_manifest.json`，登记 `PRIVATE_RAW_SOURCE_005.zip` 包 SHA256、8 个 PDF、1 个 Excel、legacy inventory 指纹和成员 hash 状态。
- 新增 `KMFA/metadata/baseline/a0_project_candidates.jsonl`，生成 9 个 A0 项目候选，均标记为 `Q3` 机器候选且 `Q4` 人工锁定未完成。
- 新增 `KMFA/tests/test_a0_file_register.py`，覆盖 public-safe inventory 路径、私有 zip 可用时的成员 SHA256 计算、错误文件数量拒绝。

## 边界

- 未提交 `PRIVATE_RAW_SOURCE_005.zip`、PDF、Excel 或任何原始业务文件。
- 未抽取合同额、支出合计、毛利、毛利率或成本分类字段；这些属于 `S05-P2`。
- 未执行 zero-delta、事实层、报告生成或 UI；这些属于后续 Stage。
- 本机未找到私有 `PRIVATE_RAW_SOURCE_005.zip`，所以 9 个成员文件的 `member_sha256` 均显式记录为 `pending_private_zip_unavailable`；没有把 legacy CRC/指纹伪装成 SHA256。

## 结果

- `S5PAT01`: 已登记 8 个 PDF + 1 个 Excel 的公开安全 inventory 指纹、source package SHA256 和成员 SHA256 待补状态。
- `S5PAT02`: 已生成 A0 权威项目成本文件清单和项目候选清单。
- `S5PAT03`: 已将候选标记为 `Q3` 机器候选，且 `Q4` 人工锁定状态为 `not_locked_pending_human_confirmation`。

## 风险

- 若后续需要真正完成成员级 SHA256，必须在本地私有路径提供 `PRIVATE_RAW_SOURCE_005.zip`，运行 `KMFA/tools/a0_file_register.py --source-zip <private-path>` 后复验；不得提交 zip 或解包文件。
- S05-P1 候选不等于字段级黄金基准，不能用于正式报告。

## 回滚

- 删除 `KMFA/tools/a0_file_register.py`
- 删除 `KMFA/tools/check_a0_file_registration.py`
- 删除 `KMFA/tests/test_a0_file_register.py`
- 删除 `KMFA/metadata/baseline/a0_file_manifest.json`
- 删除 `KMFA/metadata/baseline/a0_project_candidates.jsonl`
- 删除 `KMFA/stage_artifacts/S05_P1_a0_file_registration/`
- 恢复 S05 stage status 和中文入口记录。
