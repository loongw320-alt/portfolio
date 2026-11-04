# Discord Market Bot · 行情与提醒机器人

## 中文

Python 3.10+ / discord.py 2.x 模板：`/price` 查询 OKX USDT 永续最新价；`/alert` 设置 above / below 一次性提醒；每 60 秒轮询，每轮相同币种合并查询；JSON 原子替换保存，重启恢复。新成员加入时向服务器系统频道发送欢迎语；关键词大小写不敏感子串过滤并删除消息。HTTP 调用放入工作线程，避免阻塞 Discord 事件循环。

```sh
cd discord-bot  # 从作品集根目录开始
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
export DISCORD_TOKEN='你的机器人 token'
export DISCORD_GUILD_ID='测试服务器 ID'  # 可选；省略则注册全局命令
python3 bot.py
```

`.env.example` 为环境变量说明；程序不会自动读取 `.env`。不把真实 token 写入代码。可用 `ALERTS_FILE` 改存储路径，`FILTER_KEYWORDS` 设置逗号分隔关键词（空字符串关闭过滤）。默认 `alerts.json` 位于脚本目录；单进程运行，不支持多实例同时写同一文件。损坏 JSON 会阻止启动以避免覆盖原数据。

在 Discord Developer Portal 开启 **Server Members Intent** 与 **Message Content Intent**；以 `bot` 和 `applications.commands` scopes 邀请，授予 View Channels、Send Messages、Manage Messages。欢迎功能需要配置系统频道。只为提醒目标用户开启 mention，其他消息禁止自动提及。全局命令注册可能延迟。

交互示例（演示，非实时价格）：

```text
/price symbol:BTC
→ BTC-USDT-SWAP: 76499.9 USDT
/alert symbol:BTC target:80000 direction:above
→ 已保存 / Saved: BTC-USDT-SWAP above 80000 USDT
触发后 → @用户 🔔 BTC-USDT-SWAP: 80001 USDT | above 80000
```

提醒在创建频道发送；above 为 `>=`，below 为 `<=`，无需先跨越阈值，创建时已满足则下轮触发。每人最多 20 条。仅发送成功后删除，失败保留重试；发送后落盘前崩溃可能重复通知。轮询可能错过短时越线，耗时请求会延长轮次，不承诺精确到达时间。关键词是简单子串规则，可能误匹配；不处理编辑后的消息。可停机后编辑 JSON 删除提醒。

不联网检查（不需要安装 discord.py）：

```sh
python3 -m py_compile bot.py logic.py
python3 -m unittest discover -s tests -v
```

## English

Python 3.10+ / discord.py 2.x template with `/price`, persistent one-shot `/alert`, member welcomes and case-insensitive substring filtering. OKX requests use `User-Agent: curl/8`, run in worker threads and have timeouts. A 60-second task groups requests by symbol. JSON is replaced atomically and restored on restart; use one process per store.

Use the setup commands above; export `DISCORD_TOKEN` before launching. `.env.example` documents variables but is not loaded automatically. Optional `DISCORD_GUILD_ID` registers test-guild commands; otherwise commands are global and may take time to appear. `ALERTS_FILE` overrides the default script-local store. `FILTER_KEYWORDS` is comma-separated; an empty string disables filtering.

Enable Server Members and Message Content intents in the Developer Portal. Invite with `bot` and `applications.commands` scopes and View Channels, Send Messages and Manage Messages permissions. Configure a system channel for welcomes. Only the intended alert recipient can be mentioned.

The examples above illustrate responses, not live quotes. Alerts send to the creation channel on `>= target` (above) or `<= target` (below), including conditions already satisfied at creation. Limit: 20 active alerts per user. Remove only after successful delivery; failed sends retry. A crash between delivery and persistence can duplicate a notification. Polling may miss brief threshold crossings and slow requests may extend cycles. Filtering is a simple substring match, may have false positives, and does not inspect message edits. Stop the bot before manually editing stored alerts. Corrupt storage fails startup instead of silently overwriting data.

The compile and unittest commands above run offline without discord.py installed; HTTP is mocked. Live Discord login and server behavior require your credentials and are not part of these checks.

References / 参考：[discord.py tasks](https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html), [application commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html), [OKX API](https://www.okx.com/docs-v5/en/).
