import html
import re


def html_to_text(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</tr>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate(text: str, max_length: int, suffix: str = "\n\n[...truncated...]") -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_judgment_search_results(data: dict) -> str:
    total = data.get("info", {}).get("totalResults", "?")
    items = data.get("items", [])

    if not items:
        return f"No judgments found (total: {total})."

    lines = [f"Found {total} judgments:\n"]
    for item in items:
        jid = item.get("id", "?")
        court_type = item.get("courtType", "")
        date = item.get("judgmentDate", "")
        court_cases = item.get("courtCases", [])
        if isinstance(court_cases, dict):
            case_numbers = ", ".join(court_cases.get("caseNumbers", []))
        else:
            case_numbers = ", ".join(
                c.get("caseNumber", "") for c in court_cases if isinstance(c, dict)
            )
        keywords_list = item.get("keywords", [])
        keywords = ", ".join(keywords_list[:5]) if keywords_list else ""

        lines.append(f"--- Judgment #{jid} ---")
        if case_numbers:
            lines.append(f"Case: {case_numbers}")
        if date:
            lines.append(f"Date: {date}")
        if court_type:
            lines.append(f"Court: {court_type}")
        if keywords:
            lines.append(f"Keywords: {keywords}")

        text_content = item.get("textContent", "")
        if text_content:
            excerpt = html_to_text(text_content)
            excerpt = truncate(excerpt, 500, suffix="...")
            lines.append(f"Excerpt: {excerpt}")
        lines.append("")

    return "\n".join(lines)


def format_judgment_detail(data: dict) -> str:
    lines = []

    case_numbers = [c.get("caseNumber", "") for c in data.get("courtCases", []) if isinstance(c, dict)]
    if case_numbers:
        lines.append(f"Case: {', '.join(case_numbers)}")

    for field, label in [
        ("judgmentDate", "Date"),
        ("courtType", "Court type"),
        ("judgmentType", "Judgment type"),
    ]:
        val = data.get(field)
        if val:
            lines.append(f"{label}: {val}")

    division = data.get("division")
    if isinstance(division, dict):
        court_name = division.get("court", {}).get("name", "") if isinstance(division.get("court"), dict) else ""
        div_name = division.get("name", "")
        if court_name:
            lines.append(f"Court: {court_name}")
        if div_name:
            lines.append(f"Division: {div_name}")

    judges = data.get("judges", [])
    if judges:
        judge_strs = []
        for j in judges:
            name = j.get("name", "")
            roles = j.get("specialRoles", [])
            if roles:
                name += f" ({', '.join(roles)})"
            judge_strs.append(name)
        lines.append(f"Judges: {', '.join(judge_strs)}")

    keywords_list = data.get("keywords", [])
    if keywords_list:
        lines.append(f"Keywords: {', '.join(keywords_list)}")

    legal_bases = data.get("legalBases", [])
    if legal_bases:
        lines.append("\nLegal bases:\n" + "\n".join(f"  - {lb}" for lb in legal_bases))

    refs = data.get("referencedRegulations", [])
    if refs:
        ref_strs = [r.get("text", str(r)) for r in refs if isinstance(r, dict)]
        if ref_strs:
            lines.append("\nReferenced regulations:\n" + "\n".join(f"  - {r}" for r in ref_strs))

    text_content = data.get("textContent", "")
    if text_content:
        lines.append(f"\n--- Full text ---\n{html_to_text(text_content)}")

    return "\n".join(lines)


def format_act_search_results(data: dict) -> str:
    total = data.get("count", data.get("totalCount", "?"))
    items = data.get("items", [])
    offset = data.get("offset", 0)

    if not items:
        return f"No legal acts found (total: {total})."

    lines = [f"Found {total} legal acts (showing from offset {offset}):\n"]
    for act in items:
        title = act.get("title", "?")
        address = act.get("displayAddress", act.get("address", ""))
        status = act.get("status", "")
        act_type = act.get("type", "")
        date = act.get("announcementDate", "")
        eli = act.get("ELI", "")
        publisher = act.get("publisher", "")
        year = act.get("year", "")
        pos = act.get("pos", "")

        lines.append(f"--- {address} ---")
        lines.append(f"Title: {title}")
        if act_type:
            lines.append(f"Type: {act_type}")
        if status:
            lines.append(f"Status: {status}")
        if date:
            lines.append(f"Date: {date}")
        if eli:
            lines.append(f"ELI: {eli}")
        if publisher and year and pos:
            lines.append(f"Ref: {publisher}/{year}/{pos}")
        has_text = []
        if act.get("textHTML"):
            has_text.append("HTML")
        if act.get("textPDF"):
            has_text.append("PDF")
        if has_text:
            lines.append(f"Text available: {', '.join(has_text)}")
        lines.append("")

    return "\n".join(lines)


def format_act_detail(act: dict, references: list | None = None) -> str:
    lines = []

    title = act.get("title", "?")
    lines.append(f"Title: {title}")

    for field, label in [
        ("type", "Type"),
        ("status", "Status"),
        ("displayAddress", "Address"),
        ("ELI", "ELI"),
        ("announcementDate", "Announcement date"),
        ("promulgation", "Promulgation date"),
        ("publisher", "Publisher"),
        ("year", "Year"),
        ("pos", "Position"),
        ("volume", "Volume"),
    ]:
        val = act.get(field)
        if val:
            lines.append(f"{label}: {val}")

    keywords_list = act.get("keywords", [])
    if keywords_list:
        lines.append(f"Keywords: {', '.join(keywords_list)}")

    directives = act.get("directives", [])
    if directives:
        lines.append("\nEU directives:\n" + "\n".join(f"  - {d}" for d in directives))

    if references:
        lines.append("\nReferences:")
        for ref in references:
            ref_type = ref.get("type", "")
            ref_act = ref.get("title", ref.get("address", str(ref)))
            lines.append(f"  - [{ref_type}] {ref_act}")

    has_text = []
    if act.get("textHTML"):
        has_text.append("HTML")
    if act.get("textPDF"):
        has_text.append("PDF")
    if has_text:
        lines.append(f"\nText available: {', '.join(has_text)}")

    return "\n".join(lines)


def format_full_act(act: dict, references: list | None = None, text_html: str = "") -> str:
    detail = format_act_detail(act, references)
    if not text_html:
        return detail
    text = html_to_text(text_html)
    text = truncate(text, 100_000)
    return f"{detail}\n\n--- Full text ---\n{text}"


def format_eu_legislation_results(results: list[dict]) -> str:
    if not results:
        return "No EU legislation found."

    lines = [f"Found {len(results)} EU legislative acts:\n"]
    for item in results:
        celex = item.get("celex", "?")
        title = item.get("title", "?")
        date = item.get("date", "")
        doc_type = item.get("type", "")

        lines.append(f"--- {celex} ---")
        lines.append(f"Title: {title}")
        if doc_type:
            lines.append(f"Type: {doc_type}")
        if date:
            lines.append(f"Date: {date}")
        lines.append(f"CELEX: {celex}")
        lines.append("")

    return "\n".join(lines)


def format_eu_case_law_results(results: list[dict]) -> str:
    if not results:
        return "No EU case law found."

    lines = [f"Found {len(results)} CJEU judgments:\n"]
    for item in results:
        celex = item.get("celex", "?")
        title = item.get("title", "?")
        date = item.get("date", "")
        ecli = item.get("ecli", "")

        lines.append(f"--- {celex} ---")
        lines.append(f"Title: {title}")
        if date:
            lines.append(f"Date: {date}")
        if ecli:
            lines.append(f"ECLI: {ecli}")
        lines.append(f"CELEX: {celex}")
        lines.append("")

    return "\n".join(lines)


def format_eu_document_detail(data: dict) -> str:
    lines = []
    celex = data.get("celex", "?")
    lines.append(f"CELEX: {celex}")

    for field, label in [
        ("title", "Title"),
        ("type", "Type"),
        ("date", "Date"),
        ("ecli", "ECLI"),
        ("inForce", "In force"),
    ]:
        val = data.get(field)
        if val:
            lines.append(f"{label}: {val}")

    return "\n".join(lines)


def format_legislative_process_results(data: list) -> str:
    if not data:
        return "No legislative processes found."

    lines = [f"Found {len(data)} legislative processes:\n"]
    for item in data:
        number = item.get("number", "?")
        title = item.get("title", "?")
        doc_date = item.get("documentDate", "")
        change_date = item.get("changeDate", "")
        description = item.get("description", "")

        lines.append(f"--- Process #{number} ---")
        lines.append(f"Title: {title}")
        if description:
            lines.append(f"Description: {description}")
        if doc_date:
            lines.append(f"Document date: {doc_date}")
        if change_date:
            lines.append(f"Last update: {change_date}")
        lines.append("")

    return "\n".join(lines)


def format_combined_legislation(
    pl_data: dict | None,
    eu_data: list[dict] | None,
    errors: list[str] | None = None,
) -> str:
    sections = []

    if errors:
        sections.append("Warnings:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")

    if pl_data is not None:
        sections.append("=== Polish Legislation (ISAP) ===\n" + format_act_search_results(pl_data))

    if eu_data is not None:
        sections.append("=== EU Legislation (EUR-Lex) ===\n" + format_eu_legislation_results(eu_data))

    if not sections or (pl_data is None and eu_data is None):
        return "No legislation found from any source."

    return "\n".join(sections)


def format_combined_case_law(
    pl_data: dict | None,
    eu_data: list[dict] | None,
    errors: list[str] | None = None,
) -> str:
    sections = []

    if errors:
        sections.append("Warnings:\n" + "\n".join(f"  - {e}" for e in errors) + "\n")

    if pl_data is not None:
        sections.append("=== Polish Case Law (SAOS) ===\n" + format_judgment_search_results(pl_data))

    if eu_data is not None:
        sections.append("=== EU Case Law (CJEU) ===\n" + format_eu_case_law_results(eu_data))

    if not sections or (pl_data is None and eu_data is None):
        return "No case law found from any source."

    return "\n".join(sections)
