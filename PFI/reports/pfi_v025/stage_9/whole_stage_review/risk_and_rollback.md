
# Stage 9 整阶段风险与回滚

- 已知限制：净资产、现金和投资报告继续 blocked；消费和现金流仅 partial。不得解释成完整财务结论。
- 模型边界：真实历史/样本外验证因 ground truth 不足保持 blocked；本轮没有改模型、公式或参数值。
- 决策边界：建议只能记录人工复核状态；没有自动交易、订单创建或执行能力。
- 数据边界：证据只使用 tracked public-safe aggregate/hash；未读取真实财务行、数据库或私密金额。
- 运行边界：无头 Chrome 只使用 ephemeral loopback；未使用 Finder、LaunchServices、外部网络、安装或 push。
- 回滚：revert Stage 9 transition/evidence 提交，再依次 revert 产品整改提交 `45653bd4d57d3a4a8d6f025b5f624fed5f155d1e`、`e2a3908ee640e5392bd56450a2da75577b622c0f`、`66aaba487f8781caf4e026c170ed3ab271f98cdd` 与 `a1178bef79b982d343c4610ae7286d356214b03d`；历史 Phase 9.1/9.2/9.3 报告与证据不覆盖、不删除。
