# CodexProject M1 治理执行链减负与零质量回退 Roadmap

## 总目标

在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

## 编号兼容

为满足“全部数字顺序”，每个节点提供 `numeric_sequence`（如 `1.2.3`）。为避免破坏仓库现有 validator，正式 Task ID 继续使用 `S1PAT01` 规则。

## 总览

| 数字顺序 | Stage | Pursuing Goal | Phase | Task | 工时 | 占比 |
|---:|---|---|---:|---:|---:|---:|
| 1 | S1 基线与第一轮独立审查 | 锁定真实现状并完成第一轮 3 Agent 互不污染审查，得到证据化问题基线。 | 3 | 8 | 12.0h | 20.00% |
| 2 | S2 第二轮对抗复审与跨轮裁决 | 以全新三 Agent 反复交叉验证第一轮结论，证明候选优化不会牺牲质量、事实和发布安全。 | 3 | 7 | 10.0h | 16.67% |
| 3 | S3 影子实现与零质量回退保护 | 在现有单一入口中增加影子检查计划、紧凑输出、准确零写入检测和性能遥测，同时保持旧链完全权威。 | 3 | 9 | 16.0h | 26.67% |
| 4 | S4 等价性、压力与真实影子证明 | 以反例、故障注入、真实 PR 与性能基线证明候选路径既更快又不降低质量。 | 3 | 8 | 14.0h | 23.33% |
| 5 | S5 受控激活、验收与连续性交接 | 以最小 CI/文档改动激活安全快路径，完成全量回归、ROI 证明、回滚和后续 Agent 交接。 | 3 | 8 | 8.0h | 13.33% |

# 1 S1｜基线与第一轮独立审查

**Parental Pursuing Goal：** 在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

**Stage Pursuing Goal：** 锁定真实现状并完成第一轮 3 Agent 互不污染审查，得到证据化问题基线。

**预计：** 12.0h / 20.00%；3 Phase；8 Task

**Stage Stop Conditions**
- 无法绑定当前分支/HEAD
- 任何审查产生 tracked 写入
- 少于三份独立报告
- 阻塞结论缺证据

**Stage Stop Gate：S1-GATE**
- 基线、测量和三份报告齐全
- 第一轮汇总可重放
- 仓库前后差异为零

## 1.1 S1PA｜基线锁定与旧链测量

**Phase Pursuing Goal：** 得到可复现、可比较且不修改仓库的当前事实基线。

**预计：** 3.5h / 5.83%；3 Task

**Phase Stop Conditions**
- 无法确认实际 HEAD 或 base ref
- 基线命令会写 tracked 文件
- 读取范围扩展到无关项目业务源码

**Phase Stop Gate：S1PA-GATE**
- 完整基线记录存在
- 现有权威命令可复现
- 测试前后 Git 状态差异为零

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 1.1.1 | `S1PAT01` | 锁定分支、HEAD、工作树与当前 Roadmap 状态 | 1.00h | 1.67% | 记录 branch、full SHA、commit title、工作树状态、当前 Other8 Task；无仓库写入 |

**S1PAT01 Objective：** 确认实际执行基线；若 HEAD 已不是观察基线，则只读评估差异并重新绑定。
| 1.1.2 | `S1PAT02` | 建立读取、写入与禁区清单 | 1.00h | 1.67% | 允许/禁止路径明确；Scope Guard 可自动检测；无隐式全仓修改 |

**S1PAT02 Objective：** 限定本整改只涉及根治理执行链；EEI、arxiv-daily-push 与项目业务文件均为禁止写入。
| 1.1.3 | `S1PAT03` | 测量现有权威验证链基线 | 1.50h | 2.50% | 至少 5 次冷/热运行；p50/p95、输出字节、零写入证据齐全；失败场景不被吞掉 |

**S1PAT03 Objective：** 重复运行当前 changed-scope 命令并记录耗时、输出体积、选中项目数、退出码和 Git 状态。

## 1.2 S1PB｜第一轮三 Agent 独立审查

