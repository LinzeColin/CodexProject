# Stage 12 独立整阶段初审风险与回滚

- 初审结论为 `remediation_required`：0 critical、3 important；不代表 Stage 12 通过、release freeze 或用户最终验收。
- 三项整改：runtime manifest commit 真值、exact candidate/acceptance 绑定、旧非 canonical App 的 CLI-only 隔离。
- 五项 P2 保持透明：真实 kernel sleep/wake 未执行、Holdings source 未加载、Finder 方法被用户最新指令覆盖、axe-core 不可用、6 项历史状态测试债务。
- 本轮不修改 canonical private DB，不安装 App，不调用 Finder/LaunchServices/open/AppleScript/GUI，不访问外部网络，不 push。
- 回滚：revert 本轮初审 commit；初审只新增 review 证据与状态记录，candidate `9a7245acf` 本身保持不变。
