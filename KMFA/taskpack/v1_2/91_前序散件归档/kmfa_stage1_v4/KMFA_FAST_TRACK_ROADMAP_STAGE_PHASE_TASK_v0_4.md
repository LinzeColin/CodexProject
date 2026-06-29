# KMFA 全程开发 Roadmap v0.4｜15天MVP / 20天稳定准确专项

> 当前状态：ChatGPT 阶段一收尾。此 Roadmap 是给 Codex 的开发任务骨架，仍需在阶段二完成官方文档核验、字段合同和 TaskPack 冻结后执行。

## 总体目标
- D15 MVP上线：先解决人工项目成本分析近期急用问题，交付文件型导入、数据源检查板、项目成本分析、经营摘要报告、HTML/PDF预览、metadata运行记录。
- D20稳定准确：完成样本回归测试、数据质量门禁、口径差异复核、报告准确生成、失败告警和人工复核闭环。
- 开发原则：独立项目 `CodexProject/KMFA`；后续轻量接入 OpMe；不保存明文账号密码；不把原始敏感数据提交公开 GitHub。

## Stage 0｜阶段二研究与TaskPack冻结（ChatGPT→Codex前置）
### Phase 0.1｜样本数据清点
- Task 0.1.1：登记已上传的销售绩效考核、财务、WPS数据包。
- Task 0.1.2：提取文件路径、文件类型、工作表名称、数据规模、文件指纹。
- Task 0.1.3：识别D15 MVP可直接使用的数据源和需转换/适配的数据源。
- Task 0.1.4：生成 `metadata/sources/source_registry.yaml` 草案。
- Task 0.1.5：标记不能进入GitHub的敏感数据类型。
### Phase 0.2｜MVP字段合同
- Task 0.2.1：锁定项目成本、回款、开票、资金、应收账龄最小字段。
- Task 0.2.2：定义字段别名、必填项、数据类型、金额/日期格式。
- Task 0.2.3：定义公司主体、客户、项目名称的匹配规则。
- Task 0.2.4：定义无法匹配时的人工复核队列。
- Task 0.2.5：生成 `DATA_CONTRACT_MVP.md`。
### Phase 0.3｜验收门禁
- Task 0.3.1：定义D15上线验收标准。
- Task 0.3.2：定义D20稳定准确验收标准。
- Task 0.3.3：定义Stop Conditions与Rollback。
- Task 0.3.4：定义报告不得生成/允许降级生成的条件。
- Task 0.3.5：生成 `ACCEPTANCE_GATE_MVP.md`。

