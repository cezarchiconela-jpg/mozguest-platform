from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

icons_dir = Path("static/icons")
icons_dir.mkdir(parents=True, exist_ok=True)

def create_icon(size, filename):
    img = Image.new("RGB", (size, size), "#1d4ed8")
    draw = ImageDraw.Draw(img)

    # círculo verde
    circle_r = int(size * 0.095)
    circle_x = int(size * 0.76)
    circle_y = int(size * 0.24)
    draw.ellipse(
        (circle_x - circle_r, circle_y - circle_r, circle_x + circle_r, circle_y + circle_r),
        fill="#10b981"
    )

    try:
        font_big = ImageFont.truetype("arialbd.ttf", int(size * 0.26))
        font_small = ImageFont.truetype("arial.ttf", int(size * 0.08))
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    text = "MG"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, size * 0.40), text, font=font_big, fill="white")

    text2 = "MozGuest"
    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((size - tw2) / 2, size * 0.68), text2, font=font_small, fill="#dbeafe")

    img.save(icons_dir / filename, "PNG")

create_icon(192, "icon-192.png")
create_icon(512, "icon-512.png")

print("Ícones PNG criados com sucesso.")
