from pathlib import Path

from app.core.reporting import render_markdown_report, render_offline_index
from app.core.application_portal import (
    PortalFundInfo,
    PortalHolding,
    PortalManualReviewItem,
    PortalRun,
    PortalTimelineEvent,
    _write_app_bundle,
    render_application_portal,
)


def test_offline_index_has_search_filters_and_copy_feedback_hooks():
    html = render_offline_index(
        [
            {
                "run_id": "sda_test_r7",
                "slot": "R7",
                "run_time_bj": "20260615 - 14:00 CST",
                "run_time_au": "20260615 - 16:00 AEST",
                "status": "success",
                "quality": "pass",
                "html_file": "sda_test_r7_report.html",
                "md_file": "sda_test_r7_report.md",
            }
        ]
    )

    assert 'id="search"' in html
    assert "运行时间" in html
    assert "20260615 - 14:00 CST" in html
    assert "<td>R7</td>" not in html
    assert 'data-filter="pass"' in html
    assert 'data-copy-value="sda_test_r7"' in html
    assert "运行 ID 已复制" in html
    assert "../../outputs/application/index.html" in html


def test_application_bundle_has_custom_icon(tmp_path: Path):
    app_path = tmp_path / "Serenity 每日分析.app"
    portal_path = tmp_path / "index.html"
    portal_path.write_text("<html></html>", encoding="utf-8")

    _write_app_bundle(app_path, portal_path, tmp_path)

    info = (app_path / "Contents" / "Info.plist").read_text(encoding="utf-8")
    pkginfo = app_path / "Contents" / "PkgInfo"
    icon = app_path / "Contents" / "Resources" / "SerenityIcon.icns"
    preview = app_path.parent / "serenity-app-icon.png"
    assert "<key>CFBundleIconFile</key>" in info
    assert "<string>SerenityIcon</string>" in info
    assert "local.serenity.daily-analysis." in info
    assert pkginfo.read_text(encoding="ascii") == "APPL????"
    assert icon.exists()
    assert icon.stat().st_size > 1024
    assert preview.exists()


