import discord
import asyncio
import aiohttp
from battle import generate_battle
from discord import Permissions
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def fetch_json(session, url):
    async with session.get(url) as resp:
        return await resp.json()

def card_key(card):
    return (card.get("cmc", 0), tuple(sorted(card.get("color_identity", []))))

async def post_daily_battle():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    # await log_bot_permissions(channel)
    # note: this while loop is a bug, need to fix nested loops
    while not client.is_closed():
        path, name_a, name_b, cube_source = await generate_battle()
        msg = await CHANNEL_ID.send(file=discord.File(path), content=f"**{name_a}** 🆚 **{name_b}** (from: {cube_source}) — who wins?")
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")

        await asyncio.sleep(86400)  # 24 hours

async def log_bot_permissions(channel):
    permissions = channel.permissions_for(channel.guild.me)

    print("\n🔍 Bot Permission Check:")
    print(f"Channel: {channel.name} ({channel.id})")
    print(f"Can send messages:      {permissions.send_messages}")
    print(f"Can embed links:        {permissions.embed_links}")
    print(f"Can attach files:       {permissions.attach_files}")
    print(f"Can read message hist.: {permissions.read_message_history}")
    print(f"Raw permissions int:    {permissions.value}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(post_daily_battle())

client.run(TOKEN)
