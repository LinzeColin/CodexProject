(function attachPFIStage4Pages(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V023_STAGE4_PAGES = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage4Pages() {
  const phase41Subpages = Object.freeze({
    accounts: Object.freeze([
      page("accounts", "/accounts?tab=overview", "账户与资产 · 账户地图", ["账户与资产", "账户地图"], "account-map", "账户地图", "核对账户来源", "未加载真实账户快照时，只显示账户地图空态和下一步导入入口。", "无法读取账户快照，请检查本机 PFI 数据目录和来源权限。", "本机账户资料 / read-model", [
        section("map", "账户分组", "按现金、投资、支付平台和手工账户分组，不把未知账户静默归类。"),
        section("status", "数据健康", "显示每组账户的更新时间、币种和缺口。"),
        section("action", "下一步", "从数据源与上传补齐账户快照或进入对账。"),
      ]),
      page("accounts", "/accounts?tab=list", "账户与资产 · 账户清单", ["账户与资产", "账户清单"], "account-list", "账户清单", "打开账户明细", "未加载真实账户列表时，保留列结构并提示先导入或绑定来源。", "无法读取账户清单，请检查账户 profile 和导入批次。", "本机账户 profile / source profile", [
        section("table", "账户列表", "账户名、来源、币种、余额、最近更新和状态逐列展示。"),
        section("filter", "筛选器", "按来源、币种、状态和更新时间筛选。"),
        section("action", "账户动作", "打开账户详情、进入来源管理或标记待复核。"),
      ]),
      page("accounts", "/accounts?tab=trend", "账户与资产 · 资产趋势", ["账户与资产", "资产趋势"], "asset-trend", "资产趋势", "查看趋势缺口", "未加载真实资产序列时，不画伪造曲线，只显示趋势缺口说明。", "无法读取资产趋势，请检查 read-model hash 和汇率快照。", "SQLite read-model / FX snapshot", [
        section("chart", "趋势图", "现金、净资产、负债和总资产使用同一 CNY 基准。"),
        section("range", "时间范围", "显示数据覆盖区间和缺失月份。"),
        section("action", "趋势动作", "进入来源修复或导出趋势证据。"),
      ]),
      page("accounts", "/accounts?tab=reconcile", "账户与资产 · 账户对账", ["账户与资产", "账户对账"], "account-reconcile", "账户对账", "处理对账差异", "没有真实平台余额时，只显示待导入状态，不把差异写成 0。", "无法比对平台余额，请检查平台快照、账本余额和汇率快照。", "平台余额快照 / PFI 账本余额", [
        section("compare", "差异矩阵", "逐账户比较平台余额、账本余额、差异金额和原因。"),
        section("review", "复核队列", "缺失、过期、币种不一致进入复核。"),
        section("action", "对账动作", "确认差异、标记待处理或跳转到账本流水。"),
      ]),
    ]),
    ledger: Object.freeze([
      page("ledger", "/ledger?tab=list", "账本流水 · 流水列表", ["账本流水", "流水列表"], "ledger-table", "流水列表", "打开流水证据", "未加载真实流水时，显示空列表和导入入口，不显示财务假 0。", "无法读取流水列表，请检查 processed ledger 和原始批次。", "MetaDatabase/PFI processed ledger", [
        section("table", "标准流水表", "日期、账户、金额、币种、分类、对手方和证据链。"),
        section("batch", "批次信息", "展示来源批次、解析器版本和记录 hash。"),
        section("action", "流水动作", "打开证据、进入分类复核或跳转导入中心。"),
      ]),
      page("ledger", "/ledger?tab=filter", "账本流水 · 筛选搜索", ["账本流水", "筛选搜索"], "ledger-filter", "筛选搜索", "保存筛选条件", "没有真实流水时，筛选器保持可见并说明无可筛记录。", "无法执行筛选，请检查索引字段和日期范围。", "标准化流水索引", [
        section("query", "组合筛选", "账户、日期、金额、分类、币种和关键词组合。"),
        section("preview", "结果预览", "显示当前筛选命中、金额范围和待复核比例。"),
        section("action", "筛选动作", "保存视图、导出结果或清空条件。"),
      ]),
      page("ledger", "/ledger?tab=review", "账本流水 · 分类复核", ["账本流水", "分类复核"], "ledger-review", "分类复核", "保存分类复核", "没有真实低置信度流水时，显示复核队列为空和触发条件。", "无法加载复核队列，请检查置信度规则和导入批次。", "分类规则 / 复核队列", [
        section("queue", "复核队列", "按低置信度、未知分类、转账疑似和异常金额分组。"),
        section("decision", "复核决策", "保留原分类、修改分类、标记转账或排除非消费。"),
        section("action", "保存动作", "保存复核并记录决策理由。"),
      ]),
      page("ledger", "/ledger?tab=export", "账本流水 · 导出流水", ["账本流水", "导出流水"], "ledger-export", "导出流水", "生成导出文件", "没有真实筛选结果时，导出按钮显示阻断原因。", "无法生成导出，请检查筛选条件、文件权限和目标目录。", "当前筛选结果 / 本机导出目录", [
        section("scope", "导出范围", "展示账户、日期、分类和金额范围。"),
        section("format", "格式选择", "CSV、Markdown 或上下文快照使用同一真实结果。"),
        section("action", "导出动作", "生成文件并显示本机保存路径。"),
      ]),
    ]),
    investment: Object.freeze([
      page("investment", "/investment?tab=overview", "投资管理 · 投资总览", ["投资管理", "投资总览"], "investment-overview", "投资总览", "查看资产配置", "未加载真实持仓时，只显示投资空态和接入说明。", "无法读取投资总览，请检查持仓、现金仓位和汇率快照。", "SQLite holdings / FX snapshot", [
        section("summary", "市值摘要", "总市值、现金仓位、资产配置和更新时间。"),
        section("allocation", "资产配置", "按币种、账户、资产类型和集中度拆分。"),
        section("action", "总览动作", "进入持仓、交易记录或风险检查。"),
      ]),
      page("investment", "/investment?tab=holdings", "投资管理 · 持仓", ["投资管理", "持仓"], "investment-holdings", "持仓", "编辑持仓快照", "没有真实持仓时，显示持仓空表和新增入口，不使用浏览器缓存当正式数据。", "无法读取持仓，请检查 SQLite 服务和本机 operational database。", "SQLite operational holdings", [
        section("table", "持仓表", "标的、名称、数量、成本、价格、币种、账户和更新时间。"),
        section("draft", "草稿状态", "未提交草稿和保存状态独立显示。"),
        section("action", "持仓动作", "新增、保存、恢复默认或刷新服务状态。"),
      ]),
      page("investment", "/investment?tab=trades", "投资管理 · 交易记录", ["投资管理", "交易记录"], "investment-trades", "交易记录", "核对交易流水", "未导入真实交易时，显示券商导入入口和缺口说明。", "无法读取交易记录，请检查券商流水、费用字段和税费字段。", "券商交易流水 / 手工交易记录", [
        section("timeline", "交易时间线", "买入、卖出、费用、税费和汇率影响按时间展示。"),
        section("match", "流水匹配", "连接投资现金流和账本流水，避免重复计入消费。"),
        section("action", "交易动作", "打开证据、标记缺字段或进入账本复核。"),
      ]),
      page("investment", "/investment?tab=returns", "投资管理 · 收益分析", ["投资管理", "收益分析"], "investment-returns", "收益分析", "查看收益拆解", "没有真实持仓和交易时，不输出收益结论，只列出缺失证据。", "无法计算收益，请检查成本、成交、费用、税费和最新价格。", "持仓快照 / 交易流水 / 价格快照", [
        section("attribution", "收益归因", "市场变化、主动决策、费用、汇率和现金拖累分开显示。"),
        section("formula", "公式证据", "展示成本、现价、费用、税费和汇率的使用范围。"),
        section("action", "收益动作", "进入缺口修复或生成收益证据。"),
      ]),
    ]),
  });

  const phase42Subpages = Object.freeze({
    consumption: Object.freeze([
      page("consumption", "/consumption?tab=overview", "消费管理 · 消费总览", ["消费管理", "消费总览"], "spend-overview", "消费总览", "检查消费概览", "未加载真实消费流水时，只显示消费总览空态和导入入口。", "无法读取消费总览，请检查账本流水、分类结果和币种基准。", "MetaDatabase/PFI ledger categories", [
        section("summary", "消费摘要", "按月份、账户和分类汇总真实消费覆盖范围。"),
        section("trend", "消费趋势", "显示已加载期间、缺失期间和异常月份提示。"),
        section("gate", "数据门禁", "未通过真实流水门禁前，不生成总额结论或趋势判断。"),
        section("action", "总览动作", "进入分类、预算或异常消费复核。"),
      ]),
      page("consumption", "/consumption?tab=category", "消费管理 · 分类分析", ["消费管理", "分类分析"], "category-analysis", "分类分析", "复核消费分类", "未加载真实分类结果时，只显示分类待复核状态。", "无法读取分类分析，请检查分类规则、低置信度队列和原始流水。", "分类规则 / processed ledger", [
        section("matrix", "分类矩阵", "按一级分类、二级分类和账户来源拆分消费记录。"),
        section("confidence", "置信度", "展示低置信度、未知分类和人工覆盖记录。"),
        section("gate", "数据门禁", "分类覆盖率不足时阻断洞察和报告引用。"),
        section("action", "分类动作", "打开复核队列并保存分类理由。"),
      ]),
      page("consumption", "/consumption?tab=budget", "消费管理 · 预算", ["消费管理", "预算"], "budget-control", "预算", "调整预算规则", "未加载真实预算和消费流水时，只显示预算设置空态。", "无法读取预算，请检查预算文件、币种设置和消费分类。", "预算规则 / ledger monthly rollup", [
        section("rule", "预算规则", "按分类、账户和周期展示预算阈值。"),
        section("usage", "使用进度", "只基于已加载真实流水计算预算进度。"),
        section("gate", "数据门禁", "预算期流水不完整时标记为不可判定。"),
        section("action", "预算动作", "调整规则、记录变更原因或跳转导入中心。"),
      ]),
      page("consumption", "/consumption?tab=subscription", "消费管理 · 订阅", ["消费管理", "订阅"], "subscription-tracker", "订阅", "标记订阅状态", "未识别真实周期扣款时，只显示订阅侦测空态。", "无法读取订阅，请检查周期扣款识别、账户来源和商户字段。", "周期扣款识别 / merchant index", [
        section("list", "订阅清单", "展示候选订阅、频率、最近扣款和来源流水。"),
        section("evidence", "流水证据", "每项订阅保留匹配记录和识别理由。"),
        section("gate", "数据门禁", "缺少连续账期时阻断订阅确认。"),
        section("action", "订阅动作", "确认、忽略或进入商户规则复核。"),
      ]),
      page("consumption", "/consumption?tab=anomaly", "消费管理 · 异常消费", ["消费管理", "异常消费"], "spend-anomaly", "异常消费", "处理异常消费", "未加载真实流水和历史基线时，只显示异常检测空态。", "无法读取异常消费，请检查历史基线、分类覆盖和金额字段。", "历史消费基线 / anomaly queue", [
        section("queue", "异常队列", "按金额突增、重复扣款、未知商户和异常币种分组。"),
        section("reason", "异常理由", "显示触发条件、对比周期和证据流水。"),
        section("gate", "数据门禁", "基线不足时只允许复核，不输出异常结论。"),
        section("action", "异常动作", "确认、忽略或标记为待补证据。"),
      ]),
    ]),
    sync: Object.freeze([
      page("sync", "/sources-upload?tab=upload", "数据源与上传 · 上传中心", ["数据源与上传", "上传中心"], "upload-center", "上传中心", "选择上传文件", "未选择真实本机文件时，只显示上传空态和格式要求。", "无法启动上传，请检查本机文件权限、目录和解析器配置。", "本机上传目录 / parser registry", [
        section("dropzone", "文件入口", "展示可上传来源、格式和目标数据域。"),
        section("parser", "解析器", "匹配解析器版本、字段要求和拒绝原因。"),
        section("gate", "数据门禁", "未完成文件校验前不写入正式 PFI 数据。"),
        section("action", "上传动作", "选择文件、校验格式或转到导入中心。"),
      ]),
      page("sync", "/sources-upload?tab=import", "数据源与上传 · 导入中心", ["数据源与上传", "导入中心"], "import-center", "导入中心", "执行导入批次", "未校验真实上传文件时，只显示导入待准备状态。", "无法执行导入，请检查字段映射、重复记录和批次权限。", "staging import batch / field mapping", [
        section("mapping", "字段映射", "展示来源字段、目标字段和缺失字段。"),
        section("dedupe", "去重检查", "按记录 hash、时间和金额识别重复导入风险。"),
        section("gate", "数据门禁", "批次未通过复核前不进入 processed ledger。"),
        section("action", "导入动作", "执行导入、保存映射或退回上传。"),
      ]),
      page("sync", "/sources-upload?tab=sources", "数据源与上传 · 数据源管理", ["数据源与上传", "数据源管理"], "source-management", "数据源管理", "维护数据源", "未配置真实数据源时，只显示来源清单空态。", "无法读取数据源，请检查来源 profile、凭据状态和本机权限。", "source profile registry", [
        section("registry", "来源登记", "按账户、平台、文件夹和导入方式管理数据源。"),
        section("health", "来源健康", "展示最近更新、缺失字段和权限状态。"),
        section("gate", "数据门禁", "来源未达最低字段要求时阻断导入。"),
        section("action", "来源动作", "新增来源、停用来源或打开权限检查。"),
      ]),
      page("sync", "/sources-upload?tab=review", "数据源与上传 · 待复核", ["数据源与上传", "待复核"], "import-review", "待复核", "处理导入复核", "没有真实待复核记录时，只显示复核队列为空。", "无法读取待复核记录，请检查导入批次、字段映射和错误日志。", "import review queue", [
        section("queue", "复核队列", "按缺字段、低置信度、重复疑似和解析失败分组。"),
        section("decision", "复核决策", "保留、修正、拒绝或补充字段均记录理由。"),
        section("gate", "数据门禁", "未完成复核的记录不得进入正式账本。"),
        section("action", "复核动作", "保存决策、退回导入或打开证据。"),
      ]),
      page("sync", "/sources-upload?tab=history", "数据源与上传 · 导入历史", ["数据源与上传", "导入历史"], "import-history", "导入历史", "打开导入证据", "未存在真实导入批次时，只显示历史空态。", "无法读取导入历史，请检查批次索引、日志文件和本机权限。", "import batch log / evidence files", [
        section("timeline", "批次时间线", "展示上传、校验、导入、复核和写入状态。"),
        section("evidence", "证据文件", "保留文件 hash、记录数量和解析器版本。"),
        section("gate", "数据门禁", "缺少证据文件的批次标记为不可追溯。"),
        section("action", "历史动作", "打开证据、重新复核或导出批次日志。"),
      ]),
    ]),
    insights: Object.freeze([
      page("insights", "/reports?tab=monthly", "报告与洞察 · 月报", ["报告与洞察", "月报"], "monthly-report", "月报", "生成月报草稿", "未加载真实月度账本时，只显示月报空态和缺口说明。", "无法生成月报，请检查月度流水、账户快照和分类覆盖。", "monthly ledger rollup / account snapshot", [
        section("period", "报告期间", "显示月份、数据覆盖天数和缺失来源。"),
        section("finding", "月度发现", "只呈现已通过门禁的数据项和待复核项。"),
        section("gate", "数据门禁", "关键数据未齐时阻断报告结论生成。"),
        section("action", "月报动作", "生成草稿、补齐数据或导出证据。"),
      ]),
      page("insights", "/reports?tab=quarterly", "报告与洞察 · 季报", ["报告与洞察", "季报"], "quarterly-report", "季报", "生成季报草稿", "未加载真实季度数据时，只显示季报空态和待补月份。", "无法生成季报，请检查季度账本、投资快照和消费分类。", "quarterly rollup / holdings snapshot", [
        section("coverage", "季度覆盖", "逐月展示收入、消费、投资和账户数据完整度。"),
        section("compare", "季度对比", "对比上一季度但标明缺失项和不可比项。"),
        section("gate", "数据门禁", "季度覆盖不足时只保留草稿，不输出总结。"),
        section("action", "季报动作", "生成草稿、打开缺口或导出对比表。"),
      ]),
      page("insights", "/reports?tab=yearly", "报告与洞察 · 年报", ["报告与洞察", "年报"], "yearly-report", "年报", "生成年报草稿", "未加载真实年度数据时，只显示年报空态和年度覆盖表。", "无法生成年报，请检查年度账本、账户历史和投资收益证据。", "yearly rollup / audited evidence", [
        section("calendar", "年度日历", "展示每月数据状态、关闭状态和复核状态。"),
        section("theme", "年度主题", "从真实记录中提取消费、资产和投资变化。"),
        section("gate", "数据门禁", "未关闭月份不得进入年度结论。"),
        section("action", "年报动作", "生成草稿、锁定期间或导出证据包。"),
      ]),
      page("insights", "/reports?tab=custom", "报告与洞察 · 自定义报告", ["报告与洞察", "自定义报告"], "custom-report", "自定义报告", "配置报告范围", "未选择真实报告范围时，只显示自定义报告空态。", "无法配置自定义报告，请检查筛选范围、数据域和权限。", "report query scope / local read-model", [
        section("builder", "范围构建", "按账户、分类、日期、币种和数据域组合报告范围。"),
        section("preview", "结果预览", "显示可用记录数、缺口和门禁状态。"),
        section("gate", "数据门禁", "筛选范围没有真实记录时阻断报告生成。"),
        section("action", "自定义动作", "保存范围、生成草稿或清空条件。"),
      ]),
      page("insights", "/reports?tab=export", "报告与洞察 · 导出", ["报告与洞察", "导出"], "report-export", "导出", "导出报告文件", "未生成真实报告草稿时，只显示导出空态。", "无法导出报告，请检查报告草稿、目标目录和文件权限。", "report draft / local export directory", [
        section("format", "导出格式", "选择 PDF、Markdown 或 evidence bundle。"),
        section("destination", "保存位置", "展示本机目标目录和覆盖策略。"),
        section("gate", "数据门禁", "报告草稿未通过证据检查时阻断导出。"),
        section("action", "导出动作", "生成文件、打开目录或复制证据路径。"),
      ]),
    ]),
  });

  const phase43Subpages = Object.freeze({
    market_research: Object.freeze([
      page("market_research", "/market-research?tab=market", "市场与研究 · 市场观察", ["市场与研究", "市场观察"], "market-watch", "市场观察", "打开观察清单", "未加载真实市场观察资料时，只显示市场观察空态和来源说明。", "无法读取市场观察，请检查市场资料来源、更新时间和本机缓存。", "市场观察资料 / local research cache", [
        section("watch", "观察清单", "按指数、ETF、主题和自选对象组织观察对象。"),
        section("signal", "状态信号", "展示价格、事件、来源时间和待复核状态。"),
        section("compat", "兼容入口", "v0.1 市场入口 /market/watch 进入本页面。"),
        section("action", "观察动作", "打开对象、保存观察视图或跳转研究笔记。"),
      ], { legacyAliases: ["/market/watch"] }),
      page("market_research", "/market-research?tab=research", "市场与研究 · 研究笔记", ["市场与研究", "研究笔记"], "research-notes", "研究笔记", "整理研究笔记", "未加载真实研究笔记时，只显示研究空态和证据要求。", "无法读取研究笔记，请检查研究文件、引用位置和来源权限。", "研究笔记 / citation index", [
        section("notebook", "研究笔记", "按公司、基金、政策和主题组织研究条目。"),
        section("evidence", "引用证据", "展示来源、引用位置、更新时间和反方条件。"),
        section("compat", "兼容入口", "v0.1 研究入口 /market/research 进入本页面。"),
        section("action", "研究动作", "新建笔记、打开引用或标记待复核。"),
      ], { legacyAliases: ["/market/research"], alternateRoutes: ["/market-research?tab=policy"] }),
      page("market_research", "/market-research?tab=company", "市场与研究 · 公司研究", ["市场与研究", "公司研究"], "company-research", "公司研究", "打开公司档案", "未加载真实公司资料时，只显示公司研究空态和资料清单。", "无法读取公司研究，请检查公司资料、财报引用和研究索引。", "公司资料 / filing citations", [
        section("profile", "公司档案", "展示业务、财务资料、关键假设和风险点。"),
        section("thesis", "假设面板", "把正向、反向和验证条件分开记录。"),
        section("action", "公司动作", "打开档案、补充证据或进入基金研究。"),
      ]),
      page("market_research", "/market-research?tab=fund", "市场与研究 · 基金研究", ["市场与研究", "基金研究"], "fund-research", "基金研究", "核对基金资料", "未加载真实基金资料时，只显示基金研究空态和来源要求。", "无法读取基金研究，请检查基金持仓、费用、风格和披露来源。", "基金资料 / holdings disclosure", [
        section("holding", "持仓拆分", "展示基金持仓、行业、地区和集中度。"),
        section("cost", "费用与风格", "记录费用、风格漂移、跟踪误差和风险。"),
        section("action", "基金动作", "打开基金资料、记录观察或加入研究笔记。"),
      ]),
      page("market_research", "/market-research/strategy-lab", "市场与研究 · 策略实验室", ["市场与研究", "策略实验室"], "strategy-lab", "策略实验室", "进入策略实验", "未选择真实策略和数据范围时，只显示策略实验空态。", "无法打开策略实验室，请检查策略定义、数据范围和运行权限。", "策略注册表 / historical market data", [
        section("experiment", "实验配置", "选择策略、标的、周期、成本和数据范围。"),
        section("result", "结果证据", "展示收益、回撤、交易、风险闸门和报告证据。"),
        section("compat", "兼容入口", "v0.1 策略实验室入口 /market/lab 进入本页面。"),
        section("action", "策略动作", "运行回测、保存实验或打开复盘记录。"),
      ], { legacyAliases: ["/market/lab"] }),
    ]),
    settings: Object.freeze([
      page("settings", "/settings?tab=account", "设置 · 账户偏好", ["设置", "账户偏好"], "account-preferences", "账户偏好", "保存账户偏好", "未加载真实偏好文件时，只显示账户偏好空态。", "无法读取账户偏好，请检查本机设置文件和写入权限。", "local preferences file", [
        section("identity", "账户显示", "设置默认账户、显示币种、首页偏好和主题语言。"),
        section("scope", "应用范围", "展示影响首页、账户和报告的设置项。"),
        section("action", "偏好动作", "保存、恢复默认或记录变更理由。"),
      ], { alternateRoutes: ["/settings?tab=theme"] }),
      page("settings", "/settings?tab=data-system", "设置 · 数据与系统", ["设置", "数据与系统"], "data-system-settings", "数据与系统", "检查数据系统", "未加载真实数据目录状态时，只显示数据与系统空态。", "无法读取数据与系统，请检查数据目录、权限和服务状态。", "MetaDatabase/PFI path registry", [
        section("directory", "数据目录", "展示真实数据目录、来源状态和最近检查时间。"),
        section("service", "系统状态", "展示本机服务、缓存、质量报告和任务状态。"),
        section("compat", "兼容入口", "v0.1 数据与系统入口 /settings/data 进入本页面。"),
        section("action", "系统动作", "刷新检查、打开目录或进入备份恢复。"),
      ], { legacyAliases: ["/settings/data"] }),
      page("settings", "/settings?tab=privacy", "设置 · 隐私与本地存储", ["设置", "隐私与本地存储"], "privacy-storage", "隐私与本地存储", "检查隐私边界", "未加载真实本机存储状态时，只显示隐私空态和排除规则。", "无法读取隐私与本地存储，请检查目录权限和提交排除规则。", "local storage boundary / ignore rules", [
        section("boundary", "本地边界", "列出本机数据、原始文件和不进入仓库的路径。"),
        section("audit", "隐私检查", "展示提交排除规则、敏感目录和最近检查结果。"),
        section("action", "隐私动作", "打开边界说明、复制路径或标记待处理。"),
      ]),
      page("settings", "/settings?tab=feedback", "设置 · 反馈偏好", ["设置", "反馈偏好"], "feedback-preferences", "反馈偏好", "调整反馈偏好", "未加载真实反馈偏好时，只显示反馈设置空态。", "无法读取反馈偏好，请检查本机偏好文件和浏览器权限。", "feedback preferences / browser capability", [
        section("haptic", "触感反馈", "设置选择、确认、阻断和危险反馈强度。"),
        section("visual", "视觉声音", "设置视觉状态、声音反馈和静默降级。"),
        section("action", "反馈动作", "保存偏好、测试反馈或恢复默认。"),
      ]),
      page("settings", "/settings?tab=backup", "设置 · 备份恢复", ["设置", "备份恢复"], "backup-restore", "备份恢复", "检查备份恢复", "未加载真实备份记录时，只显示备份恢复空态。", "无法读取备份恢复，请检查备份目录、校验文件和权限。", "backup manifest / restore checkpoints", [
        section("backup", "备份记录", "展示备份时间、范围、校验状态和目标目录。"),
        section("restore", "恢复检查", "列出可恢复点、风险和需要确认的操作。"),
        section("action", "备份动作", "打开备份目录、校验备份或准备恢复。"),
      ]),
    ]),
    recommendations: Object.freeze([
      page("recommendations", "/review?tab=list", "建议与复盘 · 建议列表", ["建议与复盘", "建议列表"], "recommendation-list", "建议列表", "查看建议列表", "未加载真实建议时，只显示建议列表空态和生成条件。", "无法读取建议列表，请检查证据引用、规则结果和复盘状态。", "recommendation registry / evidence refs", [
        section("queue", "建议队列", "按消费、预算、现金流、持仓和数据质量分组。"),
        section("evidence", "证据状态", "展示每条建议的证据引用、预期效果和代价。"),
        section("action", "列表动作", "打开详情、标记优先级或进入决策记录。"),
      ]),
      page("recommendations", "/review?tab=detail", "建议与复盘 · 建议详情", ["建议与复盘", "建议详情"], "recommendation-detail", "建议详情", "复核建议详情", "未选择真实建议时，只显示详情空态和选择入口。", "无法读取建议详情，请检查建议 ID、证据引用和来源数据。", "recommendation detail / source evidence", [
        section("summary", "建议摘要", "展示建议原因、数据范围、预期效果和执行代价。"),
        section("trace", "证据链", "列出引用记录、公式、参数和不确定性。"),
        section("action", "详情动作", "接受、暂缓、忽略或补充证据。"),
      ]),
      page("recommendations", "/review?tab=decision", "建议与复盘 · 决策记录", ["建议与复盘", "决策记录"], "decision-record", "决策记录", "记录建议决策", "未存在真实决策记录时，只显示决策记录空态。", "无法读取决策记录，请检查复盘日志、建议 ID 和写入权限。", "decision log / review lifecycle", [
        section("decision", "决策表", "记录接受、暂缓、忽略、执行状态和理由。"),
        section("owner", "责任与时间", "展示决策时间、复核时间和后续动作。"),
        section("action", "决策动作", "保存决策、撤回或进入复盘记录。"),
      ]),
      page("recommendations", "/review?tab=history", "建议与复盘 · 复盘记录", ["建议与复盘", "复盘记录"], "review-history", "复盘记录", "打开复盘记录", "未存在真实复盘记录时，只显示复盘空态和触发条件。", "无法读取复盘记录，请检查建议生命周期、执行记录和证据链。", "review history / outcome evidence", [
        section("timeline", "复盘时间线", "展示建议提出、决策、执行、结果和二次调整。"),
        section("outcome", "结果评估", "记录实际效果、偏差原因和后续修正。"),
        section("action", "复盘动作", "新增复盘、导出记录或回到建议详情。"),
      ]),
    ]),
  });

  return Object.freeze({
    version: "v0.2.3",
    stage: "Stage 4",
    phaseId: "V023-S4-P4.3",
    phaseIds: Object.freeze(["V023-S4-P4.1", "V023-S4-P4.2", "V023-S4-P4.3"]),
    phaseName: "资产/账本/投资 + 消费/数据/报告 + 市场/设置/建议二级页",
    phase41Subpages,
    phase42Subpages,
    phase43Subpages,
  });
});

function page(workspace, routeAlias, title, breadcrumb, layoutKind, primaryObject, primaryAction, emptyState, errorState, dataSource, sections, extras = {}) {
  const extraFields = Object.fromEntries(
    Object.entries(extras).map(([key, value]) => [key, Array.isArray(value) ? Object.freeze(value) : value])
  );
  return Object.freeze({
    workspace,
    routeAlias,
    title,
    breadcrumb: Object.freeze(breadcrumb),
    layoutKind,
    primaryObject,
    primaryAction,
    emptyState,
    errorState,
    dataSource,
    sections: Object.freeze(sections),
    ...extraFields,
  });
}

function section(kind, title, detail) {
  return Object.freeze({ kind, title, detail });
}
