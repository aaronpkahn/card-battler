# test_battle_picker.py

import asyncio
import aiohttp
from battle import get_daily_battle_cards, get_scryfall_card
from generate_battle_image import create_battle_image

async def main():
    async with aiohttp.ClientSession() as session:
        card_a, card_b, cube_source = await get_daily_battle_cards(session)
        card_a_url = await get_scryfall_card(session, card_a)
        card_b_url = await get_scryfall_card(session, card_b)

        print("Card A:", card_a, " URL: ", card_a_url)
        print("Card B:", card_b, " URL: ", card_b_url)
        path = create_battle_image(card_a_url, card_b_url, card_a, card_b)
        print(path)

if __name__ == "__main__":
    asyncio.run(main())
