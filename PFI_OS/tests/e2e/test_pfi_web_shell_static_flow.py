from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = PROJECT_ROOT / "web"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workspace_switching_is_local_state_without_full_page_reload():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "setActiveWorkspace" in js
    assert "const nextContext = { ...currentContext(), workspace: workspaceId }" in js
    assert "delete nextContext.feature_view" in js
    assert "writeContext(nextContext)" in js
    assert "main.dataset.activeWorkspace = workspaceId" in js
    assert "location.reload" not in js
    assert "window.location.href" not in js
    assert "window.open" not in js
    assert "href=\"/\"" not in html
    assert 'data-active-workspace="home"' in html


def test_homepage_summary_read_model_updates_cards_table_and_evidence_drawer():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert 'id="pfi-home-summary"' in html
    assert "readHomeSummary" in js
    assert "applyHomeSummary(readHomeSummary())" in js
    assert "applyDecisionRows" in js
    assert "applyEvidenceDrawer" in js
    assert "data-home-card" in html
    assert "data-home-decision-rows" in html
    assert "data-evidence-field" in html
    assert "PFIOSHomeSummaryV1" in html


def test_phase_c_workflow_cards_update_from_cached_runtime_summary():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "data-workflow-cards" in html
    assert "data-workflow-evidence" in html
    assert "applyWorkflowRuntime(summary.workflow_runtime || {})" in js
    assert "supervisor_runtime" in html
    assert "applySupervisorRuntime(runtime.supervisor_runtime)" in js
    assert "PFI-003 监督器" in js
    assert "localizedWorkflowCard" in js
    assert "fastPathLabel(runtime.fast_path)" in js
    assert "showWorkflowEvidence(card)" in js
    assert "setEvidenceDrawer(true)" in js
    assert "holdings_json" not in js
    assert "private holding" not in js.lower()


def test_response_feedback_acceptance_states_are_wired():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "instant: 100" in js
    assert "skeleton: 300" in js
    assert "stepped: 1000" in js
    assert "background: 10000" in js
    assert "setPressedFeedback" in js
    assert "requestAnimationFrame" in js
    assert "data-skeleton" in html
    assert "data-error-banner" in html
    assert "data-retry" in html
    assert "data-cache-fallback" in html
    assert "showRecoverableError" in js
    assert "已切换到缓存兜底" in js
    assert "后台任务 PFI-" in js


def test_task_center_evidence_drawer_and_command_palette_are_reachable():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "data-task-center" in html
    assert "data-task-toggle" in html
    assert "toggleTaskCenter" in js
    assert "data-evidence-drawer" in html
    assert "data-evidence-toggle" in html
    assert "setEvidenceDrawer" in js
    assert "data-command-palette" in html
    assert "openCommandPalette" in js
    assert "event.key.toLowerCase() === \"k\"" in js
    assert "Escape" in js


def test_compact_table_controls_have_filter_sort_and_export_interfaces():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "compact-table" in html
    assert "data-table-filter" in html
    assert "data-table-sort" in html
    assert "data-table-export" in html
    assert "filterRows" in js
    assert "sortRows" in js
    assert "exportRows" in js
    assert "pfi-decision-queue.json" in js


def test_accessibility_contract_covers_keyboard_focus_and_named_regions():
    html = _text(WEB_ROOT / "index.html")
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert "skip-link" in html
    assert "aria-label=\"一级工作区\"" in html
    assert "aria-label=\"全局上下文\"" in html
    assert "aria-label=\"证据抽屉\"" in html
    assert "aria-live=\"polite\"" in html
    assert "aria-live=\"assertive\"" in html
    assert ":focus-visible" in css
    assert "--pfi-target: 44px" in css


def test_six_primary_workspaces_render_distinct_chinese_business_panels():
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "const DEFAULT_WORKSPACES" in js
    for marker in ["今日总览", "市场监控", "证据研究", "持仓复核", "回测与训练", "数据治理"]:
        assert marker in js
    for required_call in [
        "renderCards(workspace.cards)",
        "renderFeatureCards(workspace.features)",
        "renderDecisionRows(workspace.rows)",
        "renderTasks(workspace.tasks)",
        "applyEvidenceDrawer(workspace.evidence)",
        "drawSparkline(workspace.chart)",
    ]:
        assert required_call in js
    assert 'detail.id = "task-phase"' in js
    assert 'detail.id = "background-job-label"' in js


def test_user_visible_shell_text_is_chinese_first_not_english_placeholders():
    active_text = "\n".join(
        [
            _text(WEB_ROOT / "index.html"),
            _text(WEB_ROOT / "app" / "shell.js"),
            _text(PROJECT_ROOT / "docs" / "ux" / "PFI_WEB_SHELL_ACCEPTANCE.md"),
        ]
    )
    forbidden_visible_text = [
        "Global Search",
        "Global context",
        "Open tasks",
        "Daily decision queue",
        "Workflow cards",
        "Refresh cached slice",
        "Evidence drawer",
        "Task Center",
        "Current work",
        "Could not refresh this slice",
        "Cached fallback is active",
        "Operational evidence",
        "DisabledProvider",
        "Fast Path Review",
    ]

    for fragment in forbidden_visible_text:
        assert fragment not in active_text


