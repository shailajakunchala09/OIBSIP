"""Procedurally drawn icons (Pillow): weather glyphs, UI glyphs and the logo.

Weather icons are rendered once at 256px, cached on disk in ``assets/weather_icons``
and resized on demand — so the app needs no icon downloads and works offline.
"""
from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from config import ICON_DIR

MASTER = 256
_U = 1024  # design grid for weather icons

WEATHER_ICON_NAMES = ("sun", "moon", "partly-day", "partly-night", "cloud", "rain", "storm", "snow", "fog")


# ── helpers ───────────────────────────────────────────────────────────────────
def _rgb(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _vgrad(size: int, y0: float, y1: float, top: str, bottom: str) -> Image.Image:
    """RGBA image with a vertical gradient between y0 and y1 (solid outside)."""
    h = max(1, int(y1 - y0))
    g = Image.linear_gradient("L").resize((size, h))
    band = Image.composite(Image.new("RGBA", (size, h), _rgb(bottom) + (255,)),
                           Image.new("RGBA", (size, h), _rgb(top) + (255,)), g)
    full = Image.new("RGBA", (size, size), _rgb(top) + (255,))
    full.paste(band, (0, int(y0)))
    if y1 < size:
        full.paste(Image.new("RGBA", (size, size - int(y1)), _rgb(bottom) + (255,)), (0, int(y1)))
    return full


def _fill_mask(img: Image.Image, mask: Image.Image, y0, y1, top, bottom) -> None:
    layer = _vgrad(img.width, y0, y1, top, bottom)
    layer.putalpha(mask)
    img.alpha_composite(layer)


def _glow(img: Image.Image, cx, cy, r, color, alpha, blur) -> None:
    layer = Image.new("RGBA", img.size, _rgb(color) + (0,))
    ImageDraw.Draw(layer).ellipse((cx - r, cy - r, cx + r, cy + r), fill=_rgb(color) + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def _cloud_shape(d: ImageDraw.ImageDraw, cx, cy, s, fill) -> None:
    d.rounded_rectangle((cx - 240 * s, cy + 10 * s, cx + 240 * s, cy + 130 * s), radius=60 * s, fill=fill)
    for dx, dy, r in ((-125, -5, 90), (-5, -60, 125), (125, -10, 95)):
        x, y, rr = cx + dx * s, cy + dy * s, r * s
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=fill)


def _cloud(img, cx, cy, s, top="#FFFFFF", bottom="#CDD9EA") -> None:
    mask = Image.new("L", img.size, 0)
    _cloud_shape(ImageDraw.Draw(mask), cx, cy, s, 255)
    soft = ImageChops.offset(mask.filter(ImageFilter.GaussianBlur(18)), 0, 22).point(lambda v: int(v * 0.28))
    shade = Image.new("RGBA", img.size, (14, 28, 56, 0))
    shade.putalpha(soft)
    img.alpha_composite(shade)
    _fill_mask(img, mask, cy - 185 * s, cy + 130 * s, top, bottom)


def _sun(img, cx, cy, s) -> None:
    _glow(img, cx, cy, 250 * s, "#FFC23D", 120, 55 * s)
    d = ImageDraw.Draw(img)
    for k in range(8):
        a = math.radians(k * 45)
        p1 = (cx + math.cos(a) * 215 * s, cy + math.sin(a) * 215 * s)
        p2 = (cx + math.cos(a) * 275 * s, cy + math.sin(a) * 275 * s)
        d.line((p1, p2), fill=(255, 196, 61, 255), width=int(40 * s))
        for p in (p1, p2):
            d.ellipse((p[0] - 20 * s, p[1] - 20 * s, p[0] + 20 * s, p[1] + 20 * s), fill=(255, 196, 61, 255))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse((cx - 160 * s, cy - 160 * s, cx + 160 * s, cy + 160 * s), fill=255)
    _fill_mask(img, mask, cy - 160 * s, cy + 160 * s, "#FFE372", "#FFA31A")


def _star4(d, x, y, r, fill) -> None:
    pts = [(x, y - r), (x + .28 * r, y - .28 * r), (x + r, y), (x + .28 * r, y + .28 * r),
           (x, y + r), (x - .28 * r, y + .28 * r), (x - r, y), (x - .28 * r, y - .28 * r)]
    d.polygon(pts, fill=fill)


def _moon(img, cx, cy, r) -> None:
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    off, rr = r * 0.52, r * 0.86
    md.ellipse((cx + off - rr, cy - off * 0.6 - rr, cx + off + rr, cy - off * 0.6 + rr), fill=0)
    glow = Image.new("RGBA", img.size, _rgb("#FFE9A6") + (0,))
    glow.putalpha(mask.filter(ImageFilter.GaussianBlur(r * 0.16)).point(lambda v: int(v * 0.45)))
    img.alpha_composite(glow)
    _fill_mask(img, mask, cy - r, cy + r, "#FFF6CF", "#F2C769")
    d = ImageDraw.Draw(img)
    _star4(d, cx + r * 0.72, cy - r * 0.95, r * 0.16, (255, 240, 190, 255))
    _star4(d, cx + r * 1.02, cy - r * 0.35, r * 0.10, (255, 240, 190, 235))


def _shadow_under(img: Image.Image) -> Image.Image:
    solid = img.getchannel("A").point(lambda v: v if v > 200 else 0)  # ignore soft glows
    soft = ImageChops.offset(solid.filter(ImageFilter.GaussianBlur(20)), 0, 26).point(lambda v: int(v * 0.30))
    shadow = Image.new("RGBA", img.size, (12, 24, 48, 0))
    shadow.putalpha(soft)
    return Image.alpha_composite(shadow, img)


def _drops(img, xs, y, length=110, color=(70, 160, 255, 255), width=36) -> None:
    d = ImageDraw.Draw(img)
    for x in xs:
        p1, p2 = (x, y), (x - 38, y + length)
        d.line((p1, p2), fill=color, width=width)
        for p in (p1, p2):
            d.ellipse((p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2), fill=color)


def _draw_weather(name: str) -> Image.Image:
    img = Image.new("RGBA", (_U, _U), (0, 0, 0, 0))
    if name == "sun":
        _sun(img, 512, 512, 1.32)
    elif name == "moon":
        _moon(img, 490, 545, 300)
    elif name == "partly-day":
        _sun(img, 385, 390, 0.95)
        _cloud(img, 575, 650, 1.02)
    elif name == "partly-night":
        _moon(img, 390, 400, 200)
        _cloud(img, 575, 650, 1.02)
    elif name == "cloud":
        _cloud(img, 610, 470, 0.80, "#C5D2E5", "#94A8C4")
        _cloud(img, 470, 640, 1.06)
    elif name == "rain":
        _cloud(img, 512, 430, 1.15, "#E6EDF7", "#A9BBD3")
        _drops(img, (340, 512, 684), 650)
        _drops(img, (426, 598), 770)
    elif name == "storm":
        _cloud(img, 512, 420, 1.15, "#B0BDD0", "#6C7C97")
        ImageDraw.Draw(img).polygon([(566, 545), (418, 770), (516, 770), (452, 950), (652, 705), (552, 705), (618, 545)],
                                    fill=(255, 208, 60, 255))
    elif name == "snow":
        _cloud(img, 512, 420, 1.15, "#E6EDF7", "#AEBFD6")
        d = ImageDraw.Draw(img)
        for x, y in ((350, 690), (512, 740), (674, 690), (430, 860), (594, 860)):
            d.ellipse((x - 34, y - 34, x + 34, y + 34), fill=(236, 246, 255, 255), outline=(126, 180, 240, 255), width=10)
    elif name == "fog":
        _cloud(img, 512, 400, 1.02, "#EEF3FA", "#BCCADD")
        d = ImageDraw.Draw(img)
        for (x0, x1, y) in ((250, 760, 640), (330, 800, 735), (210, 690, 830)):
            d.rounded_rectangle((x0, y, x1, y + 52), radius=26, fill=(176, 194, 216, 255))
    else:
        raise ValueError(f"unknown weather icon: {name}")
    return img.resize((MASTER, MASTER), Image.LANCZOS)


def generate_weather_icons() -> None:
    """Render all bundled weather icons to ``assets/weather_icons``."""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for name in WEATHER_ICON_NAMES:
        _draw_weather(name).save(ICON_DIR / f"{name}.png")


@lru_cache(maxsize=None)
def _master(name: str) -> Image.Image:
    path = ICON_DIR / f"{name}.png"
    try:
        return Image.open(path).convert("RGBA")
    except (OSError, ValueError):
        image = _draw_weather(name)
        try:
            ICON_DIR.mkdir(parents=True, exist_ok=True)
            image.save(path)
        except OSError:
            pass
        return image


@lru_cache(maxsize=256)
def weather_icon(name: str, size: int) -> Image.Image:
    return _master(name).resize((size, size), Image.LANCZOS)


# ── UI glyphs (single colour, drawn on a mask) ───────────────────────────────
def _line(d, pts, w, fill=255):
    d.line(pts, fill=fill, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=fill)


def _ring(d, cx, cy, r, w, fill=255):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fill, width=int(w))


