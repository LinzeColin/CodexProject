# Phase 10.2 Risk and Rollback

- 九域 registry 是 coarse-grained dependency contract。交易原始层只显式影响消费与报告指标；parameter/formula/fx/read-model 全指标影响是登记事实。未来新增指标必须先更新 registry 与对应测试，不能依赖隐式全量重算。
- `interconnection` 仍为 `blocked_economic_event_adapter`；本 Phase 只让该阻断进入 hash/DAG，不能据此宣称 economic-event adapter 或 lineage 已完成。
- 普通运行只读 SQLite 观察器使用 `mode=ro`、`query_only` 和非金额列投影。Phase acceptance 仅对空隔离 canonical schema 验证了零写入；没有读取 canonical 私有 PFI DB，也没有产生真实财务结论。
- Streamlit cache TTL 固定 30 秒且 `persist=None`。dependency snapshot 变化会改变 process key；运行中发生 drift 时 policy fail closed，需要受控重启形成新 process key，不进行后台网络刷新。
- frontend validator 已改变正式 source closure，但本 Phase 只做 Node 行为执行，不宣称可见 UI/浏览器 whole-stage acceptance。正式 UI/DB 状态一致性仍属于 Phase 10.3 与 Stage 10 整阶段审查。
- release manifest 只更新 frontend/backend source hash；build ID 和历史 git semantic binding 未改。PFI.app 仍保持未安装，唯一 canonical reinstall 留在 Stage 12。
- 未修改任何 model/formula/parameter 数值；只读取 canonical 文件 bytes 计算 hash。未输出财务值、未调用外网/Codex/LLM、未执行交易。

Rollback：先 revert Phase 10.2 证据/治理提交，再 revert 产品提交 `a64f3b51576ebe507bd65b3f5b54c5b2a3b74c41`。本 Phase 未修改真实数据库、缓存持久层或生产安装，无需数据逆向迁移；回退后重启本地进程即可恢复上一 release-cache identity。
