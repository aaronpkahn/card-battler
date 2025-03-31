from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

def download_card_image(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).convert("RGB")

def create_battle_image(url_a, url_b, name_a, name_b, out_path="/tmp/battle.jpg"):
    img_a = download_card_image(url_a)
    img_b = download_card_image(url_b)

    # Resize to same height
    base_height = 488
    img_a = img_a.resize((int(img_a.width * base_height / img_a.height), base_height))
    img_b = img_b.resize((int(img_b.width * base_height / img_b.height), base_height))

    # Combine side-by-side
    combined = Image.new("RGB", (img_a.width + img_b.width, base_height))
    combined.paste(img_a, (0, 0))
    combined.paste(img_b, (img_a.width, 0))

    # Add text (optional)
    draw = ImageDraw.Draw(combined)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    draw.text((10, 10), name_a, fill="white", font=font)
    draw.text((img_a.width + 10, 10), name_b, fill="white", font=font)

    combined.save(out_path)
    return out_path
