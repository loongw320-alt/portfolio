# Local Developer Portfolio · 本地开发作品集

三个可独立运行的小项目，展示行情数据处理、异步机器人与前端风险计算。

Three independent projects covering market-data processing, an asynchronous bot and a browser-based risk calculator.

| 项目 / Project | 亮点 / Highlights | 入口 / Entry |
| --- | --- | --- |
| [Crypto Scraper](crypto-scraper/README.md) | 标准库 OKX 行情采集、离线适配、三类 CSV 排行 / Standard-library ingestion, offline snapshots and ranked CSVs | [HTML 示例 / Report](crypto-scraper/examples/report.html) |
| [Discord Bot](discord-bot/README.md) | 斜杠命令、持久化价格提醒、新人欢迎和关键词过滤 / Slash commands, persistent alerts, welcomes and filtering | [机器人模板 / Template](discord-bot/bot.py) |
| [Position Calculator](position-calc/README.md) | 无依赖本地仓位、止损与逐仓爆仓近似计算 / Dependency-free position sizing and isolated liquidation estimates | [打开计算器 / Open calculator](position-calc/index.html) |

## 在线预览 / Live preview (phone-friendly)

- [Crypto Scraper report](https://raw.githack.com/loongw320-alt/portfolio/main/crypto-scraper/examples/report.html)
- [Position Calculator](https://raw.githack.com/loongw320-alt/portfolio/main/position-calc/index.html)

## 快速体验 / Quick start

Python 项目要求 Python 3.10+。从本目录执行 / Python projects require Python 3.10+. From this directory:

```sh
python3 crypto-scraper/scraper.py --offline market.json --output crypto-scraper/examples
(cd crypto-scraper && python3 -m unittest discover -s tests -v)
(cd discord-bot && python3 -m py_compile bot.py logic.py && python3 -m unittest discover -s tests -v)
```

用浏览器打开 `crypto-scraper/examples/report.html` 或 `position-calc/index.html`。启动机器人需安装依赖、配置 Discord token 与服务器权限，详见项目 README；本地检查无需连接 Discord。

Open either HTML file in a browser. Running the bot requires dependencies, a Discord token and server permissions; see its README. Local checks do not connect to Discord.

`market.json` 为已有的 30 条行情快照，原文件保留，采集时间未知。示例不是实时行情，离线处理不会补造全市场数据。每个项目 README 均含中英双语功能、运行方式与输出示例。

The existing `market.json` contains 30 snapshot rows and is preserved unchanged. Capture time is unknown. Examples are not live quotes; offline processing does not invent full-market coverage. Each project has bilingual features, setup instructions and output examples.
