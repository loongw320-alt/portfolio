# Crypto Scraper — OKX Perpetual Market Radar

## English

A Python 3.10+ scraper that uses only the standard library. It pulls every USDT-margined perpetual from the OKX public API, then writes three ranked CSV files and a dark, mobile-friendly HTML report. No API key is needed and it never trades.

**How it works**
- One request to `/api/v5/market/tickers?instType=SWAP` and one bulk request to `/api/v5/public/funding-rate?instId=ANY`. Any contract missing from the bulk response is looked up individually.
- A full run (~525 contracts) takes about a second.
- 15-second timeouts, 3 attempts with exponential backoff, and OKX error codes are checked. A contract whose funding rate can't be fetched is kept with an empty value and a warning, never a fake zero.
- `--offline FILE` processes a saved JSON snapshot with zero network calls.

**Run it** (from this directory)

```sh
python3 scraper.py --output output                      # live
python3 scraper.py --offline ../market.json --output examples
python3 -m pytest tests                                 # or: python3 -m unittest discover -s tests
```

**Output**
- `report.html`: summary stats and three ranked tables ([live example](https://raw.githack.com/loongw320-alt/portfolio/main/crypto-scraper/examples/report.html)).
- `gainers.csv` (24h change, high→low), `losers.csv` (low→high), `funding.csv` (signed funding rate, high→low). UTF-8 with BOM so Excel opens them cleanly.
- `metadata.json`: source, generation time (UTC) and warnings.

```csv
rank,inst_id,last,change_24h_pct,funding_pct
1,NET-USDT-SWAP,265.01,-2.955178,0.147039
```

Units: 24h change = `(last / open24h − 1) × 100`; funding is the per-period rate in percent, not annualized. Missing values sort last; ties sort by instrument. Tickers and funding come from two requests, so the snapshot is not perfectly atomic. `examples/` is a real live run from 2026-11-04 and does not auto-update.

API reference: [OKX v5 docs](https://www.okx.com/docs-v5/en/).

---

## 中文

Python 3.10+，仅用标准库。在线请求 OKX `GET /api/v5/market/tickers?instType=SWAP`，过滤 `-USDT-SWAP`，用 `/api/v5/public/funding-rate?instId=ANY` 一次批量获取资金费率（缺失时再逐个补查），请求头固定 `User-Agent: curl/8`。输出最新价、24h 涨跌百分比、单期资金费率百分比，以及三份全量排行榜和自适应深色 HTML 报表。含超时、三次尝试、请求间隔；资金费获取失败保留合约并记录警告。

从本目录运行：

```sh
python3 scraper.py --offline ../market.json --output examples
python3 scraper.py --output output  # 在线，需要 OKX 网络可用
python3 -m unittest discover -s tests -v
```

`--offline JSON` 完全不请求网络。适配当前 `market.json` 数组：`sym` → 合约名，`last` → 最新价，`ch24` / `funding_pct` 已是百分数，不再乘 100；也支持 OKX `{ "code": "0", "data": [...] }` 或 ticker 数组，可附带 `fundingRate`。OKX `fundingRate` 为小数，乘 100；24h 涨跌为 `(last/open24h−1)×100`。无有效开盘价或费率显示空值，不伪造零。

`examples/` 是 2026-11-04 用在线模式实跑生成的真实 OKX 数据（生成时间见 `metadata.json`），非实时更新。在线模式获取 API 当次返回的全部 USDT 永续 ticker；全市场约 500+ 合约，在线运行通常 1 秒左右完成；行情与费率分两次请求，不保证同一时刻快照。

输出：[`examples/report.html`](examples/report.html)、`gainers.csv`（涨跌幅降序）、`losers.csv`（升序）、`funding.csv`（有符号费率降序，非绝对值）、`metadata.json`（来源、生成时间、警告）。三榜均含全部合约，缺失值置末，平手按合约名排序。CSV 使用 UTF-8 BOM，可直接用表格软件打开。

```csv
rank,inst_id,last,change_24h_pct,funding_pct
1,BTC-USDT-SWAP,76499.9,-0.38,0.01
```

以上仅演示字段格式，实际名次见 CSV。生成时间不是数据采集时间。无需 API key，无交易功能。