def _disc(d, cx, cy, r, fill=255):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def _star_pts(cx, cy, r_out, r_in):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def _glyph(name: str, d: ImageDraw.ImageDraw, W: int) -> None:
    w = W * 0.085
    P = lambda x, y: (x * W, y * W)
    if name == "search":
        _ring(d, .43 * W, .43 * W, .27 * W, w)
        _line(d, [P(.64, .64), P(.87, .87)], w)
    elif name == "search-x":
        _ring(d, .40 * W, .40 * W, .25 * W, w)
        _line(d, [P(.60, .60), P(.84, .84)], w)
        _line(d, [P(.31, .31), P(.49, .49)], w * .8)
        _line(d, [P(.49, .31), P(.31, .49)], w * .8)
    elif name == "locate":
        _ring(d, .5 * W, .5 * W, .26 * W, w)
        _disc(d, .5 * W, .5 * W, .09 * W)
        for a, b in (((.5, .06), (.5, .2)), ((.5, .8), (.5, .94)), ((.06, .5), (.2, .5)), ((.8, .5), (.94, .5))):
            _line(d, [P(*a), P(*b)], w)
    elif name == "pin":
        _disc(d, .5 * W, .38 * W, .27 * W)
        d.polygon([P(.27, .5), P(.73, .5), P(.5, .93)], fill=255)
        _disc(d, .5 * W, .38 * W, .1 * W, 0)
    elif name in ("star", "star-outline"):
        pts = _star_pts(.5 * W, .54 * W, .42 * W, .18 * W)
        if name == "star":
            d.polygon(pts, fill=255)
        else:
            _line(d, pts + [pts[0]], w * .85)
    elif name == "refresh":
        box = (.14 * W, .14 * W, .86 * W, .86 * W)
        d.arc(box, 40, 320, fill=255, width=int(w))
        a = math.radians(320)
        px, py = .5 * W + .36 * W * math.cos(a), .5 * W + .36 * W * math.sin(a)
        tx, ty = -math.sin(a), math.cos(a)
        nx, ny = math.cos(a), math.sin(a)
        size = .2 * W
        d.polygon([(px + tx * size * 1.1, py + ty * size * 1.1), (px + nx * size, py + ny * size),
                   (px - nx * size, py - ny * size)], fill=255)
    elif name == "sun":
        _disc(d, .5 * W, .5 * W, .19 * W)
        for k in range(8):
            a = math.radians(k * 45)
            _line(d, [P(.5 + .32 * math.cos(a), .5 + .32 * math.sin(a)), P(.5 + .43 * math.cos(a), .5 + .43 * math.sin(a))], w * .9)
    elif name == "moon":
        _disc(d, .48 * W, .5 * W, .36 * W)
        _disc(d, .64 * W, .38 * W, .31 * W, 0)
    elif name == "drop":
        _disc(d, .5 * W, .62 * W, .27 * W)
        d.polygon([P(.5, .08), P(.25, .55), P(.75, .55)], fill=255)
    elif name == "wind":
        d.arc((.52 * W, .12 * W, .86 * W, .46 * W), -90, 130, fill=255, width=int(w))
        _line(d, [P(.1, .36), P(.68, .36)], w)
        d.arc((.5 * W, .44 * W, .88 * W, .82 * W), -90, 140, fill=255, width=int(w))
        _line(d, [P(.1, .58), P(.7, .58)], w)
        _line(d, [P(.1, .8), P(.5, .8)], w)
    elif name == "gauge":
        d.arc((.1 * W, .16 * W, .9 * W, .96 * W), 180, 360, fill=255, width=int(w))
        _line(d, [P(.5, .56), P(.7, .34)], w)
        _disc(d, .5 * W, .56 * W, .09 * W)
    elif name == "eye":
        d.ellipse((.06 * W, .27 * W, .94 * W, .73 * W), outline=255, width=int(w))
        _disc(d, .5 * W, .5 * W, .13 * W)
    elif name == "cloud":
        s = W / 1024 * 1.8
        _cloud_shape(d, .5 * W, .5 * W + 27 * s, s, 255)
    elif name in ("sunrise", "sunset"):
        d.pieslice((.22 * W, .44 * W, .78 * W, 1.0 * W), 180, 360, fill=255)
        _line(d, [P(.06, .72), P(.94, .72)], w * .9)
        if name == "sunrise":
            _line(d, [P(.5, .34), P(.5, .1)], w * .85)
            d.polygon([P(.5, .02), P(.35, .19), P(.65, .19)], fill=255)
        else:
            _line(d, [P(.5, .06), P(.5, .3)], w * .85)
            d.polygon([P(.5, .38), P(.35, .21), P(.65, .21)], fill=255)
    elif name == "clock":
        _ring(d, .5 * W, .5 * W, .4 * W, w)
        _line(d, [P(.5, .5), P(.5, .26)], w)
        _line(d, [P(.5, .5), P(.68, .6)], w)
    elif name == "alert":
        d.polygon([P(.5, .08), P(.95, .88), P(.05, .88)], fill=255)
        _line(d, [P(.5, .34), P(.5, .6)], w * 1.1, 0)
        _disc(d, .5 * W, .74 * W, .06 * W, 0)
    elif name == "wifi-off":
        for r in (.42, .28, .14):
            d.arc((.5 * W - r * W, .78 * W - r * W, .5 * W + r * W, .78 * W + r * W), 225, 315, fill=255, width=int(w))
        _disc(d, .5 * W, .78 * W, .06 * W)
        _line(d, [P(.14, .1), P(.86, .9)], w * 1.1)
    elif name == "key":
        _ring(d, .32 * W, .5 * W, .2 * W, w)
        _line(d, [P(.5, .5), P(.9, .5)], w)
        _line(d, [P(.76, .5), P(.76, .68)], w)
        _line(d, [P(.9, .5), P(.9, .64)], w)
    elif name == "close":
        _line(d, [P(.22, .22), P(.78, .78)], w)
        _line(d, [P(.78, .22), P(.22, .78)], w)
    elif name == "check":
        _line(d, [P(.18, .54), P(.42, .76), P(.84, .26)], w)
    else:
        raise ValueError(f"unknown glyph: {name}")


