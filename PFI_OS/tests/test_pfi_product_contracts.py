from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_pfi_contract_documents_exist():
    required = [
        "docs/product/PFI_OS_PRODUCT_CONSTITUTION.md",
        "docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md",
        "docs/product/PFI_FEATURE_DISPOSITION.md",
        "docs/data/PFI_DATA_BOUNDARIES.md",
        "docs/data/PFI_SOURCE_OF_TRUTH.md",
        "docs/ux/PFI_UX_CONTRACT.md",
        "docs/architecture/PFI_TARGET_ARCHITECTURE.md",
        "docs/archive/legacy-migration.md",
    ]

    missing = [path for path in required if not (ROOT / path).exists()]

    assert missing == []


def test_pfi_constitution_sets_product_boundaries():
    text = _read("docs/product/PFI_OS_PRODUCT_CONSTITUTION.md")

    assert "PFI-first controlled re-foundation" in text
    assert "PFI OS" in text
    assert "PFI_OS" in text
    assert "Strategy backtesting is a core workflow" in text
    assert "Market-feel training is retained" in text
    assert "No autonomous live trading" in text
    assert "DisabledProvider" not in text  # provider details belong in architecture, not product constitution
    assert "manual_review_queue" in text


def test_pfi_information_architecture_has_v02_target_and_six_compat_workspaces():
    text = _read("docs/product/PFI_OS_INFORMATION_ARCHITECTURE.md")
    v02_target = ["首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与同步", "建议与复盘", "报告与洞察"]
    current_compatibility = ["首页", "市场", "研究", "持仓", "策略实验室", "数据与系统"]

    for index, workspace in enumerate(v02_target, start=1):
        assert f"{index}. {workspace}" in text

    for index, workspace in enumerate(current_compatibility, start=1):
        assert f"{index}. {workspace}" in text

    assert "PFI V0.2 Stage 0" in text
    assert "docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md" in text
    assert "PFI/大数据模拟器" in text
    assert "投资管理 > 策略实验室 / 大数据模拟器" in text
    assert "ResearchBus is an internal" in text
    assert "训练模式" in text
    assert "Market-feel training lives under 训练模式" in text


def test_pfi_feature_disposition_locks_keep_delete_merge_decisions():
    text = _read("docs/product/PFI_FEATURE_DISPOSITION.md")

    assert "| Market-feel training | Keep and rebuild | 策略实验室 -> 训练模式 |" in text
    assert "| Single-symbol backtest | Keep kernel, rebuild UI | 策略实验室 -> 回测 |" in text
    assert "| Parameter scan | Keep kernel, rebuild UI | 策略实验室 |" in text
    assert "| ResearchBus page | Delete user entrance | Internal workflow/event layer |" in text


def test_pfi_data_contracts_keep_private_runtime_out_of_git():
    boundaries = _read("docs/data/PFI_DATA_BOUNDARIES.md")
    source_truth = _read("docs/data/PFI_SOURCE_OF_TRUTH.md")

    for domain in ["PUBLIC_SHARED_RAW", "PRIVATE_USER", "PRIVATE_DERIVED", "SECRET", "EPHEMERAL"]:
        assert domain in boundaries

    assert "$PFI_OS_DATA_HOME" in boundaries
    assert "Never commit" in boundaries
    assert "tracked `data/**` runtime artifacts" in boundaries
    assert "Operational SQLite" in source_truth
    assert "DuckDB + Parquet" in source_truth
    assert "ResearchBus is demoted" in source_truth
    assert "Market-feel training truth" in source_truth


def test_pfi_ux_and_architecture_contracts_cover_feedback_and_stack():
    ux = _read("docs/ux/PFI_UX_CONTRACT.md")
    architecture = _read("docs/architecture/PFI_TARGET_ARCHITECTURE.md")

    for marker in ["0-100ms", "over 300ms", "over 1s", "over 10s", "44px"]:
        assert marker in ux

    assert "human_review_required: true" in ux
    assert "Training mode must hide future bars" in ux
    assert "React/Next.js + TypeScript" in architecture
    assert "FastAPI" in architecture
    assert "DisabledProvider" in architecture
    assert "PFI_OS.app" in architecture
    assert "There is no live automatic order route" in architecture


def test_pfi_transition_entrypoints_point_to_contracts():
    agents = _read("AGENTS.md")
    readme = _read("README.md")
    plans = _read("PLANS.md")

    assert "PFI-First Transition Contract" in agents
    assert "PFI-First Transition Notice" in readme
    assert "PFI-001 Active Transition Plan" in plans
    assert "docs/product/PFI_OS_PRODUCT_CONSTITUTION.md" in readme
    assert "PFI-002" in plans
    assert "PFI-003" in plans
    assert "PFI-004" in plans


def test_retired_value_layer_is_archive_only():
    patterns = [
        "Token" + " ROI",
        "token" + "_roi",
        "token" + "Roi",
        "".join(["E", "V", "A", "Token"]),
    ]
    scanned = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] == "data":
            continue
        if str(relative) == "docs/archive/legacy-migration.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in patterns:
            if pattern in text:
                scanned.append(f"{relative}:{pattern}")

    assert scanned == []
