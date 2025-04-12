import discord
from battle import generate_battle, generate_battle_from_cube_card
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
    path, name_a, name_b, cube_source = await generate_battle()
    msg = await ctx.send(file=discord.File(path), content=f"**{name_a}** 🆚 **{name_b}** (from: {cube_source}) — who wins?")
    await msg.add_reaction("🅰️")
    await msg.add_reaction("🅱️")

@bot.tree.command(name="battle", description="Start a card battle")
@app_commands.describe(card_name="(Optional) Specify the first card to use in the battle")
async def battle(interaction: discord.Interaction, card_name: str = None):
    await interaction.response.defer(thinking=True)
    if card_name:
        path, name_b, cube_source, error_msg = await generate_battle_from_cube_card(card_name)
        if error_msg:
            await interaction.edit_original_response(content=error_msg)
            return
        name_a = card_name
    else:
        path, name_a, name_b, cube_source = await generate_battle()
    msg = await interaction.edit_original_response(
        content=f"**{name_a}** 🆚 **{name_b}** (from: {cube_source}) — who wins?",
        attachments=[discord.File(path)]
    )
    await msg.add_reaction("🅰️")
    await msg.add_reaction("🅱️")

bot.run(TOKEN)