**Phase Pursuing Goal：** 由三个互不读取彼此结果的只读 Agent，从安全代码、运行压力和信息交互三个角度建立第一轮问题基线。

**预计：** 4.5h / 7.50%；3 Task

**Phase Stop Conditions**
- 任一 Agent 读取其他 Agent 输出
- 任一 Agent 修改仓库或运行写模式
- 报告没有可核验证据却判定阻塞

**Phase Stop Gate：S1PB-GATE**
- 恰好 3 份独立报告完成
- 三份报告均为 read-only
- 输出符合统一 schema

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 1.2.1 | `S1PBT01` | Agent 1：安全、代码质量、Bug、竞态、测试稳定性与维护性审查 | 1.50h | 2.50% | 独立报告符合 finding schema；严重度、阻塞、修复与测试建议齐全 |

**S1PBT01 Objective：** 只读审查治理入口、验证器、工作流和测试；每项问题必须有路径/符号/命令证据。
| 1.2.2 | `S1PBT02` | Agent 2：压力、极限流程、生命周期、缓存与数据保存审查 | 1.50h | 2.50% | 独立报告覆盖运行启动-执行-关闭-清理；未把未运行测试写成已验证 |

**S1PBT02 Objective：** 审查 0/1/多项目范围、重复运行、并发、取消、超时、临时文件、自动调度和清理。
| 1.2.3 | `S1PBT03` | Agent 3：人类界面、CLI 反馈、信息架构与功能连接审查 | 1.50h | 2.50% | 独立报告区分必要事实与重复信息；不得建议新增平行真相源 |

**S1PBT03 Objective：** 将 UI/交互审查应用于仓库导航、CLI 输出、错误反馈、Agent 入口、双平面和交接链路。

## 1.3 S1PC｜第一轮证据汇总与决策

**Phase Pursuing Goal：** 去重但不掩盖分歧，形成可供第二轮攻击性复核的候选问题集与 M1-S 候选方案。

**预计：** 4.0h / 6.67%；2 Task

**Phase Stop Conditions**
- P0/P1 证据无法重放
- 汇总删除了少数意见
- 候选方案改变双平面或弱化 Acceptance/Evidence

**Phase Stop Gate：S1PC-GATE**
- 第一轮汇总完成
- 所有阻塞项有 owner 可理解的说明
- 第二轮输入不含未验证的完成声明

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 1.3.1 | `S1PCT01` | 验证证据、去重并登记分歧 | 2.00h | 3.33% | 每个 P0/P1 至少一条可重放证据；重复项有映射；UNKNOWN 不伪装 VERIFIED |

**S1PCT01 Objective：** 逐项重放路径/命令证据，合并同源问题，保留严重度分歧和证据不足状态。
| 1.3.2 | `S1PCT02` | 形成第一轮风险登记表与 M1-S 候选决策 | 2.00h | 3.33% | 问题含严重度、是否阻塞合并、修复方式；候选方案明确非目标与回滚 |

**S1PCT02 Objective：** 给出最小改动候选：影子测量优先，不改变权威门禁，不新增 CURRENT/SHIP 等文件。

# 2 S2｜第二轮对抗复审与跨轮裁决

**Parental Pursuing Goal：** 在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

**Stage Pursuing Goal：** 以全新三 Agent 反复交叉验证第一轮结论，证明候选优化不会牺牲质量、事实和发布安全。

**预计：** 10.0h / 16.67%；3 Phase；7 Task

**Stage Stop Conditions**
- 第二轮不独立
- 任何 P0/P1 未裁决
- 候选直接替换权威链
- 性能目标没有基线

**Stage Stop Gate：S2-GATE**
- 两轮共 6 份报告完成
- 跨轮裁决可追踪
- 仅影子实施获得许可

## 2.1 S2PA｜候选方案与反例矩阵

**Phase Pursuing Goal：** 把第一轮建议转为可被攻击、可被证明错误的候选设计，而不是直接实施。

**预计：** 3.0h / 5.00%；2 Task

