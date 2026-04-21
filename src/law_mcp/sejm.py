import httpx

from law_mcp.cache import cached

BASE_URL = "https://api.sejm.gov.pl/sejm"
DEFAULT_TERM = 10

_client: httpx.AsyncClient | None = None


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


def set_client(client: httpx.AsyncClient) -> None:
    global _client
    _client = client


async def _request(path: str, params: dict | None = None) -> httpx.Response:
    try:
        resp = await _get_client().get(f"{BASE_URL}{path}", params=params)
        resp.raise_for_status()
        return resp
    except httpx.HTTPStatusError as e:
        raise APIError(f"Sejm API returned {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        raise APIError(f"Sejm API request failed: {e}") from e


@cached()
async def search_processes(
    title: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    term: int = DEFAULT_TERM,
    limit: int = 20,
    offset: int = 0,
) -> list:
    params: dict[str, str | int] = {"limit": limit, "offset": offset}
    if title:
        params["title"] = title
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to

    resp = await _request(f"/term{term}/processes", params=params)
    return resp.json()