def test_application_portal_homepage_is_chinese_and_position_first():
    project_root = Path(__file__).resolve().parents[1]
    run = PortalRun(
        run_id="sda_test_r7",
        slot="R7",
        run_time_bj="2026-06-15T14:00:00+08:00",
        run_time_au="2026-06-15T16:00:00+10:00",
        created_at="2026-06-13T00:00:00+00:00",
        status="success",
        quality="pass",
        notification_status="sent",
        report_path="data/reports/sda_test_r7_report.md",
        html_path=str(project_root / "data/reports/sda_test_r7_report.html"),
    )
    holding = PortalHolding(
        rank=1,
        code="007300",
        name="国联安中证半导体ETF联接A",
        grade="Action-Ready",
        score=93.6958,
        target_weight=0.209267,
        current_weight=0.209267,
        action_label="Maintain",
        trigger_reason="serenity judgment supported by evidence confidence",
    )

    previous_holding = PortalHolding(
        rank=1,
        code="007300",
        name="国联安中证半导体ETF联接A",
        grade="Action-Ready",
        score=92.0,
        target_weight=0.189267,
        current_weight=0.189267,
        action_label="Maintain",
        trigger_reason="previous run",
    )
    previous_run = PortalRun(
        run_id="sda_previous_r7",
        slot="R7",
        run_time_bj="2026-06-15T13:30:00+08:00",
        run_time_au="2026-06-15T15:30:00+10:00",
        created_at="2026-06-12T23:29:00+00:00",
        status="success",
        quality="pass",
        notification_status="sent",
        report_path="data/reports/sda_previous_r7_report.md",
        html_path="data/reports/sda_previous_r7_report.html",
    )
    fund_info = PortalFundInfo(
        code="007300",
        name="国联安中证半导体ETF联接A",
        first_top5_time_bj="2026-06-12T13:30:00+08:00",
        last_top5_entry_time_bj="2026-06-13T06:00:00+08:00",
        current_candidate_days=3,
        candidate_status="在当前候选池",
        rule_snapshot_time_bj="2026-06-15T14:00:00+08:00",
        subscription_status="open",
        redemption_status="open",
        cutoff_time="15:00",
        confirm_lag="T+1",
        redeem_lag="T+3",
        subscription_fee=0.008,
        redemption_fee=0.015,
        subscription_fee_schedule="M<100万元 0.80%；100万元≤M<500万元 0.60%；M≥500万元 1000元/笔",
        redemption_fee_schedule="N<7天 1.50%；7天≤N<365天 0.50%；N≥365天 0.00%",
        fee_schedule_as_of="2026-06-15",
        fee_schedule_note="A类前端费率；执行前以支付宝交易确认页为准",
        management_fee=0.005,
        custody_fee=0.001,
        sales_service_fee=0.0,
        min_purchase_amount=10.0,
        alipay_trade_status="待支付宝交易页确认（基金本身申赎开放）",
        moomoo_trade_status="未验证MooMoo场外基金交易；MooMoo仅作行情/代理数据参考",
        platform_trade_note="平台交易可用性只作建议；不支持支付宝或MooMoo交易不能单独排除候选",
        source_name="official source",
        source_type="official",
        source_priority=3,
        source_url="https://example.com/fund/007300",
    )
    timeline_events = [
        PortalTimelineEvent(
            slot="R7",
            run_time_bj="20260615 - 14:00 CST",
            run_time_au="20260615 - 16:00 AEST",
            status="成功",
            quality="通过",
            direction="buy",
            buy_count=1,
            sell_count=0,
            top5_count=5,
            summary="买入/增加 1",
            detail="第一句话；第二句话；第三句话",
        ),
        PortalTimelineEvent(
            slot="R8",
            run_time_bj="20260615 - 14:30 CST",
            run_time_au="20260615 - 16:30 AEST",
            status="成功",
            quality="通过",
            direction="sell",
            buy_count=0,
            sell_count=1,
            top5_count=5,
            summary="卖出/减少 1",
            detail="国联安中证半导体ETF联接A 减少 -1.00%",
        ),
        PortalTimelineEvent(
            slot="R7",
            run_time_bj="20260615 - 14:00 CST",
            run_time_au="20260615 - 16:00 AEST",
            status="成功",
            quality="通过",
            direction="flat",
            buy_count=0,
            sell_count=0,
            top5_count=5,
            summary="维持",
            detail="重复时间应被隐藏",
        ),
    ]
    review_items = [
        PortalManualReviewItem(
            review_id=65,
            run_id="sda_test_r7",
            code="018043",
            name="天弘纳斯达克100指数发起(QDII)A",
            reason="fee/redemption/subscription status missing or closed",
            action_blocked="No-New-Order",
            status="open",
            created_at="20260613 - 14:00 CST",
        )
    ]

    html = render_application_portal(
        run,
        [holding],
        previous_run,
        [previous_holding],
        baseline_time_bj="2026-06-15T13:30:00+08:00",
        fund_library={"007300": fund_info},
        run_timeline=timeline_events,
        manual_review_items=review_items,
    )

    assert "<h1>Serenity 每日分析</h1>" in html
    assert "本地策略工作台。首页展示 Serenity 基准生成的持仓建议" not in html
    assert "Top5 discipline（策略份额）" not in html
    assert "当前持仓建议" in html
    assert "20260615 - 14:00 CST · 通过" in html
    assert "验证回填，生成时间" not in html
    assert "最新更新时间 20260613 - 10:00 AEST" in html
    assert "相较对比时间 20260613 - 09:29 AEST" in html
    assert "运行 ID：" not in html
    assert 'fetch("/api/refresh"' in html
    assert "持仓建议" in html
    assert "当前持仓及时间" in html
    assert "上轮持仓及时间" in html
    assert "申购费分档规则" in html
    assert "赎回费分档规则" in html
    assert "支付宝交易可用性" in html
    assert "MooMoo交易可用性" in html
    assert "平台交易备注" in html
    assert "不支持支付宝或MooMoo交易不能单独排除候选" in html
    assert "M<100万元 0.80%" in html
    assert "N<7天 1.50%" in html
    assert "当前/上轮持仓对比" not in html
    assert "当前策略份额" not in html
    assert "上轮策略份额" not in html
    assert "运行时间线" in html
    assert 'data-timeline-mode="table"' in html
    assert 'data-timeline-mode="visual"' in html
    assert 'data-timeline-view="visual" hidden' in html
    assert "<strong>R7</strong>" not in html
    assert "<strong>R8</strong>" not in html
    assert "<strong>20260615 - 14:00 CST</strong>" in html
    assert "<strong>20260615 - 14:30 CST</strong>" in html
    assert html.count('<tr class="timeline-row-buy"><td><strong>20260615 - 14:00 CST</strong>') == 1
    assert "重复时间应被隐藏" not in html
    assert (
        '<div class="timeline-detail-lines"><span>第一句话；</span><span>第二句话；</span><span>第三句话</span></div>'
        in html
    )
    assert "买入/增加 1" in html
    assert "卖出/减少 1" in html
    assert 'timeline-row-buy' in html
    assert 'timeline-row-sell' in html
    assert 'timeline-dot buy' in html
    assert 'timeline-dot sell' in html
    assert "人工复核" in html
    assert "1 项待复核" in html
    assert 'data-open-review' in html
    assert 'id="review-modal" hidden' in html
    assert "天弘纳斯达克100指数发起(QDII)A" in html
    assert "保持禁止新增" in html
    assert "需要补证据" in html
    assert "确认观察" in html
    assert "已人工处理" in html
    assert "data-save-review" in html
    assert 'data-review-run-id="sda_test_r7"' in html
    assert "data-copy-review-log" in html
    assert "serenityManualReview.v1.cache" in html
    assert 'fetch("/api/manual-review"' in html
    assert "保存复核" in html
    assert "保存本地复核" not in html
    assert "清空复核记录" in html
    assert "清空本地复核" not in html
    assert "人工复核已保存到数据库" in html
    assert "已保存到数据库" in html
    assert "初始持仓权重" in html
    assert "上轮对比权重" in html
    assert "相对比例" in html
    assert "相对上轮" not in html
    assert "目标时间：20260615 - 14:00 CST" in html
    assert "初始持仓权重时间：20260615 - 13:30 CST" in html
    assert "上轮对比权重时间：20260615 - 13:30 CST" in html
    assert 'data-previous-value="18.93%"' in html
    assert 'data-previous-value="+10.57%"' in html
    assert "需操作的行为" in html
    assert "不建议因为本轮结果新增申购或赎回" not in html
    assert "所有申购、赎回、增配、减配都必须在支付宝或对应官方平台人工确认后执行" not in html
    assert "增加/买入" in html
    assert "颜色规则" not in html
    assert "增加/买入 = 红色" not in html
    assert "减少/卖出 = 绿色" not in html
    assert "维持 = 浅蓝色" not in html
    assert '<span class="change up">增加/买入</span>' in html
    assert '<span class="change down">减少/卖出</span>' in html
    assert '<span class="change flat">维持</span>' in html
    assert "pct" not in html
    assert ".change.flat { color: var(--hold); background: var(--hold-bg); }" in html
    assert ".badge.hold { background: var(--hold-bg); border-color: var(--hold-border); color: var(--hold); }" in html
    assert '<span class="badge hold">维持</span>' in html
    assert 'class="change up"' in html
    assert 'class="floating-refresh"' in html
    assert 'data-fund-code="007300"' in html
    assert "首次进入策略 Top5" in html
    assert "上次进入候选池时间" in html
    assert "当前进入候选池天数" in html
    assert "当前状态" in html
    assert "20260613 - 06:00 CST" in html
    assert "3 天" in html
    assert "在当前候选池" in html
    assert "费用/状态快照时间" in html
    assert "20260612 - 13:30 CST" in html
    assert "合计运营费（年）" in html
    assert "基金库" in html
    assert "已入库 1 只基金" in html
    assert "查看报告" in html
    assert "查看快照" in html
    assert "查看基金" in html
    assert "查看说明" in html
    assert "处理复核" in html
    assert "保存到数据库" in html
    assert "复制预检命令" not in html
    assert "复制审计命令" not in html
    assert "cmd-preflight" not in html
    assert "cmd-audit" not in html
    assert "SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json" not in html
    assert "SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json" not in html
    assert 'data-copy="' not in html
    assert 'data-open-fund-library' in html
    assert 'id="fund-library-modal" hidden' in html
    assert 'id="fund-library-body"' in html
    assert 'data-fund-library-mode="gallery"' in html
    assert 'data-fund-library-mode="table"' in html
    assert 'data-fund-library-view="gallery"' in html
    assert 'data-fund-library-view="table" hidden' in html
    assert 'id="fund-library-table-body"' in html
    assert "fundLibraryTableBody" in html
    assert "fundLibrarySummaryLabels" in html
    assert '#fund-library-modal { z-index: 32; }' in html
    assert '#fund-modal { z-index: 36; }' in html
    assert 'data-close-fund-button' in html
    assert "返回基金库" in html
    assert "已返回基金库" in html
    assert "data-open-fund-detail" in html
    assert "openFundModal(info.code, { fromLibrary: true })" in html
    assert "openFundModal(button.dataset.fundCode, { fromLibrary: false })" in html
    assert "fundLibraryModal.hidden = true;\n          openFundModal(info.code)" not in html
    assert "查看详情" in html
    assert "使用说明" in html
    assert 'data-open-usage-guide' in html
    assert 'id="usage-guide-modal" hidden' in html
    assert "Skill 选股逻辑" in html
    assert "不是先拿一张规则表机械筛选" in html
    assert "如何挑选：先看高成长主题是否仍有景气度" in html
    assert "怎么挑选：先按产业链卡点、稀缺层、主题暴露" in html
    assert "为什么挑选：Top5 先由 Serenity 判断决定，不由 Score 机械排序" in html
    assert "为什么调仓：当新一轮证据显示产业链强弱" in html
    assert "思考公示方式：页面展示证据置信度、等级、目标权重、基准权重" in html
    assert "ConfidenceScore = Data 25 + Timeliness 15 + Source 15 + Return 15 + Risk 20 + Executable 10" in html
    assert "SerenityRank_i = 产业链卡点优先级 + 主题暴露 + 场外可执行性" in html
    assert "ConfidenceModifier_i = 0.85 + 0.15 x ConfidenceScore_i / 100" in html
    assert "低 Serenity 优先级标的不会仅凭更高 ConfidenceScore 超过高优先级标的" in html
    assert "RawWeight_i = Score_i / sum(Top5 Score)" not in html
    assert "Deviation = TargetWeight - BaselineWeight" in html
    assert "凭什么：先确认数据质量通过、基金申赎和费率可执行" in html
    assert "为什么：偏离不是账户盈亏" in html
    assert "怎么做：|Deviation| &lt;= 1.00%：维持" in html
    assert "做多少：策略调整份额 = TargetWeight - BaselineWeight" in html
    assert "为什么做这么多：TargetWeight 已由 Serenity 优先级" in html
    assert "为什么 1.00% 内维持" in html
    assert "|Deviation| <= 5.00%" not in html
    assert "所有真实申购、赎回、增配、减配都必须在支付宝或官方平台人工确认" in html
    assert "0.80%" in html
    assert "无自动交易" in html
    assert "人工复核记录已复制" in html
    assert 'href="../../data/reports/sda_test_r7_report.html"' in html
    assert "../..//Users/" not in html


def test_markdown_report_uses_standard_display_time_format():
    markdown = render_markdown_report(
        "sda_test_r7",
        "R7",
        "2026-06-15T14:00:00+08:00",
        "2026-06-15T16:00:00+10:00",
        "success",
        "pass",
        "available",
        [],
        {"Shanghai Composite": {"1m": 0.01, "3m": 0.02, "10d": 0.03}},
        "notification",
    )

    assert "- Slot: R7" not in markdown
    assert "- 最新运行时间：20260615 - 14:00 CST" in markdown
    assert "- 北京时间：20260615 - 14:00 CST" in markdown
    assert "- 澳洲时间：20260615 - 16:00 AEST" in markdown
    assert "Serenity 每日分析正式报告" in markdown
    assert "Run Status" not in markdown
