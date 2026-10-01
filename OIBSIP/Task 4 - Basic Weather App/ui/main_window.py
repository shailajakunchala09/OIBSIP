"""Main application window: header, search, suggestion chips and the dashboard states."""
from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from datetime import datetime

from config import APP_NAME, APP_TAGLINE, APP_TITLE, DEFAULT_CITIES, Settings
from errors import SkyPulseError, ValidationError
from location_service import LocationService
from models import GeoLocation, WeatherQuery, WeatherReport
from storage import Preferences, SearchHistory, city_query
from theme import ThemeManager
from units import Formatter, UnitSystem, beaufort_label, compass, fmt_clock, fmt_duration, fmt_hour
from validators import validate_city
from weather_service import WeatherService
from ui import style
from ui.cards import DayCard, ErrorCard, HeroCard, HourCard, LoadingCard, MetricCard, WelcomeCard
from ui.icons import logo
from ui.style import S, font, photo
from ui.widgets import CanvasButton, ChipRow, ScrollFrame, SearchBar, Segmented, ThemedFrame, ThemedLabel

log = logging.getLogger(__name__)

WIDE_BREAKPOINT = 1040  # design px; below this the metric tiles move under the hero card


# ── dashboard ─────────────────────────────────────────────────────────────────
class DashboardView(ThemedFrame):
    """Hero + metrics + 6-hour strip + 5-day cards. Re-lays itself out when the window narrows."""

    METRICS = ("humidity", "wind", "pressure", "visibility", "clouds", "sunrise", "sunset", "daylight")

    def __init__(self, master, theme: ThemeManager, on_favorite):
        super().__init__(master, theme)
        self.theme = theme
        self._wide = None
        self.hero = HeroCard(self, theme, on_favorite)
        self.metric_frame = ThemedFrame(self, theme)
        self.tiles = {name: MetricCard(self.metric_frame, theme) for name in self.METRICS}
        for i, name in enumerate(self.METRICS):
            self.tiles[name].grid(row=i // 4, column=i % 4, sticky="nsew")
        for c in range(4):
            self.metric_frame.columnconfigure(c, weight=1, uniform="m")
        for r in range(2):
            self.metric_frame.rowconfigure(r, weight=1)

        self.hour_title = ThemedLabel(self, theme, "Next 6 hours", font=font(18, True), anchor="w")
        self.hour_note = ThemedLabel(self, theme, "Hourly temperatures are interpolated from 3-hour data",
                                     fg="text_faint", font=font(12), anchor="e")
        self.hour_frame = ThemedFrame(self, theme)
        self.hours = [HourCard(self.hour_frame, theme) for _ in range(6)]
        for i, card in enumerate(self.hours):
            card.grid(row=0, column=i, sticky="nsew")
            self.hour_frame.columnconfigure(i, weight=1, uniform="h")

        self.day_title = ThemedLabel(self, theme, "5-day forecast", font=font(18, True), anchor="w")
        self.day_frame = ThemedFrame(self, theme)
        self.days = [DayCard(self.day_frame, theme) for _ in range(5)]
        for i, card in enumerate(self.days):
            card.grid(row=0, column=i, sticky="nsew")
            self.day_frame.columnconfigure(i, weight=1, uniform="d")

        self.columnconfigure(0, weight=1, uniform="top")
        self.columnconfigure(1, weight=1, uniform="top")
        self.bind("<Configure>", lambda e: self._layout(e.width))
        self._layout(S(WIDE_BREAKPOINT) + 1)

    # -- responsive layout ---------------------------------------------------
    def _layout(self, width: int):
        wide = width >= S(WIDE_BREAKPOINT)
        if wide == self._wide:
            return
        self._wide = wide
        tile_h = S(146) if wide else S(140)
        for tile in self.tiles.values():
            tile.configure(height=tile_h)
        pad = S(6)
        if wide:
            self.hero.grid(row=0, column=0, columnspan=1, sticky="nsew", padx=(0, pad))
            self.metric_frame.grid(row=0, column=1, columnspan=1, sticky="nsew", padx=(pad, 0), pady=0)
            next_row = 1
        else:
            self.hero.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=0)
            self.metric_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=0, pady=(S(6), 0))
            next_row = 2
        self.hour_title.grid(row=next_row, column=0, columnspan=1, sticky="w", padx=S(8), pady=(S(14), S(2)))
        self.hour_note.grid(row=next_row, column=1, columnspan=1, sticky="e", padx=S(8), pady=(S(14), S(2)))
        self.hour_frame.grid(row=next_row + 1, column=0, columnspan=2, sticky="nsew")
        self.day_title.grid(row=next_row + 2, column=0, columnspan=2, sticky="w", padx=S(8), pady=(S(14), S(2)))
        self.day_frame.grid(row=next_row + 3, column=0, columnspan=2, sticky="nsew", pady=(0, S(12)))

    # -- data ------------------------------------------------------------------
    def update_report(self, report: WeatherReport, fmt: Formatter, favorite: bool):
        c = report.current
        self.hero.set_report(report, fmt, favorite)

        if c.humidity < 30:
            hum = ("Dry", "warn")
        elif c.humidity <= 60:
            hum = ("Comfortable", "good")
        elif c.humidity <= 80:
            hum = ("Humid", "neutral")
        else:
            hum = ("Very humid", "warn")
        pr = ("Low", "warn") if c.pressure_hpa < 1000 else ("Normal", "good") if c.pressure_hpa <= 1020 else ("High", "neutral")
        vis_m = c.visibility_m
        if vis_m is None:
            vis = ("", "neutral")
        elif vis_m >= 8000:
            vis = ("Excellent", "good")
        elif vis_m >= 4000:
            vis = ("Good", "good")
        elif vis_m >= 1000:
            vis = ("Moderate", "warn")
        else:
            vis = ("Poor", "warn")
        cl = "Clear" if c.clouds < 20 else "Partly cloudy" if c.clouds < 60 else "Mostly cloudy" if c.clouds < 90 else "Overcast"
        wind_sub = beaufort_label(c.wind_speed_ms) + (f" · {compass(c.wind_deg)}" if c.wind_deg is not None else "")
        length = c.day_length_minutes

        t = self.tiles
        t["humidity"].set_data("drop", "Humidity", f"{c.humidity}%", *hum)
        t["wind"].set_data("wind", "Wind", fmt.wind(c.wind_speed_ms), wind_sub)
        t["pressure"].set_data("gauge", "Pressure", fmt.pressure(c.pressure_hpa), *pr)
        t["visibility"].set_data("eye", "Visibility", fmt.distance(vis_m), *vis)
        t["clouds"].set_data("cloud", "Cloud cover", f"{c.clouds}%", cl)
        t["sunrise"].set_data("sunrise", "Sunrise", fmt_clock(c.sunrise), "Local time")
        t["sunset"].set_data("sunset", "Sunset", fmt_clock(c.sunset), "Local time")
        t["daylight"].set_data("clock", "Daylight", fmt_duration(length) if length is not None else "—", "Sunrise to sunset")

        for card, h in zip(self.hours, report.hourly):
            card.set_data(fmt_hour(h.time), h.icon, fmt.temp(h.temp_c), h.condition_main, h.pop)

        lows = [d.low_c for d in report.daily]
        highs = [d.high_c for d in report.daily]
        lo, hi = min(lows), max(highs)
        span = (hi - lo) or 1.0
        for card, d in zip(self.days, report.daily):
            card.set_data(d.day.strftime("%a"), f"{d.day:%b} {d.day.day}", d.icon, d.description.capitalize(),
                          fmt.temp(d.high_c), fmt.temp(d.low_c), d.pop, (d.low_c - lo) / span,
                          (d.high_c - lo) / span, today=d.is_today, kind=d.kind)


