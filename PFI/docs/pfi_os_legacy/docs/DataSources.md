# DataSources

## Principles

数据必须真实、及时、可靠、可验证、可追溯。

Data must be authentic, timely, reliable, verifiable, and traceable.

每次数据请求都应记录数据源、标的、市场、时间区间、周期、请求时间和行数。

Each data request should record provider, symbol, market, date range, interval, request time, and row count.

## Priority

真实数据优先使用 Moomoo，其次 A 股使用 TuShare 和 AKShare。

Real data should prioritize Moomoo first, then TuShare and AKShare for A-shares.

美股第二优先接入 Alpha Vantage、Polygon 和 Yahoo Finance。

US stocks should next use Alpha Vantage, Polygon, and Yahoo Finance.

moomoo AU 只考虑行情接口，不接交易接口。

moomoo AU is considered for quote data only, not trading APIs.

## Supported Providers

`Sample` 用于演示和测试，不代表真实市场。

`Sample` is for demos and tests only and does not represent the real market.

`Sample` 会按代码和时间戳稳定生成演示行情。同一个代码、同一个时间点在不同请求起点下应返回相同价格和成交量，避免因为改变展示开始日期而造成情绪分或热点热度不合理跳变。

`Sample` generates demo bars deterministically by symbol and timestamp. The same symbol and timestamp should return the same price and volume regardless of request start date, preventing sentiment or hotspot scores from jumping only because the display start date changed.

`CSV` 用于导入你已经下载或购买的数据。

`CSV` imports data that you already downloaded or purchased.

`Moomoo` 作为优先真实数据入口，需要本机安装 `futu-api` 并启动 Moomoo OpenD；系统只使用行情接口，不接交易接口。

`Moomoo` is the primary real-data entry and requires local `futu-api` plus Moomoo OpenD; the system uses quote APIs only and does not connect to trading APIs.

`AKShare` 用于 A 股历史行情，当前优先支持日线、周线和月线。

`AKShare` is used for A-share historical bars and currently prioritizes daily, weekly, and monthly data.

`TuShare` 用于 A 股日线行情，需要 `TUSHARE_TOKEN`。

`TuShare` is used for A-share daily bars and requires `TUSHARE_TOKEN`.

`Yahoo Finance` 用于美股和 ETF 行情，通过 `yfinance` 获取。

`Yahoo Finance` is used for US stocks and ETFs through `yfinance`.

`Alpha Vantage` 用于美股和 ETF 行情，需要 `ALPHA_VANTAGE_API_KEY`。

`Alpha Vantage` is used for US stocks and ETFs and requires `ALPHA_VANTAGE_API_KEY`.

`Polygon` 用于美股聚合行情，需要 `POLYGON_API_KEY`。

`Polygon` is used for US aggregate market data and requires `POLYGON_API_KEY`.

## Supported Intervals

工作台周期选择支持 `1min`、`5min`、`15min`、`30min`、`60min`、`1d`、`1w`、`1m`、`1q` 和 `1y`。

The workbench interval selector supports `1min`, `5min`, `15min`, `30min`, `60min`, `1d`, `1w`, `1m`, `1q`, and `1y`.

不同真实数据源的原生周期能力不同。Moomoo、Yahoo Finance 和 Polygon 通常覆盖分钟线到月线，AKShare 优先覆盖 A 股日线、周线和月线，TuShare 当前用于 A 股日线。

Native interval support differs by provider. Moomoo, Yahoo Finance, and Polygon usually cover minute bars through monthly bars; AKShare prioritizes A-share daily, weekly, and monthly bars; TuShare is currently used for A-share daily bars.

当所选数据源不原生支持 `1w`、`1m`、`1q` 或 `1y` 时，PFIOS 会尝试从日线或月线本地重采样。

When the selected provider does not natively support `1w`, `1m`, `1q`, or `1y`, PFIOS attempts local resampling from daily or monthly bars.

本地重采样不会伪造额外价格点，只会按 OHLCV 规则汇总已有数据：open 取第一条，high 取最高，low 取最低，close 取最后一条，volume 求和。

Local resampling does not fabricate extra price points. It aggregates existing bars with OHLCV rules: open uses the first value, high uses the maximum, low uses the minimum, close uses the last value, and volume is summed.

如果发生重采样，数据质量报告的 notes 字段会记录基础周期，例如 `Resampled locally from 1m bars`。

If resampling happens, the data quality report records the base interval in the notes field, such as `Resampled locally from 1m bars`.

## Data Quality

每次下载数据后，系统会生成数据质量报告。

The system creates a data quality report after each data download.

质量报告保存到 `~/Downloads/量化回测分析/YYYY-MM-DD/DataQuality/`。

Quality reports are saved to `~/Downloads/量化回测分析/YYYY-MM-DD/DataQuality/`.

质量报告包含 provider、symbol、market、interval、row_count、missing_values、duplicate_datetimes、checksum 和 quality_status。

Quality reports include provider, symbol, market, interval, row_count, missing_values, duplicate_datetimes, checksum, and quality_status.

`quality_status = Pass` 表示关键字段没有缺失值且时间戳没有重复。

`quality_status = Pass` means required fields have no missing values and timestamps are not duplicated.

`quality_status = Review` 表示数据需要人工检查。

`quality_status = Review` means the data requires manual review.

`quality_status = Empty` 表示数据源没有返回记录。

