import os
from PIL import Image


def optimize_image_field(image_field, max_size=(1600, 1200), quality=75):
    """
    Optimiza imagem carregada: reduz tamanho, comprime e mantém qualidade aceitável.
    Funciona com ImageField depois de o objecto ser salvo.
    """
    if not image_field:
        return

    try:
        image_path = image_field.path
    except Exception:
        return

    if not image_path or not os.path.exists(image_path):
        return

    try:
        img = Image.open(image_path)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(max_size)

        img.save(
            image_path,
            format="JPEG",
            quality=quality,
            optimize=True
        )
    except Exception:
        return
