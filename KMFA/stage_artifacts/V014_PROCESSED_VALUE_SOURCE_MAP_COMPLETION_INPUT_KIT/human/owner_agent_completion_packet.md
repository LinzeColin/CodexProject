# 可转发补齐包：KMFA processed value source-map completion

## 可公开事实

- 当前有 `113` 个 keep-pending target slots。
- private-only completion template 已在本机 git-ignored runtime 生成。
- public evidence 只包含 counts/status/gate，不包含原始文件、字段、表名、行列或业务值。

## 填写规则

- 每个 target slot 必须选择一个 allowed action code。
- 若选择 `supply_authorized_processed_value_fingerprint`，必须提供授权 processed value fingerprint 和依据 ref。
- 若选择 sibling mapping，必须提供可复核的 private sibling ref。
- 若无法授权，继续 `keep_pending`，不得伪造值。

## 禁止事项

- 不要把 raw 文件、Excel/PDF/zip、字段明文、表名、行列坐标或业务值放入公开仓库。
- 不要把本补齐包解释为已经完成 raw-to-processed comparison。
