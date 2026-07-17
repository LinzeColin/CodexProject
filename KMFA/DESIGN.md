---
name: KMFA 经营分析系统
description: 面向管理层与财务人员的可信中文经营分析工作台
colors:
  business-navy: "#102F50"
  action-blue: "#17679B"
  action-blue-deep: "#114B74"
  action-blue-soft: "#EDF6FB"
  page-cool: "#F3F6F8"
  surface: "#FFFFFF"
  text-primary: "#152331"
  text-muted: "#5E6D79"
  divider: "#CFDAE3"
  success: "#147A4A"
  danger: "#A62E2E"
  warning-ink: "#7A4B00"
  dark-page: "#0B1723"
  dark-surface: "#102638"
  dark-text: "#F2F7FA"
  dark-primary: "#6BC2F2"
typography:
  headline:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif'
    fontSize: "25px"
    fontWeight: 700
    lineHeight: 1.3
  title:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif'
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif'
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.4
rounded:
  sm: "6px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "9px 14px"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-deep}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "9px 14px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.action-blue-deep}"
    rounded: "{rounded.sm}"
    padding: "9px 14px"
  status-chip:
    backgroundColor: "{colors.action-blue-soft}"
    textColor: "{colors.action-blue-deep}"
    rounded: "{rounded.pill}"
    padding: "4px 8px"
motion:
  fast: "100ms"
  standard: "160ms"
  deliberate: "220ms"
  reducedMotion: "1ms"
---

# Design System: KMFA 经营分析系统

## 1. Overview

**Creative North Star: “可信经营台”**

KMFA 的界面像一张经过整理的经营工作台：可靠、克制、信息紧凑，先帮助用户完成判断和处理，再提供专业证据。视觉设计服务于任务，不制造表演感；用户应当迅速分辨层级、状态、影响和操作。

系统拒绝技术控制台、字段或哈希墙、日志浏览器、营销落地页、装饰性卡片陈列、巨大告警色块，以及必须依赖颜色才能理解的状态。业务蓝用于导航、焦点和主要动作，状态色只出现在小型徽标、图标和文字中。

**Key Characteristics:**

- 中文优先，机器细节后置
- 商务蓝主导，状态色克制
- 表格和工作区紧凑但清晰
- 标准控件、明确反馈、可键盘操作
- 后端事实只读，流程动作可追溯

## 2. Colors

主色为稳重的深海军蓝与业务蓝，背景使用冷白和浅蓝灰；状态色只承担局部语义。

### Primary

- **经营海军蓝** (`#102F50`)：侧栏、一级标题和关键层级锚点。
- **行动业务蓝** (`#17679B`)：主要按钮、当前选择、链接和焦点关联元素。
- **深行动蓝** (`#114B74`)：主要动作的悬停和按下状态。
- **浅行动蓝** (`#EDF6FB`)：选中行、轻量提示和次级交互背景。

### Neutral

- **冷灰页面** (`#F3F6F8`)：页面底色。
- **白色工作面** (`#FFFFFF`)：表格、工具栏和详情工作区。
- **主文本** (`#152331`)：正文与数据。
- **辅助文本** (`#5E6D79`)：说明、时间和次要信息。
- **分隔线** (`#CFDAE3`)：表格、输入框和区域边界。

### Named Rules

**小面积状态色规则。** 成功、警告和失败色只用于状态徽标、符号、图标和短文字，不得铺满卡片、整行或大面积背景；任何状态必须同时有文字和符号。

## 3. Typography

**Display Font:** 系统无衬线字体栈
**Body Font:** 系统无衬线字体栈

**Character:** 使用用户设备原生的中文无衬线字体，稳定、清楚、加载快。字号差异克制，用字重、留白和边界建立层级。

### Hierarchy

- **Headline** (700, 25px, 1.3)：页面主标题，每页一个。
- **Title** (700, 18px, 1.4)：工作区、详情和分组标题。
- **Body** (400, 14px, 1.6)：正文、表格内容和说明；长说明控制在 70 个中文字符左右的可读宽度。
- **Label** (700, 12px, 1.4)：表头、徽标、字段名和短提示。

### Named Rules

**中文任务优先规则。** 按钮、表头和默认详情使用普通中文；内部代码、英文状态和长路径只能放入专业详情或开发证据。

## 4. Elevation

系统以边框和浅色层级为主，阴影只用于需要从页面脱离的抽屉、弹层或悬浮提示。静态卡片和表格默认无重阴影，避免形成装饰性卡片墙。

