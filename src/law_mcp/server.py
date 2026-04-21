import asyncio

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from law_mcp import eurlex, formatting, isap, saos, sejm
from law_mcp.query import tokenize

mcp = FastMCP("LawMCP")

SEARCH_TIMEOUT = 90  # seconds per source


def _keyword_variants(keywords: str | None) -> list[str | None]:
    """Generate progressively relaxed keyword combinations.

    "prawo karne, kradzież" → ["prawo karne, kradzież", "prawo karne", "kradzież", None]
    """
    if not keywords:
        return [None]
    kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not kw_list:
        return [None]
    if len(kw_list) == 1:
        return [keywords, None]
    variants: list[str | None] = [keywords]
    for kw in kw_list:
        variants.append(kw)
    variants.append(None)
    return variants


async def _run_isap_queries(
    title_queries: list[str | None],
    keywords: str | None,
    publisher: str | None,
    act_type: str | None,
    date_from: str | None,
    date_to: str | None,
    in_force: bool,
    limit: int,
) -> dict:
    """Fire parallel ISAP queries for multiple title variants and merge results."""
    tasks = [
        isap.search_acts(
            title=q, keywords=keywords, publisher=publisher, act_type=act_type,
            date_from=date_from, date_to=date_to, in_force=in_force, limit=limit,
        )
        for q in title_queries
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    seen: set[str] = set()
    items: list[dict] = []
    for r in results:
        if isinstance(r, BaseException):
            continue
        for item in r.get("items", []):
            addr = item.get("address", "")
            if addr and addr not in seen:
                seen.add(addr)
                items.append(item)

    return {
        "items": items[:limit],
        "count": min(len(items), limit),
        "totalCount": len(items),
        "offset": 0,
    }


async def _search_isap_expanded(
    query: str | None,
    title: str | None,
    keywords: str | None,
    publisher: str | None,
    act_type: str | None,
    date_from: str | None,
    date_to: str | None,
    in_force: bool,
    limit: int,
) -> dict:
    """Search ISAP with query expansion and keyword fallback.

    1. Splits multi-word queries into parallel title searches
    2. If keywords produce 0 results, progressively relaxes them
    """
    search_text = title or query
    words = tokenize(search_text)

    # Build title queries: full phrase + individual words
    title_queries: list[str | None] = []
    if search_text:
        title_queries.append(search_text)
    if len(words) > 1:
        title_queries.extend(w for w in words if w != (search_text or "").lower())
    if not title_queries:
        title_queries = [None]

    kw_chain = _keyword_variants(keywords)

    # Try each keyword variant (most specific first); stop on first hit
    for kw in kw_chain:
        result = await _run_isap_queries(
            title_queries, kw, publisher, act_type,
            date_from, date_to, in_force, limit,
        )
        if result["items"]:
            return result

    # All variants exhausted — return empty result
    return {"items": [], "count": 0, "totalCount": 0, "offset": 0}


async def _search_sejm_expanded(
    title: str | None,
    date_from: str | None,
    date_to: str | None,
    term: int,
    limit: int,
) -> list:
    """Search Sejm with query expansion — fires parallel queries per word and merges results."""
    words = tokenize(title)

    title_queries = []
    if title:
        title_queries.append(title)
    if len(words) > 1:
        title_queries.extend(w for w in words if w != (title or "").lower())

    if len(title_queries) <= 1:
        return await sejm.search_processes(
            title=title, date_from=date_from, date_to=date_to,
            term=term, limit=limit,
        )

    tasks = [
        sejm.search_processes(
            title=q, date_from=date_from, date_to=date_to,
            term=term, limit=limit,
        )
        for q in title_queries
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    seen: set[str] = set()
    items: list[dict] = []
    for r in results:
        if isinstance(r, BaseException) or not isinstance(r, list):
            continue
        for item in r:
            num = str(item.get("number", ""))
            if num and num not in seen:
                seen.add(num)
                items.append(item)

    return items[:limit]


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
async def search_legislation(
    query: str | None = None,
    title: str | None = None,
    keywords: str | None = None,
    publisher: str | None = None,
    act_type: str | None = None,
    doc_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    source: str | None = None,
    in_force: bool = False,
    limit: int = 10,
) -> str:
    """Search legislation across Polish (ISAP) and EU (EUR-Lex) databases in parallel.

    Returns all acts by default, including repealed ones (marked with their status).
    Set in_force=True to show only acts currently in force.
    Multi-word queries are automatically expanded for better matching.
    If combined keywords return no results, they are progressively relaxed.

    Args:
        query: Full-text search query (used for both ISAP title and EUR-Lex).
        title: Search in Polish act titles only (ISAP-specific).
        keywords: Comma-separated ISAP keywords. Common values:
            "prawo karne", "prawo cywilne", "prawo pracy", "prawo administracyjne",
            "postępowanie karne", "postępowanie cywilne", "postępowanie administracyjne",
            "podatki", "finanse publiczne", "ochrona środowiska", "ochrona danych osobowych",
            "zamówienia publiczne", "prawo handlowe", "prawo budowlane",
            "ubezpieczenia społeczne", "prawo autorskie", "transport", "edukacja".
            Multiple keywords can be combined: "prawo karne, kradzież".
        publisher: ISAP publisher filter. Values: "DU" (Dziennik Ustaw), "MP" (Monitor Polski).
        act_type: ISAP act type filter. Values: "Ustawa", "Rozporządzenie",
            "Obwieszczenie", "Zarządzenie".
        doc_type: EUR-Lex document type filter. Values: "directive", "regulation", "decision".
        date_from: Earliest date (yyyy-MM-dd).
        date_to: Latest date (yyyy-MM-dd).
        source: "PL" for Polish only, "EU" for EU only, or omit for both.
        in_force: Only return acts currently in force (default: False).
        limit: Max results per source (default: 10).
    """
    search_pl = source is None or source.upper() == "PL"
    search_eu = source is None or source.upper() == "EU"

    tasks = {}
    if search_pl:
        tasks["pl"] = asyncio.wait_for(
            _search_isap_expanded(
                query=query,
                title=title,
                keywords=keywords,
                publisher=publisher,
                act_type=act_type,
                date_from=date_from,
                date_to=date_to,
                in_force=in_force,
                limit=limit,
            ),
            timeout=SEARCH_TIMEOUT,
        )
    if search_eu:
        tasks["eu"] = asyncio.wait_for(
            eurlex.search_legislation(
                query=query or title or keywords,
                date_from=date_from,
                date_to=date_to,
                doc_type=doc_type,
                in_force=in_force,
                limit=limit,
            ),
            timeout=SEARCH_TIMEOUT,
        )

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values(), return_exceptions=True)))

    pl_data = None
    eu_data = None
    errors = []

    for key, label in [("pl", "ISAP"), ("eu", "EUR-Lex")]:
        if key not in results:
            continue
        val = results[key]
        if isinstance(val, asyncio.TimeoutError):
            errors.append(f"{label}: timed out after {SEARCH_TIMEOUT}s")
        elif isinstance(val, BaseException):
            errors.append(f"{label}: {val}")
        elif key == "pl":
            pl_data = val
        else:
            eu_data = val

    return formatting.format_combined_legislation(pl_data, eu_data, errors or None)


