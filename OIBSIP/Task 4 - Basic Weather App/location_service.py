"""IP-based automatic location detection with provider fallback."""
from __future__ import annotations

import logging

import requests

from config import APP_NAME, APP_VERSION
from errors import LocationError, NoConnectionError, RequestTimeoutError
from models import GeoLocation

log = logging.getLogger(__name__)


def _parse_ipwhois(data: dict) -> GeoLocation:
    if not data.get("success", False):
        raise ValueError("provider reported failure")
    return GeoLocation(str(data.get("city") or ""), str(data.get("country_code") or ""),
                       float(data["latitude"]), float(data["longitude"]), "ipwho.is")


def _parse_ipapi(data: dict) -> GeoLocation:
    if data.get("error"):
        raise ValueError("provider reported failure")
    return GeoLocation(str(data.get("city") or ""), str(data.get("country_code") or ""),
                       float(data["latitude"]), float(data["longitude"]), "ipapi.co")


PROVIDERS = (
    ("https://ipwho.is/", _parse_ipwhois),
    ("https://ipapi.co/json/", _parse_ipapi),
)


class LocationService:
    """Estimates the user's location from their public IP address (approximate)."""

    def __init__(self, session: requests.Session | None = None, timeout: tuple = (4.0, 6.0),
                 providers=PROVIDERS):
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", f"{APP_NAME}/{APP_VERSION}")
        self.timeout = timeout
        self.providers = providers

    def detect(self) -> GeoLocation:
        """Return the detected location or raise :class:`LocationError`."""
        network_error: Exception | None = None
        for url, parser in self.providers:
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                payload = resp.json()
                if not isinstance(payload, dict):
                    raise ValueError("unexpected payload")
                location = parser(payload)
                if not location.city and not (location.lat or location.lon):
                    raise ValueError("no usable location")
                return location
            except requests.exceptions.Timeout:
                network_error = RequestTimeoutError()
            except requests.exceptions.ConnectionError:
                network_error = NoConnectionError()
            except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as exc:
                log.info("Location provider %s failed: %s", url, type(exc).__name__)

        if isinstance(network_error, NoConnectionError):
            raise LocationError("No internet connection, so your location couldn't be detected.")
        if isinstance(network_error, RequestTimeoutError):
            raise LocationError("The location service took too long to respond.")
        raise LocationError()
