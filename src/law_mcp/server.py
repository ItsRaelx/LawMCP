from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from law_mcp import formatting, isap, saos

mcp = FastMCP("LawMCP")


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@mcp.tool()
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
) -> str:
    """Search Polish court judgments in the SAOS database.

    Args:
        query: Full-text search query.
        date_from: Earliest judgment date (yyyy-MM-dd).
        date_to: Latest judgment date (yyyy-MM-dd).
        court_type: COMMON, SUPREME, ADMINISTRATIVE, CONSTITUTIONAL_TRIBUNAL, or NATIONAL_APPEAL_CHAMBER.
        judgment_type: SENTENCE, DECISION, RESOLUTION, or REASONS.
        sort_by: JUDGMENT_DATE or DATABASE_ID.
        sort_dir: ASC or DESC.
        page_size: Results per page (1-100, default 10).
        page_number: Page number (default 0).
    """
    try:
        data = await saos.search_judgments(
            query=query,
            date_from=date_from,
            date_to=date_to,
            court_type=court_type,
            judgment_type=judgment_type,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page_size=page_size,
            page_number=page_number,
        )
        return formatting.format_judgment_search_results(data)
    except saos.APIError as e:
        return f"Error searching judgments: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def get_judgment(judgment_id: int) -> str:
    """Get full details of a Polish court judgment by its SAOS ID.

    Returns the complete text, judges, legal bases, and referenced regulations.
    Use search_judgments first to find judgment IDs.

    Args:
        judgment_id: Numeric judgment ID from SAOS.
    """
    try:
        data = await saos.get_judgment(judgment_id)
        return formatting.format_judgment_detail(data)
    except saos.APIError as e:
        return f"Error fetching judgment: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def search_legal_acts(
    title: str | None = None,
    keywords: str | None = None,
    publisher: str | None = None,
    act_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
    offset: int = 0,
    sort: str | None = None,
) -> str:
    """Search Polish legal acts in the ISAP database (Dziennik Ustaw, Monitor Polski).

    Args:
        title: Search in act titles.
        keywords: Comma-separated keywords.
        publisher: DU (Dziennik Ustaw) or MP (Monitor Polski).
        act_type: e.g. Ustawa, Rozporządzenie, Obwieszczenie, Uchwała.
        date_from: Earliest date (yyyy-MM-dd).
        date_to: Latest date (yyyy-MM-dd).
        limit: Max results (1-500, default 20).
        offset: Result offset for pagination (default 0).
        sort: Sort field, e.g. 'date' or '-date' for descending.
    """
    try:
        data = await isap.search_acts(
            title=title,
            keywords=keywords,
            publisher=publisher,
            act_type=act_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return formatting.format_act_search_results(data)
    except isap.APIError as e:
        return f"Error searching legal acts: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def get_legal_act(publisher: str, year: int, position: int) -> str:
    """Get details and references for a specific Polish legal act.

    Args:
        publisher: DU (Dziennik Ustaw) or MP (Monitor Polski).
        year: Publication year.
        position: Position number in the journal.
    """
    try:
        act, refs = await isap.get_act_with_references(publisher, year, position)
        return formatting.format_act_detail(act, refs)
    except isap.APIError as e:
        return f"Error fetching legal act: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def get_legal_act_text(publisher: str, year: int, position: int) -> str:
    """Get the full text of a Polish legal act as plain text.

    Warning: some acts are very long and the response may be truncated.

    Args:
        publisher: DU (Dziennik Ustaw) or MP (Monitor Polski).
        year: Publication year.
        position: Position number in the journal.
    """
    try:
        html = await isap.get_act_text_html(publisher, year, position)
        text = formatting.html_to_text(html)
        return formatting.truncate(text, 100_000)
    except isap.APIError as e:
        return f"Error fetching act text: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
async def get_legal_act_by_eli(eli: str) -> str:
    """Get details of a legal act using its ELI identifier.

    Args:
        eli: ELI string in format PUBLISHER/YEAR/POSITION (e.g. 'DU/2024/1673').
    """
    try:
        publisher, year, position = isap.parse_eli(eli)
    except ValueError as e:
        return str(e)

    try:
        act, refs = await isap.get_act_with_references(publisher, year, position)
        return formatting.format_act_detail(act, refs)
    except isap.APIError as e:
        return f"Error fetching legal act: {e.message}"
    except Exception as e:
        return f"Unexpected error: {e}"
