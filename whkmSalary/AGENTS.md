# whkmSalary Agent 规则

默认用户可见输出使用中文。

## S4 精简执行胶囊

普通任务先读本文件、`README.md` 和被任务直接点名的任务/证据文件；不得扫描无关项目。

- 不得读取完整 `模型参数文件.md`，除非变更涉及工资公式、税/rounding、权重、payroll/legal
  假设、阈值或发布验收。
- 治理验证：`python -B scripts/lean_governance.py validate --project whkmSalary --semantic`。
- owner 预览：`python -B scripts/lean_governance.py check-render --project whkmSalary`。
- 代码变更要补：`python -B -m unittest discover -s whkmSalary/tests -p "test_*.py" -q`。

## 边界

- 没有明确证据和 owner 接受前，不得宣称 payroll、法律、税务或生产正确性。
- 私人工资数据和本地运行 artifacts 不得进入 Git，除非当前任务明确允许提交脱敏证据。