**Phase Stop Conditions**
- 候选方案直接成为权威链
- 反例只覆盖成功路径
- 用主观 Token 估计代替真实测量

**Phase Stop Gate：S2PA-GATE**
- 候选处于 shadow 状态
- 不变量与测试矩阵完整
- 旧链仍是唯一权威结果

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 2.1.1 | `S2PAT01` | 定义 M1-S 影子候选与不变量 | 1.50h | 2.50% | 双平面/中文三文件/T0-T3/required check/full gate 不变量清单可机器验证 |

**S2PAT01 Objective：** 定义只压缩调用、输出和误触发，不压缩语义、验收、证据、发布门禁。
| 2.1.2 | `S2PAT02` | 建立正反例、故障注入与性能比较矩阵 | 1.50h | 2.50% | 每个风险至少一个反例；预期退出码和证据明确 |

**S2PAT02 Objective：** 覆盖合法/非法 fixture、路径变更、base ref 失败、并发、取消和输出预算。

## 2.2 S2PB｜第二轮三 Agent 新鲜上下文交叉验证

**Phase Pursuing Goal：** 使用三名全新 Agent 攻击第一轮汇总和 M1-S 候选，寻找漏检、误判和质量回退。

**预计：** 4.5h / 7.50%；3 Task

**Phase Stop Conditions**
- 第二轮 Agent 复用第一轮 Agent 会话
- 三个 Agent 互看未完成结果
- 候选缺陷被以“后续再说”跳过

**Phase Stop Gate：S2PB-GATE**
- 恰好 3 份新鲜独立报告
- 覆盖第一轮全部 P0/P1
- 产生明确的新增/确认/驳回映射

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 2.2.1 | `S2PBT01` | Agent 4：安全与代码对抗复审 | 1.50h | 2.50% | 独立报告；能指出第一轮漏项或明确确认无新增；证据可重放 |

**S2PBT01 Objective：** 重点攻击 fail-open、分类绕过、缓存污染、供应链、required check 与范围隔离。
| 2.2.2 | `S2PBT02` | Agent 5：压力与故障注入复审 | 1.50h | 2.50% | 给出可运行 stress matrix；区分实际运行与待执行 |

**S2PBT02 Objective：** 重点攻击脏工作树、0/1/8 项目、Unicode/rename/delete、并发、取消、超时、重复确定性。
| 2.2.3 | `S2PBT03` | Agent 6：信息交互与架构对抗复审 | 1.50h | 2.50% | 给出人类首屏、错误信息、Agent 入口和交接的可验收标准 |

**S2PBT03 Objective：** 重点检查压缩后是否造成偏离、遗忘、幻觉、低可读性或新真相源。

## 2.3 S2PC｜跨轮裁决与实施许可

**Phase Pursuing Goal：** 交叉验证两轮结论，只允许证据充分且可回滚的影子实施进入下一 Stage。

**预计：** 2.5h / 4.17%；2 Task

**Phase Stop Conditions**
- 存在未裁决 P0/P1
- 候选需要删除旧 validator 才能实施
- 无法证明 EEI/arxiv 零写入

**Phase Stop Gate：S2PC-GATE**
- 最终风险登记表完成
- 实施边界锁定
- Owner/Integrator 给出唯一决策

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 2.3.1 | `S2PCT01` | 跨轮问题映射与严重度裁决 | 1.25h | 2.08% | 每个问题有 round1/round2 状态；P0/P1 无未解释分歧 |

**S2PCT01 Objective：** 比较两轮证据、置信度和分歧；严重度向高风险保守收敛，但不夸大无证据问题。
| 2.3.2 | `S2PCT02` | 发布 PROCEED_SHADOW / FIX-ONE / STOP 决策 | 1.25h | 2.08% | 决策唯一；允许文件、测试、回滚和 Stop Conditions 明确 |

**S2PCT02 Objective：** 只有零未决阻塞且影子实施不改变权威结果时才允许进入 S3。

# 3 S3｜影子实现与零质量回退保护

