import pytest

from law_mcp import isap


@pytest.fixture(autouse=True)
def _reset_client():
    isap._client = None
    yield
    isap._client = None


class TestSearchActs:
    @pytest.mark.anyio
    async def test_basic_search(self, isap_search_response, httpx_mock):
        httpx_mock.add_response(json=isap_search_response)

        result = await isap.search_acts(title="kodeks")
        assert result["items"][0]["address"] == "WDU20240001673"

    @pytest.mark.anyio
    async def test_param_mapping(self, isap_search_response, httpx_mock):
        httpx_mock.add_response(json=isap_search_response)

        await isap.search_acts(
            title="kodeks",
            publisher="DU",
            date_from="2024-01-01",
            limit=5,
        )

        request = httpx_mock.get_request()
        assert request.url.params["title"] == "kodeks"
        assert request.url.params["publisher"] == "DU"
        assert request.url.params["dateFrom"] == "2024-01-01"
        assert request.url.params["limit"] == "5"
        assert request.url.params["inForce"] == "1"

    @pytest.mark.anyio
    async def test_in_force_default(self, isap_search_response, httpx_mock):
        httpx_mock.add_response(json=isap_search_response)
        await isap.search_acts(title="kodeks")

        request = httpx_mock.get_request()
        assert request.url.params["inForce"] == "1"

    @pytest.mark.anyio
    async def test_in_force_disabled(self, isap_search_response, httpx_mock):
        httpx_mock.add_response(json=isap_search_response)
        await isap.search_acts(title="kodeks", in_force=False)

        request = httpx_mock.get_request()
        assert "inForce" not in request.url.params

    @pytest.mark.anyio
    async def test_http_error(self, httpx_mock):
        httpx_mock.add_response(status_code=503)

        with pytest.raises(isap.APIError, match="503"):
            await isap.search_acts(title="test")


class TestGetAct:
    @pytest.mark.anyio
    async def test_get_act(self, isap_act_detail, httpx_mock):
        httpx_mock.add_response(json=isap_act_detail)

        result = await isap.get_act("DU", 2024, 1673)
        assert result["title"] == "Ustawa z dnia 14 czerwca 1960 r. - Kodeks postępowania administracyjnego"

    @pytest.mark.anyio
    async def test_not_found(self, httpx_mock):
        httpx_mock.add_response(status_code=404)

        with pytest.raises(isap.APIError, match="404"):
            await isap.get_act("DU", 2024, 99999)


class TestGetActReferences:
    @pytest.mark.anyio
    async def test_returns_list(self, isap_references, httpx_mock):
        httpx_mock.add_response(json=isap_references)

        result = await isap.get_act_references("DU", 2024, 1673)
        assert len(result) == 2
        assert result[0]["type"] == "Zmienia"


class TestGetActTextHtml:
    @pytest.mark.anyio
    async def test_returns_html(self, httpx_mock):
        httpx_mock.add_response(text="<html><body><p>Art. 1.</p></body></html>")

        result = await isap.get_act_text_html("DU", 2024, 1673)
        assert "<p>Art. 1.</p>" in result


class TestGetActWithReferences:
    @pytest.mark.anyio
    async def test_parallel_fetch(self, isap_act_detail, isap_references, httpx_mock):
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673",
            json=isap_act_detail,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/references",
            json=isap_references,
        )

        act, refs = await isap.get_act_with_references("DU", 2024, 1673)
        assert act["address"] == "WDU20240001673"
        assert len(refs) == 2

    @pytest.mark.anyio
    async def test_references_failure_returns_empty(self, isap_act_detail, httpx_mock):
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673",
            json=isap_act_detail,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/references",
            status_code=500,
        )

        act, refs = await isap.get_act_with_references("DU", 2024, 1673)
        assert act["address"] == "WDU20240001673"
        assert refs == []


class TestGetActFull:
    @pytest.mark.anyio
    async def test_parallel_fetch_all(self, isap_act_detail, isap_references, httpx_mock):
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673",
            json=isap_act_detail,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/references",
            json=isap_references,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/text.html",
            text="<html><body><p>Art. 1.</p></body></html>",
        )

        act, refs, text = await isap.get_act_full("DU", 2024, 1673)
        assert act["address"] == "WDU20240001673"
        assert len(refs) == 2
        assert "Art. 1." in text

    @pytest.mark.anyio
    async def test_text_failure_returns_empty(self, isap_act_detail, isap_references, httpx_mock):
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673",
            json=isap_act_detail,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/references",
            json=isap_references,
        )
        httpx_mock.add_response(
            url="https://api.sejm.gov.pl/eli/acts/DU/2024/1673/text.html",
            status_code=404,
        )

        act, refs, text = await isap.get_act_full("DU", 2024, 1673)
        assert act["address"] == "WDU20240001673"
        assert len(refs) == 2
        assert text == ""


class TestParseEli:
    def test_valid_eli(self):
        assert isap.parse_eli("DU/2024/1673") == ("DU", 2024, 1673)

    def test_valid_eli_with_whitespace(self):
        assert isap.parse_eli("  MP/2023/42  ") == ("MP", 2023, 42)

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid ELI format"):
            isap.parse_eli("invalid")

    def test_invalid_lowercase(self):
        with pytest.raises(ValueError, match="Invalid ELI format"):
            isap.parse_eli("du/2024/1673")

    def test_invalid_missing_parts(self):
        with pytest.raises(ValueError, match="Invalid ELI format"):
            isap.parse_eli("DU/2024")
