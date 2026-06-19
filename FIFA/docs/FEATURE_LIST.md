# TAB FIFA 盘口研究系统功能清单

## 当前可用

| 模块 | 功能 | 当前状态 |
| --- | --- | --- |
| 本地网站入口 | `http://127.0.0.1:8767/` 决策工作台 | 可用 |
| Downloads App | `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app` | 可用 |
| 推荐下注板块 | 展示时间、板块、盘口、下注、赔率、金额、EV、Edge、套利率、Risk of ruin、置信度、市场资金倾向分 | 可用但执行金额 AUD 0 |
| 市场资金分析 | 总资金/净资金/成交量/流动性/盘口深度/日均盘口变动率的公开盘口代理指标 | 可用，非真实成交资金 |
| 主动测试与自动补缺 | 检查每天至少 4 次分析和 1 份日报；先显示缓存，再返回实时结果 | 可用，正式补跑受 raw gate 阻断 |
| Research-only 日报 | raw 不完整时生成研究诊断 PDF/JSON/MD | 可用但不等于正式下注日报 |
| Raw 合规状态 | TAB 拒绝 AI controlled access 时 fail-closed | 可用 |
| 授权 odds provider raw | The Odds API / OpticOdds 的 TAB-labeled odds staging、coverage manifest、人工 TAB final verification gate | The Odds API Matches 已实测；OpticOdds 1010 阻断 |
| Provider TLS fallback | 本机 Python CA 缺失时自动使用 certifi CA bundle 重试 The Odds API，且不关闭 TLS 验证 | 可用 |
| Provider 配置医生 | 检查 ignored provider env、key 是否存在、Unknown Sport 防护、旧 sport key、credit-safe event probe 参数，并输出 PDF/JSON/MD | 可用，当前 `ready`；本机 ignored env 已收敛到 `soccer_fifa_world_cup` |
| Provider historical merge 防倒退 | Team Total 小批量 probe 不会让历史 Total O/U 覆盖倒退 | 可用，当前 Result 68/68、Total O/U 55/68、Team Total 0/68 |
| Provider 运营决策层 | 根据小样本 provider evidence 和 credit 预算，判断继续 probe、暂停、转人工或官方访问 | 可用，当前 Team Total 为人工/官方访问优先 |
| Public Raw Snapshot 导入 | 导入用户或外部工具导出的 Matches JSON，生成 research-only preview raw、hash、PDF/JSON/MD 状态 | 可用，当前 waiting_for_snapshot_import，不解锁正式发布 |
| Public Snapshot 发布预检 | 生成签名模板，校验 snapshot hash、preview raw hash、operator、source note 是否匹配 | 可用，当前 waiting_for_snapshot_import，未通过不发布 |
| Public Snapshot Raw 发布命令 | 签名预检通过后显式发布 Matches raw slot，输出 publish JSON/MD/PDF 状态 | 可用，当前 blocked_publish_preflight，不写 batch manifest，不解锁下注 |
| Team Total 人工校验队列 | 将 provider 无法覆盖的 Team Total 转成候选级人工校验任务，输出 PDF/JSON/MD | 可用，队列 68 场，高优先级 55 场 |
| Team Total 人工导入闭环 | 生成 CSV 模板、成对 Over/Under 模板、读取人工填写文件、校验 Over/Under 成对完整性、输出完成度和错误行 | 可用，当前导入缺失 0/68；全量成对模板 136 行 |
| Team Total 人工校验工作台 | 将 68 个候选拆成批次，显示下一批、剩余高优先级、操作清单、成对模板入口和 gate 快照 | 可用，9 个批次，下一批 TT-001；下一批成对模板 16 行 |
| Team Total 人工 Hash Gate | 对人工导入 CSV 的规范化完整候选生成 sha256 和签名前置草案 | 可用，当前 waiting_for_import |
| Team Total Overlay 预览 | 将通过结构校验的人工 Team Total CSV 合入 preview-only raw，输出 overlay PDF/JSON/MD 和 preview raw | 可用，当前 waiting_for_import，overlay 0/68 |
| Team Total Overlay 发布预检 | 生成签名模板，校验人工签名是否匹配 refresh/board/manual hash/overlay raw hash | 可用，当前 waiting_for_import，未通过不发布 |
| Team Total Overlay Raw 发布命令 | 签名预检通过后显式发布 Matches raw slot，输出 overlay publish JSON/MD/PDF 状态 | 可用，当前 blocked_overlay_publish_preflight，不写 batch manifest，不解锁下注 |
| Live 合规状态 | live discovery access-policy blocked 时 fail-closed | 可用 |
| 可用板块策略 | 判断 4/5 可研究板块和 1/5 不可用板块 | 可用 |
| 持仓监控 | My Bets 只读 bootstrap、私有快照导入合约、收益率字段 | 合约可用，真实持仓需登录授权 |
| 报告下载 | 业务 PDF、JSON、Markdown 和 latest artifact 索引 | 可用 |
| GitHub continuity | `https://github.com/LinzeColin/FIFA` 主仓库同步 | 可用 |
| app 图标 | `Research Compass` macOS icon | 可用 |

## 严禁行为

- 不自动下注。
- 不点击赔率。
- 不加入 Bet Slip。
- 不提交投注单。
- 不保存 TAB 密码、OTP、session secret。
- 不使用 headed fallback、CAPTCHA bypass、fingerprint spoofing、stealth browser 去绕过 TAB public raw 拒绝。

## 未完成

| 模块 | 缺口 | 为什么重要 |
| --- | --- | --- |
| Team Total provider coverage | The Odds API TAB sample 不支持，OpticOdds 当前 1010 阻断；人工导入闭环、overlay 预览和发布预检已可用但还没有人工数据 | 需要 OpticOdds 官方访问/白名单或填写 `manual_verification/provider_team_total_manual_verification.csv` |
| Team Total 真实导入与签名 | 显式 overlay publish 命令已可用，但当前没有人工 CSV 与 approval 文件 | 需要填写 `manual_verification/provider_team_total_manual_verification.csv` 并保存匹配的 `manual_verification/provider_team_total_overlay_approval.json` |
| Public Snapshot 真实导入与签名 | 显式 publish 命令已可用，但当前没有真实 snapshot 与 approval 文件 | 需要把有效 Matches JSON 放入 `manual_verification/public_raw_snapshots/` 并保存匹配的 `manual_verification/public_snapshot_import_approval.json` |
| Australia Markets | 当前 route mismatch/unavailable | 阻塞 5/5 板块覆盖 |
| My Bets 授权读取 | 需要用户在本机登录授权 | 阻塞持仓金额、累计收益率、真实 bankroll 动态更新 |
| 完整正式 automation | raw/private/preflight 未全通过 | 不能每日发布可执行下注研究报告 |
| 概率工程深层模型 | 部分 xG/MCMC/Monte Carlo 仍是规划或代理层 | 报告中不能夸大为生产级完整模型 |