**Parental Pursuing Goal：** 在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

**Stage Pursuing Goal：** 在现有单一入口中增加影子检查计划、紧凑输出、准确零写入检测和性能遥测，同时保持旧链完全权威。

**预计：** 16.0h / 26.67%；3 Phase；9 Task

**Stage Stop Conditions**
- 需要新文件体系才能运行
- 权威退出结果改变
- CI/READ_ONLY 写仓库
- 竞态或残留无法消除

**Stage Stop Gate：S3-GATE**
- 所有新增测试通过
- 旧 required 结果不变
- compact/JSON/telemetry 可复现
- 无项目业务文件变更

## 3.1 S3PA｜测试先行与输出合同

**Phase Pursuing Goal：** 先用测试固定不变量、零写入和 fail-closed，再碰实现代码。

**预计：** 4.0h / 6.67%；3 Task

**Phase Stop Conditions**
- 先改实现后补测试
- 测试只断言文本不验证退出码/写入
- 任一未知路径 fail-open

**Phase Stop Gate：S3PA-GATE**
- 红灯测试能复现问题
- 不变量均有测试
- 现有权威测试未被弱化

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 3.1.1 | `S3PAT01` | 定义 compact plan 与机器 JSON 输出合同 | 1.00h | 1.67% | compact stdout <= 2 KB；JSON 字段稳定；错误可定位 |

**S3PAT01 Objective：** 把 Agent 需要的摘要限制为检查计划、范围、失败和下一动作；完整细节进入临时 JSON。
| 3.1.2 | `S3PAT02` | 增加 pre/post Git 状态差异测试 | 1.50h | 2.50% | 本地已有无关改动不被当成新写入；CI clean-start 模式仍可严格要求干净 |

**S3PAT02 Objective：** 区分“调用前已有修改”和“验证器新增修改”，避免本地脏工作树误报为验证器写入。
| 3.1.3 | `S3PAT03` | 增加分类 fail-closed 与范围隔离测试 | 1.50h | 2.50% | 未知路径不跳检；EEI/arxiv 不被写入；分类不可由 Prompt 自报覆盖 |

**S3PAT03 Objective：** 任何未知、Git diff 失败、根契约/schema/validator 变更都必须走完整 changed-scope。

## 3.2 S3PB｜现有入口内的影子实现

**Phase Pursuing Goal：** 只在现有 lean_governance.py 入口内增加可观测、可比较的候选路径，不创建新控制平面。

**预计：** 8.0h / 13.33%；4 Task

**Phase Stop Conditions**
- 新增 CURRENT.md/SHIP.md/projectctl 或平行事实源
- 重命名 Required Check
- 删除旧 validator
- 修改项目业务目录

**Phase Stop Gate：S3PB-GATE**
- 旧链仍权威
- 影子输出可关闭
- 所有实现局限于允许文件

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 3.2.1 | `S3PBT01` | 实现只读 check plan / explain 输出 | 2.00h | 3.33% | 同一输入输出确定；失败原因可读；无 tracked 写入 |

**S3PBT01 Objective：** 根据真实 Git diff 解释选中项目、检查项和升级原因；不改变现有退出结果。
| 3.2.2 | `S3PBT02` | 修复零写入判断为 pre/post delta | 2.00h | 3.33% | 脏工作树 fixture、干净 CI fixture、git status 错误 fixture 全通过 |

**S3PBT02 Objective：** 本地模式检测验证器新增差异，CI 模式可保留 clean-start 严格要求。
| 3.2.3 | `S3PBT03` | 增加 compact 人类输出与完整临时证据输出 | 2.00h | 3.33% | stdout 预算达标；失败信息含类别/文件/复现命令/下一动作 |

**S3PBT03 Objective：** 减少 Agent 上下文，保留完整机器证据；不得吞掉原 validator 退出码和尾部错误。
| 3.2.4 | `S3PBT04` | 增加无持久缓存的性能遥测 | 2.00h | 3.33% | 无凭据；无 tracked 文件；取消/异常后临时文件清理 |

