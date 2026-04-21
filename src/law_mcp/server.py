import asyncio

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from law_mcp import eurlex, formatting, isap, saos, sejm

mcp = FastMCP("LawMCP")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
async def search_legislation(
    query: str | None = None,
    title: str | None = None,
    keywords: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    source: str | None = None,
    in_force: bool = True,
    limit: int = 10,
) -> str:
    """Search legislation across Polish (ISAP) and EU (EUR-Lex) databases in parallel.

    By default only returns acts currently in force. Set in_force=False to include repealed acts.

    Args:
        query: Full-text search query (used for both ISAP title and EUR-Lex search).
        title: Search in Polish act titles only (ISAP-specific).
        keywords: Comma-separated keywords (ISAP-specific).
        date_from: Earliest date (yyyy-MM-dd).
        date_to: Latest date (yyyy-MM-dd).
        source: "PL" for Polish only, "EU" for EU only, or omit for both.
        in_force: Only return acts currently in force (default: True).
        limit: Max results per source (default: 10).
    """
    search_pl = source is None or source.upper() == "PL"
    search_eu = source is None or source.upper() == "EU"

    tasks = {}
    if search_pl:
        tasks["pl"] = isap.search_acts(
            title=title or query,
            keywords=keywords,
            date_from=date_from,
            date_to=date_to,
            in_force=in_force,
            limit=limit,
        )
    if search_eu:
        tasks["eu"] = eurlex.search_legislation(
            query=query or title or keywords,
            date_from=date_from,
            date_to=date_to,
            in_force=in_force,
            limit=limit,
        )

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values(), return_exceptions=True)))

    pl_data = None
    eu_data = None
    errors = []

    if "pl" in results:
        if isinstance(results["pl"], BaseException):
            errors.append(f"ISAP: {results['pl']}")
        else:
            pl_data = results["pl"]

    if "eu" in results:
        if isinstance(results["eu"], BaseException):
            errors.append(f"EUR-Lex: {results['eu']}")
        else:
            eu_data = results["eu"]

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
        publisher: DU (Dziennik Ustaw) or MP (Monitor Polski).
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
    source: str | None = None,
    limit: int = 10,
) -> str:
    """Search case law across Polish courts (SAOS) and EU Court of Justice (CJEU) in parallel.

    Args:
        query: Full-text search query.
        date_from: Earliest judgment date (yyyy-MM-dd).
        date_to: Latest judgment date (yyyy-MM-dd).
        court_type: Polish court filter — COMMON, SUPREME, ADMINISTRATIVE,
            CONSTITUTIONAL_TRIBUNAL, or NATIONAL_APPEAL_CHAMBER. Ignored for CJEU.
        source: "PL" for Polish only, "EU" for EU only, or omit for both.
        limit: Max results per source (default: 10).
    """
    search_pl = source is None or source.upper() == "PL"
    search_eu = source is None or source.upper() == "EU"

    tasks = {}
    if search_pl:
        tasks["pl"] = saos.search_judgments(
            query=query,
            date_from=date_from,
            date_to=date_to,
            court_type=court_type,
            page_size=limit,
        )
    if search_eu:
        tasks["eu"] = eurlex.search_cjeu_cases(
            query=query,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    results = dict(zip(tasks.keys(), await asyncio.gather(*tasks.values(), return_exceptions=True)))

    pl_data = None
    eu_data = None
    errors = []

    if "pl" in results:
        if isinstance(results["pl"], BaseException):
            errors.append(f"SAOS: {results['pl']}")
        else:
            pl_data = results["pl"]

    if "eu" in results:
        if isinstance(results["eu"], BaseException):
            errors.append(f"CJEU: {results['eu']}")
        else:
            eu_data = results["eu"]

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

    Args:
        title: Search in process titles.
        date_from: Earliest date (yyyy-MM-dd).
        date_to: Latest date (yyyy-MM-dd).
        term: Sejm term number (default: 10, current term).
        limit: Max results (default: 20).
    """
    try:
        data = await sejm.search_processes(
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
