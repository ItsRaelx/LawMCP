import pytest

from law_mcp import saos


@pytest.fixture(autouse=True)
def _reset_client():
    saos._client = None
    yield
    saos._client = None


class TestSearchJudgments:
    @pytest.mark.anyio
    async def test_basic_search(self, saos_search_response, httpx_mock):
        httpx_mock.add_response(json=saos_search_response)

        result = await saos.search_judgments(query="kradzież")
        assert result["items"][0]["id"] == 12345

    @pytest.mark.anyio
    async def test_param_mapping(self, saos_search_response, httpx_mock):
        httpx_mock.add_response(json=saos_search_response)

        await saos.search_judgments(
            query="test",
            date_from="2024-01-01",
            court_type="SUPREME",
            page_size=5,
        )

        request = httpx_mock.get_request()
        assert request.url.params["all"] == "test"
        assert request.url.params["judgmentDateFrom"] == "2024-01-01"
        assert request.url.params["courtType"] == "SUPREME"
        assert request.url.params["pageSize"] == "5"

    @pytest.mark.anyio
    async def test_http_error(self, httpx_mock):
        httpx_mock.add_response(status_code=500)

        with pytest.raises(saos.APIError, match="500"):
            await saos.search_judgments(query="test")


class TestGetJudgment:
    @pytest.mark.anyio
    async def test_get_by_id(self, saos_judgment_detail, httpx_mock):
        httpx_mock.add_response(json=saos_judgment_detail)

        result = await saos.get_judgment(12345)
        assert result["id"] == 12345
        assert result["courtType"] == "COMMON"

    @pytest.mark.anyio
    async def test_not_found(self, httpx_mock):
        httpx_mock.add_response(status_code=404)

        with pytest.raises(saos.APIError, match="404"):
            await saos.get_judgment(99999)
