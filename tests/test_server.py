from unittest.mock import AsyncMock, patch

import pytest

from law_mcp.server import mcp


def _text(result: tuple) -> str:
    content_list, _ = result
    return content_list[0].text


class TestSearchJudgmentsTool:
    @pytest.mark.anyio
    async def test_returns_formatted_text(self, saos_search_response):
        mock = AsyncMock(return_value=saos_search_response)
        with patch("law_mcp.server.saos.search_judgments", mock):
            result = await mcp.call_tool("search_judgments", {"query": "kradzież"})
            text = _text(result)
            assert "Found 1 judgments" in text
            assert "II K 123/24" in text

    @pytest.mark.anyio
    async def test_api_error_returns_message(self):
        from law_mcp.saos import APIError

        mock = AsyncMock(side_effect=APIError("SAOS API returned 500", 500))
        with patch("law_mcp.server.saos.search_judgments", mock):
            result = await mcp.call_tool("search_judgments", {"query": "test"})
            text = _text(result)
            assert "Error" in text
            assert "500" in text


class TestGetJudgmentTool:
    @pytest.mark.anyio
    async def test_returns_detail(self, saos_judgment_detail):
        mock = AsyncMock(return_value=saos_judgment_detail["data"])
        with patch("law_mcp.server.saos.get_judgment", mock):
            result = await mcp.call_tool("get_judgment", {"judgment_id": 12345})
            text = _text(result)
            assert "Jan Kowalski" in text
            assert "WYROK" in text


class TestSearchLegalActsTool:
    @pytest.mark.anyio
    async def test_returns_formatted_text(self, isap_search_response):
        mock = AsyncMock(return_value=isap_search_response)
        with patch("law_mcp.server.isap.search_acts", mock):
            result = await mcp.call_tool("search_legal_acts", {"title": "kodeks"})
            text = _text(result)
            assert "Found 1 legal acts" in text
            assert "Kodeks" in text


class TestGetLegalActTool:
    @pytest.mark.anyio
    async def test_returns_detail_with_refs(self, isap_act_detail, isap_references):
        mock = AsyncMock(return_value=(isap_act_detail, isap_references))
        with patch("law_mcp.server.isap.get_act_with_references", mock):
            result = await mcp.call_tool(
                "get_legal_act", {"publisher": "DU", "year": 2024, "position": 1673}
            )
            text = _text(result)
            assert "Kodeks" in text
            assert "Zmienia" in text


class TestGetLegalActTextTool:
    @pytest.mark.anyio
    async def test_returns_plain_text(self):
        html = "<html><body><p>Art. 1. Ustawa reguluje...</p></body></html>"
        with patch("law_mcp.server.isap.get_act_text_html", AsyncMock(return_value=html)):
            result = await mcp.call_tool(
                "get_legal_act_text", {"publisher": "DU", "year": 2024, "position": 1673}
            )
            text = _text(result)
            assert "Art. 1." in text
            assert "<p>" not in text


class TestGetLegalActByEliTool:
    @pytest.mark.anyio
    async def test_valid_eli(self, isap_act_detail, isap_references):
        mock = AsyncMock(return_value=(isap_act_detail, isap_references))
        with patch("law_mcp.server.isap.get_act_with_references", mock):
            result = await mcp.call_tool("get_legal_act_by_eli", {"eli": "DU/2024/1673"})
            text = _text(result)
            assert "Kodeks" in text

    @pytest.mark.anyio
    async def test_invalid_eli(self):
        result = await mcp.call_tool("get_legal_act_by_eli", {"eli": "invalid"})
        text = _text(result)
        assert "Invalid ELI format" in text


class TestToolListing:
    @pytest.mark.anyio
    async def test_all_tools_registered(self):
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert names == {
            "search_judgments",
            "get_judgment",
            "search_legal_acts",
            "get_legal_act",
            "get_legal_act_text",
            "get_legal_act_by_eli",
        }