`quality_status = Empty` means the provider returned no rows.

## A-Share Symbol Helper

A 股代码助手支持 `000001`、`000001.SZ`、`SZ000001`、`600000.SH` 和 `SH600000` 等格式。

The A-share symbol helper supports formats such as `000001`, `000001.SZ`, `SZ000001`, `600000.SH`, and `SH600000`.

它的作用是把同一个 A 股代码转换成不同数据源需要的格式。

Its purpose is to convert the same A-share code into the formats required by different data providers.

AKShare 使用纯六位代码，例如 `000001`。

AKShare uses the six-digit code, such as `000001`.

TuShare 使用带交易所后缀的代码，例如 `000001.SZ`。

TuShare uses exchange-suffixed codes, such as `000001.SZ`.

Moomoo 使用市场前缀格式，例如 `SZ.000001` 或 `SH.600000`。

Moomoo uses market-prefixed formats, such as `SZ.000001` or `SH.600000`.

## Cross-Source Validation

多源交叉校验会把多个数据源的同一标的按日期对齐，并比较收盘价差异。

Cross-source validation aligns the same symbol across providers by date and compares close price differences.

如果最大差异超过阈值，结果会标记为 `Review`。

If the maximum difference exceeds the tolerance threshold, the result is marked as `Review`.

如果数据没有重叠日期，结果会标记为 `NoOverlap`。

If the data has no overlapping dates, the result is marked as `NoOverlap`.

## Credential Rules

不要把 API Key 写入源码、报告或测试输出。

Do not write API keys into source code, reports, or test output.

优先使用 `.env` 管理本地数据源凭证。

Use `.env` for local data source credentials.

`.env` 文件放在 `$PFI_OS_HOME/.env`。

The `.env` file should be placed at `$PFI_OS_HOME/.env`.

可以从 `.env.example` 复制变量名，然后只填写你实际拥有的 key。

You can copy variable names from `.env.example`, then fill only the keys you actually have.

也可以运行脚本创建 `.env` 模板。脚本不会覆盖已有 `.env`。

You can also run the setup script to create the `.env` template. It does not overwrite an existing `.env`.

```bash
$PFI_OS_HOME/scripts/setupEnv.sh
```

```text
TUSHARE_TOKEN=your_tushare_token
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
POLYGON_API_KEY=your_polygon_key
MOOMOO_HOST=127.0.0.1
MOOMOO_PORT=11111
```

如果同一个 key 同时存在于系统环境变量和 `.env` 文件，系统环境变量优先。

If the same key exists both in exported environment variables and in `.env`, the exported environment variable takes priority.

## Real-Data Validation

联网验证真实数据源：

Validate real data providers through the network:

```bash
$PFI_OS_HOME/scripts/validateRealData.sh
```

Moomoo 只读行情诊断：

Moomoo quote-only diagnostic:

```bash
$PFI_OS_HOME/scripts/checkMoomoo.sh
```

Moomoo 诊断会按顺序检查 `futu-api` 是否安装、Moomoo OpenD 端口是否可连接、历史 K 线行情是否可返回数据，并生成数据质量报告。

The Moomoo diagnostic checks whether `futu-api` is installed, whether the Moomoo OpenD port is reachable, whether historical K-line quote data can be returned, and then creates a data quality report.

如果状态是 `NeedsPackage`，需要在 PFIOS 环境安装 `futu-api`。

If the status is `NeedsPackage`, install `futu-api` in the PFIOS environment.

如果状态是 `NeedsOpenD`，需要启动 Moomoo OpenD，并确认 `.env` 中的 `MOOMOO_HOST` 和 `MOOMOO_PORT`。

If the status is `NeedsOpenD`, start Moomoo OpenD and confirm `MOOMOO_HOST` and `MOOMOO_PORT` in `.env`.

打开 moomoo 桌面程序不等于启动 OpenD；只有 `127.0.0.1:11111` 端口可连接时，PFIOS 才能读取 Moomoo 行情。

Opening the moomoo desktop app is not the same as starting OpenD. PFIOS can read Moomoo quote data only when `127.0.0.1:11111` is reachable.

多源交叉校验脚本：

Cross-source validation script:

```bash
$PFI_OS_HOME/scripts/validateCrossSource.sh
```

当前脚本验证 Yahoo Finance 的 `AAPL` 和 AKShare 的 `600000`，并生成数据质量报告。

The current script validates Yahoo Finance `AAPL` and AKShare `600000`, then generates data quality reports.

AKShare/Eastmoney 偶尔会远端断开，脚本会自动重试并尝试备用 A 股标的。

AKShare/Eastmoney may occasionally disconnect remotely, so the script retries automatically and tries backup A-share symbols.

TuShare、Alpha Vantage 和 Polygon 需要先配置对应 API Key。

TuShare, Alpha Vantage, and Polygon require their API keys first.

当同一市场只有一个真实数据源可用时，交叉校验脚本会跳过并说明原因，不会伪造比较结果。

When only one real provider is available for a market, the cross-source script skips with an explanation and does not fabricate a comparison.

## Notes

分钟级数据通常存在历史长度、延迟和接口权限限制。

Minute-level data often has history length, delay, and entitlement limits.

Yahoo Finance 和 AKShare 是便捷数据源，正式研究时仍应与其他来源交叉验证。

Yahoo Finance and AKShare are convenient data sources, but serious research should cross-check them against other sources.
