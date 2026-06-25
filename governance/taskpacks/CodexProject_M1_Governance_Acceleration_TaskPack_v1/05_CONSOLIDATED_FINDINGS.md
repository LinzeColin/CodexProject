# 两轮六轨静态预审：汇总问题种子

> 状态：`PARTIALLY_VERIFIED`。以下结论来自当前公开代码、工作流和文档的静态交叉检查；真实 Codex 运行、压力和并发测试仍必须在 S1/S2 由六个独立 Agent 完成。本表不得替代真实报告。

| ID | 严重度 | 阻塞合并 | 问题 | 建议修复 |
|---|---|---:|---|---|
| M1-001 | P1 | 是 | 本地脏工作树会被当前 zero_diff 直接判失败 | 改为 pre/post 状态 delta；CI 增加显式 clean-start 模式；覆盖干净、预存改动、validator 新写入和 git status 错误。 |
| M1-002 | P1 | 是 | 任何“快路径”若直接减少 semantic/enforce-sync/check-render，会产生 false negative 风险 | 先 shadow 生成候选 check plan；旧链继续判定；用合法/非法 fixture、真实 PR 和故障注入证明零 false negative。 |
| M1-003 | P1 | 是 | README 保存易漂移的动态治理基线 | README 只保留稳定导航/命令；动态组合状态放 CI artifact 或按需报告，不新增 CURRENT/SHIP。 |
| M1-004 | P1 | 是 | 根治理路径前缀会 fan-out 到全部非排除项目 | 先测量实际成本；候选分类必须 fail-closed；根契约/schema/validator/workflow 变化仍完整 fan-out。 |
| M1-005 | P1 | 是 | Required Check 身份变更会破坏分支保护连续性 | 保持 `Project Governance` workflow 和 `governance` job 不变；内部实现可影子切换；新增测试/Owner 核验。 |
| M1-006 | P1 | 是 | 活跃 EEI/arxiv 必须零写入且不能被根整改接管 | Scope Guard 比对 changed paths；只允许 read-only compatibility；任何触碰立即 STOP。 |
| M1-007 | P1 | 是 | 并发、取消和临时证据若共享路径会产生竞态和残留 | 每次使用唯一 temp/run id；原子写临时证据；取消清理；初版禁止持久缓存。 |
| M1-008 | P2 | 否/条件 | lean_governance.py 体积大，修改回归面高 | 本任务不做大重构；只抽取小型纯函数和测试；结构重构另立任务。 |
| M1-009 | P2 | 否/条件 | 当前 selected project 会统一渲染三个人类视图，是否为主要瓶颈尚未测量 | 先做分阶段耗时遥测；只有证据显示显著成本且字段影响矩阵可靠，才考虑单视图优化。 |
| M1-010 | P2 | 否/条件 | 完整机器结果直接进入 Agent stdout 会放大上下文 | stdout 仅给 compact 摘要；完整 JSON 写 runner temp/artifact；失败保留精确路径和复现命令。 |
| M1-011 | P2 | 否/条件 | 根 AGENTS.md 超过标准自身建议预算 | 不在本任务冒险删规则；先做语义等价测试，再另 Task 微缩并把细节留在 STANDARD/Skill。 |
| M1-012 | P2 | 否/条件 | GitHub Action 依赖只固定 major tag，存在供应链追踪不足 | 作为独立安全加固任务固定受信 commit SHA 并建立升级流程；不与快路径混改。 |
| M1-013 | P2 | 是 | 空值渲染为 NOT_APPLICABLE 可能掩盖 UNKNOWN | 先追踪调用点；必填/未知字段改为 UNKNOWN 或显式状态；增加信息真实性测试。若影响关键模型/验收字段则升级 P1。 |
| M1-014 | P2 | 否/条件 | 没有真实基线就不能宣称 Token/CI ROI | 按命令阶段、输出字节和 selected-project proxy 测量；只报告可观测数据。 |
| M1-015 | P1 | 是 | Git/base/diff 错误必须 fail-closed | 加入故障 fixture；任何无法可靠求 diff 的情况 BLOCKED 或升级 full changed-scope。 |
| M1-016 | P2 | 否/条件 | 手动 changed-only 还额外运行 information-quality，可能重复 | 测量和比较覆盖；仅在证明重复后合并入口，普通 PR 当前不受此额外步骤影响。 |

## 关键证据摘要

- 当前 `run_changed_only_ci` 固定调用 `--changed-only --enforce-sync --semantic`，随后对 selected projects 进行 check-render。
- 它在调用末尾把整个 `git status --porcelain` 非空直接作为失败条件，未比较调用前后 delta。
- 根治理路径前缀包含 `.agents/`、`.codex/`、workflow、`AGENTS.md`、`docs/governance/`、`governance/`、`scripts/`、`tests/governance/`。
- `governance/projects.yaml` 当前排除 `EEI` 与 `arxiv-daily-push` 的 root changed-scope fan-out。
- PR/push 运行单一 changed-only governance job；scheduled/manual all 执行完整信息质量、semantic/drift、生成视图和 attestation。
- 最近可见 Project Governance 运行约 20-24 秒；仓库存在多类其他工作流，因此总 CI 量不能全部归因于治理。
- README 的动态 snapshot SHA 已明显落后于当前观察 HEAD。

## 两轮交叉验证重点

Round 1 建立事实：是否真实存在、如何复现、影响什么。

Round 2 攻击方案：是否可绕过、是否在极限和并发下失效、压缩后是否遗忘或制造新真相源。

最终汇总必须为每项问题输出：

```text
问题
严重度
是否阻塞合并
证据状态
建议修复
必需测试
Owner 决策
```
