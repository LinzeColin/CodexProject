#!/usr/bin/env python3
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT_DIR / "app_bundle" / "assets"
ICONSET_DIR = ASSET_DIR / "OpMeIcon.iconset"
PNG_PATH = ASSET_DIR / "OpMeIcon.png"
ICNS_PATH = ASSET_DIR / "OpMeIcon.icns"


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def draw_gradient_base(size: int) -> Image.Image:
    top_left = rgb("#08111f")
    bottom_right = rgb("#15516a")
    accent = rgb("#0f2c3d")
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            tx = x / (size - 1)
            ty = y / (size - 1)
            t = min(1, (tx * 0.55 + ty * 0.75))
            r = lerp(top_left[0], bottom_right[0], t)
            g = lerp(top_left[1], bottom_right[1], t)
            b = lerp(top_left[2], bottom_right[2], t)
            if x > size * 0.55 and y < size * 0.4:
                shine = (x / size - 0.55) * (0.4 - y / size)
                r = min(255, r + int(accent[0] * shine))
                g = min(255, g + int(accent[1] * shine))
                b = min(255, b + int(accent[2] * shine))
            pixels[x, y] = (r, g, b, 255)
    image.putalpha(rounded_mask(size, round(size * 0.19)))
    return image


def draw_shadow(base: Image.Image, mask: Image.Image, offset: tuple[int, int], blur: int, opacity: int) -> None:
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    shadow_alpha = mask.filter(ImageFilter.GaussianBlur(blur))
    shadow.putalpha(shadow_alpha.point(lambda p: min(opacity, p)))
    base.alpha_composite(shadow, offset)