**S3PBT04 Objective：** 记录阶段耗时、选中项目、渲染数和输出体积到 stdout/runner temp；不写仓库。

## 3.3 S3PC｜集成、竞态与确定性验证

**Phase Pursuing Goal：** 证明新观测路径在重复、并发和取消下不会产生竞态、缓存污染或 Git 噪声。

**预计：** 4.0h / 6.67%；2 Task

**Phase Stop Conditions**
- 出现非确定性结果
- 并发共享同一输出文件
- 候选结果参与 required pass/fail

**Phase Stop Gate：S3PC-GATE**
- 影子实现测试通过
- 无竞态/残留
- 权威行为零变化

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 3.3.1 | `S3PCT01` | 运行单元、并发、取消与 20 次确定性测试 | 2.00h | 3.33% | 20 次摘要 hash 一致；并发退出码稳定；临时目录清理 |

**S3PCT01 Objective：** 并发运行使用每次独立临时目录；取消后无孤儿进程、共享缓存和残留。
| 3.3.2 | `S3PCT02` | 建立 legacy-authoritative 与 candidate-shadow 对比器 | 2.00h | 3.33% | 差异报告可复现；候选失败不掩盖旧链；零写入 |

**S3PCT02 Objective：** 同一 fixture 同时记录旧结果与候选计划；任何差异只报告，不改变 required 结果。

# 4 S4｜等价性、压力与真实影子证明

**Parental Pursuing Goal：** 在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

**Stage Pursuing Goal：** 以反例、故障注入、真实 PR 与性能基线证明候选路径既更快又不降低质量。

**预计：** 14.0h / 23.33%；3 Phase；8 Task

**Stage Stop Conditions**
- 出现任一 false negative
- 候选 fail-open
- 并发/取消残留
- 未达到真实 shadow 数量

**Stage Stop Gate：S4-GATE**
- 合成与真实 parity 通过
- 性能目标有实测
- OWNER 给出唯一激活裁决

## 4.1 S4PA｜合成语料与故障注入等价性

**Phase Pursuing Goal：** 用足够苛刻的正反例证明候选不会漏掉原有质量问题。

**预计：** 5.0h / 8.33%；3 Task

**Phase Stop Conditions**
- 任何旧链失败样本候选漏报
- base/Git 错误被当作无变更
- 中文路径解析不稳定

**Phase Stop Gate：S4PA-GATE**
- 等价矩阵 100% 通过
- 零 false negative
- 失败证据可重放

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 4.1.1 | `S4PAT01` | 运行合法与非法治理 fixture 全矩阵 | 2.00h | 3.33% | 所有旧链失败样本候选不得判定可跳过；零 false negative |

**S4PAT01 Objective：** 覆盖缺中文文件、非法 Roadmap、completed 无证据、模型/参数漂移和引用断裂。
| 4.1.2 | `S4PAT02` | 运行路径、Unicode、rename/delete 与 base-ref 故障矩阵 | 1.50h | 2.50% | 全部 fail-closed 或给出明确 BLOCKED；无异常吞噬 |

**S4PAT02 Objective：** 验证中文文件名、重命名、删除、首提交、错误 base、detached HEAD 和 Git 错误。
| 4.1.3 | `S4PAT03` | 验证 T0-T3 升级和根治理 fan-out | 1.50h | 2.50% | 选中范围与原因正确；EEI/arxiv 排除规则保持；T2/T3 不降级 |

**S4PAT03 Objective：** 测试 0/1/8 项目选择和根契约变化；风险无法确定时走完整检查。

## 4.2 S4PB｜性能、操作极限与真实影子运行

**Phase Pursuing Goal：** 用真实数据证明提速，而不是以删除检查或主观 Token 估计制造假收益。

**预计：** 5.0h / 8.33%；3 Task

**Phase Stop Conditions**
- 性能收益来自跳过必要语义/证据检查
- 任一压力测试留下后台进程或缓存
- 真实 shadow 结果不一致

