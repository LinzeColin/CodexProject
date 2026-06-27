#!/usr/bin/env python3
"""Generate and optionally install the EEI macOS/web app icon.

The renderer intentionally uses only the Python standard library plus macOS
`sips`/`iconutil` for resized PNG and ICNS generation.
"""

from __future__ import annotations

import argparse
import json
import math
import plistlib
import shutil
import struct
import subprocess
import zlib
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "app_icon"
WEB_PUBLIC_DIR = ROOT / "apps" / "web" / "public"
ICON_NAME = "EEIAppIcon"
PNG_PATH = ASSET_DIR / f"{ICON_NAME}.png"
SVG_PATH = ASSET_DIR / f"{ICON_NAME}.svg"
ICNS_PATH = ASSET_DIR / f"{ICON_NAME}.icns"
ICONSET_DIR = ASSET_DIR / f"{ICON_NAME}.iconset"
WEB_SVG_PATH = WEB_PUBLIC_DIR / "eei-app-icon.svg"
WEB_PNG_PATH = WEB_PUBLIC_DIR / "eei-app-icon.png"
APPLE_TOUCH_PATH = WEB_PUBLIC_DIR / "apple-touch-icon.png"

ICONSET_SIZES = {
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


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * clamp(t))


def mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t))


def png_chunk(kind: bytes, data: bytes) -> bytes:
    payload = kind + data
    return (
        struct.pack(">I", len(data))
        + payload
        + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
    )


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    rows = bytearray()
    stride = width * 4
    for y in range(height):
        rows.append(0)
        rows.extend(pixels[y * stride : (y + 1) * stride])
    payload = b"\x89PNG\r\n\x1a\n"
    payload += png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    payload += png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    payload += png_chunk(b"IEND", b"")
    path.write_bytes(payload)