# ── main window ───────────────────────────────────────────────────────────────
class MainWindow(tk.Tk):
    def __init__(self, settings: Settings, service: WeatherService | None = None,
                 locator: LocationService | None = None, prefs: Preferences | None = None):
        super().__init__()
        style.init(self)
        self.settings = settings
        self.service = service or WeatherService(settings)
        self.locator = locator or LocationService()
        self.prefs = prefs or Preferences()
        self.history = SearchHistory()
        self.theme = ThemeManager(self.prefs.theme)
        self.fmt = Formatter(self.prefs.units)

        self.report: WeatherReport | None = None
        self._last: tuple | None = None
        self._busy = False
        self._token = 0
        self._results: queue.Queue = queue.Queue()

        self.title(APP_TITLE)
        self._logo = photo(logo(S(46)))
        try:
            self.iconphoto(True, photo(logo(64)))
        except tk.TclError:
            pass
        self.configure(bg=self.theme.palette.bg)
        self.theme.subscribe(lambda p: self.configure(bg=p.bg))
        self._set_geometry()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self._build_header()
        self._build_search()
        self._build_stage()
        self._refresh_chips()
        self._bind_keys()
        self._show("welcome")
        self._tick_clock()
        self.after(60, self._poll)
        self.after(200, self.search_bar.focus)

    # -- construction --------------------------------------------------------
    def _set_geometry(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(S(1240), sw - S(60)), min(S(940), sh - S(110))
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        self.minsize(min(S(900), sw), min(S(620), sh))

    def _build_header(self):
        header = ThemedFrame(self, self.theme)
        header.grid(row=0, column=0, sticky="ew", padx=S(20), pady=(S(16), S(6)))
        header.columnconfigure(3, weight=1)
        ThemedLabel(header, self.theme, image=self._logo).grid(row=0, column=0, rowspan=2, padx=(0, S(12)))
        ThemedLabel(header, self.theme, APP_NAME, font=font(26, True), anchor="w").grid(row=0, column=1, sticky="sw")
        ThemedLabel(header, self.theme, APP_TAGLINE, fg="text_muted", font=font(13), anchor="w").grid(row=1, column=1, sticky="nw")
        self.clock = ThemedLabel(header, self.theme, "", fg="text_muted", font=font(14), anchor="e")
        self.clock.grid(row=0, column=3, rowspan=2, sticky="e", padx=S(16))
        self.units_toggle = Segmented(header, self.theme, [("metric", "°C"), ("imperial", "°F")],
                                      self.fmt.system.value, self.set_units)
        self.units_toggle.grid(row=0, column=4, rowspan=2, padx=(0, S(10)))
        self.refresh_btn = CanvasButton(header, self.theme, icon="refresh", command=self.refresh, square=True,
                                        height=40, icon_size=18)
        self.refresh_btn.grid(row=0, column=5, rowspan=2, padx=(0, S(10)))
        self.theme_btn = CanvasButton(header, self.theme, icon="sun" if self.theme.mode == "dark" else "moon",
                                      command=self.toggle_theme, square=True, height=40, icon_size=18)
        self.theme_btn.grid(row=0, column=6, rowspan=2)

    def _build_search(self):
        row = ThemedFrame(self, self.theme)
        row.grid(row=1, column=0, sticky="ew", padx=S(20), pady=(S(8), 0))
        row.columnconfigure(0, weight=1)
        self.search_bar = SearchBar(row, self.theme, "Search a city — e.g. London, Tokyo or Paris, FR",
                                    self.search, on_change=lambda: self._inline_error(""))
        self.search_bar.grid(row=0, column=0, sticky="ew")
        self.go_btn = CanvasButton(row, self.theme, text="Get Weather", icon="cloud", command=self.search,
                                   style="primary", height=48, padx=24)
        self.go_btn.grid(row=0, column=1, padx=(S(10), 0))
        self.locate_btn = CanvasButton(row, self.theme, text="My Location", icon="locate", command=self.use_my_location,
                                       height=48, padx=20)
        self.locate_btn.grid(row=0, column=2, padx=(S(10), 0))

        self.inline = ThemedLabel(self, self.theme, "", fg="danger", font=font(13, True), anchor="w")
        self.inline.grid(row=2, column=0, sticky="ew", padx=S(30), pady=(S(2), 0))
        self.chips = ChipRow(self, self.theme, self._pick_chip)
        self.chips.grid(row=3, column=0, sticky="ew", padx=S(28), pady=(S(4), S(8)))

    def _build_stage(self):
        self.scroll = ScrollFrame(self, self.theme)
        self.scroll.grid(row=4, column=0, sticky="nsew", padx=(S(12), S(6)), pady=(0, S(6)))
        inner = self.scroll.inner
        inner.columnconfigure(0, weight=1)
        self.welcome = WelcomeCard(inner, self.theme)
        self.welcome.set_key_missing(not self.settings.has_api_key)
        self.loading = LoadingCard(inner, self.theme)
        self.error = ErrorCard(inner, self.theme, self.retry)
        self.dashboard = DashboardView(inner, self.theme, self.toggle_favorite)
        self._states = {"welcome": self.welcome, "loading": self.loading, "error": self.error,
                        "dashboard": self.dashboard}

    def _bind_keys(self):
        self.bind("<F5>", lambda _e: self.refresh())
        self.bind("<Control-r>", lambda _e: self.refresh())
        self.bind("<Control-l>", lambda _e: self.search_bar.focus())
        self.bind("<Control-t>", lambda _e: self.toggle_theme())

    # -- state switching -----------------------------------------------------
    def _show(self, name: str):
        for key, frame in self._states.items():
            if key == name:
                frame.grid(row=0, column=0, sticky="ew", padx=S(2))
            else:
                frame.grid_remove()
        if name == "loading":
            self.loading.start()
        else:
            self.loading.stop()
        self.scroll.scroll_top()

    def _show_error(self, err: SkyPulseError):
        self.error.set_error(err)
        self._show("error")

    def _inline_error(self, message: str):
        self.inline.configure(text=message)
        self.search_bar.set_error(bool(message))

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.search_bar.set_busy(busy)
        for button in (self.go_btn, self.locate_btn, self.refresh_btn):
            button.set_enabled(not busy)

    # -- actions ---------------------------------------------------------------
    def search(self):
        """Validate the search box and fetch weather for that city."""
        try:
            city = validate_city(self.search_bar.get_text())
        except ValidationError as err:
            self._inline_error(err.message)
            self.search_bar.focus()
            return
        self._inline_error("")
        self._start(("query", WeatherQuery(city=city)))

    def use_my_location(self):
        self._inline_error("")
        self._start(("location", None))

    def refresh(self):
        if self._busy:
            return
        if self._last is None:
            self._inline_error("Search for a city first, then refresh to update it.")
            return
        self._start(self._last)

    def retry(self):
        self.refresh() if self._last else self.search()

    def set_units(self, value: str):
        self.prefs.units = UnitSystem.parse(value)
        self.fmt = Formatter(self.prefs.units)
        self.units_toggle.select(self.prefs.units.value)
        self.prefs.save()
        if self.report:
            self._render_report()

    def toggle_theme(self):
        mode = self.theme.toggle()
        self.prefs.theme = mode
        self.prefs.save()
        self.theme_btn.set_icon("sun" if mode == "dark" else "moon")

    def toggle_favorite(self):
        if not self.report:
            return
        c = self.report.current
        self.prefs.toggle_favorite(c.city, c.country)
        self._render_report()
        self._refresh_chips()

    def _pick_chip(self, value: str):
        self.search_bar.set_text(value.split(",")[0])
        self._inline_error("")
        self._start(("query", WeatherQuery(city=value)))

    # -- background fetching -------------------------------------------------
    def _start(self, spec: tuple):
        if self._busy:
            return
        self._token += 1
        self._set_busy(True)
        self._show("loading")
        threading.Thread(target=self._worker, args=(self._token, spec), daemon=True).start()

    def _worker(self, token: int, spec: tuple):
        try:
            kind, arg = spec
            if kind == "location":
                loc = self.locator.detect()
                result = self.service.fetch_report(WeatherQuery.for_location(loc))
            else:
                result = self.service.fetch_report(arg)
            self._results.put((token, spec, "ok", result))
        except SkyPulseError as err:
            self._results.put((token, spec, "err", err))
        except Exception:  # never let a worker die silently
            log.exception("Unexpected error while fetching weather")
            self._results.put((token, spec, "err", SkyPulseError()))

    def _poll(self):
        try:
            while True:
                token, spec, status, payload = self._results.get_nowait()
                if token != self._token:
                    continue  # stale result from an older request
                self._set_busy(False)
                if status == "ok":
                    self._on_success(spec, payload)
                else:
                    self._last = spec if spec[0] == "location" or payload.kind != "validation" else self._last
                    self._show_error(payload)
        except queue.Empty:
            pass
        except Exception:
            log.exception("Failed to display result")
            self._set_busy(False)
            self._show_error(SkyPulseError())
        self.after(60, self._poll)

    def _on_success(self, spec: tuple, report: WeatherReport):
        c = report.current
        self.report = report
        self._last = spec if spec[0] == "query" else ("query", WeatherQuery.for_location(
            GeoLocation(c.city, c.country, c.lat, c.lon)))
        self.history.add(c.city, c.country)
        self.search_bar.set_text(c.city)
        self._render_report()
        self._refresh_chips()
        self._show("dashboard")

    def _render_report(self):
        c = self.report.current
        self.dashboard.update_report(self.report, self.fmt, self.prefs.is_favorite(c.city, c.country))

    def _refresh_chips(self):
        favs = [(f["name"], city_query(f["name"], f["country"])) for f in self.prefs.favorites]
        recents = [(r["name"], city_query(r["name"], r["country"])) for r in self.history.items()]
        groups = [("Favorites", "star", favs), ("Recent", None, recents)]
        if not favs and not recents:
            groups = [("Try", None, [(n, n) for n in DEFAULT_CITIES])]
        self.chips.set_groups(groups)

    def _tick_clock(self):
        now = datetime.now()
        self.clock.configure(text=f"{now:%a}, {now.day} {now:%b}   ·   {fmt_clock(now)}")
        self.after(1000, self._tick_clock)

    def report_callback_exception(self, exc, val, tb):
        """Last line of defence: log and show a friendly card instead of dying."""
        log.error("Unhandled UI error", exc_info=(exc, val, tb))
        try:
            self._set_busy(False)
            self._show_error(SkyPulseError())
        except Exception:
            pass

    # -- helpers used by scripts/capture_screenshots.py ----------------------
    @property
    def busy(self) -> bool:
        return self._busy

    def wait_idle(self, timeout: float = 25.0):
        import time
        end = time.time() + timeout
        while time.time() < end:
            self.update()
            if not self._busy and self._results.empty():
                break
            time.sleep(0.03)
        for _ in range(12):
            self.update()
            time.sleep(0.03)
