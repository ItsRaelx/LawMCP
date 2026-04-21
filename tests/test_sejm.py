import pytest

from law_mcp import sejm


@pytest.fixture(autouse=True)
def _reset_client():
    sejm._client = None
    yield
    sejm._client = None


class TestSearchProcesses:
    @pytest.mark.anyio
    async def test_basic_search(self, sejm_process_search_response, httpx_mock):
        httpx_mock.add_response(json=sejm_process_search_response)

        result = await sejm.search_processes(title="kodeks")
        assert result[0]["number"] == "1"
        assert result[0]["title"].startswith("Rządowy projekt")

    @pytest.mark.anyio
    async def test_param_mapping(self, sejm_process_search_response, httpx_mock):
        httpx_mock.add_response(json=sejm_process_search_response)

        await sejm.search_processes(
            title="kodeks",
            date_from="2024-01-01",
            limit=5,
        )

        request = httpx_mock.get_request()
        assert request.url.params["title"] == "kodeks"
        assert request.url.params["dateFrom"] == "2024-01-01"
        assert request.url.params["limit"] == "5"

    @pytest.mark.anyio
    async def test_default_term(self, sejm_process_search_response, httpx_mock):
        httpx_mock.add_response(json=sejm_process_search_response)

        await sejm.search_processes()

        request = httpx_mock.get_request()
        assert "/term10/processes" in str(request.url)

    @pytest.mark.anyio
    async def test_custom_term(self, sejm_process_search_response, httpx_mock):
        httpx_mock.add_response(json=sejm_process_search_response)

        await sejm.search_processes(term=9)

        request = httpx_mock.get_request()
        assert "/term9/processes" in str(request.url)

    @pytest.mark.anyio
    async def test_http_error(self, httpx_mock):
        httpx_mock.add_response(status_code=503)

        with pytest.raises(sejm.APIError, match="503"):
            await sejm.search_processes(title="test")
