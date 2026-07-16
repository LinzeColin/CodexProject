# PFI v0.2.5 Stage 8 整阶段审查

## 唯一执行合同

- Contract：`PFI-V025-STAGE8-WHOLE-REVIEW`
- Acceptance：`ACC-PFI-V025-STAGE8-WHOLE-REVIEW`
- Review base：`2c7b25efd2916c909027333283b499a119d088e0`
- 范围：只复核 Stage 8 的 12/12 tasks、三笔 immutable Phase commits、产品整改 overlay、当前内容浏览器证据、治理与 transition acceptance。
- 停止边界：Stage 9 本轮保持 `not_started`；不 push、不安装、不执行 production/final acceptance。

## 整改后的产品事实

1. 非首页不再复用首页六问卡；10 个核心 workspace 使用真实 DOM 形成 status board、balance sheet、review table、portfolio analytics、spending flow、data pipeline、decision inbox、report library、research workspace、control center 十类差异化结构。
2. 全局 click feedback 只提供 pressed/ripple，不再用 180ms timer 自动宣告 progress/success；延迟 503 的实际浏览器回归证明失败不会被自动成功覆盖。
3. 持仓软删除在持久写入前要求显式确认并可取消；所有正式交互 target 统一为 44px。
4. durable job 的 sessionStorage 只保存 id/state/timestamps/completedUnits/totalUnits，不保存任意 label 或 stageLabel。
5. 当前整改内容覆盖 10 个核心与 10 个不同二级路由、desktop/mobile 共 40 张截图；键盘二级流程为 `/accounts/reconcile`，Chrome CDP AX 与 WCAG 审计均覆盖 20 个唯一路由。

## Pass Gate 证据

- 亮色与 token：`design_tokens.json`，暖白/浅灰默认、蓝/绿/金语义色、10 类 token family。
- 动效与反馈：`reduced_motion.json` 与 `motion_feedback/browser_validation.json`，100/300/1000/10000ms 预算、220ms 上限、reduced-motion 0ms、View Transition 渐进增强、haptic/sound 显式 opt-in。
- 无障碍：`keyboard_flow.json`、`contrast_results.json`、`final_browser/accessibility_tree.json`、`final_browser/error_prevention_audit.json`。
- axe 事实：本地 `axe-core` 不可用，`axe_results.json` 必须保持 `not_run` / `axe_pass_claimed=false`；不伪造 axe pass，绑定 deterministic WCAG 2.2 AA 与 Chrome CDP AX substitute。
- 视觉与响应式：`visual_acceptance.json`，20 唯一路由 × 2 viewport = 40 PNG，near-black ratio 最大值 0，正式 desktop/mobile 布局，无手机样机。
- Release：`release_identity_binding.json` 绑定产品整改提交、canonical/embedded manifest 与 frontend/backend hash。

## 审查、授权与边界

- 初审为 code/security `C1/I4/M1`、governance/renderer `C0/I8/M0`、acceptance/evidence `C3/I2/M1`；所有真实 P0/P1 与高价值 P2 已在产品整改提交关闭。最终结果必须由三位独立 reviewer 同时绑定 `reviewed_worktree_overlay.json` 与 `reviewed_evidence_overlay.json`，并返回 `ACCEPT C0/I0/M0`；空 verification、重复/额外 reviewer 或任一 evidence hash 漂移均 fail closed。
- Phase 8.2 的跨层治理/release/compatibility 文件超出窄 deliverable 名称，`scope_override.json` 明确记录 `allowed_files_obeyed=false` 与用户在最终验收前的统一授权；immutable Phase commits 不改写。
- 用户站立授权仅用于 Stage 8 transition 和 Stage 9 entry，不等于 production/final acceptance，也不代表 Stage 9 已开始。
- 本 sparse/multi-project worktree 的全根 semantic command 会报告继承的其他项目/root manifest 错误；本 Gate 以完整 Git archive + 当前 PFI source overlay 的项目验证和当前 PFI renderer 为 changed-scope 证据，不声称修复无关根问题。
- 本整阶段审查未使用 Finder、LaunchServices 或 GUI 文件操作。历史 Phase 8.3 曾意外启动一次 `lsregister -dump` 并立即中止，保留为真实历史事件，不改写成“从未发生”。
- 未加载或修改财务数据，未修改数据库、模型、公式或参数值；网络仅为本机 ephemeral loopback，无外部网络。

## 回滚与下一步

回滚以 Stage 8 whole-review 本地提交和产品整改提交为边界，同时恢复匹配的 frontend release identity；无需数据回滚。只有本 Gate 通过后，下一工作单元才是 `S9-P1-T1` / `ACC-PFI-V025-STAGE9-WHOLE-REVIEW`，且必须在新 run 执行。
