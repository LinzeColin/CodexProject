# PFI v0.2.5 Stage 8 Phase 8.3 实施记录

## 唯一验收目标

- Phase：`V025-S8-P8.3 无障碍与人工质感验收`
- Tasks：`S8-P3-T1`、`S8-P3-T2`、`S8-P3-T3`、`S8-P3-T4`
- Acceptance：`ACC-PFI-V025-STAGE8-WHOLE-REVIEW`
- 本轮只形成 Phase 8.3 candidate；Stage 8 整阶段独立审查和用户确认均保留到下一 run。

## 实施范围

1. `web/app/accessibility.js` 统一 route announcer、键盘路由焦点、main/heading 关联、status/alert live region 和 5 个财务/数据防误操作描述。
2. 导入确认在真实解析预览通过前保持 disabled；持仓保存/重置和设置保存/重置均绑定可解析的 `aria-describedby`。
3. `styles/tokens.css` 提供 3px 可见焦点、44px 正式控件目标、forced-colors 降级，以及旧暗色反馈样式在亮色正式 Shell 中的对比度修复。
4. 真实 Playwright/Chrome harness 审计 10 个核心 canonical 页面和 10 个重点二级页；使用 CDP `Accessibility.getFullAXTree`、真实键盘事件、WCAG 对比度/target-size 检查和 `pixelmatch` 视觉回归。
5. `axe-core` 不在本地依赖中，因此证据明确记录 `axe_core_available=false`；不伪造 axe 通过。当前门禁由可复现的本地 WCAG 2.2 AA/contrast/AX/keyboard 引擎执行。

## 真实验证

- RED：实现前专项测试 `8 failed`；失败均指向缺失的 Phase 8.3 runtime、harness 与证据。
- GREEN：20 个路由、3776 个文本样本，contrast/target/name/duplicate-id/heading/main-landmark 和防误操作阻断均为 0。
- 键盘：skip link 到 main、一级/二级路由、焦点可见且无遮挡、`Ctrl+K` 搜索、30 次 Tab 无 trap；15 个唯一焦点目标。
- AX：CDP 汇总 801 个可访问节点、14 个 heading；unnamed interactive 与 duplicate ID 均为 0，一级入口 10/10。
- 视觉：10 页面 × desktop 1440×1000/mobile 390×844，共 20 PNG；解码、尺寸和回归失败均为 0，最大 diff 7.8533%，门限 12%。
- 浏览器 console/page/HTTP/external request 均为 0；trace 删除 resource body 并脱敏。

## Release identity

新增 canonical `accessibility.js` 并修改 index/tokens，因此 frontend source 数从 19 增至 20，frontend bundle hash 重算为 `f130b7a3f2bf249151e08daa321d4a5c67130340069f1653946753fb1c62afa3`。backend sources 未变，backend build hash 保持 `499096a4762a7f1117395a209eba1ee08035180fd07ed78038e95effcbf2e65e`。版本、build id、data schema、公式版本和参数版本均不改变。

## 非目标与停止边界

- 未执行 Stage 8 whole-stage review，未记录 Stage 8 user acceptance，未进入 Stage 9。
- 本轮自动浏览器结果是正式 Shell 的工程门禁，不替代用户对“明亮、专业、有质感”的明确确认。
- 未读取或修改财务数据、数据库、模型、公式或参数。
- 未 push、未安装 PFI.app、未执行 production/final acceptance。
- 未使用 Finder 或任何 GUI 文件操作。收口回归曾意外触发一次历史测试内的 `lsregister -dump`；发现后立即中止该测试，未进行文件打开、定位、安装或 GUI 操作，且后续测试明确排除 LaunchServices 路径。

回滚以本 Phase 单一提交为边界；frontend release hash 必须与对应前端源码一起回滚，不需要数据回滚。
