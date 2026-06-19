# Artifacts and QA Evidence

本目录保存 Task Pack 生成、视觉检查和后续 Codex 执行的可复核证据；它不是实时企业事实来源。

## 已包含

- `governance_blueprint_v42_source.html`：16 页治理蓝图 PDF 的可复现 HTML 源。
- `pdf_contact_sheet.png`：16 页 PDF 逐页渲染联系表，用于检查分页、字体、截断、空页和视觉一致性。
- `pdf_visual_inspection.txt`：PDF 视觉检查范围、结果和已修复问题。
- `static_validation.txt`：目录、治理、模型、契约、JavaScript 和 shell 的最终校验记录。
- `prototype_smoke_test.txt`：离线原型的浏览器交互冒烟测试记录。
- `visual_coverage_validation.txt`：三种视口下首页与系统可视化覆盖验收记录。
- `preflight_output.txt`：当前执行环境的前置工具检查记录。
- `model_config_import_preview.json`：模型配置 dry-run 的确定性导入预览；不是生产激活记录。

## Codex 执行后应追加

- `01_plan_output.txt`
- `02_build_output.txt`
- `03_qa_output.txt`
- 单元、合同、集成、E2E、视觉、可访问性、性能、数据质量、新鲜度、迁移与回滚证据

不得提交密钥、个人数据、付费数据源原始载荷或受限文件。任何 fixture 必须明确标识，不能作为生产事实证据。