@lru_cache(maxsize=512)
def ui_icon(name: str, size: int, color: str) -> Image.Image:
    ss = 8
    W = size * ss
    mask = Image.new("L", (W, W), 0)
    _glyph(name, ImageDraw.Draw(mask), W)
    mask = mask.resize((size, size), Image.LANCZOS)
    img = Image.new("RGBA", (size, size), _rgb(color) + (255,))
    img.putalpha(mask)
    return img


@lru_cache(maxsize=8)
def logo(size: int) -> Image.Image:
    """SkyPulse mark: gradient tile, rising-sun arc and a pulse line."""
    ss = 4
    W = size * ss
    tile = Image.new("RGBA", (W, W))
    grad = _vgrad(W, 0, W, "#4F9DFF", "#1B4FD6")
    tile.paste(grad, (0, 0))
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, W - 1), radius=int(W * .27), fill=255)
    tile.putalpha(mask)
    d = ImageDraw.Draw(tile)
    d.pieslice((W * .22, W * .18, W * .78, W * .74), 180, 360, fill=(255, 214, 102, 255))
    pts = [(W * .14, W * .62), (W * .34, W * .62), (W * .42, W * .44), (W * .53, W * .8),
           (W * .62, W * .54), (W * .68, W * .62), (W * .86, W * .62)]
    d.line(pts, fill=(255, 255, 255, 255), width=int(W * .07), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - W * .035, y - W * .035, x + W * .035, y + W * .035), fill=(255, 255, 255, 255))
    return tile.resize((size, size), Image.LANCZOS)
