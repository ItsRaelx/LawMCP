import time
from unittest.mock import AsyncMock

import pytest

from law_mcp.cache import _store, cached, clear


class TestCached:
    @pytest.mark.anyio
    async def test_returns_result(self):
        inner = AsyncMock(return_value="hello")

        @cached()
        async def fn(x):
            return await inner(x)

        result = await fn(1)
        assert result == "hello"
        inner.assert_called_once_with(1)

    @pytest.mark.anyio
    async def test_cache_hit(self):
        inner = AsyncMock(return_value="hello")

        @cached()
        async def fn(x):
            return await inner(x)

        await fn(1)
        await fn(1)
        inner.assert_called_once()

    @pytest.mark.anyio
    async def test_different_args_different_cache(self):
        inner = AsyncMock(side_effect=lambda x: x * 2)

        @cached()
        async def fn(x):
            return await inner(x)

        assert await fn(1) == 2
        assert await fn(2) == 4
        assert inner.call_count == 2

    @pytest.mark.anyio
    async def test_kwargs_cached(self):
        inner = AsyncMock(return_value="ok")

        @cached()
        async def fn(a, b=10):
            return await inner(a, b=b)

        await fn(1, b=20)
        await fn(1, b=20)
        inner.assert_called_once()

    @pytest.mark.anyio
    async def test_ttl_expiry(self, monkeypatch):
        call_count = 0

        @cached(ttl=1)
        async def fn():
            nonlocal call_count
            call_count += 1
            return call_count

        assert await fn() == 1

        # Advance monotonic clock past TTL
        original_monotonic = time.monotonic
        monkeypatch.setattr(time, "monotonic", lambda: original_monotonic() + 2)

        assert await fn() == 2

    @pytest.mark.anyio
    async def test_clear(self):
        inner = AsyncMock(return_value="v1")

        @cached()
        async def fn():
            return await inner()

        await fn()
        clear()
        inner.return_value = "v2"
        result = await fn()
        assert result == "v2"
        assert inner.call_count == 2

    @pytest.mark.anyio
    async def test_store_populated(self):
        @cached()
        async def fn(x):
            return x

        await fn(42)
        assert len(_store) >= 1

    @pytest.mark.anyio
    async def test_exception_not_cached(self):
        call_count = 0

        @cached()
        async def fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("boom")
            return "ok"

        with pytest.raises(ValueError):
            await fn()

        result = await fn()
        assert result == "ok"
        assert call_count == 2
