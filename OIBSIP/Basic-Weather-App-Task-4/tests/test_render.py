import unittest

from ui import render
from ui.icons import WEATHER_ICON_NAMES, logo, ui_icon, weather_icon
from models import icon_name


class RenderTests(unittest.TestCase):
    def test_surface_has_requested_size_and_opaque_page_background(self):
        img = render.surface(300, 160, 20, "#131B2E", "#0A0F1E", inset=8, border="#25314F",
                             shadow_alpha=120, shadow_blur=6, shadow_offset=3)
        self.assertEqual(img.size, (300, 160))
        self.assertEqual(img.getpixel((0, 0))[3], 255)

    def test_gradient_surface_with_every_atmosphere(self):
        for kind in ("clear", "clouds", "rain", "storm", "snow", "fog", "night"):
            img = render.surface(320, 200, 24, "#123456", "#000000", inset=8, gradient=("#123456", "#654321"),
                                 atmosphere_kind=kind, night=(kind == "night"))
            self.assertEqual(img.size, (320, 200), kind)

    def test_tiny_sizes_do_not_crash(self):
        self.assertEqual(render.surface(2, 2, 30, "#ffffff", "#000000").size, (4, 4))
        self.assertEqual(render.pill(1, 1, "#ffffff").size, (4, 4))


class IconTests(unittest.TestCase):
    def test_every_condition_maps_to_a_bundled_icon(self):
        for cid in (200, 300, 500, 600, 701, 800, 801, 802, 803, 804):
            for night in (False, True):
                self.assertIn(icon_name(cid, night), WEATHER_ICON_NAMES)

    def test_weather_icons_render_at_any_size(self):
        for name in WEATHER_ICON_NAMES:
            self.assertEqual(weather_icon(name, 48).size, (48, 48))

    def test_ui_glyphs_and_logo(self):
        for name in ("search", "search-x", "locate", "pin", "star", "star-outline", "refresh", "sun", "moon",
                     "drop", "wind", "gauge", "eye", "cloud", "sunrise", "sunset", "clock", "alert",
                     "wifi-off", "key", "close", "check"):
            img = ui_icon(name, 24, "#ffffff")
            self.assertEqual(img.size, (24, 24))
            self.assertGreater(img.getchannel("A").getbbox()[2], 0, name)  # something was drawn
        self.assertEqual(logo(64).size, (64, 64))


if __name__ == "__main__":
    unittest.main()
