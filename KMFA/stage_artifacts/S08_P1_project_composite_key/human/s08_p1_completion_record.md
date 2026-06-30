# S08-P1 项目组合键完成记录

## 范围

- Stage/Phase: `S08-P1｜项目组合键`
- Task: `S8PAT01-S8PAT03`
- 基线: `KMFA/taskpack/v1_2/roadmap/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md`
- 完成时间: `2026-06-30T20:00:00+10:00`

## 已完成

- 建立项目组合键组件：合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash。
- 将 TaskPack 的项目身份权重转换为整数 basis points，避免业务金额或匹配分数使用 float。
- 建立 strong auto match、human review、weak candidate 三个阈值，当前 strong auto match 为 `8500` bps，human review 为 `7000` bps。
- 验证缺单字段不会全阻断：缺合同编号时仍形成候选，score=`8000` bps，进入人工复核。
- 验证低于强匹配阈值的候选进入人工复核队列，禁止自动合并。
- 输出 S08-P1 manifest、identity profiles、match results、manual review queue 和 machine manifest。

## Public-Safe 边界

- 未提交 raw business data、zip、Excel、PDF、私有 CSV 或字段明文。
- 未提交合同编号、项目名称、对手方、主体、责任人、金额原值或来源表头明文。
- 公开仓库只保存 component hash、private ref、权重、score、status、queue metadata 和 evidence ref。
- `formal_report_allowed=false`，`github_upload_allowed=false`，中间 Phase 不上传 GitHub。
- 本 Phase 不包含 S08-P2 业务实体模型、S08-P3 匹配质量测试、事实层、lineage 完整检查、正式报告、UI 或外部接口。

## 输出

- `KMFA/tools/project_composite_key.py`
- `KMFA/tools/check_s08_p1_project_composite_key.py`
- `KMFA/tests/test_project_composite_key.py`
- `KMFA/metadata/schema_maps/project_composite_key_manifest.json`
- `KMFA/metadata/schema_maps/project_identity_profiles.jsonl`
- `KMFA/metadata/schema_maps/project_composite_key_matches.jsonl`
- `KMFA/metadata/quality/project_identity_review_queue.jsonl`
- `KMFA/stage_artifacts/S08_P1_project_composite_key/machine/s08_p1_manifest.json`
- `KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md`

## 下一步

下一轮只能执行 `S08-P2｜业务实体模型`；不得跳到 S08-P3、Stage 8 review、UI、报告、事实层、lineage 或外部接口。

