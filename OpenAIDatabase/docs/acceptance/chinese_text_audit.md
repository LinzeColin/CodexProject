# Memory Atlas 中文文本审计验收

更新时间：2026-07-01

适用版本：Memory Atlas v1.1.6 Stage 0 Phase 0.1

本文件定义中文编码、文案可读性和 UI 文本承载的验收方法。它用于证明 Stage 0 Phase 0.1 的合同层已经建立，并为后续浏览器截图验收提供固定检查表。

## 1. 验收目标

Memory Atlas 的中文文本必须满足：

- 不乱码。
- 不出现未知编码残留。
- 不把英文内部字段当作用户说明。
- 不在表格、按钮、卡片中塞入长句。
- 不在低宽度视口下重叠或横向撑破。
- proposal-only 行为必须被用户看懂。

## 2. 审计对象

### 2.1 本阶段必须审计

- `docs/product/chinese_ui_quality_contract.md`
- `docs/acceptance/chinese_text_audit.md`
- `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- `功能清单.md`
- `开发记录.md`
- `模型参数文件.md`

### 2.2 后续实现阶段必须审计

- `apps/memory-atlas/src/**/*.{ts,tsx,css}`
- `data/derived/visualization/memory_atlas.json`
- browser screenshots for Overview / Galaxy / Timeline / Data Map / Search / Review / Inspector。
- exported Markdown reports。

本阶段不读取 raw/private 数据。

## 3. 异常字符检查

阻断级异常：

| 类型 | 示例 | 处理 |
|---|---|---|
| 替换字符 | `U+FFFD` | 必须修复 |
| UTF-8 mojibake | UTF-8 被错误按 Latin-1/CP1252 解码后的连续乱码片段 | 必须定位来源 |
| Latin-1 残留 | `U+00C2`、`U+00C3` | 必须修复或说明 |
| 未替换占位 | 未解释的空值或开发占位字符串 | 用户主界面禁止 |
| 调试字段裸露 | `raw_payload`、`source_ref` | 必须折叠到 Debug |

建议命令：

```bash
python3 - <<'PY'
from pathlib import Path

paths = [
    Path("OpenAIDatabase/docs/product/chinese_ui_quality_contract.md"),
    Path("OpenAIDatabase/docs/acceptance/chinese_text_audit.md"),
]
bad_chars = [chr(0xFFFD), chr(0x00C2), chr(0x00C3)]
for path in paths:
    text = path.read_text(encoding="utf-8")
    hits = [(index, ch) for index, ch in enumerate(text) if ch in bad_chars]
    if hits:
        raise SystemExit(f"{path}: forbidden mojibake characters: {hits[:5]}")
print("PASS")
PY
```

说明：开发计划或任务文档可以描述占位概念；本阶段不以全仓占位词扫描作为阻断。用户主界面占位词检查进入后续浏览器验收。

## 4. 中文 UI 检查表

| 检查项 | 阻断标准 | 当前 Phase 0.1 证据 |
|---|---|---|
| UTF-8 文档 | 新增文档必须为 UTF-8 | `file` 命令 |
| 乱码字符 | 不得出现替换字符或 mojibake | grep |
| 中文主标签 | 导航、按钮、卡片、Inspector 有稳定中文标签 | 产品合同 |
| 长摘要 | 不进入表格和按钮 | 产品合同 |
| 表格内容 | 只放短标签、数字、状态、日期 | 产品合同 |
| Inspector | 默认人类可读，Debug 折叠 | 产品合同 |
| proposal-only | 明确不直接写长期记忆 | 产品合同 |
| 低宽度视口 | 不重叠、不不可读、不横向撑破 | 后续截图验收 |

## 5. 后续浏览器验收

后续实现阶段需要补充 Playwright 或等效浏览器检查：

1. 打开 `记忆总览`。
2. 捕获桌面截图。
3. 捕获低宽度视口截图。
4. 检查主要中文标题、按钮、卡片、Inspector 标签可读。
5. 检查表格中没有长段落。
6. 检查长摘要进入展开层或 Inspector。
7. 检查 proposal-only 提示可见。
8. 检查 console 无编码相关错误。

建议视口：

- Desktop: `1440x900`
- Tablet: `768x1024`
- Mobile: `390x844`

## 6. 通过条件

Stage 0 Phase 0.1 通过需要同时满足：

1. 新增合同文件存在。
2. 异常字符扫描无命中。
3. 合同包含编码、中文主标签、文案承载、表格限制、Inspector、proposal-only、低宽度视口规则。
4. 开发记录登记本 phase 的目标、范围、风险、验收和回滚。
5. 不新增核心 UI 实现，不读取 raw/private，不直接写长期记忆。

## 7. 未通过处理

若发现乱码或不可读文本：

1. 先定位来源：文件编码、前端渲染、CSS/字体、数据快照、旧文案。
2. 能在合同层修正的，更新合同。
3. 需要实现修复的，登记到后续 Stage 0 Phase 0.2 或后续实现 phase。
4. 不得把不可读问题归因于用户操作。
