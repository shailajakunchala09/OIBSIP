import unittest

from errors import MalformedResponseError
from models import classify, icon_name
from tests.factories import current_payload, forecast_payload
from weather_service import parse_current, parse_forecast


class ParseCurrentTests(unittest.TestCase):
    def test_parses_a_full_payload(self):
        cur = parse_current(current_payload())
        self.assertEqual((cur.city, cur.country), ("London", "GB"))
        self.assertAlmostEqual(cur.temp_c, 18.4)
        self.assertAlmostEqual(cur.feels_like_c, 17.9)
        self.assertEqual((cur.humidity, cur.pressure_hpa, cur.clouds), (62, 1013, 75))
        self.assertAlmostEqual(cur.wind_speed_ms, 4.1)
        self.assertEqual(cur.visibility_m, 10000)
        self.assertEqual(cur.description, "broken clouds")
        self.assertFalse(cur.night)
        self.assertEqual(cur.kind, "clouds")
        self.assertEqual(cur.icon, "cloud")

    def test_times_are_shifted_to_city_local_time(self):
        cur = parse_current(current_payload())
        self.assertEqual(cur.observed_at.hour, 14)   # 13:20 UTC + 1h
        self.assertEqual(cur.sunrise.hour, 6)        # 05:50 UTC + 1h
        self.assertEqual(cur.sunset.hour, 18)        # 17:35 UTC + 1h
        self.assertEqual(cur.day_length_minutes, 705)

    def test_optional_fields_may_be_missing(self):
        payload = current_payload()
        for key in ("visibility", "wind"):
            payload.pop(key)
        payload["sys"] = {"country": "GB"}
        cur = parse_current(payload)
        self.assertIsNone(cur.visibility_m)
        self.assertEqual(cur.wind_speed_ms, 0.0)
        self.assertIsNone(cur.wind_deg)
        self.assertIsNone(cur.sunrise)
        self.assertIsNone(cur.day_length_minutes)

    def test_night_icon_is_detected(self):
        payload = current_payload(weather=[{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01n"}])
        cur = parse_current(payload)
        self.assertTrue(cur.night)
        self.assertEqual(cur.icon, "moon")

    def test_garbage_raises_malformed(self):
        for bad in ({}, {"weather": []}, current_payload(main={}), current_payload(dt="soon"),
                    current_payload(weather=[{"main": "x"}])):
            with self.subTest(bad=bad), self.assertRaises(MalformedResponseError):
                parse_current(bad)


class ParseForecastTests(unittest.TestCase):
    def test_parses_and_sorts_entries(self):
        payload = forecast_payload()
        payload["list"].reverse()
        entries = parse_forecast(payload)
        self.assertEqual(len(entries), 40)
        self.assertEqual(entries, sorted(entries, key=lambda e: e.time))
        self.assertEqual(entries[0].time.hour, 16)  # 15:00 UTC + 1h
        self.assertEqual(entries[0].condition_id, 802)

    def test_empty_or_broken_forecast_raises(self):
        for bad in ({}, {"list": []}, {"list": [{"dt": 1}]}):
            with self.subTest(bad=bad), self.assertRaises(MalformedResponseError):
                parse_forecast(bad)


class ClassificationTests(unittest.TestCase):
    def test_condition_ids_map_to_kinds(self):
        cases = {200: "storm", 211: "storm", 781: "storm", 300: "rain", 501: "rain", 601: "snow",
                 701: "fog", 741: "fog", 800: "clear", 801: "clouds", 804: "clouds"}
        for cid, kind in cases.items():
            with self.subTest(cid=cid):
                self.assertEqual(classify(cid), kind)

    def test_icon_names(self):
        self.assertEqual(icon_name(800, False), "sun")
        self.assertEqual(icon_name(800, True), "moon")
        self.assertEqual(icon_name(801, False), "partly-day")
        self.assertEqual(icon_name(802, True), "partly-night")
        self.assertEqual(icon_name(804, False), "cloud")
        self.assertEqual(icon_name(502, True), "rain")
        self.assertEqual(icon_name(211, False), "storm")


if __name__ == "__main__":
    unittest.main()
