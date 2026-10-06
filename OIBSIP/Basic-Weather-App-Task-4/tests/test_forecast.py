import unittest
from datetime import date, datetime

from forecast import build_daily, build_hourly
from tests.factories import current_payload, forecast_payload
from weather_service import parse_current, parse_forecast

NOW = datetime(2026, 9, 29, 14, 20)  # city-local


class HourlyTests(unittest.TestCase):
    def setUp(self):
        self.current = parse_current(current_payload())
        self.entries = parse_forecast(forecast_payload())
        self.hourly = build_hourly(self.current, self.entries, now=NOW)

    def test_six_consecutive_hours_from_next_full_hour(self):
        self.assertEqual(len(self.hourly), 6)
        self.assertEqual([p.time.hour for p in self.hourly], [15, 16, 17, 18, 19, 20])
        self.assertTrue(all(p.time.minute == 0 for p in self.hourly))

    def test_temperature_is_interpolated_not_stepped(self):
        temps = [p.temp_c for p in self.hourly]
        self.assertEqual(len(set(round(t, 3) for t in temps)), 6)  # every hour differs
        first_step = self.entries[0]   # 16:00 local
        at_16 = next(p for p in self.hourly if p.time.hour == 16)
        self.assertAlmostEqual(at_16.temp_c, first_step.temp_c, places=6)
        # 15:00 lies between the observation (18.4 @14:20) and the 16:00 step
        lo, hi = sorted((self.current.temp_c, first_step.temp_c))
        self.assertTrue(lo <= self.hourly[0].temp_c <= hi)

    def test_day_night_flag_follows_sunset(self):
        by_hour = {p.time.hour: p.night for p in self.hourly}
        self.assertFalse(by_hour[17])   # before 18:35 local sunset
        self.assertTrue(by_hour[19])    # after sunset
        self.assertTrue(by_hour[20])

    def test_conditions_come_from_the_nearest_step(self):
        self.assertEqual(self.hourly[0].condition_id, 803)  # nearer the observation
        self.assertEqual(self.hourly[-1].condition_id, 802)

    def test_short_forecast_is_clamped_without_crashing(self):
        short = parse_forecast(forecast_payload(steps=1))
        points = build_hourly(self.current, short, now=NOW)
        self.assertEqual(len(points), 6)
        self.assertAlmostEqual(points[-1].temp_c, short[0].temp_c)


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.current = parse_current(current_payload())
        self.entries = parse_forecast(forecast_payload())
        self.daily = build_daily(self.current, self.entries, now=NOW)

    def test_five_days_starting_today(self):
        self.assertEqual(len(self.daily), 5)
        self.assertEqual(self.daily[0].day, date(2026, 9, 29))
        self.assertTrue(self.daily[0].is_today)
        self.assertFalse(any(d.is_today for d in self.daily[1:]))
        days = [d.day for d in self.daily]
        self.assertEqual(days, sorted(set(days)))

    def test_high_is_not_below_low(self):
        for d in self.daily:
            self.assertGreaterEqual(d.high_c, d.low_c)

    def test_today_range_includes_current_observation(self):
        today = self.daily[0]
        self.assertGreaterEqual(today.high_c, self.current.temp_max_c)
        self.assertLessEqual(today.low_c, self.current.temp_min_c)
        self.assertEqual(today.condition_id, self.current.condition_id)

    def test_future_days_use_the_afternoon_condition_and_max_pop(self):
        rainy = [d for d in self.daily if d.condition_id == 500]
        self.assertTrue(rainy, "fixture contains a rainy day")
        self.assertAlmostEqual(rainy[0].pop, 0.6)

    def test_past_entries_are_ignored(self):
        later = datetime(2026, 9, 30, 9, 0)
        daily = build_daily(self.current, self.entries, now=later)
        self.assertEqual(daily[0].day, date(2026, 9, 30))
        self.assertTrue(daily[0].is_today)


if __name__ == "__main__":
    unittest.main()
