# Report Validation Hub

`scripts/reportValidation.sh` 是报告和验证链路的默认用户入口。它把三件常见工作合并成一个低噪音只读摘要：

默认只读合并报告证据、补证据候选和验证优先级，先给用户一个可判断的摘要，再把写入、入队和执行留给高级动作。

- 报告证据索引：判断报告能否继续研究、需要补证据、只能观察或不要使用。
- 补证据任务预览：把证据不足报告拆成候选验证任务，但默认不写入队列。
- 验证优先级计划：读取现有验证队列，展示候选任务和处理优先级。

默认命令：

```bash
$PFI_OS_HOME/scripts/reportValidation.sh
```

无参数时等价于：

```bash
$PFI_OS_HOME/scripts/reportValidation.sh --mode daily --summary-json
```

## Safety Boundary

默认 daily 模式只读运行：

- 不写报告产物。
- 不追加 `data/validationQueue/ValidationTasks.json`。
- 不执行验证任务。
- 不刷新行情。
- 不连接券商。
- 不创建订单。
- 不修改持仓。
- 不输出完整报告 records、完整任务队列、原始行情、日志或本机私有 evidence。

## Modes

| Mode | 用途 |
| --- | --- |
| `daily` | 默认入口，同时查看报告证据、补证据候选和验证优先级。 |
| `decision` | 只看报告证据索引摘要。 |
| `gaps` | 只看补证据候选任务摘要。 |
| `priority` | 只看验证队列优先级摘要。 |

查看模式和高级命令：

```bash
$PFI_OS_HOME/scripts/reportValidation.sh --list-modes
```

## Advanced Commands

确认要生成文件、入队或执行验证时，再使用底层命令：

```bash
$PFI_OS_HOME/scripts/reportDecisionSupport.sh --output-dir data/reportDecision
$PFI_OS_HOME/scripts/reportGapTasks.sh --dry-run --output-dir data/reportDecision
$PFI_OS_HOME/scripts/reportGapTasks.sh --output-dir data/reportDecision
$PFI_OS_HOME/scripts/validationPriorityPlan.sh --output-dir data/validationQueue
$PFI_OS_HOME/scripts/runValidationTask.sh --output-dir data/validationQueue
```

其中 `reportGapTasks.sh --output-dir ...` 会追加验证队列，`runValidationTask.sh` 会执行最高优先级验证任务；这两个动作不再作为默认入口。
