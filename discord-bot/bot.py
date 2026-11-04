"""Discord template. Importing this module never logs in."""
import asyncio
import logging
import os
from pathlib import Path
from typing import Literal

import discord
from discord import app_commands
from discord.ext import tasks
from logic import AlertStore, blocked, fetch_price, instrument, reached

log = logging.getLogger(__name__)


class MarketBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents, allowed_mentions=discord.AllowedMentions.none())
        self.tree = app_commands.CommandTree(self)
        self.store = AlertStore(os.getenv('ALERTS_FILE', str(Path(__file__).with_name('alerts.json'))))
        self.keywords = os.getenv('FILTER_KEYWORDS', 'spam-example,scam-example').split(',')

    async def setup_hook(self):
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()
        self.poll_alerts.start()

    async def close(self):
        self.poll_alerts.cancel()
        await super().close()

    @tasks.loop(seconds=60)
    async def poll_alerts(self):
        prices = {}
        for item in list(self.store.items):
            try:
                symbol = item['symbol']
                if symbol not in prices:
                    try:
                        prices[symbol] = await asyncio.to_thread(fetch_price, symbol)
                    except Exception:
                        prices[symbol] = None
                        raise
                price = prices[symbol]
                if price is None or not reached(item, price):
                    continue
                channel = self.get_channel(item['channel_id']) or await self.fetch_channel(item['channel_id'])
                await channel.send(f"<@{item['user_id']}> 🔔 {symbol}: {price:g} USDT | {item['direction']} {item['target']:g}",
                                   allowed_mentions=discord.AllowedMentions(users=[discord.Object(id=item['user_id'])]))
                self.store.remove(item['id'])
            except Exception:
                # Preserve failed alerts for retry; one failure must not stop the loop.
                log.exception('Alert delivery failed: %s', item['id'])

    @poll_alerts.before_loop
    async def wait_until_connected(self):
        await self.wait_until_ready()

    async def on_member_join(self, member):
        channel = member.guild.system_channel
        if channel:
            try:
                await channel.send(f'欢迎 / Welcome, {member.display_name}! 👋')
            except discord.HTTPException:
                log.exception('Welcome message failed')

    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return
        if blocked(message.content, self.keywords):
            try:
                await message.delete()
            except discord.HTTPException:
                log.exception('Cannot delete filtered message')


def create_bot():
    client = MarketBot()

    @client.tree.command(name='price', description='查询 OKX USDT 永续价格 / Get perpetual price')
    async def price(interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(ephemeral=True)
        try:
            inst = instrument(symbol)
            last = await asyncio.to_thread(fetch_price, inst)
            await interaction.followup.send(f'{inst}: {last:g} USDT', ephemeral=True)
        except (ValueError, OSError, KeyError, TypeError):
            await interaction.followup.send('查询失败，请检查币种或稍后重试 / Price unavailable; check symbol or retry.', ephemeral=True)

    @client.tree.command(name='alert', description='设置一次性价格提醒 / Set a one-shot price alert')
    @app_commands.guild_only()
    async def alert(interaction: discord.Interaction, symbol: str, target: float,
                    direction: Literal['above', 'below']):
        await interaction.response.defer(ephemeral=True)
        try:
            inst = instrument(symbol)
            await asyncio.to_thread(fetch_price, inst)  # Reject nonexistent markets before persisting.
            item = client.store.add(interaction.user.id, interaction.channel_id, inst, target, direction)
            await interaction.followup.send(f"已保存 / Saved: {item['symbol']} {direction} {target:g} USDT; 每 60 秒检查 / checked every 60s.", ephemeral=True)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            log.warning('Alert creation failed: %s', exc)
            await interaction.followup.send('无法设置提醒，请检查参数或稍后重试 / Cannot create alert; check parameters or retry.', ephemeral=True)

    @client.tree.command(name='alerts', description='List your active price alerts / 查看我的提醒')
    async def alerts(interaction: discord.Interaction):
        mine = client.store.for_user(interaction.user.id)
        if not mine:
            await interaction.response.send_message('You have no active alerts / 暂无提醒', ephemeral=True)
            return
        lines = [f"`{a['id'][:8]}` {a['symbol']} {a['direction']} {a['target']:g} USDT" for a in mine]
        await interaction.response.send_message('\n'.join(lines) + '\nCancel with /cancel <id>', ephemeral=True)

    @client.tree.command(name='cancel', description='Delete one of your alerts by id / 按 ID 删除提醒')
    async def cancel(interaction: discord.Interaction, alert_id: str):
        try:
            item = client.store.cancel(interaction.user.id, alert_id)
            await interaction.response.send_message(f"Cancelled / 已删除: {item['symbol']} {item['direction']} {item['target']:g}", ephemeral=True)
        except ValueError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)

    return client


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise SystemExit('Set DISCORD_TOKEN in your environment first.')
    create_bot().run(token)
