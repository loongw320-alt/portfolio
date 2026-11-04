# Crypto Scraper · 永续市场雷达

## 中文

Python 3.10+，仅用标准库。在线请求 OKX `GET /api/v5/market/tickers?instType=SWAP`，过滤 `-USDT-SWAP`，逐个查询 `/api/v5/public/funding-rate`，请求头固定 `User-Agent: curl/8`。输出最新价、24h 涨跌百分比、单期资金费率百分比，以及三份全量排行榜和自适应深色 HTML 报表。含超时、三次尝试、请求间隔；资金费获取失败保留合约并记录警告。

从本目录运行：

```sh
python3 scraper.py --offline ../market.json --output examples
python3 scraper.py --output output  # 在线，需要 OKX 网络可用
python3 -m unittest discover -s tests -v
```

`--offline JSON` 完全不请求网络。适配当前 `market.json` 数组：`sym` → 合约名，`last` → 最新价，`ch24` / `funding_pct` 已是百分数，不再乘 100；也支持 OKX `{ "code": "0", "data": [...] }` 或 ticker 数组，可附带 `fundingRate`。OKX `fundingRate` 为小数，乘 100；24h 涨跌为 `(last/open24h−1)×100`。无有效开盘价或费率显示空值，不伪造零。

示例来自仓库提供的快照，采集时间未知，非实时、非全市场覆盖证明。在线模式获取 API 当次返回的全部 USDT 永续 ticker；逐次请求不保证同一时刻快照。

输出：[`examples/report.html`](examples/report.html)、`gainers.csv`（涨跌幅降序）、`losers.csv`（升序）、`funding.csv`（有符号费率降序，非绝对值）、`metadata.json`（来源、生成时间、警告）。三榜均含全部合约，缺失值置末，平手按合约名排序。CSV 使用 UTF-8 BOM，可直接用表格软件打开。

```csv
rank,inst_id,last,change_24h_pct,funding_pct
1,BTC-USDT-SWAP,76499.9,-0.38,0.01
```

以上仅演示字段格式，实际名次见 CSV。生成时间不是数据采集时间。无需 API key，无交易功能。

## English

A Python 3.10+ standard-library monitor for all USDT perpetual tickers returned by OKX. Fetches latest prices, 24-hour changes and individual funding rates using `User-Agent: curl/8`; includes timeouts, retries and paced requests. Funding failures retain the instrument with a missing value and a warning.

Run the commands above from this directory. `--offline ../market.json` makes no network requests. Local `sym/last/ch24/funding_pct` snapshots use percentage units already; raw OKX ticker lists or successful `data` envelopes are also supported. OKX fractional funding rates are converted to percentages; change is `(last/open24h−1)×100`. Missing data stays missing.

Open `examples/report.html` locally. The three CSV files rank all contracts by descending change, ascending change and descending signed funding; missing values sort last, ties by instrument. `metadata.json` records provenance, report-generation time and warnings. The supplied example is an offline snapshot with unknown capture time, not a live or complete-market assertion. Online requests are sequential, not an atomic snapshot. The CSV snippet illustrates the schema, not the real ranking. No API key or trading functionality.

API reference / 接口文档：[OKX official documentation](https://www.okx.com/docs-v5/en/).
