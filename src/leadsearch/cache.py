"""Caching so repeated queries don't re-hit (and re-bill) the search API.

``CachingProvider`` wraps any :class:`~leadsearch.providers.Provider` and serves
identical queries from a cache. Use :class:`MemoryCache` for a single run or
:class:`JSONFileCache` to persist across runs.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Optional

from .providers import Provider
from .types import SearchItem

__all__ = ["Cache", "MemoryCache", "JSONFileCache", "CachingProvider"]


class Cache:
    """Cache interface: ``get(key)`` / ``set(key, items)``."""

    def get(self, key: str):  # pragma: no cover - interface
        raise NotImplementedError

    def set(self, key: str, items):  # pragma: no cover - interface
        raise NotImplementedError


class MemoryCache(Cache):
    def __init__(self):
        self._d: dict = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            return self._d.get(key)

    def set(self, key, items):
        with self._lock:
            self._d[key] = items


class JSONFileCache(Cache):
    """Persist the cache to a JSON file (loaded once, saved on each write)."""

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._d: dict = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    self._d = json.load(fh)
            except (OSError, ValueError):
                self._d = {}

    def get(self, key):
        with self._lock:
            raw = self._d.get(key)
        return None if raw is None else [SearchItem(**it) for it in raw]

    def set(self, key, items):
        with self._lock:
            self._d[key] = [it.__dict__ for it in items]
            tmp = f"{self.path}.tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._d, fh)
            os.replace(tmp, self.path)


class CachingProvider(Provider):
    """Wrap a provider so identical ``(query, num)`` lookups are served from cache."""

    def __init__(self, provider: Provider, cache: Optional[Cache] = None):
        self.provider = provider
        self.cache = cache or MemoryCache()
        self.hits = 0
        self.misses = 0

    def search(self, query: str, num: int = 5) -> list[SearchItem]:
        key = f"{num}\x00{query}"
        cached = self.cache.get(key)
        if cached is not None:
            self.hits += 1
            return list(cached)
        self.misses += 1
        items = self.provider.search(query, num)
        self.cache.set(key, items)
        return items
