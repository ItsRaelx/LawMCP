import pytest

from law_mcp import eurlex


@pytest.fixture(autouse=True)
def _reset_client():
    eurlex._client = None
    yield
    eurlex._client = None


class TestEscapeSparql:
    def test_escapes_quotes(self):
        assert eurlex._escape_sparql('test "value"') == 'test \\"value\\"'

    def test_escapes_backslash(self):
        assert eurlex._escape_sparql("path\\to") == "path\\\\to"

    def test_plain_text_unchanged(self):
        assert eurlex._escape_sparql("hello world") == "hello world"


class TestSearchLegislation:
    @pytest.mark.anyio
    async def test_basic_search(self, eurlex_sparql_legislation_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_legislation_response)

        results = await eurlex.search_legislation(query="data protection")
        assert len(results) == 1
        assert results[0]["celex"] == "32016R0679"
        assert "General Data Protection" in results[0]["title"]

    @pytest.mark.anyio
    async def test_sends_sparql_query(self, eurlex_sparql_legislation_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_legislation_response)

        await eurlex.search_legislation(query="data protection")

        request = httpx_mock.get_request()
        assert "query" in request.url.params
        sparql = request.url.params["query"]
        # Per-word CONTAINS filters instead of exact phrase
        assert 'CONTAINS(LCASE(?title), "data")' in sparql
        assert 'CONTAINS(LCASE(?title), "protection")' in sparql
        assert request.headers["accept"] == "application/sparql-results+json"

    @pytest.mark.anyio
    async def test_single_word_query(self, eurlex_sparql_legislation_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_legislation_response)

        await eurlex.search_legislation(query="GDPR")

        request = httpx_mock.get_request()
        sparql = request.url.params["query"]
        assert 'CONTAINS(LCASE(?title), "gdpr")' in sparql

    @pytest.mark.anyio
    async def test_in_force_filter(self, eurlex_sparql_legislation_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_legislation_response)

        await eurlex.search_legislation(query="test", in_force=True)

        request = httpx_mock.get_request()
        assert "resource_legal_in-force" in request.url.params["query"]

    @pytest.mark.anyio
    async def test_no_in_force_filter(self, eurlex_sparql_legislation_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_legislation_response)

        await eurlex.search_legislation(query="test", in_force=False)

        request = httpx_mock.get_request()
        assert "resource_legal_in-force" not in request.url.params["query"]

    @pytest.mark.anyio
    async def test_http_error(self, httpx_mock):
        httpx_mock.add_response(status_code=500)

        with pytest.raises(eurlex.APIError, match="500"):
            await eurlex.search_legislation(query="test")


class TestSearchCjeuCases:
    @pytest.mark.anyio
    async def test_basic_search(self, eurlex_sparql_caselaw_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_caselaw_response)

        results = await eurlex.search_cjeu_cases(query="schrems")
        assert len(results) == 1
        assert results[0]["celex"] == "62014CJ0362"
        assert results[0]["ecli"] == "ECLI:EU:C:2015:650"

    @pytest.mark.anyio
    async def test_sends_judg_type_filter(self, eurlex_sparql_caselaw_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_sparql_caselaw_response)

        await eurlex.search_cjeu_cases(query="test")

        request = httpx_mock.get_request()
        assert "resource-type/JUDG" in request.url.params["query"]


class TestGetDocumentByCelex:
    @pytest.mark.anyio
    async def test_found(self, eurlex_document_detail_response, httpx_mock):
        httpx_mock.add_response(json=eurlex_document_detail_response)

        doc = await eurlex.get_document_by_celex("32016R0679")
        assert doc["celex"] == "32016R0679"
        assert "General Data Protection" in doc["title"]
        assert doc["type"] == "REG"

    @pytest.mark.anyio
    async def test_not_found(self, httpx_mock):
        httpx_mock.add_response(json={"results": {"bindings": []}})

        with pytest.raises(eurlex.APIError, match="No document found"):
            await eurlex.get_document_by_celex("INVALID123")
