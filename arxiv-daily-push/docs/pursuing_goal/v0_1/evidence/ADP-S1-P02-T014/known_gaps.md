# Known gaps · ADP-S1-P02-T014

- **health / backfill plan 为占位**：runtime 输出携带 authority/enabled 等，health_status 取 Registry 值、backfill plan 尚未生成（Registry 有 cursor/health 字段；完整 backfill 计划属后续 S2 回填任务）。
- **seed 未应用于生产**：compiled/seed.sql 是 D1 cn_sources 的确定性 INSERT，但 T014 NOT_DEPLOYED，未应用；应用与 worker 改读 compiled/runtime.json 属后续部署任务（那时才产生 D1 写入与真部署）。
- **worker 仍读自身 REGISTRY**：本任务只生成 compiled/runtime.json，未让 worker 改为消费它；切换属后续部署任务（需保六主题 + 部署验证）。
- **validator 复用 T012**：compiler 先跑 validate_source_registry（schema + china/media 硬规则），再加 duplicate/enabled/authority 硬检查；三负例均被拦。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