@mcp.tool()
async def read_act(
    eli: str | None = None,
    publisher: str | None = None,
    year: int | None = None,
    position: int | None = None,
) -> str:
    """Read a Polish legal act with full metadata, references, and text in one call.

    Provide either an ELI identifier or publisher+year+position.
    Returns act details, cross-references to other acts, and the full text.

    Args:
        eli: ELI identifier, e.g. "DU/2024/1673". If provided, publisher/year/position are ignored.
        publisher: "DU" (Dziennik Ustaw) or "MP" (Monitor Polski).
        year: Publication year.
        position: Position number in the journal.
    """
    if eli:
        try:
            publisher, year, position = isap.parse_eli(eli)
        except ValueError as e:
            return str(e)
    elif not (publisher and year and position):
        return "Provide either 'eli' (e.g. DU/2024/1673) or 'publisher', 'year', and 'position'."

    try:
        act, refs, text_html = await isap.get_act_full(publisher, year, position)
        return formatting.format_full_act(act, refs, text_html)
    except isap.APIError as e:
        return f"Error reading act: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def search_case_law(
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    court_type: str | None = None,
    judgment_type: str | None = None,
    source: str | None = None,
    limit: int = 10,
) -> str:
    """Search case law across Polish courts (SAOS) and EU Court of Justice (CJEU) in parallel.

    Multi-word queries are automatically expanded for better matching.

    Args:
        query: Full-text search query.
        date_from: Earliest judgment date (yyyy-MM-dd).
        date_to: Latest judgment date (yyyy-MM-dd).
        court_type: Polish court filter (SAOS only). Values:
            "COMMON" (sądy powszechne), "SUPREME" (Sąd Najwyższy),
            "ADMINISTRATIVE" (sądy administracyjne),
            "CONSTITUTIONAL_TRIBUNAL" (Trybunał Konstytucyjny),
            "NATIONAL_APPEAL_CHAMBER" (Krajowa Izba Odwoławcza).
        judgment_type: Polish judgment type filter (SAOS only). Values:
            "DECISION" (postanowienie), "RESOLUTION" (uchwała),
            "SENTENCE" (wyrok), "REGULATION" (zarządzenie),
            "REASONS" (uzasadnienie).
        source: "PL" for Polish only, "EU" for EU only, or omit for both.
        limit: Max results per source (default: 10).
    """
    search_pl = source is None or source.upper() == "PL"
    search_eu = source is None or source.upper() == "EU"

    tasks = {}
    if search_pl:
        tasks["pl"] = asyncio.wait_for(
            saos.search_judgments(
                query=query,
                date_from=date_from,
                date_to=date_to,
                court_type=court_type,
                judgment_type=judgment_type,
                page_size=limit,
            ),
            timeout=SEARCH_TIMEOUT,
        )
    if search_eu:
        tasks["eu"] = asyncio.wait_for(
            eurlex.search_cjeu_cases(
                query=query,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
            ),
            timeout=SEARCH_TIMEOUT,
        )

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values(), return_exceptions=True)))

    pl_data = None
    eu_data = None
    errors = []

    for key, label in [("pl", "SAOS"), ("eu", "CJEU")]:
        if key not in results:
            continue
        val = results[key]
        if isinstance(val, asyncio.TimeoutError):
            errors.append(f"{label}: timed out after {SEARCH_TIMEOUT}s")
        elif isinstance(val, BaseException):
            errors.append(f"{label}: {val}")
        elif key == "pl":
            pl_data = val
        else:
            eu_data = val

    return formatting.format_combined_case_law(pl_data, eu_data, errors or None)


