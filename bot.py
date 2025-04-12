import discord
from battle import generate_battle
from generate_battle_image import create_battle_image
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BATTLE_MSG = os.getenv("BATTLE_MSG")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.command(name="battle")
async def battle(ctx):
    print(f"Received battle command from {ctx.author.name} in {ctx.channel.name}")
    if BATTLE_MSG:
        await ctx.send(BATTLE_MSG)
    await generate_battle(ctx)

@bot.tree.command(name="battle", description="Start a card battle")
@app_commands.describe(card_name="(Optional) Specify the first card to use in the battle")
async def battle(interaction: discord.Interaction, card_name: str = None):
    await interaction.response.defer(thinking=True)
    await generate_battle(interaction.followup)

bot.run(TOKEN)
