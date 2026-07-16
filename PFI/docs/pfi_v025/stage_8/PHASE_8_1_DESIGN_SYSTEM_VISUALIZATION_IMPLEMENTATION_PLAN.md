# PFI v0.2.5 Stage 8 Phase 8.1 实施记录

## 唯一验收目标

- Phase：`V025-S8-P8.1 设计系统与可视化`
- Tasks：`S8-P1-T1`、`S8-P1-T2`、`S8-P1-T3`、`S8-P1-T4`
- Acceptance：`ACC-PFI-V025-STAGE8-WHOLE-REVIEW`
- 本轮结果只证明 Phase 8.1 candidate pass；Stage 8 整体仍为 `in_progress`。

## 实施范围

1. 在 `web/styles/tokens.css` 建立显式亮色默认的颜色、间距、字体、圆角、阴影、焦点、状态、图表和层级 token。
2. 在 `web/app/components/designSystem.js` 从既有 10 项 canonical 导航树绑定 10 种页面 archetype，不创建第二份路由事实源。
3. 为趋势图补充 `empty/error/stale/ready` 状态、可读状态文本、canvas `role=img`、`aria-label` 和 `aria-describedby`；空/错状态隐藏 canvas，不绘制假线。
4. 实现 1440px desktop、1180px compact desktop、780px mobile 和 480px compact mobile 正式布局；移动导航复用 canonical primary entry click path，不展示手机样机。
5. `index.html` 只增加 Phase marker 和组件挂载；业务数据、公式、参数、数据库与 runtime API 均不改变。

## 视觉方向

- 默认背景：暖白/浅灰；主信息使用深墨色，蓝色用于导航/信息，绿色用于成功，金色用于注意，红色用于风险。
- 组件使用克制的 6–10px 圆角、1px 边框和 1–2px 小阴影；不使用玻璃拟态、渐变文字、宽泛阴影或装饰性动效。
- 页面原型分别为：status board、balance sheet、review table、portfolio analytics、spending flow、data pipeline、decision inbox、report library、research workspace、control center。
- 图表颜色不是唯一编码；状态同时由文本、图例和端点标签表达。

## 真实验证

- Python contract：亮色 token、对比度、10 archetype、图表四状态、响应式与证据边界。
- Playwright + local Chrome：10 路由 × desktop/mobile 共 20 个正式视口。
- 浏览器 OS color scheme 强制为 dark，验证产品计算结果仍是 light。
- 每个路由使用独立 browser context，避免跨页 compositor layer 污染；PNG 逐张 RGB decode，最终黑像素文件数为 0。
- 外部请求被阻断；只允许临时 `127.0.0.1` loopback；不加载个人财务数据。
- Playwright trace 删除 resource body，并脱敏绝对本地路径后才进入 tracked evidence。

## Release identity 例外

`tokens.css`、`designSystem.js` 和 `index.html` 都属于已发布前端 bundle，因此同步更新 `config/release_manifest.json` 与 embedded manifest 的 `frontend_bundle_hash`。版本、build id、backend hash、公式版本和参数版本不改变。

## 非目标与停止边界

- 未开始 Phase 8.2 动效/进度/触感。
- 未开始 Phase 8.3 accessibility automation 与用户阶段验收。
- 未开始 Stage 8 whole-stage review。
- 未 push、未安装 PFI.app、未执行 production 或 final human acceptance。
- 未使用 Finder、LaunchServices 或 GUI 文件操作。

项目根 `PRODUCT.md` 当前描述 Memory Atlas，不是 PFI 产品合同；本 Phase 只以 v0.2.5 Roadmap、Task Pack、PFI governance 与当前正式 Shell 为依据。