def test_feature_cards_have_working_open_actions_for_real_function_pages():
    html = _text(WEB_ROOT / "index.html")
    js = _text(WEB_ROOT / "app" / "shell.js")
    css = _text(WEB_ROOT / "styles" / "tokens.css")

    assert "data-function-detail" in html
    assert "FUNCTION_VIEWS" in js
    assert "openFunctionView" in js
    assert "renderFunctionDetail" in js
    assert "runFunctionAction" in js
    assert "navigateToFunctionPage" in js
    assert 'target = "_blank"' in js
    assert "anchor.click()" in js
    assert 'data-function-action>打开功能</a>' in html
    assert "进入${detail.title}功能页" in js
    assert "打开旧版详细页" not in html
    for view in ["single", "hotspots", "reports", "holdings"]:
        assert f'data-feature-view="{view}"' in html
    for view in ["single", "scan", "market_feel", "big_data", "hotspots", "reports", "holdings", "policy", "tools"]:
        assert f'view: "{view}"' in js
    assert "featureOpenControl" in js
    assert "legacyViewUrl" in js
    for mapped_view in ['legacyView: "hotspots"', 'legacyView: "holdings"', 'legacyView: "tools"', 'legacyView: "policy"', 'legacyView: "reports"']:
        assert mapped_view in js
    assert 'button.dataset.featureView = target.view' in js
    assert 'featureControl.dataset.featureView' in js
    assert 'appUrl.searchParams.set("pfi_shell", "0")' in js
    assert 'appUrl.searchParams.set("view", view)' in js
    assert "currentAppUrl()" in js
    assert "document.referrer" in js
    assert 'url.protocol === "about:"' in js
    assert 'url.pathname.includes("/component/")' in js
    assert "return appUrl.toString()" in js
    assert "dataset.featureWorkspace" in js
    assert ".workflow-actions" in css
    assert ".workflow-open" in css
    assert ".function-detail" in css
    assert "white-space: nowrap" in css


def test_streamlit_legacy_detail_nav_is_pfi_six_entry_surface():
    source = _text(PROJECT_ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py")
    nav_block = source.split("ACTIVE_PFI_VIEW_OPTIONS = {", maxsplit=1)[1].split("PFI_PRIMARY_NAV_LABELS", maxsplit=1)[0]
    navigation_source = source.split("def navigation_view", maxsplit=1)[1].split("def _view_key_from_target", maxsplit=1)[0]

    assert '("首页", "市场", "研究", "持仓", "策略实验室", "数据与系统")' in source
    for label in [
        "首页｜总控驾驶舱",
        "市场｜热点分析",
        "研究｜报告中心",
        "持仓｜持仓复核",
        "策略实验室｜单标的回测",
        "策略实验室｜盘感训练",
        "数据与系统｜数据中心",
    ]:
        assert label in nav_block
    for retired_nav in ["现金流", "消费守卫", "行研报告", "研究总线", "组合轮动"]:
        assert retired_nav not in nav_block
    assert "ACTIVE_PFI_VIEW_OPTIONS" in navigation_source
    assert "### PFI 六入口" in navigation_source
    assert "只保留当前 PFI 核心功能" in navigation_source


def test_streamlit_detail_pages_keep_runtime_compatible_controls():
    source = _text(PROJECT_ROOT / "src" / "pfi_os" / "app" / "streamlit_app.py")

    assert "def install_streamlit_runtime_compat" in source
    assert 'kwargs.get("width") == "stretch"' in source
    assert 'kwargs.setdefault("use_container_width", True)' in source
    assert "def _pfi_segmented_control" in source
    assert "return st.radio(label, options, index=index, key=key, horizontal=True)" in source
    assert "st.segmented_control(" not in source
    assert 'if selected_view in {"command", "tools"}:' in source


def test_runtime_summary_cannot_replace_core_home_feature_matrix():
    js = _text(WEB_ROOT / "app" / "shell.js")
    runtime_block = js.split("function applyWorkflowRuntime", maxsplit=1)[1].split("function localizedWorkflowCard", maxsplit=1)[0]

    for core_feature in ["单标的回测", "参数扫描", "盘感训练", "热点分析", "报告中心", "持仓", "政策雷达", "数据中心"]:
        assert core_feature in js
    assert "WORKSPACES.home.features" not in runtime_block


def test_date_context_defaults_to_browser_local_today_not_stale_hardcoded_value():
    js = _text(WEB_ROOT / "app" / "shell.js")

    assert "localDateValue(new Date())" in js
    assert "getTimezoneOffset" in js
