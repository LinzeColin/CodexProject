# Accuracy and Robustness Design

## Core conclusion

KMFA 钉钉考勤要成为数据库和工资计算依据，关键不是让 agent 记住更多上下文，而是让每次运行都产生可重放、可比较、可验收的证据链。

## 三层准确性

### 1. Source accuracy - 原始证据准确

要求：

- 打卡结果和打卡详情都采集。
- 地点、经纬度、基准地点、轨迹点字段进入 raw + normalized。
- 每个 API 响应都有 batch、endpoint、范围、hash。
- 钉钉同步延迟导致的变化通过次月 1-5 五次夜间运行捕获。

### 2. Transformation accuracy - 派生计算准确

要求：

- raw -> normalized -> classification -> payroll baseline 的每一步都有 hash。
- 每个派生事实链接 raw IDs 和 policy version。
- 规则版本锁定后才能阶段二。
- 规则漂移阻断阶段二。

### 3. Decision accuracy - 工资基线准确

要求：

- 只有完整月份进入阶段二。
- 只有次月 1-5 夜间 run 被计入阶段二。
- 5 次 canonical snapshot hash 完全一致才通过。
- 通过后生成 Q5 证书和 payroll baseline candidate。

## Canonical hash 设计

Canonical snapshot 包含：

- target month
- policy version
- identity version
- source batch hashes
- normalized attendance day facts
- punch facts
- location and trajectory evidence summary
- exception summary
- payroll baseline candidate rows

Canonical snapshot 排除：

- run_id
- generated_at
- local path
- API request nonce
- token/signature
- transient trace IDs

## 为什么不用 majority vote

工资标准需要确定性，不适合 3/5 多数投票。5 次完全一致说明：

1. 钉钉延迟数据稳定。
2. 采集范围稳定。
3. 数据库写入幂等。
4. 规则版本没有漂移。
5. 派生逻辑是确定性的。

任意不一致都必须生成 divergence report。
