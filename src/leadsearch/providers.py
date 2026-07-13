"""Search providers behind a common interface.

``Provider.search(query, num)`` returns a list of :class:`SearchItem`. Real
providers (Google / Bing CustomSearch) use ``requests``; :class:`MockProvider`
lets the whole pipeline be tested offline.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

from .types import SearchItem

__all__ = ["Provider", "GoogleProvider", "BingProvider", "MockProvider"]


class Provider(ABC):
    """A search backend restricted to LinkedIn profile lookups."""

    @abstractmethod
    def search(self, query: str, num: int = 5) -> list[SearchItem]:
        ...


def _with_retry(fn: Callable, retries: int, backoff: float, sleep: Callable[[float], None]):
    last = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as exc:  # network / decode errors -> retry then give up
            last = exc
            if attempt < retries:
                sleep(backoff * (2 ** attempt))
    if last:
        raise last


class GoogleProvider(Provider):
    """Google Programmable Search (CustomSearch) JSON API."""

    ENDPOINT = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, cx: str, *, delay: float = 0.2,
                 retries: int = 2, backoff: float = 0.5,
                 sleep: Callable[[float], None] = time.sleep):
        self.api_key, self.cx = api_key, cx
        self.delay, self.retries, self.backoff, self._sleep = delay, retries, backoff, sleep

    def search(self, query: str, num: int = 5) -> list[SearchItem]:
        import requests  # imported lazily so the core stays dependency-free to test
        self._sleep(self.delay)

        def _call():
            r = requests.get(self.ENDPOINT, params={
                "key": self.api_key, "cx": self.cx, "q": query,
                "num": min(max(num, 1), 10),
            }, timeout=15)
            r.raise_for_status()
            return r.json()

        data = _with_retry(_call, self.retries, self.backoff, self._sleep) or {}
        return [
            SearchItem(title=it.get("title", ""), link=it.get("link", ""),
                       snippet=it.get("snippet", ""))
            for it in (data.get("items") or [])
        ]


class BingProvider(Provider):
    """Bing Web Search API v7."""

    ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"

    def __init__(self, api_key: str, *, delay: float = 0.2, retries: int = 2,
                 backoff: float = 0.5, sleep: Callable[[float], None] = time.sleep):
        self.api_key = api_key
        self.delay, self.retries, self.backoff, self._sleep = delay, retries, backoff, sleep

    def search(self, query: str, num: int = 5) -> list[SearchItem]:
        import requests
        self._sleep(self.delay)

        def _call():
            r = requests.get(self.ENDPOINT,
                             headers={"Ocp-Apim-Subscription-Key": self.api_key},
                             params={"q": query, "count": min(max(num, 1), 10)},
                             timeout=15)
            r.raise_for_status()
            return r.json()

        data = _with_retry(_call, self.retries, self.backoff, self._sleep) or {}
        return [
            SearchItem(title=it.get("name", ""), link=it.get("url", ""),
                       snippet=it.get("snippet", ""))
            for it in ((data.get("webPages") or {}).get("value") or [])
        ]


class MockProvider(Provider):
    """Deterministic provider for tests / offline use.

    Pass a list of items (returned for every query) or a callable
    ``query -> list[SearchItem]``.
    """

    def __init__(self, items=None, fn: Optional[Callable[[str, int], list]] = None):
        self._items = items or []
        self._fn = fn
        self.calls: list[str] = []

    def search(self, query: str, num: int = 5) -> list[SearchItem]:
        self.calls.append(query)
        if self._fn:
            return list(self._fn(query, num))
        return list(self._items)
