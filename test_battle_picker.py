# test_battle_picker.py

import asyncio
import aiohttp
from battle import get_battle_cards, get_scryfall_card, generate_battle_from_card, generate_battle_from_cube_card
from generate_battle_image import create_battle_image

async def test_get_cards():
    async with aiohttp.ClientSession() as session:
        card_a, card_b, cube_source = await get_battle_cards(session)
        card_a_url = await get_scryfall_card(session, card_a)
        card_b_url = await get_scryfall_card(session, card_b)

        print("Card A:", card_a, " URL: ", card_a_url)
        print("Card B:", card_b, " URL: ", card_b_url)
        path = create_battle_image(card_a_url, card_b_url, card_a, card_b)
        print(path)

async def test_get_card():
    name = "Nethergoyf"
    path, card_2, card_source, error_msg = await generate_battle_from_cube_card(name)
    print("Card A:", name)
    print("Card B:", card_2)
    print("Path:", path)
    print("Cube Source:", card_source)
    print("Error Message:", error_msg)

if __name__ == "__main__":
    asyncio.run(test_get_card())
