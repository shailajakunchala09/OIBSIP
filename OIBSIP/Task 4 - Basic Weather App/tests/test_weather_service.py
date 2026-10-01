import unittest

import requests

from config import Settings
from errors import (CityNotFoundError, InvalidApiKeyError, MalformedResponseError, MissingApiKeyError,
                    NoConnectionError, RateLimitError, RequestTimeoutError, ServiceUnavailableError,
                    ValidationError)
from models import WeatherQuery
from tests.factories import FakeResponse, FakeSession, current_payload, forecast_payload
from weather_service import WeatherService
from datetime import datetime

NOW = datetime(2026, 9, 29, 14, 20)


def ok_responder(url, params):
    return FakeResponse(200, forecast_payload() if url.endswith("/forecast") else current_payload())


def service(responder, key="test-key"):
    return WeatherService(Settings(api_key=key), session=FakeSession(responder))


class FetchReportTests(unittest.TestCase):
    def test_success_builds_full_report(self):
        svc = service(ok_responder)
        report = svc.fetch_report(WeatherQuery(city="  London "), now=NOW)
        self.assertEqual(report.current.city, "London")
        self.assertEqual(len(report.hourly), 6)
        self.assertEqual(len(report.daily), 5)

    def test_request_shape_uses_env_key_metric_units_and_cleaned_city(self):
        svc = service(ok_responder)
        svc.fetch_report(WeatherQuery(city="  New   York "), now=NOW)
        urls = [c[0] for c in svc.session.calls]
        self.assertTrue(urls[0].endswith("/weather") and urls[1].endswith("/forecast"))
        params = svc.session.calls[0][1]
        self.assertEqual(params["q"], "New York")
        self.assertEqual(params["appid"], "test-key")
        self.assertEqual(params["units"], "metric")

    def test_coordinate_query_and_display_name_override(self):
        svc = service(ok_responder)
        report = svc.fetch_report(WeatherQuery(lat=51.5, lon=-0.12, display_name="Hackney"), now=NOW)
        self.assertEqual(svc.session.calls[0][1]["lat"], 51.5)
        self.assertNotIn("q", svc.session.calls[0][1])
        self.assertEqual(report.current.city, "Hackney")


class ErrorMappingTests(unittest.TestCase):
    def assert_raises_for(self, responder, exc_type, key="test-key", query=None):
        svc = service(responder, key)
        with self.assertRaises(exc_type):
            svc.fetch_report(query or WeatherQuery(city="London"), now=NOW)

    def test_http_status_codes(self):
        cases = {401: InvalidApiKeyError, 404: CityNotFoundError, 429: RateLimitError,
                 500: ServiceUnavailableError, 503: ServiceUnavailableError}
        for status, exc in cases.items():
            with self.subTest(status=status):
                self.assert_raises_for(lambda u, p, s=status: FakeResponse(s, {"cod": s}), exc)

    def test_network_failures(self):
        def raiser(exc):
            def responder(url, params):
                raise exc
            return responder
        self.assert_raises_for(raiser(requests.exceptions.ConnectTimeout("x")), RequestTimeoutError)
        self.assert_raises_for(raiser(requests.exceptions.ReadTimeout("x")), RequestTimeoutError)
        self.assert_raises_for(raiser(requests.exceptions.ConnectionError("dns")), NoConnectionError)
        self.assert_raises_for(raiser(requests.exceptions.TooManyRedirects("x")), ServiceUnavailableError)

    def test_invalid_json_and_wrong_shapes(self):
        self.assert_raises_for(lambda u, p: FakeResponse(200, json_error=True), MalformedResponseError)
        self.assert_raises_for(lambda u, p: FakeResponse(200, ["not", "a", "dict"]), MalformedResponseError)
        self.assert_raises_for(lambda u, p: FakeResponse(200, {"unexpected": True}), MalformedResponseError)

    def test_missing_or_placeholder_key(self):
        for key in ("", "  ", "your_api_key_here"):
            with self.subTest(key=key):
                self.assert_raises_for(ok_responder, MissingApiKeyError, key=key)

    def test_empty_city_never_reaches_the_network(self):
        svc = service(ok_responder)
        for bad in ("", "   ", None):
            with self.assertRaises(ValidationError):
                svc.fetch_report(WeatherQuery(city=bad), now=NOW)
        self.assertEqual(svc.session.calls, [])

    def test_error_messages_never_leak_the_api_key(self):
        def responder(url, params):
            raise requests.exceptions.ConnectionError(f"failed for {url}?appid=SECRET123")
        svc = service(responder, key="SECRET123")
        with self.assertRaises(NoConnectionError) as ctx:
            svc.fetch_report(WeatherQuery(city="London"), now=NOW)
        self.assertNotIn("SECRET123", str(ctx.exception))
        self.assertNotIn("SECRET123", ctx.exception.message)

    def test_every_error_has_gui_copy(self):
        for exc in (InvalidApiKeyError(), CityNotFoundError(), RateLimitError(), RequestTimeoutError(),
                    NoConnectionError(), ServiceUnavailableError(), MalformedResponseError(),
                    MissingApiKeyError(), ValidationError()):
            with self.subTest(exc=type(exc).__name__):
                self.assertTrue(exc.title and exc.message and exc.icon)


if __name__ == "__main__":
    unittest.main()
