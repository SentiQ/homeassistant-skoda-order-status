import asyncio

import pytest
from myskoda.auth.authorization import (
    AuthorizationFailedError,
    NotAuthorizedError,
    TokenExpiredError,
)

from custom_components.skoda_order_status.api import (
    SkodaOrderApiClient,
    SkodaOrderApiError,
    SkodaOrderAuthError,
)


class _Myskoda:
    def __init__(self, results: list[BaseException | None]) -> None:
        self._results = results
        self.calls: list[dict] = []

    async def connect(self, **kwargs) -> None:
        self.calls.append(kwargs)
        result = self._results.pop(0)
        if result is not None:
            raise result


def _client(refresh_token: str | None = "stored-token") -> SkodaOrderApiClient:
    return SkodaOrderApiClient(None, None, "driver@example.com", "secret", refresh_token)


def test_password_auth_errors_raise_auth_error():
    async def _run(error: Exception) -> None:
        client = _client(None)
        myskoda = _Myskoda([error])
        with pytest.raises(SkodaOrderAuthError):
            await client._connect(myskoda)
        assert myskoda.calls == [{"email": "driver@example.com", "password": "secret"}]

    asyncio.run(_run(AuthorizationFailedError("denied")))
    asyncio.run(_run(NotAuthorizedError("denied")))


def test_password_network_error_raises_api_error():
    async def _run() -> None:
        client = _client(None)
        myskoda = _Myskoda([TimeoutError("timed out")])
        with pytest.raises(SkodaOrderApiError) as caught:
            await client._connect(myskoda)
        assert not isinstance(caught.value, SkodaOrderAuthError)

    asyncio.run(_run())


def test_rejected_refresh_token_retries_with_password():
    async def _run(error: Exception) -> None:
        client = _client()
        myskoda = _Myskoda([error, None])
        await client._connect(myskoda)
        assert myskoda.calls == [
            {"refresh_token": "stored-token"},
            {"email": "driver@example.com", "password": "secret"},
        ]

    asyncio.run(_run(AuthorizationFailedError("rejected")))
    asyncio.run(_run(NotAuthorizedError("rejected")))
    asyncio.run(_run(TokenExpiredError("expired")))


def test_refresh_network_error_does_not_retry_or_reauth():
    async def _run() -> None:
        client = _client()
        myskoda = _Myskoda([OSError("dns")])
        with pytest.raises(SkodaOrderApiError) as caught:
            await client._connect(myskoda)
        assert not isinstance(caught.value, SkodaOrderAuthError)
        assert myskoda.calls == [{"refresh_token": "stored-token"}]

    asyncio.run(_run())
