# v0.1.4 最终整体复审 Findings

- `V014-FINAL-REVIEW-F01` [high/fixed]：S10 post-review checker 永久要求 VERSION 和 HANDOFF 停在历史 active phase。 处理：永久校验 profile，只有 S10 为 active phase 时才校验当前路由。
- `V014-FINAL-REVIEW-F02` [medium/fixed]：S17 post-review test 永久要求 HANDOFF 下一步为 S18-P1。 处理：只在 S17 review 为 active phase 时校验旧路由。
- `V014-FINAL-REVIEW-F03` [high/fixed]：S14 三个 generator-backed test 会覆盖固定公共证据并污染后续测试。 处理：新增公共证据快照 helper，在异常和 tearDown 后恢复原状态。
- `V014-FINAL-REVIEW-F04` [validation/fixed]：system Python 缺少工作簿/PDF依赖且 cryptography ABI 不兼容，形成无效失败基线。 处理：最终全量验收固定使用 Codex bundled Python 3.12 runtime。
- `V014-FINAL-REVIEW-F05` [control/passed]：18 个 current Stage review validator 必须全部复跑。 处理：S01-S08 original 与 S09-S18 post-remediation 双链缓存复跑 18/18 PASS。
- `V014-FINAL-REVIEW-F06` [control/passed]：完整测试套件必须使用有效 runtime 顺序执行。 处理：bundled Python 顺序全量测试全部通过。
- `V014-FINAL-REVIEW-F07` [control/passed]：测试生成物不得伪装成最终变更。 处理：全量测试后恢复固定路径副作用，仅保留真实修复。
- `V014-FINAL-REVIEW-F08` [control/passed]：raw 在最终复审前后必须完全一致。 处理：私有前后、跨 S18 review 和 fresh 快照一致，不复制或修改 raw。
- `V014-FINAL-REVIEW-F09` [control/passed]：HTML 人类流程审计必须保持无警告无失败。 处理：6 文件、54 行、54 PASS、0 WARN、0 FAIL。
- `V014-FINAL-REVIEW-F10` [control/passed]：复审通过不得关闭未解决业务差异。 处理：Q4/D/NO_GO 与 3-9-2-1 结构保持不变。
- `V014-FINAL-REVIEW-F11` [control/passed]：历史 overall review 和旧 upload 状态不得作为当前权威状态。 处理：两份历史 evidence 仅作结构基线，动态和上传状态均非权威。
- `V014-FINAL-REVIEW-F12` [control/passed]：代码上传 readiness 不得被解释为业务 release GO。 处理：只开放下一独立 public-safe code upload phase，业务交付、App重装和执行保持关闭。
- `V014-FINAL-REVIEW-F13` [high/fixed]：S18 post-review checker 和 focused test 永久锁死旧 VERSION、HANDOFF、AGENTS 与 ASSURANCE 动态总数。 处理：历史 profile、formula、parameter 和 evidence 永久校验；current pointer、路由、snapshot 时间和动态总数仅在 S18 review active 时校验。
- `V014-FINAL-REVIEW-F14` [critical/fixed]：历史 tracked KMFA 文件仍引用本机 raw 实际文件名；第一次别名修复的治理事件还出现历史行重排和 files_changed 覆盖不足。 处理：只在 tracked KMFA 内替换为稳定 public-safe source IDs，恢复治理 JSONL 原顺序后仅追加当前事件，并完整登记别名修复文件；raw 未写入，名称复扫与 governance-sync 均通过。
