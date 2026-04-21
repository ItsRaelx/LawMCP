import asyncio
import re

import httpx

from law_mcp.cache import cached

BASE_URL = "https://api.sejm.gov.pl/eli"

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
        raise APIError(f"ISAP API returned {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        raise APIError(f"ISAP API request failed: {e}") from e


@cached()
async def search_acts(
    title: str | None = None,
    keywords: str | None = None,
    publisher: str | None = None,
    act_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    in_force: bool = False,
    limit: int = 20,
    offset: int = 0,
    sort: str | None = None,
) -> dict:
    params: dict[str, str | int] = {"limit": limit, "offset": offset}
    if in_force:
        params["inForce"] = "1"
    if title:
        params["title"] = title
    if keywords:
        params["keywords"] = keywords
    if publisher:
        params["publisher"] = publisher
    if act_type:
        params["type"] = act_type
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to
    if sort:
        params["sort"] = sort

    resp = await _request("/acts/search", params=params)
    return resp.json()


@cached()
async def get_act(publisher: str, year: int, position: int) -> dict:
    resp = await _request(f"/acts/{publisher}/{year}/{position}")
    return resp.json()


@cached()
async def get_act_references(publisher: str, year: int, position: int) -> list:
    resp = await _request(f"/acts/{publisher}/{year}/{position}/references")
    data = resp.json()
    if isinstance(data, list):
        return data
    return data.get("references", data.get("items", []))


@cached()
async def get_act_text_html(publisher: str, year: int, position: int) -> str:
    resp = await _request(f"/acts/{publisher}/{year}/{position}/text.html")
    return resp.text


@cached()
async def get_act_text_pdf(publisher: str, year: int, position: int) -> bytes:
    resp = await _request(f"/acts/{publisher}/{year}/{position}/text.pdf")
    return resp.content


async def get_act_with_references(publisher: str, year: int, position: int) -> tuple[dict, list]:
    act, refs = await asyncio.gather(
        get_act(publisher, year, position),
        get_act_references(publisher, year, position),
        return_exceptions=True,
    )
    if isinstance(act, BaseException):
        raise act
    if isinstance(refs, BaseException):
        refs = []
    return act, refs


async def get_act_full(publisher: str, year: int, position: int) -> tuple[dict, list, str]:
    from law_mcp.formatting import pdf_to_text

    act, refs, text = await asyncio.gather(
        get_act(publisher, year, position),
        get_act_references(publisher, year, position),
        get_act_text_html(publisher, year, position),
        return_exceptions=True,
    )
    if isinstance(act, BaseException):
        raise act
    if isinstance(refs, BaseException):
        refs = []
    has_html = isinstance(act, dict) and act.get("textHTML")
    has_pdf = isinstance(act, dict) and act.get("textPDF")

    if isinstance(text, BaseException) or not has_html:
        text = ""
        if has_pdf:
            try:
                pdf_bytes = await get_act_text_pdf(publisher, year, position)
                text = pdf_to_text(pdf_bytes)
            except Exception:
                pass
    return act, refs, text


_ELI_PATTERN = re.compile(r"^([A-Z]{2})/(\d{4})/(\d+)$")


def parse_eli(eli: str) -> tuple[str, int, int]:
    match = _ELI_PATTERN.match(eli.strip())
    if not match:
        raise ValueError(f"Invalid ELI format: '{eli}'. Expected format: PUBLISHER/YEAR/POSITION (e.g. DU/2024/1673)")
    return match.group(1), int(match.group(2)), int(match.group(3))
