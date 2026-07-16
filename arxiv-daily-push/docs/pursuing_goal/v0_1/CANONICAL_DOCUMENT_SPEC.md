# CanonicalDocument 身份 · 转载归并 · 去重规则（ADP-S2-P02-T024）

> 区分同一文档、转载、附件、修订和完全不同事件。NOT_DEPLOYED：只定规则 + 工具 + fixtures，不改运行时。机器实现见 `tools/canonicalize.py`。

## 1. 身份（确定性 canonical_id）
- **有 DOI**：`canonical_id = "doi:" + 归一化 DOI`（小写、去尾标点；版本后缀如 `v2` 拆到 `revision`，主体仍归一到同一文档）。
- **无 DOI**：`canonical_id = "ttl:" + sha256(归一化标题)[:16]`（标题小写、压空白、去标点）。

## 2. 五类区分
| 类型 | 判据 | 归并行为 |
|---|---|---|
| 同一文档 | 相同 canonical_id、相同 source | 去重（不新增 document），artifact 保留 |
| 转载 repost | 相同 canonical_id、不同 source | **归并为一个 document**，`sources` 列出全部来源，**每来源 artifact 保留** |
| 附件 attachment | 同 document、不同文件（不同 sha256 R2 对象） | 挂到同 document 的 artifact 集 |
| 修订 revision | 同 DOI 主体、版本后缀不同 | 同 document，`revisions` 记录 v1/v2… |
| 完全不同事件 | 不同 canonical_id | 不同 document |

## 3. artifact 保留（关键）
- 去重/归并**只作用于 document**；每个贡献来源的**原始 artifact（R2 content-addressed 对象）逐一保留**（`artifact_keys`）。转载不丢任何一份原文。

## 4. 碰撞（collision）与可解释
- ttl 身份下若两条**归一化标题相同但实为不同文档**（罕见）→ 记入 `collisions`（含 reason + a/b + resolution）。
- 解决：优先回退到 DOI；无 DOI 时用内容 sha256（R2 键）区分。碰撞**可解释、可解决**，不静默合并异文。

## 5. 验收（tools/canonicalize.py + fixtures，见证据 test-results）
- 同文重跑不增 document（fixture + 真实 500：498 doc / 2 dup 收拢 / 0 碰撞）。
- 转载归并但 artifact 保留（fixture：nature+chinanews 同 DOI → 1 doc、2 artifact）。
- 修订同 document（fixture：DOI vN → revisions[v2]）。
- 完全不同事件 → 不同 document。
- 碰撞可解释（检测逻辑 + resolution；真实 500 = 0 碰撞）。