def gear_points(cx: int, cy: int, inner: int, outer: int, teeth: int) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for i in range(teeth * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -math.pi / 2 + (math.pi * 2 * i) / (teeth * 2)
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return points


def draw_polyline(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], width: int, fill: tuple[int, int, int, int]) -> None:
    for a, b in zip(points, points[1:]):
        draw.line((a, b), width=width, fill=fill, joint="curve")
    radius = max(2, width // 2)
    for x, y in points:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def draw_rotated_kiln(base: Image.Image, scale: int) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = (228 * scale, 445 * scale, 802 * scale, 586 * scale)
    radius = 52 * scale

    draw.rounded_rectangle((left, top, right, bottom), radius=radius, fill=(31, 58, 70, 255))
    draw.rounded_rectangle((left, top + 8 * scale, right, bottom - 8 * scale), radius=44 * scale, fill=(78, 103, 112, 255))
    draw.rounded_rectangle((left + 16 * scale, top + 24 * scale, right - 16 * scale, bottom - 36 * scale), radius=30 * scale, fill=(139, 159, 164, 245))
    draw.line((left + 34 * scale, bottom - 38 * scale, right - 38 * scale, bottom - 18 * scale), fill=(255, 145, 47, 235), width=18 * scale)

    for x in (314, 512, 708):
        draw.rounded_rectangle(
            (x * scale - 24 * scale, top - 16 * scale, x * scale + 24 * scale, bottom + 16 * scale),
            radius=15 * scale,
            fill=(9, 19, 31, 245),
        )
        draw.rounded_rectangle(
            (x * scale - 13 * scale, top - 12 * scale, x * scale + 13 * scale, bottom + 12 * scale),
            radius=10 * scale,
            fill=(52, 210, 218, 205),
        )

    end_cx = right
    draw.ellipse((end_cx - 52 * scale, top + 8 * scale, end_cx + 52 * scale, bottom - 8 * scale), fill=(12, 25, 38, 245))
    draw.ellipse((end_cx - 34 * scale, top + 28 * scale, end_cx + 34 * scale, bottom - 28 * scale), fill=(255, 129, 35, 230))

    layer = layer.rotate(-9, resample=Image.Resampling.BICUBIC, center=(512 * scale, 512 * scale))
    base.alpha_composite(layer)


def make_icon(size: int = 1024) -> Image.Image:
    scale = size // 1024
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base = draw_gradient_base(size)
    canvas.alpha_composite(base)
    draw = ImageDraw.Draw(canvas)

    # Subtle HMI grid and dashboard frame.
    grid = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    for step in range(154, 871, 102):
        grid_draw.line((step * scale, 132 * scale, step * scale, 892 * scale), fill=(96, 220, 222, 34), width=max(1, 2 * scale))
        grid_draw.line((132 * scale, step * scale, 892 * scale, step * scale), fill=(96, 220, 222, 28), width=max(1, 2 * scale))
    grid.putalpha(rounded_mask(size, round(size * 0.19)))
    canvas.alpha_composite(grid)

    # Gear ring with depth.
    gear_mask = Image.new("L", (size, size), 0)
    gear_draw = ImageDraw.Draw(gear_mask)
    gear_draw.polygon(gear_points(512 * scale, 536 * scale, 263 * scale, 303 * scale, 20), fill=255)
    gear_draw.ellipse((283 * scale, 307 * scale, 741 * scale, 765 * scale), fill=0)
    draw_shadow(canvas, gear_mask, (0, 18 * scale), 28 * scale, 105)

    draw.polygon(gear_points(512 * scale, 536 * scale, 263 * scale, 303 * scale, 20), fill=(19, 38, 54, 255))
    draw.ellipse((255 * scale, 279 * scale, 769 * scale, 793 * scale), outline=(67, 219, 224, 220), width=16 * scale)
    draw.ellipse((319 * scale, 343 * scale, 705 * scale, 729 * scale), outline=(255, 145, 45, 235), width=18 * scale)
    draw.ellipse((350 * scale, 374 * scale, 674 * scale, 698 * scale), fill=(10, 24, 38, 215))

    draw_rotated_kiln(canvas, scale)

    # Monitoring line, sized to remain readable at small icon sizes.
    trend = [
        (198 * scale, 260 * scale),
        (288 * scale, 260 * scale),
        (337 * scale, 214 * scale),
        (402 * scale, 302 * scale),
        (462 * scale, 244 * scale),
        (560 * scale, 244 * scale),
        (616 * scale, 189 * scale),
        (704 * scale, 276 * scale),
        (826 * scale, 276 * scale),
    ]
    draw_polyline(draw, trend, 17 * scale, (81, 232, 233, 245))
    draw_polyline(draw, [(x, y + 27 * scale) for x, y in trend], 8 * scale, (15, 45, 58, 150))

    # Status badge.
    badge_mask = Image.new("L", (size, size), 0)
    badge_draw = ImageDraw.Draw(badge_mask)
    badge_draw.ellipse((705 * scale, 704 * scale, 861 * scale, 860 * scale), fill=255)
    draw_shadow(canvas, badge_mask, (0, 12 * scale), 18 * scale, 95)
    draw.ellipse((705 * scale, 704 * scale, 861 * scale, 860 * scale), fill=(255, 129, 35, 255))
    draw.ellipse((741 * scale, 740 * scale, 825 * scale, 824 * scale), fill=(14, 25, 34, 235))
    draw.rectangle((773 * scale, 756 * scale, 793 * scale, 799 * scale), fill=(255, 244, 224, 255))
    draw.ellipse((773 * scale, 807 * scale, 793 * scale, 827 * scale), fill=(255, 244, 224, 255))

    # Glass highlight and outline.
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    high_draw = ImageDraw.Draw(highlight)
    high_draw.rounded_rectangle((55 * scale, 52 * scale, 969 * scale, 970 * scale), radius=190 * scale, outline=(255, 255, 255, 58), width=5 * scale)
    high_draw.arc((106 * scale, 82 * scale, 842 * scale, 655 * scale), 202, 305, fill=(255, 255, 255, 42), width=20 * scale)
    canvas.alpha_composite(highlight)

    return canvas


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    master = make_icon(1024)
    master.save(PNG_PATH)

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
    for filename, output_size in sizes.items():
        resized = master.resize((output_size, output_size), Image.Resampling.LANCZOS)
        resized.save(ICONSET_DIR / filename)

    if ICNS_PATH.exists():
        ICNS_PATH.unlink()
    subprocess.run(["/usr/bin/iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(ICNS_PATH)], check=True)
    print(PNG_PATH)
    print(ICNS_PATH)


if __name__ == "__main__":
    main()
