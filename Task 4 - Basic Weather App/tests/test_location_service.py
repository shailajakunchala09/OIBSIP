import unittest

import requests

from errors import LocationError
from location_service import LocationService
from models import WeatherQuery, GeoLocation
from tests.factories import FakeResponse, FakeSession

IPWHOIS_OK = {"success": True, "city": "Hyderabad", "country_code": "IN",
              "latitude": 17.385, "longitude": 78.4867}
IPAPI_OK = {"city": "Pune", "country_code": "IN", "latitude": 18.52, "longitude": 73.85}


def locate(responder):
    return LocationService(session=FakeSession(responder)).detect()


class LocationTests(unittest.TestCase):
    def test_primary_provider_success(self):
        loc = locate(lambda url, p: FakeResponse(200, IPWHOIS_OK))
        self.assertEqual((loc.city, loc.country, loc.provider), ("Hyderabad", "IN", "ipwho.is"))
        self.assertAlmostEqual(loc.lat, 17.385)

    def test_falls_back_to_second_provider(self):
        def responder(url, p):
            if "ipwho.is" in url:
                return FakeResponse(200, {"success": False, "message": "limit"})
            return FakeResponse(200, IPAPI_OK)
        loc = locate(responder)
        self.assertEqual((loc.city, loc.provider), ("Pune", "ipapi.co"))

    def test_http_error_then_fallback(self):
        def responder(url, p):
            return FakeResponse(503, {}) if "ipwho.is" in url else FakeResponse(200, IPAPI_OK)
        self.assertEqual(locate(responder).city, "Pune")

    def test_all_providers_fail(self):
        with self.assertRaises(LocationError):
            locate(lambda url, p: FakeResponse(200, {"error": True, "success": False}))

    def test_garbage_payloads_do_not_crash(self):
        for payload in ({}, {"success": True}, [], "nope", None):
            with self.subTest(payload=payload), self.assertRaises(LocationError):
                locate(lambda url, p, pl=payload: FakeResponse(200, pl))

    def test_offline_and_timeout_have_specific_messages(self):
        def offline(url, p):
            raise requests.exceptions.ConnectionError("dns")
        def slow(url, p):
            raise requests.exceptions.ReadTimeout("slow")
        with self.assertRaises(LocationError) as off:
            locate(offline)
        with self.assertRaises(LocationError) as to:
            locate(slow)
        self.assertIn("internet", off.exception.message.lower())
        self.assertIn("too long", to.exception.message.lower())

    def test_location_converts_to_a_coordinate_query(self):
        q = WeatherQuery.for_location(GeoLocation("Hyderabad", "IN", 17.385, 78.4867))
        self.assertEqual((q.lat, q.lon, q.display_name, q.city), (17.385, 78.4867, "Hyderabad", None))


if __name__ == "__main__":
    unittest.main()
