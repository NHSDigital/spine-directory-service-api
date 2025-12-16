"""
Making several API calls to get an access token per-test is very expensive.

This module is for caching access tokens.
"""
from typing import Optional, Dict, Any, Hashable, Tuple
from time import time
from functools import wraps

from .log import log, log_method


class _TokenCache:
    def __init__(self):
        self._cache = {}

    @log_method
    def insert(self, key: Hashable, token_data: Dict[str, Any]):
        if "issued_at" not in token_data:
            # only present on app-restricted tokens.  we can inject
            # this ourselves. Assume 5 seconds ago, probably was more
            # recently
            token_data["issued_at"] = time() - 5000
        self._cache[key] = token_data

    @log_method
    def get(self, key) -> Optional[Dict[str, Any]]:
        """
        Return a non-expired access token with the same client_id or None.
        """
        if key not in self._cache:
            return None

        old_token_data = self._cache[key]
        grace_period_seconds = 5
        now_ish = int(time()) + grace_period_seconds

        # issued_at is epoch_time in milliseconds
        # but expires_in is in seconds
        # => need factor of 1000 in this sum.
        expiry_time = int(old_token_data["issued_at"]) + 1000 * int(
            old_token_data["expires_in"]
        )
        if now_ish > expiry_time:
            self._cache.pop(key)
            return None
        return old_token_data


_CACHES = {}
_KWD_MARK = object()


def _recursive_make_hashable(d):
    if isinstance(d, dict):
        return tuple(
            sorted({k: _recursive_make_hashable(v) for k, v in d.items()}.items())
        )
    if isinstance(d, tuple):
        return tuple(_recursive_make_hashable(x) for x in d)

    return d


def cache_tokens(f):
    """
    Cache response tokens from an oauth server.

    This decorator checks a per-function _TokenCache for matching
    entries and returns the cached entries if they exist.

    The _TokenCache class understands that tokens have expiry times
    and automatically deletes them from the cache when appropriate.

    This means you can just call whatever get_access_token function
    you have decorated and not actually have to run the whole
    authentication journey.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        force_new_token = kwargs.pop("force_new_token", False)
        func_name = f.__name__
        if func_name not in _CACHES:
            _CACHES[func_name] = _TokenCache()
        cache = _CACHES[func_name]

        # We need to use the *args and **kwargs to construct a unique
        # dictionary key.  Dictionary keys must be hashable, which
        # means we can't have any dictionaries, but we can have
        # tuples. The tuple-of-just-a-blank-object, (_KWD_MARK,) is
        # how the python standard library marks the separation between
        # args and kwargs for its @functools.cache decorator. See
        # https://stackoverflow.com/a/10220908
        cache_key = (
            _recursive_make_hashable(args)
            + (_KWD_MARK,)
            + _recursive_make_hashable(kwargs)
        )
        token_data = cache.get(cache_key)
        if token_data and not force_new_token:
            log.debug(f"Cache hit for {func_name} with cache_key {cache_key}")
            return token_data
        log.debug(f"Cache miss for {func_name} with cache_key {cache_key}")
        token_data = f(*args, **kwargs)
        cache.insert(cache_key, token_data)
        return token_data

    return wrapper
