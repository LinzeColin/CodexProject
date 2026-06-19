# 34 - GitHub 开发文档、备份与防漂移

## 目标

压缩包解压后可直接作为 GitHub 仓库根目录。GitHub 不只是代码备份，也保存功能、模型、数据范围、任务、风险、验收和决策历史。

## 仓库基线

- 根目录六份治理文档；
- `docs/` 详细规格；
- `data/` 机器目录和台账；
- `models/` 模型/公式 JSON；
- `config/` 可执行配置；
- `.github/ISSUE_TEMPLATE/` 结构化变更入口；
- `.github/pull_request_template.md` 同步检查；
- `.github/CODEOWNERS` 责任人；
- `.github/branch_protection.md` 分支保护契约；
- `.github/release_checklist.md` 发布检查清单；
- `.github/workflows/governance-validation.yml` 自动校验；
- `scripts/validate_governance_consistency.py` 校验目录、模型、任务、验收、P0 traceability 和 clean-room 前置文件一致性；
- `scripts/manage_development_status_artifacts.py` 生成并校验开发状态摘要、功能-任务-验收-测试证据矩阵和 A184 状态证据；
- `scripts/manage_risk_control_artifacts.py` 生成并校验 high/critical 风险的功能、任务、验收、owner、trigger、control 和 release gate 映射；
- `scripts/manage_clean_room_release.py` 生成并校验 A200 clean-room ZIP、内部 manifest/checksums 和 Markdown/CSV/JSON/GitHub/原型/PDF 一致性；
- `CHECKSUMS.sha256` 发布包完整性校验。

## 变更规则

1. 功能变更必须提供 Function ID、用户问题、输入输出、主可视化、对象、表、API、任务、验收、风险。
2. 模型变更必须提供 Model/Formula/Parameter ID、前后值、影响预览、缺失值语义、版本和回滚。
3. 数据范围变更必须提供定义、方向、时间、证据门槛、迁移和弃用规则。
4. 每个 PR 更新 `DEVELOPMENT_STATUS.md` 或明确说明为何无状态变化。
5. 任何目录变化触发 `python scripts/validate_task_pack.py`。
6. 任何目录、模型、任务或验收变更必须通过 `python scripts/validate_governance_consistency.py`。

## 建议分支规则

`main` 只接受 PR；要求治理校验通过并由 CODEOWNER 审查。实际 GitHub 仓库启用 branch protection 后生效。

## 发布备份规则

发布前按 `.github/release_checklist.md` 执行 `make verify`、`make verify-g2-db`、`sha256sum -c CHECKSUMS.sha256`，并在 release note 中记录任务、Acceptance ID、CI run、rollback 和未解决风险。T1212 起，clean-room 发布验证前置条件由 `scripts/validate_governance_consistency.py` 硬校验；A200 最终状态仍需 T1215 完整 clean-room 运行确认。
