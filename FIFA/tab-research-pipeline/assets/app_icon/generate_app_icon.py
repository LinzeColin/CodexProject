from __future__ import annotations

import math
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
PNG_PATH = ROOT / "TABFIFAResearch.png"
ICNS_PATH = ROOT / "TABFIFAResearch.icns"
ICONSET_DIR = ROOT / "TABFIFAResearch.iconset"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[index] * (1 - t) + b[index] * t) for index in range(3))


def rounded_rect_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(count * 2):
        radius = outer if index % 2 == 0 else inner
        angle = -math.pi / 2 + index * math.pi / count
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def regular_polygon(cx: float, cy: float, radius: float, count: int, rotation: float = -math.pi / 2) -> list[tuple[float, float]]:
    return [
        (cx + math.cos(rotation + 2 * math.pi * index / count) * radius, cy + math.sin(rotation + 2 * math.pi * index / count) * radius)
        for index in range(count)
    ]


def draw_icon(size: int = 1024, scale: int = 3) -> Image.Image:
    canvas_size = size * scale
    image = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    s = scale

    bg_mask = rounded_rect_mask(canvas_size, 222 * s)
    gradient_size = 512
    bg_small = Image.new("RGBA", (gradient_size, gradient_size), (0, 0, 0, 0))
    bg_px = bg_small.load()
    top = hex_to_rgb("#053D3F")
    mid = hex_to_rgb("#075B52")
    bottom = hex_to_rgb("#031E29")
    for y in range(gradient_size):
        ty = y / (gradient_size - 1)
        base = blend(top, mid, min(ty * 1.35, 1.0)) if ty < 0.62 else blend(mid, bottom, (ty - 0.62) / 0.38)
        for x in range(gradient_size):
            dx = (x - gradient_size * 0.34) / gradient_size
            dy = (y - gradient_size * 0.20) / gradient_size
            light = max(0.0, 1.0 - math.sqrt(dx * dx + dy * dy) * 2.5)
            color = blend(base, hex_to_rgb("#13C19A"), light * 0.18)
            bg_px[x, y] = (*color, 255)
    bg = bg_small.resize((canvas_size, canvas_size), Image.Resampling.BICUBIC)
    bg.putalpha(bg_mask)
    image.alpha_composite(bg)

    # Soft inner vignette.
    vignette = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    vd.rounded_rectangle((30 * s, 30 * s, canvas_size - 30 * s, canvas_size - 30 * s), radius=196 * s, outline=(255, 255, 255, 28), width=5 * s)
    vd.rounded_rectangle((55 * s, 55 * s, canvas_size - 55 * s, canvas_size - 55 * s), radius=176 * s, outline=(0, 0, 0, 64), width=8 * s)
    image.alpha_composite(vignette)

    center = canvas_size / 2

    # Pitch/radar grid.
    grid = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    radar_color = (87, 238, 197, 58)
    for radius in (185, 285, 385):
        gd.ellipse((center - radius * s, center - radius * s, center + radius * s, center + radius * s), outline=radar_color, width=4 * s)
    for angle in range(0, 360, 30):
        length = 420 * s
        x = center + math.cos(math.radians(angle)) * length
        y = center + math.sin(math.radians(angle)) * length
        gd.line((center, center, x, y), fill=(87, 238, 197, 32), width=3 * s)
    gd.rounded_rectangle((205 * s, 290 * s, 819 * s, 734 * s), radius=58 * s, outline=(255, 255, 255, 48), width=5 * s)
    gd.line((512 * s, 290 * s, 512 * s, 734 * s), fill=(255, 255, 255, 35), width=4 * s)
    gd.ellipse((442 * s, 442 * s, 582 * s, 582 * s), outline=(255, 255, 255, 35), width=4 * s)
    image.alpha_composite(grid)

    # Data value path.
    path = [(214, 653), (334, 596), (448, 622), (569, 477), (706, 410), (826, 330)]
    path_scaled = [(x * s, y * s) for x, y in path]
    draw.line(path_scaled, fill=(78, 244, 210, 170), width=15 * s, joint="curve")
    draw.line(path_scaled, fill=(245, 199, 92, 235), width=6 * s, joint="curve")
    for x, y in path:
        draw.ellipse(((x - 15) * s, (y - 15) * s, (x + 15) * s, (y + 15) * s), fill=(248, 204, 91, 255), outline=(255, 255, 255, 210), width=3 * s)

    # Central ball shadow and core.
    shadow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((318 * s, 324 * s, 718 * s, 724 * s), fill=(0, 0, 0, 115))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20 * s))
    image.alpha_composite(shadow)

    ball_box = (304 * s, 296 * s, 720 * s, 712 * s)
    draw.ellipse(ball_box, fill=(244, 250, 242, 255), outline=(209, 229, 219, 255), width=8 * s)
    draw.ellipse((330 * s, 322 * s, 694 * s, 686 * s), outline=(10, 75, 72, 42), width=5 * s)

    dark = (8, 55, 58, 255)
    line = (17, 99, 91, 225)
    pent = regular_polygon(512 * s, 500 * s, 78 * s, 5, rotation=-math.pi / 2)
    draw.polygon(pent, fill=dark)

    outer_centers = [
        (512, 365, -90),
        (652, 468, -18),
        (598, 630, 54),
        (426, 630, 126),
        (372, 468, 198),
    ]
    for cx, cy, rot in outer_centers:
        poly = regular_polygon(cx * s, cy * s, 52 * s, 5, rotation=math.radians(rot))
        draw.polygon(poly, fill=(10, 83, 75, 230))
        draw.line([(512 * s, 500 * s), (cx * s, cy * s)], fill=line, width=8 * s)

    # Ball seam arcs.
    for start, end in [(205, 285), (330, 50), (86, 158)]:
        draw.arc((350 * s, 338 * s, 674 * s, 662 * s), start=start, end=end, fill=(17, 99, 91, 135), width=6 * s)

    # Gold value star and subtle terminal ticks.
    draw.polygon(star_points(745 * s, 274 * s, 44 * s, 18 * s), fill=(248, 204, 91, 255))
    draw.ellipse((730 * s, 259 * s, 760 * s, 289 * s), fill=(255, 247, 184, 255))
    for index, height in enumerate((62, 96, 142, 118)):
        x0 = (236 + index * 38) * s
        y1 = 284 * s
        draw.rounded_rectangle((x0, y1 - height * s, x0 + 18 * s, y1), radius=9 * s, fill=(95, 239, 202, 105))

    # Gloss and bottom depth.
    gloss = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.rounded_rectangle((96 * s, 84 * s, 928 * s, 470 * s), radius=150 * s, fill=(255, 255, 255, 22))
    gd.rounded_rectangle((0, 680 * s, canvas_size, canvas_size), radius=220 * s, fill=(0, 0, 0, 28))
    image.alpha_composite(gloss)

    return image.resize((size, size), Image.Resampling.LANCZOS)


def write_iconset(png: Image.Image) -> None:
    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True)
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    for size, name in sizes:
        png.resize((size, size), Image.Resampling.LANCZOS).save(ICONSET_DIR / name)


def main() -> None:
    png = draw_icon()
    png.save(PNG_PATH)
    write_iconset(png)
    png.save(
        ICNS_PATH,
        format="ICNS",
        sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)],
    )
    if os.getenv("TAB_FIFA_KEEP_ICONSET", "").lower() not in {"1", "true", "yes"}:
        shutil.rmtree(ICONSET_DIR)
    print(f"wrote {PNG_PATH}")
    print(f"wrote {ICNS_PATH}")


if __name__ == "__main__":
    main()
