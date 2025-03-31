# battle.py

import discord
import random
import aiohttp
from generate_battle_image import create_battle_image

CUBE_URL = "https://cubecobra.com/cube/api/cubeJSON/thepenismightier"
OTHER_CUBE_IDS = ["modovintage", "wtwlf123", "LSVCube", "AlphaFrog"]

async def generate_battle(ctx):
    async with aiohttp.ClientSession() as session:
        # loop 10 times to find a valid battle
        for _ in range(10):
            name_a, name_b, cube_source = await get_daily_battle_cards(session)
            card_a_url = await get_scryfall_card(session, name_a)
            card_b_url = await get_scryfall_card(session, name_b)

            if not card_a_url or not card_b_url:
                continue
            break

        path = create_battle_image(card_a_url, card_b_url, name_a, name_b)
        msg = await ctx.send(file=discord.File(path), content=f"**{name_a}** 🆚 **{name_b}** (from: {cube_source}) — who wins?")
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")

def card_key(card):
    return (card["details"].get("cmc", 0), tuple(sorted(card["details"].get("colorcategory", []))))

def card_valid(card):
    if not card["details"]:
        return False
    if card["details"]["colorcategory"] == "Lands":
        return False
    if card["details"].get("cmc", 0) > 6:
        return False
    return True

def get_my_card(my_cards):
    random.shuffle(my_cards)
    for card in my_cards:
        if card_valid(card):
            return card 
    print(f"No valid cards found in my cube")

async def fetch_json(session, url):
    async with session.get(url) as resp:
        return await resp.json()

async def get_daily_battle_cards(session):
    from battle import fetch_json, card_key  # Safe even inside own file for modular reuse

    cube_data = await fetch_json(session, CUBE_URL)
    my_cards = cube_data["cards"]["mainboard"]
    card_a = get_my_card(my_cards)

    key = card_key(card_a)

    random.shuffle(OTHER_CUBE_IDS)
    for cube_id in OTHER_CUBE_IDS:
        other_url = f"https://cubecobra.com/cube/api/cubeJSON/{cube_id}"
        try:
            other_data = await fetch_json(session, other_url)
            other_cards = other_data["cards"]["mainboard"]
            matches = [c for c in other_cards if card_valid(c) and card_key(c) == key and c["details"]["name"] != card_a["details"]["name"]]
            if matches:
                card_b = random.choice(matches)
                return card_a["details"]["name"], card_b["details"]["name"], cube_id
        except Exception as e:
            print(f"Error with cube {cube_id}: {e}")
            continue

    return card_a["details"]["name"], None, None

async def get_scryfall_card(session, name):
    url = f"https://api.scryfall.com/cards/named?exact={name.replace(' ', '%20')}"
    data = await fetch_json(session, url)
    return data["image_uris"]["normal"] if "image_uris" in data else None