### Shadow Vocabulary

- **浮层阴影** (`box-shadow: 0 18px 48px rgba(16,47,80,.18)`): 仅用于详情抽屉或受控弹层。
- **轻提示阴影** (`box-shadow: 0 8px 24px rgba(16,47,80,.10)`): 仅用于临时提示或窄幅悬浮菜单。

### Named Rules

**静态平面规则。** 静态工作区靠边框、间距和背景分层；没有交互或遮挡关系时不添加阴影。

## 5. Components

### Buttons

- **Shape:** 小圆角 (`6px`)，不使用胶囊形主按钮。
- **Primary:** `#17679B` 背景、白字、`9px 14px` 内边距，只用于当前最重要动作。
- **Hover / Focus:** 悬停变为 `#114B74`；键盘焦点使用清晰的 3px 蓝色外轮廓，不靠阴影猜测。
- **Secondary / Ghost:** 白底蓝字、1px 分隔线；次要动作不与主按钮竞争。

### Chips

- **Style:** 胶囊形只用于状态和筛选，紧凑到 `4px 8px`；文字与符号必须同时出现。
- **State:** 未选中使用白底和边框，选中使用浅业务蓝；失败、警告、成功只更换小面积颜色。

### Cards / Containers

- **Corner Style:** `6px–8px`，不使用夸张圆角。
- **Background:** 页面为 `#F3F6F8`，工作面为白色。
- **Shadow Strategy:** 静态内容无重阴影，参照 Elevation。
- **Border:** 1px `#CFDAE3`。
- **Internal Padding:** 紧凑区 `12px–16px`，主要工作区 `20px–24px`。

### Inputs / Fields

- **Style:** 白底、1px 分隔线、`6px` 圆角，标签始终可见。
- **Focus:** 边框变为业务蓝并显示 3px 半透明外轮廓。
- **Error / Disabled:** 错误同时显示文字原因；禁用态降低对比但仍保持可读，并说明为何不可用。

### Navigation

桌面端和窄屏都使用七项横向顶部导航：经营首页、项目、回款、资金、税务与政策、数据更新、报告。窄屏允许横向滚动，不使用旧版堆叠侧栏。活动项同时使用背景、文字、底部标记和 `aria-current` 表达。

### Component States

按钮、表单、筛选、表格、信息区块、图表、弹窗、抽屉、提示、空状态和状态徽标都必须覆盖默认、悬停、焦点、禁用、加载、错误和成功七种状态。无可见反馈的控件不得上线；错误必须同时说明原因和修复动作。

### Light and Dark Themes

浅色主题是默认，使用冷灰页面、白色工作面、深海军蓝导航和业务蓝操作。深色主题是可选显示方式，使用 `#0B1723` 页面、`#102638` 工作面、`#F2F7FA` 正文和 `#6BC2F2` 操作蓝。两种主题共用相同的信息层级、状态含义和操作位置，不能因切换主题丢失内容。

### Motion

动效只用于方向、状态变化和操作反馈。快速反馈为 100ms，标准变化为 160ms，抽屉等方向变化最长 220ms；不得循环播放、不得使用布局动画、不得阻塞操作。系统开启“减少动态效果”时，过渡缩短为 1ms 且内容不能丢失。

### 检查板矩阵

首列保持层级缩进和展开控件，表头在滚动时固定；状态、影响和下一步是优先列。点击状态打开右侧详情工作区，返回后保留搜索、筛选、展开项、滚动位置和键盘焦点。

## 6. Do's and Don'ts

### Do:

- **Do** 使用 `#102F50`、`#17679B`、白色和浅蓝灰建立稳定的经营工作台。
- **Do** 用普通中文同时说明状态、影响、负责人和下一步。
- **Do** 保持 6px–8px 圆角、1px 边框和清晰的 3px 键盘焦点。
- **Do** 让表格、筛选、详情和返回流程在窄屏与放大文字下仍可使用。
- **Do** 把机器字段和内部证据放在折叠的专业详情中。

### Don't:

- **Don't** 把默认界面做成技术控制台、字段或哈希墙、日志浏览器。
- **Don't** 使用营销落地页式巨型标题、装饰性卡片陈列或无任务意义的动效。
- **Don't** 使用巨大黄色、红色或绿色背景表达状态；状态色不得铺满卡片、整行或大面积区域。
- **Don't** 只用颜色表达状态，或让普通用户先理解英文内部状态和技术编号。
- **Don't** 让界面按钮直接把后端失败状态改成“已通过”。
