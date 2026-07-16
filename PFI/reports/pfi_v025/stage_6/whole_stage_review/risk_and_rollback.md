# Stage 6 Whole-stage Review 风险与回滚

## 风险

- 当前浏览器证据来自本机正式 Shell 的隔离 loopback，不声明已安装 PFI.app 或生产服务器 parity。
- 旧版本测试保留四项已替代预期；它们已分类，不得掩盖未来未分类失败。
- Stage 6 接受只授权进入 Stage 7，不等于 production acceptance 或 final human acceptance。

## 回滚

revert 本次单一本地 whole-review commit，保留三个 immutable Phase commits。不得改写 Git 历史、真实财务数据、数据库、远端 main 或已安装 App。
