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

  return Object.freeze({
    version: "v0.2.3",
    stage: "Stage 4",
    phaseId: "V023-S4-P4.1",
    phaseName: "资产/账本/投资二级页",
    phase41Subpages,
  });
});

function page(workspace, routeAlias, title, breadcrumb, layoutKind, primaryObject, primaryAction, emptyState, errorState, dataSource, sections) {
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
  });
}

function section(kind, title, detail) {
  return Object.freeze({ kind, title, detail });
}
