from __future__ import annotations

from dataclasses import asdict, dataclass


VERSION_NAME = "v0.2.1.1 Product UI Recovery"
STAGE0_TASK_ID = "V0211-S0-T01"
STAGE1_TASK_ID = "V0211-S1-T01"
TOTAL_EXECUTION_STAGES = 6


@dataclass(frozen=True)
class V0211SourceFile:
    label: str
    path: str
    role: str


@dataclass(frozen=True)
class V0211ExecutionStage:
    stage_id: str
    name: str
    inherited_phase_scope: tuple[str, ...]
    delivery_focus: tuple[str, ...]
    forbidden_work: tuple[str, ...]
    acceptance_gate: tuple[str, ...]


@dataclass(frozen=True)
class V0211Decision:
    item: str
    source_conflict: str
    default_resolution: str
    stage_to_finalize: str


SOURCE_FILES: tuple[V0211SourceFile, ...] = (
    V0211SourceFile(
        "用户 RTF 纠偏稿",
        "/Users/linzezhang/Downloads/v0.2.1.1.rtf",
        "最新产品判断和反 AI 演示壳约束",
    ),
    V0211SourceFile(
        "Markdown taskpack roadmap",
        "/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md",
        "受控重构任务包、验收条件和禁止事项",
    ),
)


RTF_PRIMARY_NAVIGATION = (
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
)

MARKDOWN_PRIMARY_NAVIGATION = (
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "设置",
)

LEGACY_ROUTE_ALIASES = {
    "首页": "首页总览",
    "市场": "市场与研究",
    "研究": "市场与研究",
    "持仓": "投资管理 > 持仓",
    "策略实验室": "市场与研究 > 策略实验室",
    "数据与系统": "设置 > 数据与系统",
}


EXECUTION_STAGES: tuple[V0211ExecutionStage, ...] = (
    V0211ExecutionStage(
        "S0",
        "准备轮：失败冻结与执行锁",
        ("Phase 0", "Stage 0.1", "资料读取", "路线纠偏"),
        (
            "标记当前 v0.2.1 前端优化不再作为正式 UI 交付基础",
            "锁定 6 个执行 Stage，纠正 roadmap 中 Phase/Stage 的母子关系",
            "建立来源清单、路线锁、Stage 0 合同和目标测试",
            "记录导航数量与策略实验室归属的来源差异和默认处理",
        ),
        (
            "不修改正式 Web Shell",
            "不重建导航",
            "不实现图表、上传、持仓保存或报告",
            "不声明 v0.2.1.1 完成",
        ),
        (
            "Stage 0 文档可读",
            "合同测试通过",
            "下一轮只能进入 Stage 1",
        ),
    ),
    V0211ExecutionStage(
        "S1",
        "产品壳与路由",
        ("原 P0", "原 P1"),
        (
            "重建正式主导航",
            "建立一级页面状态和 active 状态",
            "旧入口只作为 route alias、搜索别名或二级入口",
            "浏览器前进后退可用",
        ),
        (
            "不做图表",
            "不做上传闭环",
            "不做持仓编辑",
            "不做报告",
        ),
        (
            "真实浏览器点击路径：首页总览 -> 投资管理 -> 设置 -> 后退 -> 投资管理",
            "浏览器前进后退可用",
            "首页无设置栏、运行边界、反馈控制台、手机预览和 Task Pack",
        ),
    ),
    V0211ExecutionStage(
        "S2",
        "页面骨架与去 AI 化",
        ("原 P2", "原 P3"),
        (
            "清理正式 UI 中开发者词、演示模块和默认反馈控制台",
            "建立首页、账户、投资、消费、数据源、建议、报告、设置页面骨架",
            "设置内容只在设置页出现",
        ),
        (
            "不做数据库 migration",
            "不伪造趋势数据",
            "不写字符串式假验收",
        ),
        (
            "全局可见中文扫描通过",
            "各页面二级入口真实切换",
            "无开发者词污染正式页面",
        ),
    ),
    V0211ExecutionStage(
        "S3",
        "真实操作流",
        ("原 P4"),
        (
            "上传、解析预览、字段映射、待复核和确认入库路径",
            "账本筛选、分类、复核和导出路径",
            "持仓编辑表单和设置保存路径",
        ),
        (
            "不以 toast 代替真实操作",
            "不把生产保存写进 localStorage、sessionStorage 或 IndexedDB",
            "不新增测试数据污染正式页面",
        ),
        (
            "上传、账本、持仓编辑、设置保存均有真实浏览器行为验收",
            "无真实数据时显示中文空状态",
        ),
    ),
    V0211ExecutionStage(
        "S4",
        "持久化与同步",
        ("原 P6"),
        (
            "持仓修改写入本地 SQLite",
            "刷新页面和重启服务后仍可读取",
            "首页、投资图表和报告读取同一持仓读模型",
        ),
        (
            "不把浏览器缓存作为生产持久化来源",
            "不跳过 SQLite 查询验收",
            "不声明真实账户生产联通",
        ),
        (
            "页面编辑 -> 保存 -> SQLite 查询 -> 重启服务 -> 页面读取通过",
            "首页、投资、报告数据一致",
        ),
    ),
    V0211ExecutionStage(
        "S5",
        "真实图表与最终验收",
        ("原 P5", "原 P7"),
        (
            "账户、投资、消费趋势图读取真实数据层或显示中文空状态",
            "所有一级入口、二级入口和主要按钮真实可点",
            "桌面端和移动端截图验收",
            "最终验收禁止关键词测试替代行为测试",
        ),
        (
            "不伪造收益或消费趋势",
            "不使用 demo/sample/synthetic/fixture/mock/fake 数据作为产品依据",
            "不把截图路径当作截图证据",
        ),
        (
            "Playwright 或等效真实浏览器 E2E 通过",
            "图表数据源测试通过",
            "禁词和开发词 visible text scan 通过",
        ),
    ),
)