@mcp.tool()
async def read_judgment(judgment_id: int) -> str:
    """Read a Polish court judgment by its SAOS ID.

    Returns the full text, judges, legal bases, and referenced regulations.
    Use search_case_law first to find judgment IDs.

    Args:
        judgment_id: Numeric judgment ID from SAOS.
    """
    try:
        data = await saos.get_judgment(judgment_id)
        return formatting.format_judgment_detail(data)
    except saos.APIError as e:
        return f"Error reading judgment: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def read_eu_document(celex: str) -> str:
    """Read an EU legal document by its CELEX number from EUR-Lex.

    Works for regulations, directives, decisions, and CJEU judgments.
    Use search_legislation or search_case_law first to find CELEX numbers.

    Args:
        celex: CELEX identifier, e.g. "32016R0679" (GDPR) or "62014CJ0362" (Schrems).
    """
    try:
        data = await eurlex.get_document_by_celex(celex)
        return formatting.format_eu_document_detail(data)
    except eurlex.APIError as e:
        return f"Error reading EU document: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def search_legislative_process(
    title: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    term: int = 10,
    limit: int = 20,
) -> str:
    """Search legislative processes in the Polish Sejm (parliament).

    Track bills, amendments, and their progress through the legislative process.
    Multi-word queries are automatically expanded for better matching.

    Args:
        title: Search in process titles.
        date_from: Earliest date (yyyy-MM-dd).
        date_to: Latest date (yyyy-MM-dd).
        term: Sejm term number (default: 10, current term).
        limit: Max results (default: 20).
    """
    try:
        data = await _search_sejm_expanded(
            title=title,
            date_from=date_from,
            date_to=date_to,
            term=term,
            limit=limit,
        )
        return formatting.format_legislative_process_results(data)
    except sejm.APIError as e:
        return f"Error searching legislative processes: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"
