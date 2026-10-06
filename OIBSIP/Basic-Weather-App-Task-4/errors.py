"""Exception hierarchy. Every error carries a GUI-ready title, message and hints."""
from __future__ import annotations


class SkyPulseError(Exception):
    """Base class for all errors that are shown to the user inside the GUI."""

    kind = "generic"
    icon = "alert"
    title = "Something went wrong"
    default_message = "An unexpected error occurred. Please try again."
    hints: tuple = ()
    retryable = True

    def __init__(self, message: str | None = None, *, hints=None):
        self.message = message or self.default_message
        if hints is not None:
            self.hints = tuple(hints)
        super().__init__(self.message)


class ValidationError(SkyPulseError):
    kind, icon, retryable = "validation", "search-x", False
    title = "Check your search"
    default_message = "Please enter a valid city name."


class MissingApiKeyError(SkyPulseError):
    kind, icon, retryable = "missing_key", "key", True
    title = "API key not configured"
    default_message = "SkyPulse could not find your OpenWeatherMap API key."
    hints = (
        "Copy .env.example to .env in the project folder.",
        "Set OPENWEATHER_API_KEY=<your key> and save the file.",
        "Restart SkyPulse, then press Retry.",
    )


class InvalidApiKeyError(SkyPulseError):
    kind, icon = "invalid_key", "key"
    title = "Invalid or expired API key"
    default_message = "OpenWeatherMap rejected the API key that SkyPulse sent."
    hints = (
        "Check OPENWEATHER_API_KEY in your .env file for typos.",
        "Newly created keys can take up to two hours to activate.",
        "Confirm the key is active in your OpenWeatherMap account.",
    )


class CityNotFoundError(SkyPulseError):
    kind, icon = "city_not_found", "search-x"
    title = "City not found"
    default_message = "We couldn't find a city matching your search."
    hints = (
        "Check the spelling of the city name.",
        "Add a country code, e.g. “Paris, FR” or “Springfield, US”.",
        "Try a larger nearby city.",
    )


class RateLimitError(SkyPulseError):
    kind, icon = "rate_limit", "clock"
    title = "Too many requests"
    default_message = "The OpenWeatherMap request limit was reached."
    hints = ("Wait a minute, then press Retry.", "Free keys allow 60 calls per minute.")


class RequestTimeoutError(SkyPulseError):
    kind, icon = "timeout", "clock"
    title = "The request timed out"
    default_message = "The weather service took too long to respond."
    hints = ("Your connection may be slow or busy.", "Press Retry in a moment.")


class NoConnectionError(SkyPulseError):
    kind, icon = "no_connection", "wifi-off"
    title = "No internet connection"
    default_message = "SkyPulse couldn't reach the weather service."
    hints = (
        "Check that your Wi-Fi or network cable is connected.",
        "Disable any VPN or proxy that may block the request.",
        "Press Retry once you're back online.",
    )


class ServiceUnavailableError(SkyPulseError):
    kind, icon = "service_unavailable", "alert"
    title = "Weather service unavailable"
    default_message = "OpenWeatherMap is having trouble right now."
    hints = ("This is usually temporary.", "Press Retry in a few minutes.")


class MalformedResponseError(SkyPulseError):
    kind, icon = "malformed", "alert"
    title = "Unexpected weather data"
    default_message = "The weather service returned data SkyPulse couldn't read."
    hints = ("Press Retry — this is usually a one-off glitch.",)


class LocationError(SkyPulseError):
    kind, icon = "location", "locate"
    title = "Couldn't detect your location"
    default_message = "Automatic location detection is unavailable right now."
    hints = (
        "Location is estimated from your IP address and needs internet access.",
        "A VPN can make the estimate wrong or block it entirely.",
        "You can always search for a city by name instead.",
    )