DECISIONS: tuple[V0211Decision, ...] = (
    V0211Decision(
        "正式主导航数量",
        "Markdown roadmap 写 9 个入口；RTF v0.2.1.1 纠偏稿写 10 个入口并加入市场与研究。",
        "Stage 1 默认按 RTF 最新稿执行：10 个正式入口，市场与研究作为一级入口；如用户明确要求 9 项，则 Stage 1 前更新本合同。",
        "S1",
    ),
    V0211Decision(
        "策略实验室归属",
        "旧 v0.2.1 合同归属投资管理；RTF 最新稿要求全系统唯一位置为市场与研究 > 策略实验室。",
        "Stage 1 默认按 RTF 最新稿执行：旧策略实验室入口重定向到市场与研究 > 策略实验室，不能生成第二个页面。",
        "S1",
    ),
    V0211Decision(
        "图表与持久化顺序",
        "Markdown 执行策略把图表放在持久化前；RTF 末段强调先做真实操作和持久化，再做图表。",
        "v0.2.1.1 执行顺序按用户最新纠偏：S3 操作流，S4 持久化，S5 图表与最终验收。",
        "S0",
    ),
)

STAGE0_FORBIDDEN_FILE_CHANGES = (
    "PFI/web/index.html",
    "PFI/web/app/shell.js",
    "PFI/src/pfi_os/app/streamlit_app.py",
)

STAGE1_PRIMARY_NAVIGATION = RTF_PRIMARY_NAVIGATION

STAGE1_LEGACY_ROUTE_ALIASES = {
    "首页": "/home",
    "市场": "/market-research?tab=market",
    "研究": "/market-research?tab=research",
    "持仓": "/investment?tab=holdings",
    "策略实验室": "/market-research/strategy-lab",
    "数据与系统": "/settings?tab=data-system",
}


def build_v0211_stage0_contract() -> dict[str, object]:
    return {
        "schema": "PFIV0211ProductUIRecoveryStage0ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S0 准备轮",
        "task_id": STAGE0_TASK_ID,
        "project_root": "CodexProject/PFI",
        "total_execution_stages": TOTAL_EXECUTION_STAGES,
        "one_run_max_stage_count": 1,
        "current_stage_only": True,
        "stage_parent_child_rule": "Stage is the pursuing-goal run gate; phase and task are children inside each Stage.",
        "product_register": "product",
        "source_files": [asdict(item) for item in SOURCE_FILES],
        "primary_navigation_default": RTF_PRIMARY_NAVIGATION,
        "primary_navigation_markdown_variant": MARKDOWN_PRIMARY_NAVIGATION,
        "legacy_route_aliases": LEGACY_ROUTE_ALIASES,
        "execution_stages": [asdict(item) for item in EXECUTION_STAGES],
        "decisions": [asdict(item) for item in DECISIONS],
        "stage0_forbidden_file_changes": STAGE0_FORBIDDEN_FILE_CHANGES,
        "stage0_stop_conditions": (
            "开始修改正式 Web Shell",
            "声明 v0.2.1.1 已完成",
            "把 Stage 1-5 提前并入 Stage 0",
            "继续把当前 v0.2.1 前端优化写成正式交付完成",
            "用字符串检查替代后续真实浏览器行为验收",
        ),
        "stage1_entry_conditions": (
            "Stage 0 合同测试通过",
            "路线锁文档存在",
            "三基文件已记录当前任务和下一轮边界",
            "工作区未因 Stage 0 触碰正式 UI shell",
        ),
    }


def build_v0211_stage1_contract() -> dict[str, object]:
    stage = next(item for item in EXECUTION_STAGES if item.stage_id == "S1")
    return {
        "schema": "PFIV0211ProductUIRecoveryStage1ContractV1",
        "version_name": VERSION_NAME,
        "stage": "S1 产品壳与路由",
        "task_id": STAGE1_TASK_ID,
        "project_root": "CodexProject/PFI",
        "primary_navigation_count": len(STAGE1_PRIMARY_NAVIGATION),
        "primary_navigation": STAGE1_PRIMARY_NAVIGATION,
        "legacy_route_aliases": STAGE1_LEGACY_ROUTE_ALIASES,
        "delivery_focus": stage.delivery_focus,
        "forbidden_work": stage.forbidden_work,
        "acceptance_gate": stage.acceptance_gate,
        "browser_route_contract": {
            "state_source": "hash route",
            "click_updates_history": True,
            "back_forward_supported": True,
            "home_route": "/home",
            "strategy_lab_route": "/market-research/strategy-lab",
        },
        "home_forbidden_visible_text": (
            "运行边界",
            "Task Pack",
            "Demo",
            "Prototype",
            "手机预览",
            "运行反馈控制台",
            "多模态交互反馈",
        ),
        "stage1_non_goals": (
            "不做图表",
            "不做上传闭环",
            "不做持仓编辑",
            "不做报告",
            "不声明 v0.2.1.1 完成",
        ),
    }


def v0211_stage_ids() -> tuple[str, ...]:
    return tuple(stage.stage_id for stage in EXECUTION_STAGES)


def v0211_default_navigation_labels() -> tuple[str, ...]:
    return RTF_PRIMARY_NAVIGATION


def v0211_stage1_navigation_labels() -> tuple[str, ...]:
    return STAGE1_PRIMARY_NAVIGATION
