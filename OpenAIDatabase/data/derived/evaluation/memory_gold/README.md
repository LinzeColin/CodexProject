# OpenAIDatabase Memory Gold Benchmark V1

`benchmark_v1.jsonl` 是 `TSK.OpenAIDatabase.PAM1.0013` 的唯一 Gold dataset。它恰好包含 160 条合成代表性 case，八类各 20 条：`extraction`、`cross_session`、`temporal`、`update`、`abstention`、`forgetting`、`conflict`、`cross_agent`。

## 边界

- 所有 state、scope、session、agent 和 statement 均为确定性合成值；不复制真实用户记忆、raw evidence 或私有路径。
- 每条 case 都包含 state、query、双时间 `as_of`、expected IDs、answer traits、forbidden IDs、abstain conditions、aliases、noise 与 hard negatives。
- Gold curator、独立 validator 和后续 `.PAM1.0014` 被测 evaluator 是不同角色；被测算法不得生成或批准自己的 Gold。
- `human_approval_claimed=false` 是真实性边界。当前 PASS 表示独立机器 validator 通过，不冒充人工业务签字。
- JSONL 不含 literal answer 字段；expected IDs 和 traits 是最小 Gold labels。validator 禁止 query 回显 expected statement/ID、凭证形状与本机绝对路径。

## 定义来源

本数据集只借用公开论文定义来设计合成能力覆盖，不复制其数据：

- [LongMemEval](https://arxiv.org/abs/2410.10813)：information extraction、multi-session reasoning、temporal reasoning、knowledge updates、abstention。
- [FAMA](https://arxiv.org/abs/2604.20006)：惩罚使用已过时或已失效的记忆。
- [LoCoMo](https://aclanthology.org/2024.acl-long.747/)：长程会话、时间与因果依赖。

## 重建与验收

```bash
python3 -B scripts/build_memory_gold_benchmark.py --check
python3 -B scripts/validate_memory_gold_benchmark.py
python3 -B -m unittest -q tests.test_memory_gold_benchmark
```

## Required evaluation gates (PAM1.0014)

预测器只接收 `state`、`query`、`as_of`，不接收 `expected_ids`、`forbidden_ids`、`should_abstain` 等 Gold 标签。PR 使用固定 16-case fast subset；`main`、weekly schedule 与 manual dispatch 使用完整 160-case suite：

```bash
python3 -B scripts/evaluate_memory_gold_benchmark.py --suite fast --check
python3 -B scripts/evaluate_memory_gold_benchmark.py --suite full --check
python3 -B -m unittest -q tests.test_memory_gold_evaluation
```

可复现报告位于 `reports/fast_v1.json` 与 `reports/full_v1.json`。语义、workload、source hashes 会进入报告 hash；每次执行的真实 latency 另行硬判，以免时钟噪声制造报告漂移。任何指标阈值、suite 大小、CI 路由、source hash 或 tracked report 回退均 fail closed。

仅 curator 脚本可用 `--write` 重建 tracked JSONL；正常验证只读。固定 seed、schema、分布、重复/泄漏、stale/retired、abstention、alias/noise 和 hard-negative 任一门失败即非零退出。
