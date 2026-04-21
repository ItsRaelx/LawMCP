import re

import httpx

from law_mcp.cache import cached
from law_mcp.query import tokenize

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"

_client: httpx.AsyncClient | None = None


class APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=120.0)
    return _client


def set_client(client: httpx.AsyncClient) -> None:
    global _client
    _client = client


def _escape_sparql(value: str) -> str:
    return re.sub(r'([\\"\'\n\r\t])', r"\\\1", value)


async def _sparql_query(query: str) -> dict:
    try:
        resp = await _get_client().get(
            SPARQL_ENDPOINT,
            params={"query": query},
            headers={"Accept": "application/sparql-results+json"},
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as e:
        raise APIError(f"EUR-Lex SPARQL returned {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        raise APIError(f"EUR-Lex SPARQL request failed: {e}") from e


def _parse_bindings(raw: dict) -> list[dict]:
    results = []
    for binding in raw.get("results", {}).get("bindings", []):
        item = {}
        for key, val in binding.items():
            item[key] = val.get("value", "")
        results.append(item)
    return results


@cached()
async def search_legislation(
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    doc_type: str | None = None,
    in_force: bool = False,
    limit: int = 10,
) -> list[dict]:
    filters = []
    if query:
        words = tokenize(query)
        if words:
            for word in words:
                filters.append(f'FILTER(CONTAINS(LCASE(?title), "{_escape_sparql(word)}"))')
        else:
            filters.append(f'FILTER(CONTAINS(LCASE(?title), LCASE("{_escape_sparql(query)}")))')
    if date_from:
        filters.append(f'FILTER(?date >= "{_escape_sparql(date_from)}"^^xsd:date)')
    if date_to:
        filters.append(f'FILTER(?date <= "{_escape_sparql(date_to)}"^^xsd:date)')
    if doc_type:
        type_map = {
            "directive": "DIR",
            "regulation": "REG",
            "decision": "DEC",
        }
        mapped = type_map.get(doc_type.lower(), doc_type.upper())
        filters.append(
            f"FILTER(CONTAINS(STR(?typeUri), "
            f'"http://publications.europa.eu/resource/authority/resource-type/{_escape_sparql(mapped)}"))'
        )
    if in_force:
        filters.append(
            "?work cdm:resource_legal_in-force "
            '<http://publications.europa.eu/resource/authority/in-force/INFORCE> .'
        )

    filter_block = "\n  ".join(filters)

    sparql = f"""PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?celex ?title ?date ?type WHERE {{
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_has_resource-type ?typeUri .
  ?expr cdm:expression_belongs_to_work ?work .
  ?expr cdm:expression_title ?title .
  ?expr cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  OPTIONAL {{ ?work cdm:work_date_document ?date . }}
  BIND(REPLACE(STR(?typeUri), "^.*/", "") AS ?type)
  {filter_block}
}}
ORDER BY DESC(?date)
LIMIT {limit}"""

    raw = await _sparql_query(sparql)
    return _parse_bindings(raw)


@cached()
async def search_cjeu_cases(
    query: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 10,
) -> list[dict]:
    filters = []
    if query:
        words = tokenize(query)
        if words:
            for word in words:
                filters.append(f'FILTER(CONTAINS(LCASE(?title), "{_escape_sparql(word)}"))')
        else:
            filters.append(f'FILTER(CONTAINS(LCASE(?title), LCASE("{_escape_sparql(query)}")))')
    if date_from:
        filters.append(f'FILTER(?date >= "{_escape_sparql(date_from)}"^^xsd:date)')
    if date_to:
        filters.append(f'FILTER(?date <= "{_escape_sparql(date_to)}"^^xsd:date)')

    filter_block = "\n  ".join(filters)

    sparql = f"""PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?celex ?title ?date ?ecli WHERE {{
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_has_resource-type <http://publications.europa.eu/resource/authority/resource-type/JUDG> .
  ?expr cdm:expression_belongs_to_work ?work .
  ?expr cdm:expression_title ?title .
  ?expr cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  OPTIONAL {{ ?work cdm:work_date_document ?date . }}
  OPTIONAL {{ ?work cdm:case-law_ecli ?ecli . }}
  {filter_block}
}}
ORDER BY DESC(?date)
LIMIT {limit}"""

    raw = await _sparql_query(sparql)
    return _parse_bindings(raw)


@cached()
async def get_document_by_celex(celex: str) -> dict:
    safe = _escape_sparql(celex.strip())

    sparql = f"""PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>

SELECT ?title ?date ?type ?ecli ?inForce WHERE {{
  ?work cdm:resource_legal_id_celex "{safe}" .
  ?expr cdm:expression_belongs_to_work ?work .
  ?expr cdm:expression_title ?title .
  ?expr cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> .
  OPTIONAL {{ ?work cdm:work_date_document ?date . }}
  OPTIONAL {{ ?work cdm:work_has_resource-type ?typeUri . BIND(REPLACE(STR(?typeUri), "^.*/", "") AS ?type) }}
  OPTIONAL {{ ?work cdm:case-law_ecli ?ecli . }}
  OPTIONAL {{ ?work cdm:resource_legal_in-force ?inForceUri . BIND(REPLACE(STR(?inForceUri), "^.*/", "") AS ?inForce) }}
}}
LIMIT 1"""

    raw = await _sparql_query(sparql)
    results = _parse_bindings(raw)
    if not results:
        raise APIError(f"No document found for CELEX: {celex}", 404)
    doc = results[0]
    doc["celex"] = celex.strip()
    return doc
