"""Pillow renderers for card surfaces, shadows and weather 'atmosphere' overlays.

Tk cannot draw anti-aliased rounded rectangles, gradients or soft shadows, so every
card background is rendered here (supersampled) and shown as a canvas image.
Results are cached by parameters, so window resizes stay cheap.
"""
from __future__ import annotations

import random
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from theme import hex_to_rgb


def _rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = hex_to_rgb(color)
    return r, g, b, alpha


@lru_cache(maxsize=256)
def _rounded_mask(w: int, h: int, radius: int) -> Image.Image:
    ss = 3
    mask = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius=radius * ss, fill=255)
    return mask.resize((w, h), Image.LANCZOS)


def _gradient(w: int, h: int, top: str, bottom: str) -> Image.Image:
    """Soft diagonal (top-left → bottom-right) gradient."""
    vertical = Image.linear_gradient("L").resize((w, h))
    horizontal = Image.linear_gradient("L").rotate(90).resize((w, h))
    mix_mask = ImageChops.add(vertical, horizontal, scale=2)
    return Image.composite(Image.new("RGB", (w, h), hex_to_rgb(bottom)),
                           Image.new("RGB", (w, h), hex_to_rgb(top)), mix_mask).convert("RGBA")


@lru_cache(maxsize=40)
def surface(w: int, h: int, radius: int, fill: str, page_bg: str, inset: int = 0,
            border: str | None = None, border_w: int = 1, shadow_alpha: int = 0,
            shadow_blur: int = 8, shadow_offset: int = 3, gradient: tuple | None = None,
            atmosphere_kind: str | None = None, night: bool = False,
            text_color: str = "#FFFFFF") -> Image.Image:
    """Render a card: page background, soft shadow, body (solid/gradient) and optional border."""
    w, h = max(w, 4), max(h, 4)
    canvas = Image.new("RGBA", (w, h), _rgba(page_bg))
    bw, bh = w - 2 * inset, h - 2 * inset - (shadow_offset if shadow_alpha else 0)
    bw, bh = max(bw, 4), max(bh, 4)
    radius = min(radius, bw // 2, bh // 2)
    mask = _rounded_mask(bw, bh, radius)

    if shadow_alpha:
        shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_mask = Image.new("L", (w, h), 0)
        shadow_mask.paste(mask, (inset, inset + shadow_offset))
        shade.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(shadow_blur)).point(lambda v: int(v * shadow_alpha / 255)))
        canvas.alpha_composite(shade)

    if gradient:
        body = _gradient(bw, bh, *gradient)
        if atmosphere_kind:
            body.alpha_composite(_overlay(bw, bh, atmosphere_kind, night, text_color))
    else:
        body = Image.new("RGBA", (bw, bh), _rgba(fill))
    body.putalpha(mask)
    canvas.alpha_composite(body, (inset, inset))

    if border:
        inner = _rounded_mask(max(bw - 2 * border_w, 2), max(bh - 2 * border_w, 2), max(radius - border_w, 1))
        outline = Image.new("L", (bw, bh), 0)
        outline.paste(mask, (0, 0))
        hole = Image.new("L", (bw, bh), 0)
        hole.paste(inner, (border_w, border_w))
        outline = ImageChops.subtract(outline, hole)
        line = Image.new("RGBA", (bw, bh), _rgba(border))
        line.putalpha(outline)
        canvas.alpha_composite(line, (inset, inset))
    return canvas


@lru_cache(maxsize=64)
def pill(w: int, h: int, fill: str, alpha: int = 255) -> Image.Image:
    """Small translucent rounded chip, used over gradients."""
    img = Image.new("RGBA", (max(w, 4), max(h, 4)), _rgba(fill))
    mask = _rounded_mask(img.width, img.height, img.height // 2)
    img.putalpha(mask.point(lambda v: int(v * alpha / 255)))
    return img


@lru_cache(maxsize=32)
def bar(w: int, h: int, fill: str, alpha: int = 255) -> Image.Image:
    return pill(w, h, fill, alpha)


def _overlay(w: int, h: int, kind: str, night: bool, text_color: str) -> Image.Image:
    """Elegant, low-contrast decoration matching the weather (rain streaks, stars, soft glows…)."""
    ss = 2
    W, H = w * ss, h * ss
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(f"{kind}-{night}")  # stable across redraws

    def glow(cx, cy, r, color, alpha, blur):
        g = Image.new("RGBA", (W, H), color + (0,))  # same colour, alpha 0 → no dark fringe when blurred
        ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (alpha,))
        layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(blur)))

    if kind == "night" or night and kind in ("clear", "clouds"):
        glow(W * 0.86, H * 0.2, H * 0.35, (150, 170, 255), 70, H * 0.12)
        for _ in range(38):
            x, y, r = rnd.random() * W, rnd.random() * H * 0.75, rnd.choice((1.5, 2, 2.5, 3.5))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.choice((70, 110, 160))))
    elif kind == "clear":
        glow(W * 0.85, H * 0.18, H * 0.5, (255, 240, 205), 85, H * 0.2)
        glow(W * 0.85, H * 0.18, H * 0.18, (255, 250, 225), 110, H * 0.07)
    elif kind in ("rain", "storm"):
        for _ in range(70 if kind == "rain" else 110):
            x, y, ln = rnd.random() * W * 1.1, rnd.random() * H, rnd.uniform(28, 64)
            d.line((x, y, x - ln * 0.32, y + ln), fill=(255, 255, 255, rnd.choice((22, 34, 48))), width=2)
        if kind == "storm":
            glow(W * 0.78, H * 0.05, H * 0.5, (160, 140, 255), 70, H * 0.18)
    elif kind == "snow":
        for _ in range(60):
            x, y, r = rnd.random() * W, rnd.random() * H, rnd.choice((2, 3, 4, 5))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rnd.choice((90, 140, 190))))
    elif kind == "fog":
        for i in range(4):
            y = H * (0.2 + 0.2 * i)
            band = Image.new("RGBA", (W, H), (255, 255, 255, 0))
            ImageDraw.Draw(band).rounded_rectangle((-W * 0.1 + i * W * 0.07, y, W * (0.8 + 0.05 * i), y + H * 0.07),
                                                   radius=H * 0.04, fill=(255, 255, 255, 46))
            layer.alpha_composite(band.filter(ImageFilter.GaussianBlur(H * 0.03)))
    else:  # clouds
        glow(W * 0.8, H * 0.22, H * 0.4, (255, 255, 255), 60, H * 0.16)
        glow(W * 0.62, H * 0.3, H * 0.28, (255, 255, 255), 45, H * 0.14)
    return layer.filter(ImageFilter.GaussianBlur(0.6)).resize((w, h), Image.LANCZOS)