class Canvas:
    def __init__(self, size: int) -> None:
        self.size = size
        self.pixels = bytearray(size * size * 4)

    def blend_pixel(self, x: int, y: int, color: tuple[int, int, int], alpha: float) -> None:
        if x < 0 or y < 0 or x >= self.size or y >= self.size:
            return
        a = clamp(alpha)
        if a <= 0:
            return
        idx = (y * self.size + x) * 4
        da = self.pixels[idx + 3] / 255.0
        oa = a + da * (1 - a)
        if oa <= 0:
            return
        for channel in range(3):
            src = color[channel] / 255.0
            dst = self.pixels[idx + channel] / 255.0
            self.pixels[idx + channel] = round(((src * a) + (dst * da * (1 - a))) / oa * 255)
        self.pixels[idx + 3] = round(oa * 255)

    def fill_rounded_rect_gradient(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        radius: float,
        top_left: tuple[int, int, int],
        bottom_right: tuple[int, int, int],
    ) -> None:
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        half_w = (right - left) / 2
        half_h = (bottom - top) / 2
        for y in range(math.floor(top), math.ceil(bottom)):
            for x in range(math.floor(left), math.ceil(right)):
                px = x + 0.5
                py = y + 0.5
                qx = abs(px - cx) - (half_w - radius)
                qy = abs(py - cy) - (half_h - radius)
                outside = math.hypot(max(qx, 0), max(qy, 0))
                inside = min(max(qx, qy), 0)
                sdf = outside + inside - radius
                alpha = clamp(0.5 - sdf)
                if alpha <= 0:
                    continue
                t = clamp((x / self.size) * 0.52 + (y / self.size) * 0.48)
                color = mix(top_left, bottom_right, t)
                self.blend_pixel(x, y, color, alpha)

    def rounded_rect(
        self,
        left: float,
        top: float,
        right: float,
        bottom: float,
        radius: float,
        color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        cx = (left + right) / 2
        cy = (top + bottom) / 2
        half_w = (right - left) / 2
        half_h = (bottom - top) / 2
        for y in range(math.floor(top - 2), math.ceil(bottom + 2)):
            for x in range(math.floor(left - 2), math.ceil(right + 2)):
                px = x + 0.5
                py = y + 0.5
                qx = abs(px - cx) - (half_w - radius)
                qy = abs(py - cy) - (half_h - radius)
                outside = math.hypot(max(qx, 0), max(qy, 0))
                inside = min(max(qx, qy), 0)
                sdf = outside + inside - radius
                coverage = clamp(0.5 - sdf)
                self.blend_pixel(x, y, color, alpha * coverage)

    def circle(
        self,
        cx: float,
        cy: float,
        radius: float,
        color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        for y in range(math.floor(cy - radius - 2), math.ceil(cy + radius + 2)):
            for x in range(math.floor(cx - radius - 2), math.ceil(cx + radius + 2)):
                dist = math.hypot((x + 0.5) - cx, (y + 0.5) - cy)
                coverage = clamp(radius + 0.5 - dist)
                self.blend_pixel(x, y, color, alpha * coverage)

    def circle_outline(
        self,
        cx: float,
        cy: float,
        radius: float,
        width: float,
        color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        outer = radius + width / 2
        for y in range(math.floor(cy - outer - 2), math.ceil(cy + outer + 2)):
            for x in range(math.floor(cx - outer - 2), math.ceil(cx + outer + 2)):
                dist = math.hypot((x + 0.5) - cx, (y + 0.5) - cy)
                coverage = clamp(width / 2 + 0.5 - abs(dist - radius))
                self.blend_pixel(x, y, color, alpha * coverage)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        width: float,
        color: tuple[int, int, int],
        alpha: float = 1.0,
    ) -> None:
        min_x = math.floor(min(x1, x2) - width - 2)
        max_x = math.ceil(max(x1, x2) + width + 2)
        min_y = math.floor(min(y1, y2) - width - 2)
        max_y = math.ceil(max(y1, y2) + width + 2)
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx * dx + dy * dy
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                px = x + 0.5
                py = y + 0.5
                t = 0.0 if length_sq == 0 else clamp(((px - x1) * dx + (py - y1) * dy) / length_sq)
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                dist = math.hypot(px - proj_x, py - proj_y)
                coverage = clamp(width / 2 + 0.5 - dist)
                self.blend_pixel(x, y, color, alpha * coverage)


def render_icon(size: int = 1024) -> Canvas:
    s = size / 1024.0

    def p(value: float) -> float:
        return value * s

    canvas = Canvas(size)
    canvas.fill_rounded_rect_gradient(
        p(44), p(44), p(980), p(980), p(218), (6, 25, 42), (9, 104, 105)
    )

    # Subtle network field.
    for offset, alpha in [(0, 0.12), (96, 0.08), (192, 0.06)]:
        canvas.line(
            p(118 + offset), p(250), p(870), p(840 - offset * 0.25), p(3), (91, 233, 220), alpha
        )
        canvas.line(
            p(172), p(810 - offset), p(860 - offset * 0.25), p(212), p(3), (255, 190, 88), alpha
        )

    canvas.circle_outline(p(512), p(512), p(352), p(13), (96, 232, 222), 0.33)
    canvas.circle_outline(p(512), p(512), p(260), p(8), (255, 190, 88), 0.22)

    # Supply-chain and capital graph edges.
    edges = [
        ((244, 354), (512, 512), (91, 233, 220), 0.42),
        ((512, 512), (778, 318), (255, 190, 88), 0.52),
        ((254, 710), (512, 512), (91, 233, 220), 0.40),
        ((512, 512), (770, 720), (255, 190, 88), 0.47),
        ((244, 354), (778, 318), (146, 181, 255), 0.24),
        ((254, 710), (770, 720), (146, 181, 255), 0.22),
    ]
    for (x1, y1), (x2, y2), color, alpha in edges:
        canvas.line(p(x1), p(y1), p(x2), p(y2), p(13), color, alpha)

    # Central Enterprise "E" monogram.
    shadow = (0, 16, 28)
    canvas.rounded_rect(p(330), p(265), p(432), p(760), p(42), shadow, 0.40)
    canvas.rounded_rect(p(388), p(265), p(724), p(354), p(42), shadow, 0.34)
    canvas.rounded_rect(p(388), p(468), p(660), p(556), p(42), shadow, 0.34)
    canvas.rounded_rect(p(388), p(670), p(748), p(760), p(42), shadow, 0.34)
    pearl = (234, 250, 247)
    cyan = (117, 244, 225)
    canvas.rounded_rect(p(315), p(248), p(418), p(743), p(42), pearl, 0.95)
    canvas.rounded_rect(p(374), p(248), p(714), p(337), p(42), pearl, 0.95)
    canvas.rounded_rect(p(374), p(451), p(650), p(539), p(42), cyan, 0.93)
    canvas.rounded_rect(p(374), p(653), p(740), p(743), p(42), pearl, 0.95)

    # Graph nodes on top of the monogram.
    nodes = [
        (244, 354, 39, (91, 233, 220)),
        (778, 318, 43, (255, 190, 88)),
        (512, 512, 48, (234, 250, 247)),
        (254, 710, 38, (146, 181, 255)),
        (770, 720, 42, (255, 190, 88)),
    ]
    for x, y, r, color in nodes:
        canvas.circle(p(x), p(y), p(r + 9), (0, 17, 28), 0.36)
        canvas.circle(p(x), p(y), p(r), color, 0.96)
        canvas.circle(p(x - r * 0.25), p(y - r * 0.28), p(r * 0.26), (255, 255, 255), 0.50)

    # High-contrast base line for small icon sizes.
    canvas.rounded_rect(p(260), p(818), p(764), p(850), p(16), (255, 190, 88), 0.72)
    canvas.rounded_rect(p(330), p(870), p(694), p(892), p(11), (91, 233, 220), 0.48)
    return canvas


def svg_source() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"
  role="img" aria-label="Enterprise Ecosystem Intelligence app icon">
  <defs>
    <linearGradient id="bg" x1="80" y1="80" x2="944" y2="944" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#06192a"/>
      <stop offset="0.55" stop-color="#073e49"/>
      <stop offset="1" stop-color="#096869"/>
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="22" stdDeviation="24" flood-color="#00101c" flood-opacity="0.42"/>
    </filter>
  </defs>
  <rect x="44" y="44" width="936" height="936" rx="218" fill="url(#bg)"/>
  <circle cx="512" cy="512" r="352" fill="none" stroke="#60e8de" stroke-width="13" opacity="0.33"/>
  <circle cx="512" cy="512" r="260" fill="none" stroke="#ffbe58" stroke-width="8" opacity="0.22"/>
  <g stroke-linecap="round" fill="none">
    <path d="M244 354 512 512 778 318" stroke="#5be9dc" stroke-width="13" opacity="0.42"/>
    <path d="M254 710 512 512 770 720" stroke="#ffbe58" stroke-width="13" opacity="0.47"/>
    <path d="M244 354 778 318" stroke="#92b5ff" stroke-width="13" opacity="0.24"/>
    <path d="M254 710 770 720" stroke="#92b5ff" stroke-width="13" opacity="0.22"/>
  </g>
  <g filter="url(#softShadow)">
    <rect x="315" y="248" width="103" height="495" rx="42" fill="#eafaf7"/>
    <rect x="374" y="248" width="340" height="89" rx="42" fill="#eafaf7"/>
    <rect x="374" y="451" width="276" height="88" rx="42" fill="#75f4e1"/>
    <rect x="374" y="653" width="366" height="90" rx="42" fill="#eafaf7"/>
  </g>
  <g>
    <circle cx="244" cy="354" r="39" fill="#5be9dc"/>
    <circle cx="778" cy="318" r="43" fill="#ffbe58"/>
    <circle cx="512" cy="512" r="48" fill="#eafaf7"/>
    <circle cx="254" cy="710" r="38" fill="#92b5ff"/>
    <circle cx="770" cy="720" r="42" fill="#ffbe58"/>
  </g>
  <rect x="260" y="818" width="504" height="32" rx="16" fill="#ffbe58" opacity="0.72"/>
  <rect x="330" y="870" width="364" height="22" rx="11" fill="#5be9dc" opacity="0.48"/>
</svg>
"""


def run(command: Iterable[str]) -> None:
    subprocess.run(list(command), check=True)


def resize_png(source: Path, target: Path, size: int) -> None:
    run(["/usr/bin/sips", "-z", str(size), str(size), str(source), "--out", str(target)])


def generate_assets(*, keep_iconset: bool = False) -> dict[str, object]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    WEB_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    canvas = render_icon(1024)
    write_png(PNG_PATH, 1024, 1024, canvas.pixels)
    SVG_PATH.write_text(svg_source(), encoding="utf-8")
    shutil.copy2(PNG_PATH, WEB_PNG_PATH)
    shutil.copy2(SVG_PATH, WEB_SVG_PATH)
    resize_png(PNG_PATH, APPLE_TOUCH_PATH, 180)

    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True)
    for filename, size in ICONSET_SIZES.items():
        resize_png(PNG_PATH, ICONSET_DIR / filename, size)
    run(["/usr/bin/iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(ICNS_PATH)])
    if not keep_iconset:
        shutil.rmtree(ICONSET_DIR)

    return {
        "generated": True,
        "png": str(PNG_PATH.relative_to(ROOT)),
        "svg": str(SVG_PATH.relative_to(ROOT)),
        "icns": str(ICNS_PATH.relative_to(ROOT)),
        "web_svg": str(WEB_SVG_PATH.relative_to(ROOT)),
        "web_png": str(WEB_PNG_PATH.relative_to(ROOT)),
        "apple_touch_icon": str(APPLE_TOUCH_PATH.relative_to(ROOT)),
        "iconset_kept": keep_iconset,
    }


def install_app_icon(app_path: Path) -> dict[str, object]:
    if not ICNS_PATH.is_file():
        raise FileNotFoundError(f"missing generated icon: {ICNS_PATH}")
    contents = app_path / "Contents"
    resources = contents / "Resources"
    plist_path = contents / "Info.plist"
    if not plist_path.is_file():
        raise FileNotFoundError(f"missing Info.plist: {plist_path}")
    resources.mkdir(parents=True, exist_ok=True)
    target = resources / f"{ICON_NAME}.icns"
    shutil.copy2(ICNS_PATH, target)
    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)
    plist["CFBundleIconFile"] = ICON_NAME
    plist["CFBundleIconName"] = ICON_NAME
    with plist_path.open("wb") as handle:
        plistlib.dump(plist, handle, sort_keys=False)
    (contents / "PkgInfo").write_text("APPL????", encoding="ascii")
    return verify_app_icon(app_path)


def verify_app_icon(app_path: Path) -> dict[str, object]:
    plist_path = app_path / "Contents" / "Info.plist"
    icon_path = app_path / "Contents" / "Resources" / f"{ICON_NAME}.icns"
    with plist_path.open("rb") as handle:
        plist = plistlib.load(handle)
    source_sha = zlib.crc32(ICNS_PATH.read_bytes()) & 0xFFFFFFFF if ICNS_PATH.exists() else None
    target_sha = zlib.crc32(icon_path.read_bytes()) & 0xFFFFFFFF if icon_path.exists() else None
    valid = (
        icon_path.is_file()
        and plist.get("CFBundleIconFile") == ICON_NAME
        and plist.get("CFBundleIconName") == ICON_NAME
        and source_sha == target_sha
    )
    return {
        "valid": valid,
        "app": str(app_path),
        "icon": str(icon_path),
        "icon_exists": icon_path.is_file(),
        "icon_bytes": icon_path.stat().st_size if icon_path.exists() else 0,
        "plist_icon_file": plist.get("CFBundleIconFile"),
        "plist_icon_name": plist.get("CFBundleIconName"),
        "icon_crc32_match": source_sha == target_sha,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep-iconset", action="store_true")
    parser.add_argument("--install-app", type=Path)
    parser.add_argument("--verify-app", type=Path)
    args = parser.parse_args()

    result: dict[str, object] = {"assets": generate_assets(keep_iconset=args.keep_iconset)}
    if args.install_app:
        result["installed_app"] = install_app_icon(args.install_app)
    if args.verify_app:
        result["verified_app"] = verify_app_icon(args.verify_app)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    valid = all(
        not isinstance(value, dict) or value.get("valid", True)
        for value in result.values()
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
