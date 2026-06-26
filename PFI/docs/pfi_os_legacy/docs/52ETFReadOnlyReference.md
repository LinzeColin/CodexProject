# 52ETF Read-Only Reference

`52ETF Read-Only Reference` 是 PFI_OS 热点分析的公开市场云图参考层。它读取 `https://52etf.site/` 首页公开可见的“大盘云图 / A股热力图”页面契约，生成低 token snapshot，用于对照 PFI_OS 自有热点对象池和 UI 交互口径。

## 目的

- 减少热点页面每次打开时的网络等待。
- 把 52ETF 页面契约固化为可复核的 latest JSON。
- 让后续 agent 不需要读取完整网页或 UI 上下文，也能知道 52ETF 当前作为只读参考是否可用。
- 保持 52ETF 只作为公开 UI/reference，不进入回测、订单、持仓或交易前证据。

## 使用命令

刷新本地 latest snapshot：

```bash
$PFI_OS_HOME/scripts/site52etfSnapshot.sh --output-dir data/integrations/site52etf
```

只看低 token 摘要：

```bash
$PFI_OS_HOME/scripts/site52etfSnapshot.sh --summary-json
```

使用本地 HTML fixture 做离线验证：

```bash
$PFI_OS_HOME/scripts/site52etfSnapshot.sh --source-html /path/to/52etf_sample.html --output-dir /tmp/pfi_site52etf_snapshot
```

## 输出位置

默认输出目录：

```text
data/integrations/site52etf
```

主要文件：

```text
Site52ETFPublicSnapshot_DDMMYYYY.json
Site52ETFPublicSnapshot_latest.json
```

该目录下生成的 JSON 是本地 runtime artifact，默认被 `.gitignore` 忽略；仓库只保留 `.gitkeep`。

## Snapshot Contract

输出 schema：

```text
PFIOS52ETFPublicSnapshotV1
```

关键字段：

- `status`: `Available`、`Partial` 或 `Unavailable`。
- `artifact_status`: `Pass` 或 `NeedsReview`。
- `boards`: 页面可见 A 股云图板块。
- `metrics`: 页面可见指标词，例如上涨、平盘、下跌、成交额。
- `operating_notes`: 页面可见操作提示。
- `refresh_cadence_seconds`: 从页面提示解析出的刷新节奏，目前公开页面提示为 8 秒。
- `interactions`: 双击 K 线、方向键复盘、全屏提示等交互能力。
- `evidence_gate`: SourceReachability、MarketCloudContract、InteractionNotes、ReadOnlyBoundary。
- `token_policy`: 不保存 raw HTML。
- `safety_boundary`: 只读公开参考，不替代 PFI_OS 本地/provider 数据质量闸门。

## UI Behavior

热点页面勾选 `显示 52ETF 公开参考` 后：

- 优先读取 `data/integrations/site52etf/Site52ETFPublicSnapshot_latest.json`。
- 如果 latest 缺失，才按 Streamlit cache TTL 在线读取公开页面。
- 如果公开页面不可用，页面降级为 Review/Unavailable，但本地热点分析继续运行。
- 如果 Python `urllib` 因本机证书链失败无法读取公开页面，系统会尝试 `/usr/bin/curl` 读取同一个公开 URL；curl 失败仍 fail-closed。

## Safety Boundary

52ETF 接入不做以下事情：

- 不作为正式行情源。
- 不写入回测输入。
- 不触发交易、订单、持仓或券商动作。
- 不替代本地数据质量检查。
- 不保存 raw HTML、cookies、登录态或账号信息。
