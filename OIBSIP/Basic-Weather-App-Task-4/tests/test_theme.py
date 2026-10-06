import unittest

from theme import DARK, LIGHT, PALETTES, ThemeManager, atmosphere, luminance, mix


class ThemeManagerTests(unittest.TestCase):
    def test_toggle_notifies_subscribers_with_new_palette(self):
        seen = []
        tm = ThemeManager("dark")
        tm.subscribe(lambda p: seen.append(p.name))
        self.assertEqual(tm.toggle(), "light")
        self.assertEqual(tm.toggle(), "dark")
        self.assertEqual(seen, ["light", "dark"])

    def test_invalid_mode_is_ignored(self):
        tm = ThemeManager("neon")
        self.assertEqual(tm.mode, "dark")
        tm.set_mode("sepia")
        self.assertEqual(tm.mode, "dark")

    def test_palettes_are_genuinely_different_designs(self):
        self.assertTrue(DARK.bordered and not LIGHT.bordered)
        self.assertGreater(DARK.shadow_alpha, LIGHT.shadow_alpha)
        self.assertLess(luminance(DARK.bg), 0.05)
        self.assertGreater(luminance(LIGHT.bg), 0.7)
        self.assertNotEqual(DARK.accent, LIGHT.accent)

    def test_every_palette_defines_every_field_as_valid_hex(self):
        for palette in PALETTES.values():
            for field, value in vars(palette).items():
                if isinstance(value, str) and value.startswith("#"):
                    self.assertEqual(len(value), 7, f"{palette.name}.{field}")
                    int(value[1:], 16)


class AtmosphereTests(unittest.TestCase):
    def test_all_kinds_available_in_both_modes(self):
        for mode in ("dark", "light"):
            for kind in ("clear", "clouds", "rain", "storm", "snow", "fog"):
                for night in (False, True):
                    a = atmosphere(mode, kind, night)
                    self.assertTrue(a.top.startswith("#") and a.text.startswith("#"))

    def test_night_clear_uses_night_scene(self):
        self.assertEqual(atmosphere("dark", "clear", True).kind, "night")
        self.assertEqual(atmosphere("dark", "clear", False).kind, "clear")
        self.assertEqual(atmosphere("dark", "rain", True).kind, "rain")

    def test_text_contrasts_with_background(self):
        for mode in ("dark", "light"):
            for kind in ("clear", "clouds", "rain", "storm", "snow", "fog"):
                a = atmosphere(mode, kind, False)
                avg = mix(a.top, a.bottom, 0.5)
                lo, hi = sorted((luminance(avg), luminance(a.text)))
                self.assertGreater((hi + 0.05) / (lo + 0.05), 4.0, f"{mode}/{kind}")

    def test_mix_endpoints(self):
        self.assertEqual(mix("#000000", "#ffffff", 0), "#000000")
        self.assertEqual(mix("#000000", "#ffffff", 1), "#ffffff")


if __name__ == "__main__":
    unittest.main()
