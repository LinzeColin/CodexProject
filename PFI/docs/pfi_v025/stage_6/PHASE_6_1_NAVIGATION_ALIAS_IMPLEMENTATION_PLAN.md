# PFI v0.2.5 Stage 6 Phase 6.1 导航与 Alias 实施记录

## Run Contract

- 唯一任务：`S6-P1-T1..T4`
- 唯一验收：`ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS`
- 模式：`IMPLEMENT / CONTROLLED_RUN`
- 范围：一级导航、canonical route、alias redirect、responsive DOM 与对应自动化/浏览器证据
- 非范围：Phase 6.2 页面架构与内容合同、Phase 6.3 交互/历史/无障碍完整验收、Stage 6 whole-stage review、push、App install、数据库和真实财务数据
- 回滚：只 revert 本 Phase 本地提交；不重写 Stage 5、版本号、build id 或历史数据
- 停止条件：Phase 6.1 candidate evidence 与治理闭合后立即停止，不进入 `S6-P2-*`

## 来源锁定

- Roadmap SHA-256：`fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`
- Task Pack ZIP SHA-256：`591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`
- Roadmap Appendix A 是 10 个一级入口、顺序、canonical route 与 alias 的需求事实源。
- Phase acceptance ID 由项目治理分配；来源 Roadmap/Task Pack 未提供 Phase 级 `ACC-*`。

## 实施结果

| Task | 结果 | 主要证据 |
|---|---|---|
| `S6-P1-T1` | 固定 10 个一级入口及顺序 | `nav_contract.json` |
| `S6-P1-T2` | 固定 canonical route 与 7 个 alias redirect | `alias_matrix.json`, `route_registry.json` |
| `S6-P1-T3` | alias 不进入 primary/a11y/no-JS；策略实验室唯一 canonical | `alias_matrix.json`, browser validation |
| `S6-P1-T4` | desktop/mobile 共用一个 10 节点 responsive DOM，无第二套 bottom primary tree | `dom_audit.json`, desktop/mobile screenshots |

Canonical primary routes：

1. `/overview`
2. `/accounts`
3. `/ledger`
4. `/investment`
5. `/consumption`
6. `/data`
7. `/review`
8. `/reports`
9. `/market-research`
10. `/settings`

Alias normalization：

- `/home` → `/overview`
- `/market` → `/market-research/market`
- `/research` → `/market-research/research`
- `/holdings` → `/investment/holdings`
- `/strategy-lab` → `/market-research/strategy-lab`
- `/investment/strategy-lab` → `/market-research/strategy-lab`
- `/data-system` → `/settings/data-system`

## 关键决策

- desktop/mobile 共享同一 primary DOM tree，以响应式布局适配，不复制第二套节点。
- v0.2.5 route contract 优先于旧 v0.2.3/v0.2.4 route expectations；旧 `/home`、`/sources-upload` 和双 DOM 断言仅保留为 superseded diagnostic。
- 路由源修改后同步 release manifest 的实际 frontend/backend source hash；version、build id 与 git-commit binding 语义不变，未执行安装或 push。
- 浏览器只使用 ephemeral loopback 与隔离 Chrome profile；持续脱敏避免点击 rerender 后截图重新出现财务金额。

## 验收与残余

- Phase 6.1 Python contract、Stage 5 回归、Stage 1 release identity/cache、Node identity/cache 与 desktop/mobile browser navigation 均通过。
- 截图显示金额为 `已脱敏`，trace 仅保留导航和状态字段。
- 旧 route diagnostic 的九项失败与 v0.2.5 明确替换的历史行为一致，不是 Phase gate。
- 页面唯一性、内容结构、完整 browser history、键盘/a11y 与 no-JS 行为仍属于 Phase 6.2/6.3 或 Stage 6 whole-stage review，不能由本 Phase 推断完成。

## 当前结论

`ACC-PFI-V025-S6-P61-NAVIGATION-ALIAS = candidate_pass`。Stage 6 为 `4/12 in_progress`；下一唯一工作单元为 `S6-P2-T1..T4`，本轮停止。
