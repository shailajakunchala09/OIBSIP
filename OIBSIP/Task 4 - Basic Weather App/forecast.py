"""Forecast processing: turn 3-hour API steps into an hourly strip and daily cards."""
from __future__ import annotations

from datetime import datetime, timedelta

from models import CurrentWeather, DailyForecast, ForecastEntry, HourlyPoint


def _is_night(moment: datetime, current: CurrentWeather, fallback: bool) -> bool:
    """Decide day/night for ``moment`` from today's sunrise/sunset times of day."""
    rise, sset = current.sunrise, current.sunset
    if rise is None or sset is None or rise.time() >= sset.time():
        return fallback
    return not (rise.time() <= moment.time() < sset.time())


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def build_hourly(current: CurrentWeather, entries: list[ForecastEntry],
                 now: datetime | None = None, hours: int = 6) -> list[HourlyPoint]:
    """Return ``hours`` hourly points starting at the next full hour.

    The free OpenWeatherMap forecast has 3-hour resolution, so temperature and
    rain probability are linearly interpolated between steps (anchored on the
    current observation); the condition icon comes from the nearest real step.
    """
    now = now or current.city_now()
    start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    anchor = ForecastEntry(
        time=current.observed_at, temp_c=current.temp_c, temp_min_c=current.temp_min_c,
        temp_max_c=current.temp_max_c, condition_id=current.condition_id,
        condition_main=current.condition_main, description=current.description,
        night=current.night, pop=0.0,
    )
    series = [anchor] + [e for e in sorted(entries, key=lambda e: e.time) if e.time > anchor.time]

    points: list[HourlyPoint] = []
    for k in range(hours):
        t = start + timedelta(hours=k)
        lower = series[0]
        upper = series[-1]
        for a, b in zip(series, series[1:]):
            if a.time <= t <= b.time:
                lower, upper = a, b
                break
        else:  # t is past the end (or before the start): clamp to the nearest edge
            lower = upper = series[-1] if t > series[-1].time else series[0]

        span = (upper.time - lower.time).total_seconds()
        frac = 0.0 if span <= 0 else (t - lower.time).total_seconds() / span
        nearest = upper if frac >= 0.5 else lower
        points.append(HourlyPoint(
            time=t,
            temp_c=_lerp(lower.temp_c, upper.temp_c, frac),
            condition_id=nearest.condition_id,
            condition_main=nearest.condition_main,
            description=nearest.description,
            night=_is_night(t, current, nearest.night),
            pop=upper.pop,
        ))
    return points


def build_daily(current: CurrentWeather, entries: list[ForecastEntry],
                now: datetime | None = None, days: int = 5) -> list[DailyForecast]:
    """Group forecast steps by city-local date; first card is always *today*."""
    now = now or current.city_now()
    today = now.date()

    groups: dict = {}
    for entry in entries:
        if entry.time.date() >= today:
            groups.setdefault(entry.time.date(), []).append(entry)

    # Today's range also includes what is being observed right now.
    groups.setdefault(today, [])

    result: list[DailyForecast] = []
    for day in sorted(groups)[:days]:
        items = groups[day]
        highs = [e.temp_max_c for e in items]
        lows = [e.temp_min_c for e in items]
        if day == today:
            highs += [current.temp_max_c, current.temp_c]
            lows += [current.temp_min_c, current.temp_c]
            rep_id, rep_main, rep_desc = current.condition_id, current.condition_main, current.description
        else:
            # Representative condition: the step closest to early afternoon.
            noon = datetime.combine(day, datetime.min.time()) + timedelta(hours=13)
            rep = min(items, key=lambda e: abs((e.time - noon).total_seconds()))
            rep_id, rep_main, rep_desc = rep.condition_id, rep.condition_main, rep.description
        result.append(DailyForecast(
            day=day, high_c=max(highs), low_c=min(lows),
            condition_id=rep_id, condition_main=rep_main, description=rep_desc,
            pop=max((e.pop for e in items), default=0.0), is_today=(day == today),
        ))
    return result