## Stage 1｜项目骨架与治理文件
### Phase 1.1｜KMFA项目初始化
- Task 1.1.1：创建 `KMFA/` 独立目录。
- Task 1.1.2：创建 `README.md`、`AGENTS.md`、`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- Task 1.1.3：注册 `governance/projects.yaml`。
- Task 1.1.4：创建 `metadata/` 目录结构。
- Task 1.1.5：建立 `.gitignore` 与敏感数据排除规则。
### Phase 1.2｜运行与测试基线
- Task 1.2.1：创建本地启动脚本。
- Task 1.2.2：创建测试脚本与样例数据目录。
- Task 1.2.3：建立 `run_manifest` 与日志目录。
- Task 1.2.4：建立错误码与异常处理规范。
- Task 1.2.5：建立回滚说明。

## Stage 2｜文件导入与数据源检查板（D1-D6核心）
### Phase 2.1｜文件上传与批次登记
- Task 2.1.1：支持Codex端导入zip/xlsx/xls/csv/pdf。
- Task 2.1.2：支持前端上传zip/xlsx/xls/csv/pdf。
- Task 2.1.3：生成文件hash、source_id、import_run_id。
- Task 2.1.4：写入 `metadata/imports/import_runs.jsonl`。
- Task 2.1.5：不保存账号密码或明文凭证。
### Phase 2.2｜文件结构识别
- Task 2.2.1：识别Excel工作表、范围、文件大小、格式。
- Task 2.2.2：识别WPS/OLE/xls需要转换或适配的文件。
- Task 2.2.3：PDF只作为证据附件登记，不在MVP依赖OCR。
- Task 2.2.4：生成 `metadata/lineage/file_fingerprints.jsonl`。
- Task 2.2.5：生成数据源检查板初版。
### Phase 2.3｜状态矩阵与阻塞规则
- Task 2.3.1：实现已就绪/部分阻塞/失败不适用/已过期/人工复核五色状态。
- Task 2.3.2：实现来源系统→业务板块→文件包→主体→账户/报表层级。
- Task 2.3.3：实现缺失数据自动降级或阻塞。
- Task 2.3.4：实现人工复核状态和下一步提示。
- Task 2.3.5：写入 `metadata/data_quality/data_readiness_board.json`。

## Stage 3｜项目成本分析引擎（D7-D10核心）
### Phase 3.1｜项目主数据与匹配
- Task 3.1.1：统一项目名称、客户名称、公司主体。
- Task 3.1.2：建立项目别名与模糊匹配候选。
- Task 3.1.3：把合同、回款、开票、成本归到项目。
- Task 3.1.4：无法归集项进入人工复核。
- Task 3.1.5：输出项目主数据质量报告。
### Phase 3.2｜项目成本归集
- Task 3.2.1：读取项目成本明细、费用明细、外协费用、采购领料。
- Task 3.2.2：按人工/材料/机械/外协/运输/现场/税费分类。
- Task 3.2.3：识别未归集成本与异常成本。
- Task 3.2.4：计算项目实际成本与成本完整性得分。
- Task 3.2.5：写入 `metadata/metric_lineage.jsonl`。
### Phase 3.3｜利润质量与差异摘要
- Task 3.3.1：计算合同毛利、开票利润、管理利润、现金利润。
- Task 3.3.2：生成利润桥：合同预期→结算调整→成本超支→税费影响→回款风险。
- Task 3.3.3：生成口径差异与管理调整摘要。
- Task 3.3.4：每个差异必须有来源、原因、责任人、复核状态。
- Task 3.3.5：禁止在报告中使用Reconciliation英文术语。

## Stage 4｜经营报告与系统界面（D11-D15核心）
### Phase 4.1｜经营摘要报告
- Task 4.1.1：生成周/月/季/半年/年报告结构，但D15只强制月报和本期摘要。
- Task 4.1.2：报告包含经营摘要、项目组合、项目成本、现金回款、税务政策摘要。
- Task 4.1.3：报告展示表格、图表、口径说明和下期事项。
- Task 4.1.4：报告不展示数据源检查板后台明细。
- Task 4.1.5：输出HTML和PDF。
### Phase 4.2｜系统看板
- Task 4.2.1：实现首页、经营总览、财务资金、税务政策、数据源检查板、报告中心。
- Task 4.2.2：Logo使用KM。
- Task 4.2.3：全中文化，降低AI痕迹。
- Task 4.2.4：支持二级菜单跳转。
- Task 4.2.5：支持文件下载入口。
### Phase 4.3｜通知提醒
- Task 4.3.1：报告生成完成后邮件提醒。
- Task 4.3.2：重大风险邮件提醒。
- Task 4.3.3：邮件只发提醒，不发送完整报告正文。
- Task 4.3.4：目标邮箱：linzezhang35@gmail.com。
- Task 4.3.5：通知日志写入metadata。

## Stage 5｜D20稳定准确与运行治理
### Phase 5.1｜准确性验证
- Task 5.1.1：建立不少于10个项目样本的人工核对表。
- Task 5.1.2：项目成本、回款、开票、利润关键数字误差为0或有明确差异原因。
- Task 5.1.3：所有关键指标可追溯到文件、工作表、字段、批次。
- Task 5.1.4：异常值进入人工复核队列。
- Task 5.1.5：生成准确性验证报告。
### Phase 5.2｜稳定性验证
- Task 5.2.1：连续3次导入同一数据结果一致。
- Task 5.2.2：缺文件、坏文件、WPS/OLE文件均有明确错误提示。
- Task 5.2.3：报告重复生成不覆盖历史记录。
- Task 5.2.4：metadata增量更新稳定。
- Task 5.2.5：输出稳定性测试报告。
### Phase 5.3｜后续扩展门禁
- Task 5.3.1：规划红圈自动导出/API/RPA。
- Task 5.3.2：规划金蝶API/导出模板接入。
- Task 5.3.3：规划WPS开放平台/表格同步。
- Task 5.3.4：规划合同风险扫描和报价漏项检测。
- Task 5.3.5：规划OpMe轻量接入。
