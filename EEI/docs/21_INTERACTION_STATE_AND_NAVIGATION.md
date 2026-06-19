# 21 - 交互状态、导航与递归探索

## 1. 节点状态机

```text
idle -> hover/focus -> selected -> inspecting -> pivoting -> focused
```

- `selected` 只改变右侧详情，不立即重绘图。
- 用户主动点击“以它为中心”后才进入 `pivoting`。
- 切换成功后更新 current subject、breadcrumb、URL 和本地/数据库会话。
- 失败时保留原图并显示可恢复错误，不出现空白画布。

## 2. 递归切换继承规则

| 状态 | 默认继承 | 用户可覆盖 |
|---|---|---|
| 分析视角 | 是 | 是 |
| 时间快照 | 是 | 是 |
| 关系过滤 | 是 | 是 |
| 分数/分析偏好 | 是 | 是 |
| 固定节点 | 仅保留仍相关节点 | 是 |
| 选中节点 | 重置为新主体 | 否 |
| 画布布局 | 保持方向与语义位置 | 是 |
| breadcrumb | 追加 | 可返回任一点 |

## 3. 历史与撤销

- 浏览器返回/前进与应用 breadcrumb 行为一致。
- “返回上一个主体”只回退研究中心，不撤销 Watchlist 或模型设置。
- Watchlist、权重、备注和保存视图变更提供显式撤销或版本回滚。
- 任何自动布局都不得改变数据状态。

## 4. 搜索

搜索结果按公司、子公司、品牌、设施、行业、人物、基金和主题分组。结果行显示对象类型和主行业，避免同名误选。选择结果后先打开局部图，不直接加载全局网络。

## 5. 语义缩放

- 缩小时把同类对象合并为业务/供应链阶段组。
- 放大时逐层显示公司、设施、产品和证据。
- 缩放不改变关系集合；展开才会请求新数据。
- 用户可在列表模式中查看当前被聚合的所有对象。

## 6. 持久化键

`workspace_mode`, `focus`, `selected_object_id`, `visual_lens`, `semantic_zoom_level`, `as_of`, `filters`, `pinned_object_ids`, `comparison_object_ids`, `history`, `viewport`, `sidebar_collapsed`, `inspector_open`, `timeline_open`, `saved_view_id`。
