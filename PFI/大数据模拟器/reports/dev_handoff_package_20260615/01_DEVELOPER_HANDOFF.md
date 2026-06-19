# QBVS 独立交易行为验证系统交接包

生成时间：2026-06-15 20:22:30

项目根目录：`/Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system`

## 新开发者接手指南

### 主要目录

- `qbvs/`：核心验证库，含策略、指标、回测、数据、质量、bundle、handshake、CLI。
- `tools/`：一次性或阶段性报告/验证脚本。
- `runs/current_stage_bw99_random_stress_20260606/`：当前随机压力测试 campaign 状态。
- `reports/random_stress_progress_20260606/`：当前随机压力阶段报告。
- `runs/goal_readiness_audit_random_stress_50k_20260606/`：最新 readiness audit。
- `handoff/`：QuantLab ReviewOnly 证据包与握手文件。

### 推荐续跑命令

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system
PYTHONPATH=. python3 tools/run_current_stage_random_stress_campaign.py --target-paths 100000 --batch-paths 500 --max-batches 20 --days 252 --output-dir runs/current_stage_bw99_random_stress_20260606
PYTHONPATH=. python3 tools/generate_random_stress_progress_report_20260606.py
PYTHONPATH=. python3 -m qbvs.cli verify-handshake --ack handoff/quantlab_handshake_ack.json
PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-bundle --bundle-dir handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605
```

### 不要做

- 不要把 synthetic stress 结果写进 QuantLab 已审批策略库。
- 不要在 OpenD quota 未确认时运行批量历史 K 线 refetch。
- 不要把 Yahoo 公开行情等同于用户账户可交易证明。
- 不要把候选策略表述为可直接执行的投资建议。
