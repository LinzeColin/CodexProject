# PFI v0.2.5 Stage 9 整阶段审查

## 唯一执行合同

- Contract：`PFI-V025-STAGE9-WHOLE-REVIEW`
- Acceptance：`ACC-PFI-V025-STAGE9-WHOLE-REVIEW`
- Review base：`45653bd4d57d3a4a8d6f025b5f624fed5f155d1e`
- 风险路由：`T3_FINANCIAL_MODEL_REPORT_AND_HUMAN_DECISION_REVIEW`
- 范围：只复核 Stage 9 的 12/12 tasks、三笔 immutable Phase evidence commits、当前产品整改、正式 Shell/导出、治理与 transition acceptance。
- 停止边界：Stage 10 implementation 保持 `not_started`；不 push、不安装、不执行 production/final acceptance。

## 初审与整改

三位独立 reviewer 的初审与复审新增发现合计为 `C2/I11/M3`。整改关闭以下真实问题：

1. 正式 Shell 现在直接绑定 immutable reviewed analysis contract，而不是信任 localStorage 中的完整 view model；localStorage 只保存严格 schema 的 review delta，identity/hash/extra-field 漂移均在 render 前 fail closed。
2. 主报告展示总流出、生活消费、投资资金流出、投资域配置四个双消费组件，并明确 activity flow 不等于 net-worth loss；这些组件进入同源报告与导出，不持久化任何财务金额。
3. 5 份 reviewed reports 保持 `net worth/cash/investment=blocked`、`consumption/cashflow=partial`；数据不足不输出假结论。
4. 新增正式 model validation report、Phase 9.2/9.3 DOM 与 Chrome CDP AX 证据、严格 Phase evidence normalization，以及 fallback/PyYAML 一致的治理 renderer。
5. PDF 中 Snapshot/Analysis SHA-256 以完整、可选择、单行 Courier 文本展示；实体解析、栅格与直接目视均通过。
6. Phase 9.3 validator 现在严格校验完整 `pack_hash`、确定性 `ui_contract`、pack/manifest 字段集，以及从当前 snapshot 重建的 export `byte_size`/`sha256`；即使同步重算 manifest/UI/pack hash，UI thesis、filename/content-type 或导出 size/hash 漂移仍 fail closed。
7. 双 parser renderer evidence 现在准确标记 venv 为无 PyYAML fallback、`/usr/bin/python3` 为 PyYAML parser；两路均保持零 drift/零 reference issue。

## Pass Gate 与结构化 UAT

- 数据是否够：当前 aggregate source 可支持 data-quality、消费与现金流的覆盖分析；不足以支持净资产、现金、投资金额结论，后三者继续 blocked。
- 公式是否正确：`FORM-PFI-015`、`FORM-PFI-019` 的当前 invariants/真实覆盖证据通过；`FORM-PFI-016..018` 因输入缺失 blocked；`FORM-PFI-020` 只通过 structure-level validation。
- 模型是否有效：当前只能声明 partial validation；缺 historical/out-of-sample ground truth，不声明准确率、预测能力或生产有效性。
- 参数如何调整：cashflow window 的非金额影响可见；阈值、XIRR 与 quantum 影响在缺真实输入时保持 blocked，不猜测调整结果。
- 人工决策：accepted/rejected/deferred/invalidated 只记录 review event；`automatic_trading_allowed=false`、`trade_execution_available=false`。
- 同源导出：HTML/PDF/CSV/Markdown 绑定同一 reviewed snapshot、analysis pack 和 manifest，各格式 SHA-256 可追溯。

## 验证、授权与边界

- current-content loopback browser `16/16`：完整 view model 拒绝、坏 ledger 拒绝、严格 delta restore、tamper fail-closed、四组件/五报告可见、四导出与 manifest 一致、Phase 9.2/9.3 DOM 与 CDP AX 通过。
- 最终验证绑定 focused Stage 9、selected Stage 4/5/7/8 regression、Node/Python syntax/diff、PDF/隐私，以及完整 Git archive + 当前 overlay 的 PFI governance/renderer。
- 三位独立 reviewer 必须同时绑定 `reviewed_worktree_overlay.json` 与 `reviewed_evidence_overlay.json` 并返回 `ACCEPT C0/I0/M0`；任一 hash 漂移、缺命令或 reviewer 缺失均 fail closed。
- 用户站立授权原文绑定于 `transition_authorization_binding.json`；该授权只接受 Stage 9 transition 并授权 Stage 10 entry，不等于 Stage 10 已开始、production acceptance 或 final human acceptance。
- 本轮未使用 Finder、LaunchServices 或 GUI 文件操作；网络仅为 ephemeral local loopback，无外部网络。
- 本轮未读取 raw financial rows、未修改数据库或 model/formula/parameter 数值；未 push、未安装 App。

## 结果、回滚与下一步

Stage 9 通过整阶段复核后状态为 `accepted_for_transition`，v0.2.5 进度保持 `120/156 (76.92%)`。回滚以产品整改提交 `a1178bef79b982d343c4610ae7286d356214b03d`、PDF/hash 修复提交 `66aaba487f8781caf4e026c170ed3ab271f98cdd`、decision-pack 合同修复 `e2a3908ee640e5392bd56450a2da75577b622c0f`、deterministic export bytes 绑定修复 `45653bd4d57d3a4a8d6f025b5f624fed5f155d1e` 与本整阶段 evidence/governance 提交为边界；无需数据回滚。

下一工作单元是独立 run 的 `S10-P1-T1` / `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`，本轮不得执行。
