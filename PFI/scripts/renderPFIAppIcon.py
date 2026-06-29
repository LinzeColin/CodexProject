from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PATH = ROOT / "assets" / "PFIAppIconPreview.png"
ICONSET_DIR = ROOT / "assets" / "PFIAppIcon.iconset"
SIZE = 1024


def main() -> None:
    icon = render_icon(SIZE)
    PREVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    icon.save(PREVIEW_PATH)

    sizes = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for name, pixels in sizes.items():
        resized = icon.resize((pixels, pixels), Image.Resampling.LANCZOS)
        resized.save(ICONSET_DIR / name)


def render_icon(size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base_mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(base_mask)
    radius = int(size * 0.214)
    inset = int(size * 0.035)
    mask_draw.rounded_rectangle((inset, inset, size - inset, size - inset), radius=radius, fill=255)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (inset + 12, inset + 24, size - inset - 12, size - inset + 12),
        radius=radius,
        fill=(21, 53, 67, 72),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(size * 0.028)))
    canvas.alpha_composite(shadow)

    background = vertical_gradient(size, (248, 252, 255), (226, 244, 239))
    canvas.alpha_composite(apply_mask(background, base_mask))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw_ambient_shapes(draw, size, inset, radius)
    draw_glass_panel(draw, size)
    draw_chart(draw, size)
    draw_monogram(draw, size)
    draw_finance_nodes(draw, size)
    draw_highlights(draw, size, inset, radius)
    return canvas


def vertical_gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(size):
        t = y / (size - 1)
        r = round(top[0] * (1 - t) + bottom[0] * t)
        g = round(top[1] * (1 - t) + bottom[1] * t)
        b = round(top[2] * (1 - t) + bottom[2] * t)
        for x in range(size):
            pixels[x, y] = (r, g, b, 255)
    return image


def apply_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    result.alpha_composite(image)
    result.putalpha(mask)
    return result


def draw_ambient_shapes(draw: ImageDraw.ImageDraw, size: int, inset: int, radius: int) -> None:
    draw.rounded_rectangle(
        (inset + 18, inset + 18, size - inset - 18, size - inset - 18),
        radius=radius - 22,
        outline=(255, 255, 255, 160),
        width=4,
    )
    draw.polygon(
        [(size * 0.06, size * 0.25), (size * 0.35, size * 0.04), (size * 0.56, size * 0.04), (size * 0.18, size * 0.52)],
        fill=(213, 239, 255, 118),
    )
    draw.polygon(
        [(size * 0.58, size * 0.0), (size * 0.96, size * 0.0), (size * 0.96, size * 0.34), (size * 0.70, size * 0.22)],
        fill=(182, 239, 226, 132),
    )
    draw.polygon(
        [(size * 0.00, size * 0.77), (size * 0.98, size * 0.68), (size * 0.98, size * 0.95), (size * 0.12, size * 0.95)],
        fill=(207, 240, 247, 138),
    )
    for x in range(130, 910, 118):
        draw.line((x, 160, x - 185, 835), fill=(60, 148, 167, 36), width=3)
    for y in (215, 338, 462, 610, 758):
        draw.line((135, y, 890, y), fill=(39, 105, 130, 36), width=2)


def draw_glass_panel(draw: ImageDraw.ImageDraw, size: int) -> None:
    panel = (184, 236, 848, 805)
    draw.rounded_rectangle((panel[0] + 14, panel[1] + 20, panel[2] + 14, panel[3] + 22), radius=118, fill=(22, 78, 90, 38))
    draw.rounded_rectangle(panel, radius=118, fill=(255, 255, 255, 190), outline=(255, 255, 255, 210), width=4)
    draw.rounded_rectangle((224, 276, 808, 747), radius=86, fill=(232, 250, 248, 138))


def draw_chart(draw: ImageDraw.ImageDraw, size: int) -> None:
    points = [(236, 682), (350, 608), (466, 626), (575, 505), (682, 536), (803, 382)]
    draw.line(points, fill=(23, 122, 146, 88), width=34, joint="curve")
    draw.line(points, fill=(0, 171, 162, 255), width=20, joint="curve")
    draw.line([(239, 720), (804, 720)], fill=(213, 163, 61, 210), width=10)
    for x, y in points:
        draw.ellipse((x - 26, y - 26, x + 26, y + 26), fill=(255, 255, 255, 250), outline=(0, 157, 151, 255), width=9)
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(255, 190, 77, 255))


def draw_monogram(draw: ImageDraw.ImageDraw, size: int) -> None:
    font_path = find_font()
    font = ImageFont.truetype(str(font_path), 265)
    text = "PFI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2
    y = 360 - text_height / 2
    draw.text((x + 8, y + 10), text, font=font, fill=(9, 70, 88, 55))
    draw.text((x, y), text, font=font, fill=(16, 91, 107, 255))
    draw.text((x + 2, y + 2), text, font=font, fill=(35, 151, 157, 45))

    small_font = ImageFont.truetype(str(find_cjk_font()), 44)
    label = "个人经济分析"
    label_bbox = draw.textbbox((0, 0), label, font=small_font)
    lx = (size - (label_bbox[2] - label_bbox[0])) / 2
    draw.rounded_rectangle((300, 656, 724, 716), radius=30, fill=(255, 255, 255, 172))
    draw.text((lx, 662), label, font=small_font, fill=(39, 113, 121, 232))


def draw_finance_nodes(draw: ImageDraw.ImageDraw, size: int) -> None:
    draw.rounded_rectangle((256, 776, 612, 838), radius=31, fill=(21, 116, 139, 245))
    draw.rounded_rectangle((580, 776, 782, 838), radius=31, fill=(0, 185, 166, 245))
    draw.rounded_rectangle((680, 700, 815, 758), radius=29, fill=(255, 255, 255, 232))
    draw.ellipse((665, 686, 741, 762), fill=(255, 202, 91, 255), outline=(255, 255, 255, 220), width=9)
    draw.ellipse((208, 724, 276, 792), fill=(63, 220, 197, 255), outline=(255, 255, 255, 225), width=9)


def draw_highlights(draw: ImageDraw.ImageDraw, size: int, inset: int, radius: int) -> None:
    draw.arc((150, 128, 884, 862), start=203, end=337, fill=(28, 133, 154, 156), width=18)
    draw.arc((158, 136, 876, 854), start=203, end=337, fill=(255, 255, 255, 178), width=7)
    draw.arc((178, 162, 860, 842), start=16, end=109, fill=(245, 181, 78, 210), width=13)
    draw.rounded_rectangle(
        (inset + 28, inset + 28, size - inset - 28, size - inset - 28),
        radius=radius - 30,
        outline=(5, 61, 78, 36),
        width=5,
    )


def find_font() -> Path:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError("No usable system font found for PFI app icon rendering")


def find_cjk_font() -> Path:
    candidates = (
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    )
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return find_font()


if __name__ == "__main__":
    main()
