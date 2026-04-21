import hashlib
import json
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

DEFAULT_TTL = 7200  # 2 hours

_store: dict[str, tuple[float, Any]] = {}


def _make_key(func_name: str, args: tuple, kwargs: dict) -> str:
    raw = json.dumps({"f": func_name, "a": args, "k": kwargs}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def cached(ttl: int = DEFAULT_TTL) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = _make_key(func.__qualname__, args, kwargs)
            now = time.monotonic()
            if key in _store:
                ts, value = _store[key]
                if now - ts < ttl:
                    return value
            result = await func(*args, **kwargs)
            _store[key] = (now, result)
            return result

        return wrapper

    return decorator


def clear() -> None:
    _store.clear()
