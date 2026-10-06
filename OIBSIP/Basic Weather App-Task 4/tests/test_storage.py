import json
import tempfile
import unittest
from pathlib import Path

from storage import Preferences, SearchHistory, city_query
from units import UnitSystem


class SearchHistoryTests(unittest.TestCase):
    def test_most_recent_first_deduplicated_and_capped(self):
        h = SearchHistory(limit=3)
        for name in ("A1", "B2", "C3", "A1", "D4"):
            h.add(name, "GB")
        self.assertEqual([i["name"] for i in h.items()], ["D4", "A1", "C3"])

    def test_same_name_different_country_are_distinct(self):
        h = SearchHistory()
        h.add("Paris", "FR")
        h.add("Paris", "US")
        self.assertEqual(len(h.items()), 2)

    def test_city_query(self):
        self.assertEqual(city_query("London", "GB"), "London,GB")
        self.assertEqual(city_query("London"), "London")


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "sub" / "preferences.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_defaults_when_file_missing(self):
        p = Preferences(self.path)
        self.assertEqual((p.units, p.theme, p.favorites), (UnitSystem.METRIC, "dark", []))

    def test_favorites_toggle_and_persist(self):
        p = Preferences(self.path)
        self.assertTrue(p.toggle_favorite("Tokyo", "JP"))
        self.assertTrue(p.is_favorite("tokyo", "jp"))
        p.units, p.theme = UnitSystem.IMPERIAL, "light"
        p.save()
        again = Preferences(self.path)
        self.assertEqual(again.favorites, [{"name": "Tokyo", "country": "JP"}])
        self.assertEqual((again.units, again.theme), (UnitSystem.IMPERIAL, "light"))
        self.assertFalse(again.toggle_favorite("Tokyo", "JP"))
        self.assertEqual(Preferences(self.path).favorites, [])

    def test_corrupt_file_falls_back_to_defaults(self):
        self.path.parent.mkdir(parents=True)
        for content in ("{not json", "[]", json.dumps({"theme": "neon", "units": "??", "favorites": [1, {"x": 1}]})):
            self.path.write_text(content, encoding="utf-8")
            p = Preferences(self.path)
            self.assertEqual((p.units, p.theme, p.favorites), (UnitSystem.METRIC, "dark", []))

    def test_unwritable_location_does_not_raise(self):
        blocker = Path(self.tmp.name) / "file"
        blocker.write_text("x")
        p = Preferences(blocker / "nested" / "prefs.json")
        self.assertFalse(p.save())
        self.assertTrue(p.toggle_favorite("Rome", "IT"))  # still works in memory


if __name__ == "__main__":
    unittest.main()
