"""Dashboard cards: hero, metric tiles, hourly/daily forecast cards and state panels."""
from __future__ import annotations

from models import WeatherReport, country_name, status_for, classify
from theme import atmosphere, mix
from units import (
    Formatter,
    beaufort_label,
    compass,
    fmt_clock,
    fmt_duration,
    fmt_hour,
)
from ui.widgets import ThemedFrame, ThemedLabel, CanvasButton, CanvasCard
from ui import render
from ui.icons import weather_icon
from ui.style import S, fit_text, font


STAR_GOLD = "#FFC53D"


# ─────────────────────────────────────────────────────────────────────────────
# HERO CARD
# ─────────────────────────────────────────────────────────────────────────────

class HeroCard(CanvasCard):
    """Current weather conditions on a weather-adaptive gradient."""

    radius = 28

    def __init__(self, master, theme, on_favorite):
        super().__init__(master, theme, height=292, inset=8)

        self.on_favorite = on_favorite
        self.report: WeatherReport | None = None
        self.fmt = Formatter()
        self.favorite = False

    def set_report(self, report: WeatherReport, fmt: Formatter, favorite: bool):
        self.report = report
        self.fmt = fmt
        self.favorite = favorite
        self.redraw()

    def _atm(self):
        c = self.report.current if self.report else None
        return atmosphere(
            self.theme.mode,
            c.kind if c else "clouds",
            c.night if c else False,
        )

    def surface_args(self, p):
        a = self._atm()

        return dict(
            fill=a.top,
            gradient=(a.top, a.bottom),
            atmosphere_kind=a.kind,
            night=a.night,
            text_color=a.text,
            border=None,
            **self.shadow_args(p),
        )

    def draw_content(self, w, h, p):
        if not self.report:
            return

        c = self.report.current
        fmt = self.fmt
        a = self._atm()

        x0, y0, x1, y1 = self.body_box(w, h, p)

        pad = S(30)
        left = x0 + pad
        right = x1 - pad

        icon_size = min(
            S(150),
            max(S(100), int((x1 - x0) * 0.30)),
        )

        # Status
        title, tip = status_for(c.kind, c.night)

        f_pill = font(13, True)
        pill_w = f_pill.measure(title) + S(38)
        pill_h = S(30)

        self.add_image(
            left,
            y0 + S(22),
            render.pill(pill_w, pill_h, a.pill),
        )

        dot = S(4)

        self.create_oval(
            left + S(14) - dot,
            y0 + S(37) - dot,
            left + S(14) + dot,
            y0 + S(37) + dot,
            fill=a.text,
            outline="",
        )

        self.create_text(
            left + S(26),
            y0 + S(37),
            text=title,
            anchor="w",
            fill=a.text,
            font=f_pill,
        )

        tip_x = left + pill_w + S(12)

        available_tip = max(S(100), right - S(48) - tip_x)

        self.create_text(
            tip_x,
            y0 + S(37),
            anchor="w",
            fill=a.muted,
            font=font(13),
            text=fit_text(
                font(13),
                tip,
                available_tip,
            ),
        )

        # Favourite
        star, star_color = (
            ("star", STAR_GOLD)
            if self.favorite
            else ("star-outline", a.text)
        )

        self.add_icon(
            star,
            right - S(12),
            y0 + S(37),
            26,
            star_color,
            tags="fav",
        )

        self.tag_bind(
            "fav",
            "<Button-1>",
            lambda _e: self.on_favorite(),
        )

        self.tag_bind(
            "fav",
            "<Enter>",
            lambda _e: self.configure(cursor="hand2"),
        )

        self.tag_bind(
            "fav",
            "<Leave>",
            lambda _e: self.configure(cursor=""),
        )

        # City
        text_w = max(
            S(180),
            right - left - icon_size - S(20),
        )

        f_city = font(31, True)

        self.create_text(
            left,
            y0 + S(88),
            anchor="w",
            fill=a.text,
            font=f_city,
            text=fit_text(
                f_city,
                c.city,
                text_w,
            ),
        )

        self.add_icon(
            "pin",
            left + S(8),
            y0 + S(121),
            17,
            a.muted,
        )

        country = country_name(c.country) or "—"

        self.create_text(
            left + S(24),
            y0 + S(121),
            anchor="w",
            fill=a.muted,
            font=font(15),
            text=fit_text(
                font(15),
                country,
                text_w - S(24),
            ),
        )

        # Temperature
        f_temp = font(84, True)
        temp = fmt.temp(c.temp_c)

        self.create_text(
            left - S(3),
            y0 + S(184),
            anchor="w",
            fill=a.text,
            font=f_temp,
            text=temp,
        )

        tw = f_temp.measure(temp)

        self.create_text(
            left + tw + S(2),
            y0 + S(155),
            anchor="w",
            fill=a.muted,
            font=font(26, True),
            text=fmt.temp_unit[1:],
        )

        self.create_text(
            left,
            y0 + S(238),
            anchor="w",
            fill=a.muted,
            font=font(15),
            text=f"Feels like {fmt.temp(c.feels_like_c)}",
        )

        # Weather icon
        cx = right - icon_size // 2 - S(14)

        self.add_image(
            cx,
            y0 + S(118),
            weather_icon(c.icon, icon_size),
            anchor="center",
        )

        self.create_text(
            cx,
            y0 + S(206),
            anchor="center",
            fill=a.text,
            font=font(18, True),
            text=fit_text(
                font(18, True),
                c.description.capitalize(),
                icon_size + S(70),
            ),
        )

        self.create_text(
            cx,
            y0 + S(232),
            anchor="center",
            fill=a.muted,
            font=font(14),
            text=(
                f"High {fmt.temp(c.temp_max_c)}"
                f"   ·   "
                f"Low {fmt.temp(c.temp_min_c)}"
            ),
        )

        # Footer
        updated = fmt_clock(self.report.fetched_at)

        self.create_text(
            left,
            y1 - S(20),
            anchor="w",
            fill=a.muted,
            font=font(12),
            text=(
                f"Last updated {updated}"
                f"   ·   Local time {fmt_clock(c.city_now())}"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# METRIC CARD
# ─────────────────────────────────────────────────────────────────────────────

class MetricCard(CanvasCard):
    """Small weather statistic tile."""

    radius = 20

    def __init__(self, master, theme):
        super().__init__(
            master,
            theme,
            height=124,
            inset=6,
        )

        self.data = (
            "cloud",
            "",
            "",
            "",
            "neutral",
        )

    def set_data(
        self,
        icon,
        label,
        value,
        sub="",
        level="neutral",
    ):
        self.data = (
            icon,
            label,
            value,
            sub,
            level,
        )
        self.redraw()

    def draw_content(self, w, h, p):
        icon, label, value, sub, level = self.data

        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        pad = S(15)
        badge = S(36)

        self.add_image(
            x0 + pad,
            y0 + pad,
            render.surface(
                badge,
                badge,
                S(12),
                mix(
                    p.accent,
                    p.surface,
                    0.86,
                ),
                p.surface,
            ),
        )

        self.add_icon(
            icon,
            x0 + pad + badge // 2,
            y0 + pad + badge // 2,
            20,
            p.accent,
        )

        avail = x1 - x0 - 2 * pad

        self.create_text(
            x0 + pad,
            y1 - S(60),
            anchor="w",
            fill=p.text_muted,
            font=font(12),
            text=fit_text(
                font(12),
                label,
                avail,
            ),
        )

        self.create_text(
            x0 + pad,
            y1 - S(38),
            anchor="w",
            fill=p.text,
            font=font(21, True),
            text=fit_text(
                font(21, True),
                value,
                avail,
            ),
        )

        color = {
            "good": p.good,
            "warn": p.warn,
        }.get(
            level,
            p.text_faint,
        )

        if sub:
            self.create_text(
                x0 + pad,
                y1 - S(17),
                anchor="w",
                fill=color,
                font=font(11, True),
                text=fit_text(
                    font(11, True),
                    sub,
                    avail,
                ),
            )


# ─────────────────────────────────────────────────────────────────────────────
# HOURLY CARD
# ─────────────────────────────────────────────────────────────────────────────

class HourCard(CanvasCard):
    radius = 22

    def __init__(self, master, theme):
        super().__init__(
            master,
            theme,
            height=172,
            inset=6,
        )

        self.data = None

    def set_data(
        self,
        time,
        icon,
        temp,
        cond,
        pop,
    ):
        self.data = (
            time,
            icon,
            temp,
            cond,
            pop,
        )
        self.redraw()

    def draw_content(self, w, h, p):
        if not self.data:
            return

        time, icon, temp, cond, pop = self.data

        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        cx = (x0 + x1) // 2
        avail = x1 - x0 - S(16)

        self.create_text(
            cx,
            y0 + S(24),
            text=time,
            fill=p.text_muted,
            font=font(14, True),
        )

        isz = min(
            S(58),
            max(
                S(30),
                (x1 - x0) - S(28),
            ),
        )

        self.add_image(
            cx,
            y0 + S(70),
            weather_icon(icon, isz),
            anchor="center",
        )

        self.create_text(
            cx,
            y0 + S(112),
            text=temp,
            fill=p.text,
            font=font(22, True),
        )

        self.create_text(
            cx,
            y0 + S(136),
            text=fit_text(
                font(12),
                cond,
                avail,
            ),
            fill=p.text_muted,
            font=font(12),
        )

        if pop >= 0.2:
            self.create_text(
                cx,
                y1 - S(12),
                text=f"{round(pop * 100)}% rain",
                fill=p.accent,
                font=font(11, True),
            )


# ─────────────────────────────────────────────────────────────────────────────
# DAILY CARD
# ─────────────────────────────────────────────────────────────────────────────

class DayCard(CanvasCard):
    """Five-day weather forecast card."""

    radius = 24

    def __init__(self, master, theme):
        super().__init__(
            master,
            theme,
            height=222,
            inset=6,
        )

        self.data = None
        self.kind = "clouds"

    def set_data(
        self,
        name,
        date,
        icon,
        cond,
        high,
        low,
        pop,
        lo_frac,
        hi_frac,
        today=False,
        kind="clouds",
    ):
        self.data = (
            name,
            date,
            icon,
            cond,
            high,
            low,
            pop,
            lo_frac,
            hi_frac,
            today,
        )

        self.kind = kind
        self.redraw()

    @property
    def atm(self):
        return atmosphere(
            self.theme.mode,
            self.kind,
            False,
        )

    def surface_args(self, p):
        if self.data and self.data[-1]:
            a = self.atm

            return dict(
                fill=a.top,
                gradient=(a.top, a.bottom),
                atmosphere_kind=a.kind,
                night=a.night,
                text_color=a.text,
                border=None,
                **self.shadow_args(p),
            )

        return super().surface_args(p)

    def draw_content(self, w, h, p):
        if not self.data:
            return

        (
            name,
            date,
            icon,
            cond,
            high,
            low,
            pop,
            lo_frac,
            hi_frac,
            today,
        ) = self.data

        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        a = self.atm if today else None

        fg = a.text if a else p.text
        muted = a.muted if a else p.text_muted

        cx = (x0 + x1) // 2
        pad = S(16)

        avail = x1 - x0 - 2 * pad

        if today:
            badge = font(11, True)

            bw = (
                badge.measure("TODAY")
                + S(22)
            )

            self.add_image(
                cx - bw // 2,
                y0 + S(14),
                render.pill(
                    bw,
                    S(22),
                    a.pill,
                ),
            )

            self.create_text(
                cx,
                y0 + S(25),
                text="TODAY",
                fill=fg,
                font=badge,
            )

            name_y = y0 + S(50)
            date_y = y0 + S(70)

        else:
            name_y = y0 + S(32)
            date_y = y0 + S(53)

        self.create_text(
            cx,
            name_y,
            text=name,
            fill=fg,
            font=font(17, True),
        )

        self.create_text(
            cx,
            date_y,
            text=date,
            fill=muted,
            font=font(12),
        )

        self.add_image(
            cx,
            y0 + S(112),
            weather_icon(
                icon,
                min(S(62), avail),
            ),
            anchor="center",
        )

        self.create_text(
            cx,
            y0 + S(150),
            text=fit_text(
                font(13),
                cond,
                avail,
            ),
            fill=muted,
            font=font(13),
        )

        # Temperatures
        f_hi = font(21, True)
        f_lo = font(16)

        y_t = y0 + S(176)

        self.create_text(
            cx - S(6),
            y_t,
            text=high,
            fill=fg,
            font=f_hi,
            anchor="e",
        )

        self.create_text(
            cx + S(2),
            y_t + S(2),
            text="/",
            fill=muted,
            font=f_lo,
            anchor="w",
        )

        self.create_text(
            cx + S(14),
            y_t + S(2),
            text=low,
            fill=muted,
            font=f_lo,
            anchor="w",
        )

        # Range bar
        bar_w = avail
        bar_h = S(6)
        bar_y = y1 - S(16)

        track = (
            mix(
                fg,
                a.bottom,
                0.8,
            )
            if a
            else mix(
                p.border,
                p.surface,
                0.4,
            )
        )

        self.add_image(
            cx - bar_w // 2,
            bar_y,
            render.bar(
                bar_w,
                bar_h,
                track,
            ),
        )

        seg_x = int(
            bar_w * lo_frac
        )

        seg_w = max(
            S(10),
            int(
                bar_w
                * (hi_frac - lo_frac)
            ),
        )

        seg_x = min(
            seg_x,
            bar_w - seg_w,
        )

        self.add_image(
            cx - bar_w // 2 + seg_x,
            bar_y,
            render.bar(
                seg_w,
                bar_h,
                fg if a else p.accent,
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# WELCOME CARD
# ─────────────────────────────────────────────────────────────────────────────

class WelcomeCard(CanvasCard):
    """Welcome screen shown before the first weather search."""

    radius = 28

    def __init__(self, master, theme):
        super().__init__(
            master,
            theme,
            height=360,
            inset=8,
        )

        self.key_missing = False

    def set_key_missing(self, missing: bool):
        self.key_missing = missing
        self.redraw()

    def surface_args(self, p):
        return dict(
            fill=p.surface,
            gradient=(
                mix(
                    p.surface,
                    p.accent,
                    0.16 if p.name == "dark" else 0.10,
                ),
                p.surface,
            ),
            border=p.border if p.bordered else None,
            **self.shadow_args(p),
        )

    def draw_content(self, w, h, p):
        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        cx = (x0 + x1) // 2

        # Weather icons
        icons = (
            "sun",
            "partly-day",
            "rain",
            "snow",
            "moon",
        )

        size = S(52)
        gap = S(16)

        total_w = (
            len(icons) * size
            + (len(icons) - 1) * gap
        )

        start_x = cx - total_w // 2

        for i, name in enumerate(icons):
            self.add_image(
                start_x + i * (size + gap),
                y0 + S(28),
                weather_icon(
                    name,
                    size,
                ),
            )

        # IMPORTANT:
        # Keep title and description far enough apart.
        title_y = y0 + S(120)

        self.create_text(
            cx,
            title_y,
            text="Welcome to SkyPulse",
            fill=p.text,
            font=font(30, True),
            anchor="center",
        )

        description = (
            "Search any city or use your location "
            "to see live conditions, the next six "
            "hours and a five-day outlook."
        )

        self.create_text(
            cx,
            y0 + S(170),
            anchor="n",
            justify="center",
            fill=p.text_muted,
            font=font(15),
            width=min(
                S(650),
                max(
                    S(350),
                    x1 - x0 - S(80),
                ),
            ),
            text=description,
        )

        # Tips
        tips = (
            (
                "search",
                "Type a city and press Enter",
            ),
            (
                "locate",
                "Or detect your location",
            ),
            (
                "star",
                "Star cities to pin them",
            ),
        )

        tip_font = font(13)

        widths = [
            tip_font.measure(text) + S(36)
            for _, text in tips
        ]

        total_tips = (
            sum(widths)
            + S(24) * (len(tips) - 1)
        )

        tip_x = cx - total_tips // 2

        # Place tips below the description.
        tip_y = y1 - S(60)

        for (
            (icon_name, text),
            tip_width,
        ) in zip(
            tips,
            widths,
        ):
            self.add_icon(
                icon_name,
                tip_x + S(9),
                tip_y,
                16,
                p.accent,
            )

            self.create_text(
                tip_x + S(26),
                tip_y,
                anchor="w",
                text=text,
                fill=p.text_faint,
                font=tip_font,
            )

            tip_x += (
                tip_width
                + S(24)
            )

        # API key warning
        if self.key_missing:
            msg = (
                "OpenWeatherMap API key not found — "
                "add OPENWEATHER_API_KEY to your .env file"
            )

            self.create_text(
                cx,
                y1 - S(22),
                text=msg,
                fill=p.warn,
                font=font(12, True),
                anchor="center",
            )


# ─────────────────────────────────────────────────────────────────────────────
# LOADING CARD
# ─────────────────────────────────────────────────────────────────────────────

class LoadingCard(CanvasCard):
    """Loading state."""

    radius = 28

    def __init__(self, master, theme):
        super().__init__(
            master,
            theme,
            height=330,
            inset=8,
        )

        self._angle = 0
        self._job = None
        self._arc = None
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._tick()

    def stop(self):
        self._running = False

        if self._job is not None:
            self.after_cancel(
                self._job
            )
            self._job = None

    def _tick(self):
        if not self._running:
            return

        self._angle = (
            self._angle - 10
        ) % 360

        if self._arc is not None:
            try:
                self.itemconfigure(
                    self._arc,
                    start=self._angle,
                )
            except tk.TclError:
                pass

        self._job = self.after(
            30,
            self._tick,
        )

    def draw_content(self, w, h, p):
        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        cx = (x0 + x1) // 2

        r = S(30)
        cy = y0 + S(88)

        self.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            outline=(
                p.border
                if p.bordered
                else mix(
                    p.border,
                    p.surface,
                    0.3,
                )
            ),
            width=S(6),
        )

        self._arc = self.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=self._angle,
            extent=100,
            style="arc",
            outline=p.accent,
            width=S(6),
        )

        self.create_text(
            cx,
            y0 + S(160),
            text="Fetching weather…",
            fill=p.text,
            font=font(22, True),
        )

        self.create_text(
            cx,
            y0 + S(190),
            text="Contacting OpenWeatherMap",
            fill=p.text_muted,
            font=font(14),
        )

        bar_h = S(12)

        for i, frac in enumerate(
            (0.42, 0.30, 0.20)
        ):
            bw = int(
                (x1 - x0) * frac
            )

            self.add_image(
                cx - bw // 2,
                y0 + S(226) + i * S(22),
                render.bar(
                    bw,
                    bar_h,
                    p.surface_alt,
                ),
            )


# ─────────────────────────────────────────────────────────────────────────────
# ERROR CARD
# ─────────────────────────────────────────────────────────────────────────────

class ErrorCard(CanvasCard):
    """Friendly error panel."""

    radius = 28

    _TONES = {
        "invalid_key": "danger",
        "missing_key": "warn",
        "timeout": "warn",
        "no_connection": "warn",
        "rate_limit": "warn",
        "location": "warn",
        "city_not_found": "accent",
    }

    def __init__(
        self,
        master,
        theme,
        on_retry,
    ):
        super().__init__(
            master,
            theme,
            height=430,
            inset=8,
        )

        self.err = None

        self.retry = CanvasButton(
            self,
            theme,
            text="Retry",
            icon="refresh",
            command=on_retry,
            style="primary",
            height=46,
            padx=26,
            bg_role="surface",
        )

    def set_error(self, err):
        self.err = err
        self.redraw()

    def draw_content(self, w, h, p):
        if not self.err:
            return

        e = self.err

        x0, y0, x1, y1 = self.body_box(
            w,
            h,
            p,
        )

        cx = (x0 + x1) // 2

        tone = getattr(
            p,
            self._TONES.get(
                e.kind,
                "danger",
            ),
        )

        r = S(40)
        cy = y0 + S(72)

        self.add_image(
            cx - r,
            cy - r,
            render.surface(
                2 * r,
                2 * r,
                r,
                mix(
                    tone,
                    p.surface,
                    0.84,
                ),
                p.surface,
            ),
        )

        self.add_icon(
            e.icon,
            cx,
            cy,
            38,
            tone,
        )

        self.create_text(
            cx,
            y0 + S(142),
            text=e.title,
            fill=p.text,
            font=font(25, True),
        )

        wrap = min(
            S(560),
            x1 - x0 - S(60),
        )

        msg = self.create_text(
            cx,
            y0 + S(174),
            anchor="n",
            justify="center",
            width=wrap,
            fill=p.text_muted,
            font=font(15),
            text=e.message,
        )

        bottom = self.bbox(msg)[3]

        if e.hints:
            hints = self.create_text(
                cx,
                bottom + S(14),
                anchor="n",
                justify="center",
                width=wrap,
                fill=p.text_faint,
                font=font(13),
                text="\n".join(
                    f"•  {t}"
                    for t in e.hints
                ),
            )

            bottom = self.bbox(hints)[3]

        if e.retryable:
            self.create_window(
                cx,
                bottom + S(20),
                window=self.retry,
                anchor="n",
            )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _humidity(v):
    if v < 30:
        return "Dry", "warn"

    if v <= 60:
        return "Comfortable", "good"

    if v <= 80:
        return "Humid", "neutral"

    return "Very humid", "warn"


def _pressure(v):
    if v < 1000:
        return "Low", "warn"

    if v <= 1020:
        return "Normal", "good"

    return "High", "neutral"


def _visibility(m):
    if m is None:
        return "", "neutral"

    if m >= 10000:
        return "Excellent", "good"

    if m >= 5000:
        return "Good", "good"

    if m >= 2000:
        return "Moderate", "warn"

    return "Poor", "warn"


def _clouds(v):
    if v < 20:
        return "Clear sky"

    if v < 60:
        return "Partly cloudy"

    if v < 90:
        return "Mostly cloudy"

    return "Overcast"


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD VIEW
# ─────────────────────────────────────────────────────────────────────────────

class DashboardView(ThemedFrame):
    """Hero + metrics + hourly + daily forecast."""

    WIDE_AT = 1040

    def __init__(
        self,
        master,
        theme,
        on_favorite,
    ):
        super().__init__(
            master,
            theme,
        )

        self.theme = theme

        self.hero = HeroCard(
            self,
            theme,
            on_favorite,
        )

        self.metrics = ThemedFrame(
            self,
            theme,
        )

        self.metric_cards = []

        for i in range(8):
            card = MetricCard(
                self.metrics,
                theme,
            )

            card.grid(
                row=i // 4,
                column=i % 4,
                sticky="nsew",
            )

            self.metric_cards.append(card)

        for c in range(4):
            self.metrics.columnconfigure(
                c,
                weight=1,
                uniform="metric",
            )

        for r in range(2):
            self.metrics.rowconfigure(
                r,
                weight=1,
            )

        # Hourly
        self.hour_title = ThemedLabel(
            self,
            theme,
            "Hourly forecast",
            font=font(19, True),
            anchor="w",
        )

        self.hour_note = ThemedLabel(
            self,
            theme,
            "Next 6 hours",
            fg="text_faint",
            font=font(13),
            anchor="e",
        )

        self.hour_row = ThemedFrame(
            self,
            theme,
        )

        self.hour_cards = [
            HourCard(
                self.hour_row,
                theme,
            )
            for _ in range(6)
        ]

        for i, card in enumerate(
            self.hour_cards
        ):
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
            )

            self.hour_row.columnconfigure(
                i,
                weight=1,
                uniform="hour",
            )

        # Daily
        self.day_title = ThemedLabel(
            self,
            theme,
            "5-day forecast",
            font=font(19, True),
            anchor="w",
        )

        self.day_note = ThemedLabel(
            self,
            theme,
            "Daily high / low",
            fg="text_faint",
            font=font(13),
            anchor="e",
        )

        self.day_row = ThemedFrame(
            self,
            theme,
        )

        self.day_cards = [
            DayCard(
                self.day_row,
                theme,
            )
            for _ in range(5)
        ]

        for i, card in enumerate(
            self.day_cards
        ):
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
            )

            self.day_row.columnconfigure(
                i,
                weight=1,
                uniform="day",
            )

        self.columnconfigure(
            0,
            weight=1,
            uniform="col",
        )

        self.columnconfigure(
            1,
            weight=1,
            uniform="col",
        )

        self._wide = None

        self.bind(
            "<Configure>",
            lambda e: self._relayout(e.width),
        )

        self._relayout(
            S(1200)
        )

    def _relayout(self, width):
        wide = (
            width >= S(self.WIDE_AT)
        )

        if wide == self._wide:
            return

        self._wide = wide

        title_pad = {
            "padx": S(14),
            "pady": (
                S(14),
                S(0),
            ),
        }

        if wide:
            self.hero.grid(
                row=0,
                column=0,
                columnspan=1,
                sticky="nsew",
            )

            self.metrics.grid(
                row=0,
                column=1,
                columnspan=1,
                sticky="nsew",
            )

        else:
            self.hero.grid(
                row=0,
                column=0,
                columnspan=2,
                sticky="nsew",
            )

            self.metrics.grid(
                row=1,
                column=0,
                columnspan=2,
                sticky="nsew",
            )

        base = 1 if wide else 2

        self.hour_title.grid(
            row=base,
            column=0,
            sticky="w",
            **title_pad,
        )

        self.hour_note.grid(
            row=base,
            column=1,
            sticky="e",
            **title_pad,
        )

        self.hour_row.grid(
            row=base + 1,
            column=0,
            columnspan=2,
            sticky="nsew",
        )

        self.day_title.grid(
            row=base + 2,
            column=0,
            sticky="w",
            **title_pad,
        )

        self.day_note.grid(
            row=base + 2,
            column=1,
            sticky="e",
            **title_pad,
        )

        self.day_row.grid(
            row=base + 3,
            column=0,
            columnspan=2,
            sticky="nsew",
        )

    def update_report(
        self,
        report: WeatherReport,
        fmt: Formatter,
        favorite: bool,
    ):
        c = report.current

        self.hero.set_report(
            report,
            fmt,
            favorite,
        )

        hum, hum_lvl = _humidity(
            c.humidity
        )

        wind_sub = (
            beaufort_label(
                c.wind_speed_ms
            )
            + (
                f" · {compass(c.wind_deg)}"
                if c.wind_deg is not None
                else ""
            )
        )

        pres, pres_lvl = _pressure(
            c.pressure_hpa
        )

        vis, vis_lvl = _visibility(
            c.visibility_m
        )

        length = c.day_length_minutes

        tiles = [
            (
                "drop",
                "Humidity",
                f"{c.humidity}%",
                hum,
                hum_lvl,
            ),
            (
                "wind",
                "Wind speed",
                fmt.wind(
                    c.wind_speed_ms
                ),
                wind_sub,
                "neutral",
            ),
            (
                "gauge",
                "Pressure",
                fmt.pressure(
                    c.pressure_hpa
                ),
                pres,
                pres_lvl,
            ),
            (
                "eye",
                "Visibility",
                fmt.distance(
                    c.visibility_m
                ),
                vis,
                vis_lvl,
            ),
            (
                "cloud",
                "Cloud cover",
                f"{c.clouds}%",
                _clouds(c.clouds),
                "neutral",
            ),
            (
                "sunrise",
                "Sunrise",
                fmt_clock(c.sunrise),
                "Local time",
                "neutral",
            ),
            (
                "sunset",
                "Sunset",
                fmt_clock(c.sunset),
                "Local time",
                "neutral",
            ),
            (
                "clock",
                "Daylight",
                (
                    fmt_duration(length)
                    if length is not None
                    else "—"
                ),
                "Sunrise to sunset",
                "neutral",
            ),
        ]

        for card, tile in zip(
            self.metric_cards,
            tiles,
        ):
            card.set_data(*tile)

        # Hourly
        for card, point in zip(
            self.hour_cards,
            report.hourly,
        ):
            card.set_data(
                fmt_hour(point.time),
                point.icon,
                fmt.temp(
                    point.temp_c
                ),
                point.condition_main,
                point.pop,
            )

        # Daily
        if report.daily:
            lo = min(
                d.low_c
                for d in report.daily
            )

            hi = max(
                d.high_c
                for d in report.daily
            )

            span = (
                hi - lo
            ) or 1.0

            for card, day in zip(
                self.day_cards,
                report.daily,
            ):
                card.set_data(
                    day.day.strftime("%a"),
                    f"{day.day.strftime('%b')} {day.day.day}",
                    day.icon,
                    day.description.capitalize(),
                    fmt.temp(
                        day.high_c
                    ),
                    fmt.temp(
                        day.low_c
                    ),
                    day.pop,
                    (
                        day.low_c - lo
                    ) / span,
                    (
                        day.high_c - lo
                    ) / span,
                    today=day.is_today,
                    kind=classify(
                        day.condition_id
                    ),
                )