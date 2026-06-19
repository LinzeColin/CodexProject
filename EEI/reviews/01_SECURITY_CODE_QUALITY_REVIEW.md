# 独立审查 A：安全、代码质量、Bug、并发与可维护性

> 审查口径：本文件由一个独立审查单元形成，不引用其他审查单元的结论作为证据。严重度按 CRITICAL/HIGH/MEDIUM/LOW；“阻塞合并”区分本 Task Pack 基线与未来生产发布。

## 结论

v4.2 不应原样进入下一开发 Gate。审查发现 3 个 CRITICAL、多个 HIGH：持久化 DOM 注入、公司数据集错误复用、自动运行和模型发布竞态、浏览器执行代码与被检查代码漂移。v5 已修复可在规格/原型层解决的阻塞项；生产数据库、API、数据采集仍是生产合并阻塞项。

## 发现明细

| ID | 严重度 | 状态 | 发现 | 是否阻塞生产 | 建议/处理 |
|---|---|---|---|---|---|
| SEC-001 | CRITICAL | FIXED_IN_V5 | 操作日志将用户变更说明直接拼入 innerHTML，可形成持久化 DOM 注入 | YES | 审计时间线改为 createElement/textContent；输入长度限制与控制字符清理 |
| SEC-002 | HIGH | FIXED_IN_V5 | loadState 无 Schema、枚举、范围和类型校验 | YES | 增加 sanitizeState、白名单、数值夹取、历史和日志上限 |
| BUG-001 | CRITICAL | FIXED_IN_V5 | Microsoft/Meta 复用 NVIDIA dataset，产生事实错配 | YES | 移除数据集别名；未接入对象明确禁用并显示待接入状态 |
| TEST-001 | HIGH | FIXED_IN_V5 | 浏览器执行 embedded JS，但语法检查 external app.js，二者可漂移 | YES | 建立确定性 bundle builder 和 embedded/source byte parity 校验 |
| CONC-001 | HIGH | FIXED_IN_V5 | 模型发布按钮可重复触发多个计时器和版本递增 | YES | 发布锁、token、按钮 busy/disabled、原子完成路径 |
| CONC-002 | HIGH | FIXED_IN_V5 | Codex 自主脚本无互斥锁，重叠执行可覆盖 artifacts | YES | 目录锁、run ID、每次运行独立目录、原子兼容输出 |
| OPS-001 | HIGH | FIXED_IN_V5 | 自主运行缺少 timeout、checkpoint、信号清理与最终状态 | YES | 超时、状态 JSON、检查点、trap、仅清理自有子进程/缓存 |
| STATE-001 | MEDIUM | FIXED_IN_V5 | auditLog 和历史状态无界增长，localStorage quota 失败静默 | YES | 日志上限 100、历史上限 50、保存失败提示 |
| TRUTH-001 | HIGH | FIXED_IN_V5 | Ops 页面把 fixture 指标表达为生产服务健康 | YES | 改为原型状态、0 生产 API/管线、明确生产阻塞项 |
| A11Y-001 | MEDIUM | FIXED_IN_V5 | SVG 边声明 role=button 但无键盘激活 | YES | Enter/Space 激活与 aria-label |
| A11Y-002 | MEDIUM | PARTIAL_V5 | 详情抽屉关闭后焦点恢复不完整，缺少完整 focus trap | YES | 保存触发源并恢复；生产组件仍需 focus trap/inert |
| MAINT-001 | MEDIUM | FIXED_IN_V5 | 品牌名渗透 UI、数据库名、存储键和导出名 | YES | 中性工作名、品牌策略、自动扫描；保留单一历史迁移键 |
| ARCH-001 | CRITICAL | OPEN_PRODUCTION | 当前仍是单文件 fixture 原型，无生产数据库 | YES | 按 DDL/迁移实现 PostgreSQL，事实/证据/时间/版本分层 |
| ARCH-002 | CRITICAL | OPEN_PRODUCTION | 无生产 API、图查询、评分和刷新服务 | YES | 实现受契约约束的 API/graph query/scoring/config snapshot 服务 |
| ARCH-003 | CRITICAL | OPEN_PRODUCTION | 无真实采集、实体解析和证据管线 | YES | 先完成半导体 Golden Vertical 的端到端真实数据管线 |

## 合并判断

- **v5 Task Pack 基线：可合并**，前提是本包全部验证脚本通过。
- **生产 MVP：不可发布**，直到 ARCH-001/002/003 关闭并产生真实测试证据。
- 任何 `innerHTML` 接收外部/持久化值、任何跨公司 fixture 复用、任何没有锁和 run ID 的自主脚本，均自动恢复为阻塞状态。
