# 大数据模拟器 Agent Handoff

默认先读：

1. `README.md`
2. `HANDOFF.md`
3. `BACKUP_MANIFEST.md`
4. `QUANTLAB_INTEGRATION_CONTRACT.json`
5. `HANDSHAKE_PROTOCOL.json`
6. `handoff/qbvs_resume_after_quantlab_ack_20260605.md`

## 当前边界

- 产品名：大数据模拟器。
- 历史名：QBVS / Quant Behavior Validation System。
- Python package：`qbvs`，暂不重命名，避免破坏 CLI、测试和 QuantLab adapter。
- 角色：PFI 的外部大规模策略模拟、随机压力测试、行为策略验证和 QuantLab ReviewOnly 证据包生成层。
- 禁止：实盘交易、自动下单、写 QuantLab 数据库、写 approved strategy library、保存交易账号密码或 secrets。

## S5PCT01 Structure Boundary

- Active runtime and algorithm code lives under `qbvs/`; this task does not
  rewrite strategy, backtest, cache, warehouse, or QuantLab adapter behavior.
- `config/` is the input/config layer and `tests/` is the verification layer.
- Root contracts (`QUANTLAB_INTEGRATION_CONTRACT.json`,
  `HANDSHAKE_PROTOCOL.json`, `HANDOFF.md`, `BACKUP_MANIFEST.md`) define
  interoperability and recovery, not active algorithm implementation.
- Date-stamped scripts under `tools/` are report/handoff generators. They may
  call `qbvs/`, but S5PCT01 keeps them in place and treats them as non-default
  runtime entry points.
- `runs/` and `reports/` are output/evidence layers. They are not source truth
  for active algorithms and should not be imported as default runtime inputs.

## 本机项目落地规则

- 用户要求后续 Codex project 统一落在 `/Users/linzezhang/Downloads/CodexProject`。
- 当前发现的实际目录名是 `CodexProject`，不是 `CodexProjet`；不要新建错拼目录。
- `/Users/linzezhang/Downloads/CodexProject` 当前不是 git repo，不要在其中直接 `git init` 污染资料目录。
- 如果需要新的长期项目根，先确认是否要把 GitHub checkout 迁移到该目录；不要默认在 `Documents/Codex` 下新建长期开发项目。

## 继续开发命令

```bash
cd PFI/大数据模拟器
PYTHONPATH=. python3 -m pytest tests -q
PYTHONPATH=. python3 -m qbvs.cli list-strategies --limit 20 --output runs/strategy_catalog.csv
PYTHONPATH=. python3 -m qbvs.cli verify-handshake --ack handoff/quantlab_handshake_ack.json
```

## 数据恢复原则

- GitHub 只保存可维护资产、handoff、配置、源码、测试和轻量状态摘要。
- 大体量 runtime 数据不进 Git：`data_cache_*`、`runs/*/`、`campaigns/`、`warehouse/`、`warehouse_smoke/`、SQLite。
- 若需要恢复完整历史运行数据，先查看 `BACKUP_MANIFEST.md` 的排除清单和原本机路径记录。
