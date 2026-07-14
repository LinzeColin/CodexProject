# KMFA v0.1.4 S18-P1 精度与压力测试

## 结论

- 当前依赖：Stage 17 post-remediation review 已通过严格验证。
- 精度：金额通过/拒绝=`9/9` 与 `9/9`，float 和非整分输入均拒绝。
- 零差异：完全一致 PASS；1 分差异被阻断并要求进入差异队列。
- 重复导入：连续 3 次最终状态 hash 一致；首次写入 1198 条，后两次各识别 1198 条重复且新增为 0。
- 压力：实际内存合成 file metadata 规模 `1200`，最大耗时 `9ms`，预算 `1500ms`。
- 错误：坏文件和缺字段共 2 类 blocking error report，无静默跳过。
- raw：phase 前后、跨 Stage 17 review 与当前只读快照一致。
- 当前状态：Q4 / D / NO_GO / 3-9-2-1。

## 边界

- 本轮仅完成 S18-P1；未执行 S18-P2/P3、Stage 18 review、GitHub upload 或 app reinstall。
- 性能输入全部为内存合成 metadata，不是生产吞吐证明；未复制、备份或写入 raw。
- 下一轮只能单独执行 S18-P2 全量回归和验收。
