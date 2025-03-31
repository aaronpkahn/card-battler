# battle.py

import discord
import random
import aiohttp
# Assuming generate_battle_image.py exists and has this function
from generate_battle_image import create_battle_image

# URL for the primary cube list
CUBE_URL = "https://cubecobra.com/cube/api/cubeJSON/thepenismightier"
# List of other Cube Cobra IDs to check for matching cards
OTHER_CUBE_IDS = ["modovintage", "wtwlf123", "LSVCube", "AlphaFrog"]

async def generate_battle(ctx):
    """
    Generates a battle image with two cards and posts it to Discord.

    Fetches card pairs, gets their images, creates a combined image,
    and sends it to the Discord context with voting reactions.
    Retries up to 10 times if valid card pairs/images aren't found initially.
    """
    async with aiohttp.ClientSession() as session:
        # Loop up to 10 times to find a valid battle
        for _ in range(10):
            # Get candidate card names and the source cube of the second card
            name_a, name_b, cube_source = await get_daily_battle_cards(session)

            # If no suitable second card was found, try again
            if not name_b:
                print("Could not find a suitable pair, retrying...")
                continue

            # Get image URLs from Scryfall
            card_a_url = await get_scryfall_card(session, name_a)
            card_b_url = await get_scryfall_card(session, name_b)

            # If either image URL is missing, try again
            if not card_a_url or not card_b_url:
                print(f"Missing Scryfall image for {name_a if not card_a_url else ''} {name_b if not card_b_url else ''}, retrying...")
                continue

            # If we have both names and URLs, break the loop
            break
        else:
            # If the loop finishes without breaking (10 retries failed)
            await ctx.send("Sorry, couldn't generate a battle after 10 tries. Please try again later.")
            return

        # Create the battle image using the helper function
        try:
            path = create_battle_image(card_a_url, card_b_url, name_a, name_b)
        except Exception as e:
            print(f"Error creating battle image: {e}")
            await ctx.send("Sorry, there was an error creating the battle image.")
            return

        # Send the image and message to Discord
        try:
            msg = await ctx.send(file=discord.File(path), content=f"**{name_a}** 🆚 **{name_b}** (from: {cube_source}) — who wins?")
            # Add voting reactions
            await msg.add_reaction("🅰️")
            await msg.add_reaction("🅱️")
        except discord.HTTPException as e:
            print(f"Error sending message or adding reactions: {e}")
            await ctx.send("Sorry, there was an error posting the battle to Discord.")
        except Exception as e:
             print(f"An unexpected error occurred during Discord interaction: {e}")
             await ctx.send("An unexpected error occurred.")


def card_key(card):
    """
    Generates a key for a card based on CMC and color category.

    Args:
        card (dict): Card dictionary from Cube Cobra JSON.

    Returns:
        tuple: (CMC, sorted_tuple_of_colors)
    """
    # Use .get() with default values for safety
    cmc = card.get("details", {}).get("cmc", 0)
    colors = tuple(sorted(card.get("details", {}).get("colorcategory", [])))
    return (cmc, colors)

def card_valid(card):
    """
    Checks if a card is valid for the battle based on certain criteria.

    Args:
        card (dict): Card dictionary from Cube Cobra JSON.

    Returns:
        bool: True if the card is valid, False otherwise.
    """
    details = card.get("details")
    if not details:
        return False
    # Exclude Lands
    if details.get("colorcategory") == "Lands":
        return False
    # Exclude cards with CMC > 6
    if details.get("cmc", 0) > 6:
        return False
    # Ensure it has a name
    if not details.get("name"):
        return False
    return True

def get_my_card(my_cards):
    """
    Selects a random valid card from the primary cube list.

    Args:
        my_cards (list): List of card dictionaries from the primary cube.

    Returns:
        dict or None: A valid card dictionary, or None if no valid card is found.
    """
    random.shuffle(my_cards)
    for card in my_cards:
        if card_valid(card):
            return card
    print(f"No valid cards found in my cube")
    return None # Explicitly return None if no valid card found

