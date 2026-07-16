# Version Engine Spec · ADP-S2-P02-T026

版本 Diff + 模板噪声过滤 + Replay 幂等。建立在 CanonicalDocument 身份（T024，`tools/canonicalize.py`）与
DocumentVersion append-only schema（T025，`schemas/document_version.migration.sql`）之上，**决定何时向某个
canonical 文档的版本链追加新 `version_no`**。工具：`tools/version_engine.py`（确定性，无网络/时钟/随机）。

## 1. 版本触发签名（substantive signature）

一个版本是否新增，只取决于**实质签名**，与展示层无关：

```
substantive_signature(item) = {
  body_hash    : sha256( strip_noise(body + raw_html) ),   # 去模板噪声后的正文
  attachments  : sorted([ a.sha256 for a in attachments ]), # 附件内容哈希集合
  status       : lower(strip(status)),                      # active / superseded / withdrawn ...
}
content_hash(item) = "sha256:" + sha256( canonical_json(substantive_signature) )
```

- **正文 / 附件 / 状态** 任一实质变化 ⇒ `content_hash` 改变 ⇒ **追加新版本**。
- **页脚 / 导航 / 分享组件 / 阅读计数 / "X 分钟前" / cookie 横幅 / 广告标记 / 版权 / ICP 备案** 变化被
  `strip_noise` 清除 ⇒ `content_hash` 不变 ⇒ **不追加版本**。
- `doc_date` 是**随版本记录的元数据，但不进触发签名**：纯日期回流（相对时间）属噪声，而真正的再版通常同时改动
  正文/状态；把日期单独作为触发会造成版本抖动。见 `known_gaps.md`（可配置）。

## 2. Diff（版本间解释）

`diff(prev_item, new_item)` 返回 `{body_changed, attachments_changed, status_changed, substantive, noise_only}`，
用于**解释**两次渲染之间到底变了什么（正文？附件？状态？还是仅噪声）。`noise_only == not substantive`。

## 3. 版本决策与 append-only

`ingest(chain, item)`：
- 空链 ⇒ 建 `version_no=1`（`created_v1`）；
- `content_hash == chain[-1].content_hash` ⇒ **不增版本**（`skipped_no_change`，即噪声变化或精确重放）；
- 否则 ⇒ 追加 `version_no = tip.version_no + 1`（`new_version`）。
链**只增不改**（append-only，符合 T025 `UNIQUE(canonical_id, version_no)`），历史版本的 `content_hash` 永不被覆盖。

## 4. Replay 幂等（任何任务可重放）

`replay(items, times=3)`：从零把**同一序列**跑 `times` 遍，每遍产出的版本状态指纹必须**逐字一致**
（`identical == true`）。因为版本决策是 `(现链, item 内容)` 的纯函数、无时钟/随机，故任何任务可安全重放：
- 重复注入**当前 tip** 内容 ⇒ 链不增长（`skipped_no_change`）；
- 三次重放 ⇒ 相同 `version_no` 分配、相同哈希；
- CLI 连续两次 `--out` 输出字节一致。

> 注意：把文档**振荡回**某个更早的渲染（例如 withdrawn 后又出现 active 旧正文）是**真实的实质变化**，会正确地
> 追加新版本——这不是重放。重放 = 同一输入序列重跑。

## 5. CLI

```
python3 tools/version_engine.py --items items.json [--replays 3] [--out report.json]
```
`items.json`：`[{canonical_id, body, status, attachments:[{name,sha256}], doc_date?, raw_html?}]`。
输出：每个 canonical 文档的版本链、逐步 action（created_v1 / new_version / skipped_no_change）、replay 判定、summary。

## 6. 噪声规则

见 `NOISE_RULES.md`。规则保守（只清除无歧义的展示层样板），确保真实正文永不被误删；可扩展。
