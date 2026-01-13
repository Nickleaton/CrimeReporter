import logging
from abc import ABC, abstractmethod

import requests

logger = logging.getLogger(__name__)


class GeolocationProvider(ABC):
    """Abstract base class for all geolocation providers."""

    @property
    def name(self) -> str:
        """Unique provider name (e.g., 'ipapi', 'ipwhois')."""
        name = self.__class__.__name__
        return name[:-8] if name.endswith("Provider") else name

    @abstractmethod
    def lookup(self) -> tuple[str, str | None]:
        """
        Return (ip, country), where country may be None on failure.
        """
        raise NotImplementedError


class IpapiProvider(GeolocationProvider):
    URL_TEMPLATE = "https://ipapi.co/json/"

    def lookup(self) -> tuple[str | None, str | None]:
        try:
            resp = requests.get(
                self.URL_TEMPLATE,
                timeout=5,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                },
            )

            # Handle rate limits
            if resp.status_code == 429:
                logger.warning("IpapiProvider: rate limit (429)")
                return None, None

            resp.raise_for_status()
            data = resp.json()

            # ipapi-specific structured errors
            if data.get("error"):
                logger.warning(f"{self.name}: provider error: {data.get('message')}")
                return None, None
            return data.get("ip"), data.get("country_name")

        except Exception as e:
            logger.warning(f"{self.__class__.__name__}: request failed: {e}")
            return None, None


class IpwhoisProvider(GeolocationProvider):
    URL = "https://ipwho.is/"

    @property
    def name(self) -> str:
        return "ipwho.is"

    def lookup(self) -> tuple[str | None, str | None]:
        try:
            resp = requests.get(self.URL, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # ipwho.is uses "success": false for errors
            if not data.get("success", True):
                logger.warning(f"{self.name}: provider error: {data.get('message')}")
                return None, None

            return data.get("ip"), data.get("country")

        except Exception as e:
            logger.warning(f"{self.__class__.__name__}: request failed: {e}")
            return None, None


def server_location():
    provider = IpwhoisProvider()
    ip, country = provider.lookup()
    logging.info(f"ip: {ip}, country: {country}")
    return country
