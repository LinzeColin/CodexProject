# Entity Registry

- Schema: `QuantLabEntityRegistryV1`
- Generated At: `2026-06-07T08:31:14`
- Record Count: `28`
- Status Counts: `{"MissingSymbol": 8, "ProxyMapped": 20}`
- Market Counts: `{"CN": 28}`

## Status Meaning

- `TradableSymbol`: 持仓已有可直接查询行情的确认代码。
- `ProxyMapped`: 持仓没有确认代码，但已映射到研究代理标的；只能用于研究代理，不等于真实持仓。
- `MissingSymbol`: 缺少确认代码且没有代理，禁止进入回测、情绪分析和热点分析。

## Records

| Name | Market | Canonical Symbol | Status | Confidence | Reason |
| --- | --- | --- | --- | --- | --- |
| 前海开源沪港深核心资源灵活配置混合C | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 华夏中证AH经济蓝筹股票指数A | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 华夏国证自由现金流ETF联接A | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 华夏新锦绣灵活配置混合A | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 华夏新锦绣灵活配置混合C | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 富国蓝筹精选股票(QDII) | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 广发量化多因子灵活配置混合A | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 诺安多策略混合C | CN |  | MissingSymbol |  | 缺少代码，且没有匹配到本地代理规则。 |
| 中金中证500指数增强A | CN | 510500 | ProxyMapped | ProxyHigh | 名称包含中证500，使用中证500 ETF 代理。 |
| 华夏国证半导体芯片ETF联接A | CN | 159995 | ProxyMapped | ProxyHigh | 名称包含半导体或芯片，使用国证半导体芯片 ETF 代理。 |
| 华安纳斯达克100ETF联接(QDII)A | CN | QQQ | ProxyMapped | ProxyHigh | 名称包含纳斯达克，使用 QQQ 作为行情代理。 |
| 华安纳斯达克100ETF联接(QDII)C | CN | QQQ | ProxyMapped | ProxyHigh | 名称包含纳斯达克，使用 QQQ 作为行情代理。 |
| 华泰柏瑞科创50联接A | CN | 588000 | ProxyMapped | ProxyHigh | 名称包含科创50，使用科创50 ETF 代理。 |
| 南方纳斯达克100指数(QDII)A | CN | QQQ | ProxyMapped | ProxyHigh | 名称包含纳斯达克，使用 QQQ 作为行情代理。 |
| 南方纳斯达克100指数(QDII)C | CN | QQQ | ProxyMapped | ProxyHigh | 名称包含纳斯达克，使用 QQQ 作为行情代理。 |
| 博时中证机器人指数A | CN | 562500 | ProxyMapped | ProxyMedium | 名称包含机器人，使用机器人主题 ETF 代理。 |
| 博时中证银行ETF联接(LOF)A | CN | 512800 | ProxyMapped | ProxyMedium | 名称包含银行，使用银行 ETF 作为行业代理。 |
| 博时恒生科技ETF联接(QDII)A | CN | 3033.HK | ProxyMapped | ProxyHigh | 名称包含恒生科技，使用港股恒生科技 ETF 代理。 |
| 博时标普500ETF联接(QDII)A | CN | SPY | ProxyMapped | ProxyHigh | 名称包含标普500，使用 SPY 作为行情代理。 |
| 国泰黄金ETF联接A | CN | 518880 | ProxyMapped | ProxyHigh | 名称包含黄金，使用 A 股黄金 ETF 作为行情代理。 |
| 天弘中证农业主题ETF联接C | CN | 159825 | ProxyMapped | ProxyMedium | 名称包含农业，使用农业主题 ETF 代理。 |
| 摩根标普500指数(QDII)A | CN | SPY | ProxyMapped | ProxyHigh | 名称包含标普500，使用 SPY 作为行情代理。 |
| 摩根标普500指数(QDII)C | CN | SPY | ProxyMapped | ProxyHigh | 名称包含标普500，使用 SPY 作为行情代理。 |
| 易方达人工智能ETF联接A | CN | 159819 | ProxyMapped | ProxyHigh | 名称包含人工智能，使用人工智能主题 ETF 代理。 |
| 易方达全球成长精选混合(QDII)A | CN | QQQ | ProxyMapped | ProxyLow | 名称包含全球成长，使用 QQQ 作为成长风格粗略代理。 |
| 易方达全球成长精选混合(QDII)C | CN | QQQ | ProxyMapped | ProxyLow | 名称包含全球成长，使用 QQQ 作为成长风格粗略代理。 |
| 易方达石油化工ETF联接A | CN | XLE | ProxyMapped | ProxyLow | 名称包含石油，使用美股能源行业 ETF 作为粗略代理。 |
| 易方达红利低波ETF联接A | CN | 512890 | ProxyMapped | ProxyMedium | 名称包含红利低波，使用红利低波 ETF 代理。 |
