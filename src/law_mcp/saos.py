import httpx

BASE_URL = "https://www.saos.org.pl/api"

_client: httpx.AsyncClient | None = None


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


def set_client(client: httpx.AsyncClient) -> None:
    global _client
    _client = client


PARAM_MAP = {
    "query": "all",
    "date_from": "judgmentDateFrom",
    "date_to": "judgmentDateTo",
    "court_type": "courtType",
    "judgment_type": "judgmentType",
    "sort_by": "sortingField",
    "sort_dir": "sortingDirection",
    "page_size": "pageSize",
    "page_number": "pageNumber",
}


async def search_judgments(
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    court_type: str | None = None,
    judgment_type: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    page_size: int = 10,
    page_number: int = 0,
) -> dict:
    params: dict[str, str | int] = {}
    local = {
        "query": query,
        "date_from": date_from,
        "date_to": date_to,
        "court_type": court_type,
        "judgment_type": judgment_type,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "page_size": page_size,
        "page_number": page_number,
    }
    for key, value in local.items():
        if value is not None:
            api_key = PARAM_MAP.get(key, key)
            params[api_key] = value

    try:
        resp = await _get_client().get(f"{BASE_URL}/search/judgments", params=params)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        raise APIError(f"SAOS API returned {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        raise APIError(f"SAOS API request failed: {e}") from e


async def get_judgment(judgment_id: int) -> dict:
    try:
        resp = await _get_client().get(f"{BASE_URL}/judgments/{judgment_id}")
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", data)
    except httpx.HTTPStatusError as e:
        raise APIError(f"SAOS API returned {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        raise APIError(f"SAOS API request failed: {e}") from e