**Phase Stop Gate：S4PB-GATE**
- 性能目标达成或有透明 FIX-ONE
- 操作极限稳定
- 两个真实样本零质量回退

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 4.2.1 | `S4PBT01` | 比较 legacy 与 candidate 的 p50/p95、输出和项目 fan-out | 2.00h | 3.33% | T0/T1 p50 <= legacy 70%；p95 <= legacy 85%；完整链回归不超过 10% |

**S4PBT01 Objective：** 相同 fixture 至少各 10 次，记录 wall time、CPU proxy、stdout bytes、选中项目和检查数。
| 4.2.2 | `S4PBT02` | 运行并发、重复、取消、超时和临时清理压力测试 | 1.50h | 2.50% | 无孤儿进程、无共享文件冲突、无 tracked cache、数据证据完整 |

**S4PBT02 Objective：** 验证两实例并发、20 次重复、SIGTERM/CI cancellation、超时和清理。
| 4.2.3 | `S4PBT03` | 在至少两个真实代表性 PR/commit 上 shadow 对比 | 1.50h | 2.50% | 两次 legacy/candidate 判定一致；差异解释清楚；实际耗时证据存在 |

**S4PBT03 Objective：** 选择一个根治理变更和一个单项目 T0/T1 变更；只读比较，不改 required check。

## 4.3 S4PC｜激活前 Stop Gate

**Phase Pursuing Goal：** 只在等价性、稳定性、性能和回滚同时成立时允许有限激活。

**预计：** 4.0h / 6.67%；2 Task

**Phase Stop Conditions**
- 任何 P0/P1 未关闭
- 存在 false negative
- 性能数据不可复现
- 回滚未验证

**Phase Stop Gate：S4PC-GATE**
- S4 Gate 全部通过
- 获得有限激活许可
- 旧链可一键恢复

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 4.3.1 | `S4PCT01` | 执行 false-negative 与遗漏专项审计 | 2.00h | 3.33% | 零 false negative；每个跳过均有规则和测试；UNKNOWN 升级完整检查 |

**S4PCT01 Objective：** 独立审查所有候选“跳过”决定，确认无关键检查因路径分类或缓存被绕过。
| 4.3.2 | `S4PCT02` | 给出 SHIP / FIX-ONE / STOP 激活裁决 | 2.00h | 3.33% | 裁决有 owner 签署；激活范围和 rollback 开关明确 |

**S4PCT02 Objective：** 综合两轮审查、影子测试和性能数据作唯一决定；未达标不得带病激活。

# 5 S5｜受控激活、验收与连续性交接

**Parental Pursuing Goal：** 在不改变现有双平面、三个中文人类入口、完整 Roadmap 与 T0-T3 质量门禁的前提下，降低普通开发任务的重复验证、重复读取和重复写入成本，提升每单位 Token 的可验收交付吞吐率，并保证开发、验收、发布、回滚与后续 Agent 接续的连续性和稳定性。

**Stage Pursuing Goal：** 以最小 CI/文档改动激活安全快路径，完成全量回归、ROI 证明、回滚和后续 Agent 交接。

**预计：** 8.0h / 13.33%；3 Phase；8 Task

**Stage Stop Conditions**
- Required Check 身份变化
- full/nightly/release 质量下降
- 回滚不可执行
- 合并后真实运行失败

**Stage Stop Gate：S5-GATE**
- 所有验收和 ROI 指标达标
- 两次真实运行成功
- Owner 接受并可一键回滚

## 5.1 S5PA｜受控 CI 激活与文档去漂移

**Phase Pursuing Goal：** 以最小 diff 激活已证明安全的快路径，保持 Required Check 身份、权限和完整门禁。

**预计：** 3.0h / 5.00%；3 Task

**Phase Stop Conditions**
- 需要改 branch protection check name
- workflow 权限扩大
- 完整/nightly/release 门禁被删
- README 新增另一套 current truth

