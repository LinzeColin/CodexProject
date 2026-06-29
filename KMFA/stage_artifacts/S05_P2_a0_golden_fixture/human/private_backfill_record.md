# S05-P2 私有字段 hash-only 部分回填记录

## 范围

- Stage/Phase: `S05-P2`
- Task: `S5PBT01-S5PBT03`
- 本轮只处理字段级黄金基准私有值 hash-only 回填；未进入 S05-P3、Stage 5 复审、zero-delta、事实层、报告或 UI。
- 本轮未读取其他本地压缩包，仅使用本地私有 `销售绩效考核.zip` 和已登记的 Stage2 Ring4 前序提取包做校验与回填输入。

## 私有输入审计

- 本机提供的 `销售绩效考核.zip` 存在，实际大小为 `1437252` bytes。
- 该 zip 的整包 SHA256 和大小均不匹配 v1.2 source manifest 登记值，因此不能标记为登记 source package 的整包匹配。
- 过滤 macOS 隐藏目录、resource fork 和 `.DS_Store` 后，真实业务成员数为 9。
- 9 个真实业务成员的 SHA256 与 Stage2 Ring4 authoritative registry 完全匹配。
- Stage2 Ring4 前序包 SHA256 匹配登记值，可作为本次 hash-only 回填的前序提取来源。
- 生成的私有 CSV 保存在仓库外私有运行区；公开仓库只记录 CSV 文件哈希，不提交 CSV 路径、CSV 内容或真实字段值。

## 回填结果

- A0 fixture candidates: `45`
- Hash/source anchor recorded: `40`
- Pending: `5`
- 已回填范围: 8 个 PDF A0 候选，每个候选覆盖合同额、支出合计、毛利、毛利率、成本分类。
- 未回填范围: 1 个 Excel A0 候选仍需后续私有映射或人工确认；本轮已新增机器复核记录，结论为 Excel workbook 不能安全机器合成为单一 A0 项目基准。
- 所有候选仍保持 `Q3`，`q4_human_confirmed=false`，`q5_calculation_baseline_allowed=false`。

## 公开仓库边界

- 未提交 `销售绩效考核.zip`、PDF、Excel、私有 CSV 或解包文件。
- 未提交合同额、支出合计、毛利、毛利率、成本分类的 raw value 或 normalized value。
- 公开 metadata 只保存 `sha256:<hash>`、private refs、source anchor 状态、质量状态和审计计数。
- 因仍有 5 条字段 pending 且未做 Q4 人工确认，S05-P2 不能声明完成，不能进入 S05-P3 锁定或 Stage 5 复审。
- Excel 待决策证据已记录在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md` 和 machine manifest；该记录不等同于字段回填完成。

## 下一步

- 继续停留在 `S05-P2`，由 owner 或授权私有映射确认 Excel candidate 的角色：补齐 5 条字段 private hash/source anchor，或形成明确人工豁免/不适用/降级决策。
- 补齐后再运行 `KMFA/tools/check_a0_golden_fixture.py --require-private-values` 和整套治理 validator。
