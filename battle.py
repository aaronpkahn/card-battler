# battle.py

import discord
import random
import aiohttp
from generate_battle_image import create_battle_image

CUBE_URL = "https://cubecobra.com/cube/api/cubeJSON/thepenismightier"
OTHER_CUBE_IDS = ["modovintage", "wtwlf123", "LSVCube", "AlphaFrog"]

async def generate_battle():
    async with aiohttp.ClientSession() as session:
        # loop 10 times to find a valid battle
        for _ in range(10):
            name_a, name_b, cube_source = await get_battle_cards(session)
            card_a_url = await get_scryfall_card(session, name_a)
            card_b_url = await get_scryfall_card(session, name_b)

            if not card_a_url or not card_b_url:
                continue
            break

        path = create_battle_image(card_a_url, card_b_url, name_a, name_b)
        return path, name_a, name_b, cube_source

async def generate_battle_from_cube_card(card_name):
    async with aiohttp.ClientSession() as session:
        name_b, cube_source, error_msg = await get_battle_given_card(session, card_name)
        if error_msg:
            return None, None, None, error_msg
        card_a_url = await get_scryfall_card(session, card_name)
        card_b_url = await get_scryfall_card(session, name_b)
        if not card_a_url:
            return None, None, None, "invalid card url"
        if not card_b_url:
            return None, None, None, "invalid card B url, try again"

        path = create_battle_image(card_a_url, card_b_url, card_name, name_b)
        return path, name_b, cube_source, None

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

def get_card_from_my_cards(my_cards, card_name):
    for card in my_cards:
        if card["details"]["name"] == card_name:
            return card
    return None

def get_my_card(my_cards):
    random.shuffle(my_cards)
    for card in my_cards:
        if card_valid(card):
            return card 
    print(f"No valid cards found in my cube")

async def fetch_json(session, url):
    async with session.get(url) as resp:
        return await resp.json()

async def get_battle_cards(session):
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

async def get_battle_given_card(session, card_name):
    cube_data = await fetch_json(session, CUBE_URL)
    my_cards = cube_data["cards"]["mainboard"]
    card_a = get_card_from_my_cards(my_cards, card_name)
    if not card_a:
        return None, None, "Card not found in my cube"

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
                return card_b["details"]["name"], cube_id, None
        except Exception as e:
            print(f"Error with cube {cube_id}: {e}")
            continue

    return None, None, "no card found"

async def get_scryfall_card(session, name):
    url = f"https://api.scryfall.com/cards/named?exact={name.replace(' ', '%20')}"
    data = await fetch_json(session, url)
    return data["image_uris"]["normal"] if "image_uris" in data else None

async def get_scryfall_data(session, name):
    url = f"https://api.scryfall.com/cards/named?exact={name.replace(' ', '%20')}"
    try:
        data = await fetch_json(session, url)
        return data if "image_uris" in data else None
    except:
        return None

# doesn't work
# returns a tuple of (path, name_b, cube_source, error_msg)
async def generate_battle_from_card(card_name):
    async with aiohttp.ClientSession() as session:
        # Lookup base card
        card_a_data = await get_scryfall_data(session, card_name)
        if not card_a_data or "image_uris" not in card_a_data:
            return None, None, None, "invalid card"

        cmc = card_a_data.get("cmc", 0)
        colors = tuple(sorted(card_a_data.get("color_identity", [])))
        print("cmc:", cmc)
        print("colors:", colors)

        name_b = None
        opponent_url = None
        cube_source = None

        random.shuffle(OTHER_CUBE_IDS)
        for cube_id in OTHER_CUBE_IDS:
            try:
                other_data = await fetch_json(session, f"https://cubecobra.com/cube/api/cubeJSON/{cube_id}")
                candidates = [
                    c for c in other_data["cards"]["mainboard"]
                    if c.get("cmc", 0) == cmc and tuple(sorted(c.get("color_identity", []))) == colors and c["name"] != card_a_data["name"]
                ]
                print("Candidate len:",len(candidates))
                if candidates:
                    candidate = random.choice(candidates)
                    name_b = candidate["name"]
                    opponent_card = await get_scryfall_data(session, name_b)
                    if opponent_card and "image_uris" in opponent_card:
                        opponent_url = opponent_card["image_uris"]["normal"]
                        cube_source = cube_id
                        break
            except Exception as e:
                continue

        if not opponent_url:
            return None, None, None, f"❌ Couldn't find a valid opponent for `{card_name}`."

        card_a_url = card_a_data["image_uris"]["normal"]
        path = create_battle_image(card_a_url, opponent_url, card_a_data["name"], name_b)
        return path, name_b, cube_source, None
