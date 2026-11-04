# Discord Market Bot — Prices, Alerts & Moderation

## English

A Python 3.10+ / discord.py 2.x bot for crypto communities.

**Commands** (all replies are private to the user)

| Command | What it does |
| --- | --- |
| `/price symbol:BTC` | Latest OKX USDT-perpetual price |
| `/alert symbol:BTC target:80000 direction:above` | One-shot alert, saved to disk and restored after restarts |
| `/alerts` | Lists your active alerts with short ids |
| `/cancel alert_id:1a2b3c4d` | Deletes one of your alerts (full id or a unique prefix of 4+ characters) |

**Also included**
- Welcome message for new members in the server's system channel.
- Keyword moderation: messages that contain a blocked word are deleted. Matching is case-insensitive and on whole words, so `scam` catches "total SCAM!" but not "scamper". CJK keywords match as substrings because those languages don't put spaces between words.
- Alerts are checked every 60 seconds, with one price request per symbol. Network calls run in worker threads so the bot never blocks.
- Data is saved atomically, capped at 20 alerts per user, and a failed delivery is kept and retried. Only the alert owner is ever mentioned.

**Setup**

```sh
cd discord-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DISCORD_TOKEN='your-bot-token'
export DISCORD_GUILD_ID='your-test-server-id'   # optional: instant command registration
python3 bot.py
```

In the Discord Developer Portal, enable the **Server Members** and **Message Content** intents. Invite the bot with the `bot` and `applications.commands` scopes and the View Channels, Send Messages and Manage Messages permissions.

Optional settings:
- `ALERTS_FILE` changes where alerts are stored (default `alerts.json` next to the script).
- `FILTER_KEYWORDS` takes a comma-separated list; an empty value turns filtering off.

`.env.example` lists the variables, but the bot reads them from the environment and doesn't load `.env` itself.

**Example**

```text
/price symbol:BTC                                  → BTC-USDT-SWAP: 76499.9 USDT
/alert symbol:BTC target:80000 direction:above     → Saved: BTC-USDT-SWAP above 80000 USDT
/alerts                                            → `1a2b3c4d` BTC-USDT-SWAP above 80000 USDT
when triggered                                     → @you 🔔 BTC-USDT-SWAP: 80001 USDT | above 80000
```

**Tests** run offline with HTTP mocked: `python3 -m pytest tests`, or `python3 -m unittest discover -s tests`.

**Known limits**
- Polling every 60 seconds can miss very brief price spikes.
- If the bot crashes right after sending an alert, the alert may be sent twice.
- Edited messages are not re-checked by the filter.
- Run one bot process per alerts file.

---

## 中文

Python 3.10+ / discord.py 2.x 行情机器人。命令：`/price` 查价，`/alert` 设一次性提醒（存盘，重启后自动恢复），`/alerts` 查看自己的提醒，`/cancel` 按 ID（至少 4 位前缀）删除提醒。另外支持欢迎新成员和关键词过滤：英文按整词匹配、不区分大小写，中日韩关键词按子串匹配。每 60 秒检查一次，每人最多 20 条提醒。安装和权限设置见上方英文部分：要开启 Server Members 和 Message Content 两个 Intent，并授予 Manage Messages 权限。