**Phase Stop Gate：S5PA-GATE**
- CI 最小 diff 可审查
- 回滚已演练
- 稳定文档与动态证据分离

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 5.1.1 | `S5PAT01` | 保持 workflow/check 身份不变并接入受控路径 | 1.00h | 1.67% | Required Check 名称/触发/权限不变；PR 与 push 仍 fail-closed |

**S5PAT01 Objective：** 不得重命名 Project Governance workflow/job；保留 contents:read、并发取消和 full/nightly。
| 5.1.2 | `S5PAT02` | 提供显式回滚开关或单提交回滚路径 | 1.00h | 1.67% | 回滚演练通过；旧命令可用；无数据迁移 |

**S5PAT02 Objective：** 任何异常可立即恢复 legacy-authoritative；不依赖迁移所有项目。
| 5.1.3 | `S5PAT03` | 移除 README 中易漂移的动态基线快照 | 1.00h | 1.67% | README 不再保存旧 SHA/current snapshot；没有新增平行当前文件 |

**S5PAT03 Objective：** README 只保留稳定导航和命令；当前组合状态改为 CI artifact 或按需报告。

## 5.2 S5PB｜最终回归、ROI 与 Agent 连续性

**Phase Pursuing Goal：** 验证全链质量、量化真实收益，并让下一名 Agent 无需猜测即可继续。

**预计：** 3.0h / 5.00%；3 Task

**Phase Stop Conditions**
- 全量回归失败
- ROI 只靠主观描述
- 交接需要读取历史压缩包才能理解

**Phase Stop Gate：S5PB-GATE**
- 质量回归通过
- ROI 有实测
- handoff 可独立复现

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 5.2.1 | `S5PBT01` | 运行 focused、changed-scope、full/nightly 等价回归 | 1.00h | 1.67% | 全部退出码和输出保存；无 project 业务写入；full 质量不下降 |

**S5PBT01 Objective：** 本地/CI 运行相关单元、changed-only 与手动全量模拟；EEI/arxiv 仅只读兼容。
| 5.2.2 | `S5PBT02` | 生成质量、速度、Token proxy 与 CI 重跑 ROI 报告 | 1.00h | 1.67% | 所有指标来自命令/CI；不虚构 Token；未达标项标为风险 |

**S5PBT02 Objective：** 比较前后 p50/p95、输出字节、项目 fan-out、失败可定位性和重跑原因。
| 5.2.3 | `S5PBT03` | 完成 Agent Handoff 与下一唯一 Task | 1.00h | 1.67% | 新 Agent 按 handoff 在 5 个文件内找到全部当前事实；无依赖聊天记忆 |

**S5PBT03 Objective：** 交接包含 HEAD、diff、测试、剩余风险、回滚、当前 Gate 和下一 Task。

## 5.3 S5PC｜Owner 验收、合并与短期监控

**Phase Pursuing Goal：** 作出明确发布决策，并在合并后验证两次真实运行，防止只在 fixture 中成功。

**预计：** 2.0h / 3.33%；2 Task

**Phase Stop Conditions**
- 独立审查缺失
- 合并后任一 required run 失败
- 出现项目范围外写入或新漂移

**Phase Stop Gate：S5PC-GATE**
- Owner 验收
- 两次真实运行成功
- 任务关闭且下一唯一 Task 明确

| 数字顺序 | Task ID | 名称 | 工时 | 占总工时 | Acceptance |
|---:|---|---|---:|---:|---|
| 5.3.1 | `S5PCT01` | 最终独立审查与合并决策 | 1.00h | 1.67% | P0/P1=0；合并决定唯一；PR 可独立回滚 |

**S5PCT01 Objective：** 另一审查者核对实际 diff、测试、CI、回滚和未解决风险；仅允许 SHIP/FIX-ONE/STOP。
| 5.3.2 | `S5PCT02` | 监控合并后两次真实 Governance 运行并关闭任务 | 1.00h | 1.67% | 连续 2 次成功；无新增治理噪声；开发记录/manifest 按真实结果收口 |

**S5PCT02 Objective：** 检查 push/PR 实际耗时、结果、输出和无写入；异常立即回滚。
