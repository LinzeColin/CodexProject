
# Stage 8 整阶段风险与回滚

- 验收绑定 `2c7b25efd2916c909027333283b499a119d088e0` 与 `reviewed_worktree_overlay.json` 的精确内容哈希；overlay 漂移即失效。
- `axe-core` 本地不可用，`axe_results.json` 明确为 `not_run`，不伪造 axe pass；门禁绑定 deterministic WCAG 2.2 AA 与 Chrome CDP AX。
- 当前浏览器验证未加载真实财务数据，证明的是产品体验、错误预防与 fail-closed 空/阻断状态，不替代 Stage 12 真实安装/最终交付验收。
- 本 sparse/multi-project worktree 的全根 semantic command 会报告继承的其他项目/root manifest 错误；本 Gate 使用完整 Git archive + 当前 PFI source overlay 的项目治理验证与当前 PFI renderer，不能把无关根错误改写为 PFI 本轮失败或已修复。
- 历史 Phase 8.3 曾意外启动一次 `lsregister -dump` 并立即中止；本整阶段复审未调用 Finder、LaunchServices 或 GUI 文件操作。
- 回滚：revert Stage 8 whole-review 本地提交与产品整改提交；同步回滚 release manifest/frontend hash。无需数据、数据库、模型、公式或参数回滚。
