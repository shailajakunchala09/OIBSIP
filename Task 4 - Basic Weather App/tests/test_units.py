import unittest
from datetime import datetime

from units import (Formatter, UnitSystem, beaufort_label, c_to_f, compass, fmt_clock, fmt_duration,
                   fmt_hour, m_to_km, m_to_mi, ms_to_kmh, ms_to_mph, round_half_up)


class ConversionTests(unittest.TestCase):
    def test_celsius_to_fahrenheit(self):
        self.assertAlmostEqual(c_to_f(0), 32)
        self.assertAlmostEqual(c_to_f(100), 212)
        self.assertAlmostEqual(c_to_f(-40), -40)
        self.assertAlmostEqual(c_to_f(37), 98.6)

    def test_speed_and_distance(self):
        self.assertAlmostEqual(ms_to_kmh(10), 36)
        self.assertAlmostEqual(ms_to_mph(10), 22.36936)
        self.assertAlmostEqual(m_to_km(10000), 10)
        self.assertAlmostEqual(m_to_mi(1609.344), 1.0)

    def test_rounding_is_half_up_and_never_negative_zero(self):
        self.assertEqual(round_half_up(24.5), 25)
        self.assertEqual(round_half_up(-0.4), 0)
        self.assertEqual(str(round_half_up(-0.2)), "0")
        self.assertEqual(round_half_up(-1.5), -1)

    def test_compass_and_beaufort(self):
        self.assertEqual(compass(0), "N")
        self.assertEqual(compass(90), "E")
        self.assertEqual(compass(225), "SW")
        self.assertEqual(compass(359), "N")
        self.assertEqual(compass(None), "")
        self.assertEqual(beaufort_label(0.1), "Calm")
        self.assertEqual(beaufort_label(4.1), "Gentle breeze")
        self.assertEqual(beaufort_label(50), "Hurricane force")


class FormatterTests(unittest.TestCase):
    def setUp(self):
        self.metric = Formatter(UnitSystem.METRIC)
        self.imperial = Formatter(UnitSystem.IMPERIAL)

    def test_temperature(self):
        self.assertEqual(self.metric.temp(18.4), "18°")
        self.assertEqual(self.imperial.temp(18.4), "65°")
        self.assertEqual(self.metric.temp_full(-3.6), "-4°C")
        self.assertEqual(self.imperial.temp_full(0), "32°F")
        self.assertEqual(self.metric.temp_unit, "°C")
        self.assertEqual(self.imperial.temp_unit, "°F")

    def test_wind_distance_pressure(self):
        self.assertEqual(self.metric.wind(4.1), "15 km/h")
        self.assertEqual(self.imperial.wind(4.1), "9 mph")
        self.assertEqual(self.metric.distance(10000), "10 km")
        self.assertEqual(self.metric.distance(800), "0.8 km")
        self.assertEqual(self.imperial.distance(10000), "6.2 mi")
        self.assertEqual(self.metric.distance(None), "—")
        self.assertEqual(self.metric.pressure(1013), "1013 hPa")
        self.assertEqual(self.imperial.pressure(1013), "29.91 inHg")

    def test_unit_parse_falls_back_to_metric(self):
        self.assertIs(UnitSystem.parse("imperial"), UnitSystem.IMPERIAL)
        self.assertIs(UnitSystem.parse("nonsense"), UnitSystem.METRIC)
        self.assertIs(UnitSystem.parse(None), UnitSystem.METRIC)


class TimeFormatTests(unittest.TestCase):
    def test_clock_and_hour(self):
        self.assertEqual(fmt_clock(datetime(2026, 9, 29, 6, 5)), "6:05 AM")
        self.assertEqual(fmt_clock(datetime(2026, 9, 29, 18, 45)), "6:45 PM")
        self.assertEqual(fmt_clock(None), "—")
        self.assertEqual(fmt_hour(datetime(2026, 9, 29, 15)), "3 PM")
        self.assertEqual(fmt_hour(datetime(2026, 9, 29, 0)), "12 AM")
        self.assertEqual(fmt_duration(761), "12h 41m")


if __name__ == "__main__":
    unittest.main()
