# KMFA v0.1.4 一次性 GitHub main 上传风险登记

| 风险 | 控制 | 当前状态 |
|---|---|---|
| 把代码上传误读为业务发布 | 公开记录同时保留 `Q4 / D / NO_GO / 3-9-2-1` 和全部业务关闭门禁 | 已控制 |
| 合并后带入 raw/private 二进制或 secret | tracked suffix、raw filename、private runtime 和高信号 secret 扫描 | 已通过 |
| 远端 main 在上传前再次移动 | push 前 fetch，若远端变化则停止并重新集成、复验 | 已锁定 |
| 重复或 force push | 只授权一次 `HEAD -> main`，明确禁止 force | 已锁定 |
| 上传后本机与远端不一致 | fetch、`ls-remote` 和 remote-parity validator 三重核验 | 待推送后执行 |
| 当前 App 仍指向旧状态 | App 重装与 parity 独立到下一 phase | 明确未完成 |