async def fetch_json(session, url):
    """
    Asynchronously fetches JSON data from a given URL.

    Args:
        session (aiohttp.ClientSession): The session object.
        url (str): The URL to fetch data from.

    Returns:
        dict or None: The JSON response as a dictionary, or None on error.
    """
    try:
        async with session.get(url) as resp:
            resp.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            return await resp.json()
    except aiohttp.ClientError as e:
        print(f"HTTP Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing JSON from {url}: {e}")
        return None


async def get_daily_battle_cards(session):
    """
    Finds a pair of cards: one from the primary cube, and one from another
    cube that matches the first card's key but is not in the primary cube.

    Args:
        session (aiohttp.ClientSession): The session object.

    Returns:
        tuple: (name_a, name_b, source_cube_id) or (name_a, None, None) if no match found.
    """
    # Fetch the primary cube data
    cube_data = await fetch_json(session, CUBE_URL)
    if not cube_data or "cards" not in cube_data or "mainboard" not in cube_data["cards"]:
        print("Could not fetch or parse primary cube data.")
        return None, None, None # Indicate failure
    my_cards = cube_data["cards"]["mainboard"]

    # --- Modification Start ---
    # Create a set of names from the primary cube for efficient lookup
    primary_card_names = {card["details"]["name"] for card in my_cards if card.get("details") and card["details"].get("name")}
    # --- Modification End ---

    # Select a valid card from the primary cube
    card_a = get_my_card(my_cards)
    if not card_a:
        print("Could not find a valid card in the primary cube.")
        return None, None, None # Indicate failure

    # Get the key (CMC, colors) for the first card
    key = card_key(card_a)
    card_a_name = card_a["details"]["name"]

    # Shuffle the list of other cube IDs to check them in random order
    shuffled_other_ids = random.sample(OTHER_CUBE_IDS, len(OTHER_CUBE_IDS))

    # Iterate through the other cubes to find a matching card
    for cube_id in shuffled_other_ids:
        other_url = f"https://cubecobra.com/cube/api/cubeJSON/{cube_id}"
        print(f"Checking cube: {cube_id}")
        other_data = await fetch_json(session, other_url)

        # Check if data was fetched and valid
        if not other_data or "cards" not in other_data or "mainboard" not in other_data["cards"]:
            print(f"Could not fetch or parse cube data for {cube_id}. Skipping.")
            continue

        other_cards = other_data["cards"]["mainboard"]

        # Find cards in the other cube that match the criteria
        matches = [
            c for c in other_cards if (
                card_valid(c) and
                card_key(c) == key and
                c["details"]["name"] != card_a_name and
                # --- Modification Start ---
                # Ensure the card name is not in the primary cube
                c["details"]["name"] not in primary_card_names
                # --- Modification End ---
            )
        ]

        # If matches are found, choose one randomly and return
        if matches:
            card_b = random.choice(matches)
            card_b_name = card_b["details"]["name"]
            print(f"Found match: {card_a_name} vs {card_b_name} (from {cube_id})")
            return card_a_name, card_b_name, cube_id
        else:
            print(f"No suitable match found in cube: {cube_id}")

    # If no match was found after checking all other cubes
    print(f"Could not find a suitable match for {card_a_name} in other cubes.")
    return card_a_name, None, None # Return card_a but no card_b

async def get_scryfall_card(session, name):
    """
    Fetches card data from Scryfall API by exact name and returns the image URL.

    Args:
        session (aiohttp.ClientSession): The session object.
        name (str): The exact name of the card.

    Returns:
        str or None: The URL of the 'normal' size image, or None if not found/error.
    """
    # URL encode the card name for the API query
    encoded_name = name.replace(' ', '%20') # Basic encoding for spaces
    url = f"https://api.scryfall.com/cards/named?exact={encoded_name}"

    data = await fetch_json(session, url)

    # Check if data exists and has the required image URIs
    if data and "image_uris" in data and "normal" in data["image_uris"]:
        return data["image_uris"]["normal"]
    else:
        print(f"Could not find Scryfall image for: {name}")
        return None

# Example of how generate_battle might be called (requires a Discord context object)
# This part would typically be in your main bot file within a command definition.
# async def command_name(ctx):
#     await generate_battle(ctx)
