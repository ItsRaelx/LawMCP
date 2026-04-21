import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from law_mcp.server import mcp


def _text(result: tuple) -> str:
    content_list, _ = result
    return content_list[0].text


class TestSearchLegislationTool:
    @pytest.mark.anyio
    async def test_both_sources(self, isap_search_response):
        eu_results = [{"celex": "32016R0679", "title": "GDPR", "date": "2016-04-27", "type": "REG"}]
        with (
            patch("law_mcp.server.isap.search_acts", AsyncMock(return_value=isap_search_response)),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=eu_results)),
        ):
            result = await mcp.call_tool("search_legislation", {"query": "data protection"})
            text = _text(result)
            assert "Polish Legislation (ISAP)" in text
            assert "EU Legislation (EUR-Lex)" in text

    @pytest.mark.anyio
    async def test_pl_only(self, isap_search_response):
        with patch("law_mcp.server.isap.search_acts", AsyncMock(return_value=isap_search_response)):
            result = await mcp.call_tool("search_legislation", {"query": "kodeks", "source": "PL"})
            text = _text(result)
            assert "Polish Legislation (ISAP)" in text
            assert "EU Legislation" not in text

    @pytest.mark.anyio
    async def test_eu_only(self):
        eu_results = [{"celex": "32016R0679", "title": "GDPR", "date": "2016-04-27", "type": "REG"}]
        with patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=eu_results)):
            result = await mcp.call_tool("search_legislation", {"query": "data", "source": "EU"})
            text = _text(result)
            assert "EU Legislation (EUR-Lex)" in text
            assert "Polish Legislation" not in text

    @pytest.mark.anyio
    async def test_partial_failure(self, isap_search_response):
        from law_mcp.eurlex import APIError

        with (
            patch("law_mcp.server.isap.search_acts", AsyncMock(return_value=isap_search_response)),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(side_effect=APIError("timeout"))),
        ):
            result = await mcp.call_tool("search_legislation", {"query": "kodeks"})
            text = _text(result)
            assert "Polish Legislation (ISAP)" in text
            assert "Warnings:" in text
            assert "EUR-Lex" in text

    @pytest.mark.anyio
    async def test_in_force_default_false(self, isap_search_response):
        mock_isap = AsyncMock(return_value=isap_search_response)
        mock_eu = AsyncMock(return_value=[])
        with (
            patch("law_mcp.server.isap.search_acts", mock_isap),
            patch("law_mcp.server.eurlex.search_legislation", mock_eu),
        ):
            await mcp.call_tool("search_legislation", {"query": "test"})
            mock_isap.assert_called_once()
            assert mock_isap.call_args.kwargs["in_force"] is False
            assert mock_eu.call_args.kwargs["in_force"] is False

    @pytest.mark.anyio
    async def test_in_force_filter(self, isap_search_response):
        mock_isap = AsyncMock(return_value=isap_search_response)
        mock_eu = AsyncMock(return_value=[])
        with (
            patch("law_mcp.server.isap.search_acts", mock_isap),
            patch("law_mcp.server.eurlex.search_legislation", mock_eu),
        ):
            await mcp.call_tool("search_legislation", {"query": "test", "in_force": True})
            assert mock_isap.call_args.kwargs["in_force"] is True
            assert mock_eu.call_args.kwargs["in_force"] is True

    @pytest.mark.anyio
    async def test_timeout_returns_partial(self, isap_search_response):
        async def slow_eurlex(**kwargs):
            await asyncio.sleep(30)

        with (
            patch("law_mcp.server.isap.search_acts", AsyncMock(return_value=isap_search_response)),
            patch("law_mcp.server.eurlex.search_legislation", slow_eurlex),
            patch("law_mcp.server.SEARCH_TIMEOUT", 0.1),
        ):
            result = await mcp.call_tool("search_legislation", {"query": "test"})
            text = _text(result)
            assert "Polish Legislation (ISAP)" in text
            assert "timed out" in text


    @pytest.mark.anyio
    async def test_no_expansion_when_original_has_results(self):
        """When original query returns results, do NOT expand to individual words."""
        act1 = {"address": "WDU20240001673", "title": "Kodeks postępowania administracyjnego"}
        titles_queried = []

        async def mock_search(**kwargs):
            titles_queried.append(kwargs.get("title"))
            title = kwargs.get("title", "")
            if "kodeks postępowania" in title.lower():
                return {"items": [act1], "count": 1, "totalCount": 1, "offset": 0}
            return {"items": [], "count": 0, "totalCount": 0, "offset": 0}

        with (
            patch("law_mcp.server.isap.search_acts", mock_search),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=[])),
        ):
            result = await mcp.call_tool(
                "search_legislation",
                {"query": "kodeks postępowania", "source": "PL"},
            )
            text = _text(result)
            assert "WDU20240001673" in text
            # Only the original query should have been sent, no word expansion
            assert titles_queried == ["kodeks postępowania"]

    @pytest.mark.anyio
    async def test_expansion_fallback_when_no_results(self):
        """When original query returns 0 results, expands to individual words."""
        act1 = {"address": "WDU20240001673", "title": "Kodeks postępowania administracyjnego"}
        act2 = {"address": "WDU20240001111", "title": "Kodeks cywilny"}

        async def mock_search(**kwargs):
            title = kwargs.get("title", "")
            # Full phrase returns nothing
            if "kodeks postępowania" == title.lower():
                return {"items": [], "count": 0, "totalCount": 0, "offset": 0}
            if title.lower() == "kodeks":
                return {"items": [act1, act2], "count": 2, "totalCount": 2, "offset": 0}
            if title.lower() == "postępowania":
                return {"items": [act1], "count": 1, "totalCount": 1, "offset": 0}
            return {"items": [], "count": 0, "totalCount": 0, "offset": 0}

        with (
            patch("law_mcp.server.isap.search_acts", mock_search),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=[])),
        ):
            result = await mcp.call_tool(
                "search_legislation",
                {"query": "kodeks postępowania", "source": "PL"},
            )
            text = _text(result)
            # Expanded search found results from individual words
            assert "WDU20240001673" in text
            assert "WDU20240001111" in text

    @pytest.mark.anyio
    async def test_keyword_fallback(self):
        """When combined keywords return 0, relaxes to individual keywords."""
        act = {"address": "WDU20240001673", "title": "Kodeks karny"}

        async def mock_search(**kwargs):
            kw = kwargs.get("keywords")
            # Combined keywords return nothing
            if kw and "," in kw:
                return {"items": [], "count": 0, "totalCount": 0, "offset": 0}
            # Individual keyword works
            if kw == "prawo karne":
                return {"items": [act], "count": 1, "totalCount": 1, "offset": 0}
            return {"items": [], "count": 0, "totalCount": 0, "offset": 0}

        with (
            patch("law_mcp.server.isap.search_acts", mock_search),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=[])),
        ):
            result = await mcp.call_tool(
                "search_legislation",
                {"keywords": "prawo karne, kradzież", "source": "PL"},
            )
            text = _text(result)
            assert "WDU20240001673" in text

    @pytest.mark.anyio
    async def test_publisher_and_act_type_passed(self, isap_search_response):
        mock_isap = AsyncMock(return_value=isap_search_response)
        with (
            patch("law_mcp.server.isap.search_acts", mock_isap),
            patch("law_mcp.server.eurlex.search_legislation", AsyncMock(return_value=[])),
        ):
            await mcp.call_tool(
                "search_legislation",
                {"query": "test", "publisher": "DU", "act_type": "Ustawa", "source": "PL"},
            )
            mock_isap.assert_called()
            call_kwargs = mock_isap.call_args.kwargs
            assert call_kwargs["publisher"] == "DU"
            assert call_kwargs["act_type"] == "Ustawa"

    @pytest.mark.anyio
    async def test_doc_type_passed_to_eurlex(self):
        mock_eurlex = AsyncMock(return_value=[])
        with patch("law_mcp.server.eurlex.search_legislation", mock_eurlex):
            await mcp.call_tool(
                "search_legislation",
                {"query": "test", "doc_type": "regulation", "source": "EU"},
            )
            mock_eurlex.assert_called_once()
            assert mock_eurlex.call_args.kwargs["doc_type"] == "regulation"


class TestReadActTool:
    @pytest.mark.anyio
    async def test_by_eli(self, isap_act_detail, isap_references):
        mock = AsyncMock(return_value=(isap_act_detail, isap_references, "<p>Art. 1.</p>"))
        with patch("law_mcp.server.isap.get_act_full", mock):
            result = await mcp.call_tool("read_act", {"eli": "DU/2024/1673"})
            text = _text(result)
            assert "Kodeks" in text
            assert "Art. 1." in text

    @pytest.mark.anyio
    async def test_by_publisher_year_position(self, isap_act_detail, isap_references):
        mock = AsyncMock(return_value=(isap_act_detail, isap_references, ""))
        with patch("law_mcp.server.isap.get_act_full", mock):
            result = await mcp.call_tool(
                "read_act", {"publisher": "DU", "year": 2024, "position": 1673}
            )
            text = _text(result)
            assert "Kodeks" in text

    @pytest.mark.anyio
    async def test_invalid_eli(self):
        result = await mcp.call_tool("read_act", {"eli": "invalid"})
        text = _text(result)
        assert "Invalid ELI format" in text

    @pytest.mark.anyio
    async def test_missing_params(self):
        result = await mcp.call_tool("read_act", {})
        text = _text(result)
        assert "Provide either" in text


class TestSearchCaseLawTool:
    @pytest.mark.anyio
    async def test_both_sources(self, saos_search_response):
        eu_results = [{"celex": "62014CJ0362", "title": "Schrems", "date": "2015-10-06", "ecli": "ECLI:EU:C:2015:650"}]
        with (
            patch("law_mcp.server.saos.search_judgments", AsyncMock(return_value=saos_search_response)),
            patch("law_mcp.server.eurlex.search_cjeu_cases", AsyncMock(return_value=eu_results)),
        ):
            result = await mcp.call_tool("search_case_law", {"query": "data protection"})
            text = _text(result)
            assert "Polish Case Law (SAOS)" in text
            assert "EU Case Law (CJEU)" in text

    @pytest.mark.anyio
    async def test_partial_failure(self, saos_search_response):
        from law_mcp.eurlex import APIError

        with (
            patch("law_mcp.server.saos.search_judgments", AsyncMock(return_value=saos_search_response)),
            patch("law_mcp.server.eurlex.search_cjeu_cases", AsyncMock(side_effect=APIError("timeout"))),
        ):
            result = await mcp.call_tool("search_case_law", {"query": "test"})
            text = _text(result)
            assert "Polish Case Law (SAOS)" in text
            assert "Warnings:" in text

    @pytest.mark.anyio
    async def test_judgment_type_passed(self, saos_search_response):
        mock_saos = AsyncMock(return_value=saos_search_response)
        with (
            patch("law_mcp.server.saos.search_judgments", mock_saos),
            patch("law_mcp.server.eurlex.search_cjeu_cases", AsyncMock(return_value=[])),
        ):
            await mcp.call_tool(
                "search_case_law",
                {"query": "test", "judgment_type": "SENTENCE", "source": "PL"},
            )
            mock_saos.assert_called_once()
            assert mock_saos.call_args.kwargs["judgment_type"] == "SENTENCE"


class TestReadJudgmentTool:
    @pytest.mark.anyio
    async def test_returns_detail(self, saos_judgment_detail):
        mock = AsyncMock(return_value=saos_judgment_detail["data"])
        with patch("law_mcp.server.saos.get_judgment", mock):
            result = await mcp.call_tool("read_judgment", {"judgment_id": 12345})
            text = _text(result)
            assert "Jan Kowalski" in text
            assert "WYROK" in text

    @pytest.mark.anyio
    async def test_api_error(self):
        from law_mcp.saos import APIError

        mock = AsyncMock(side_effect=APIError("SAOS API returned 404", 404))
        with patch("law_mcp.server.saos.get_judgment", mock):
            result = await mcp.call_tool("read_judgment", {"judgment_id": 99999})
            text = _text(result)
            assert "Error" in text


class TestReadEuDocumentTool:
    @pytest.mark.anyio
    async def test_returns_detail(self):
        doc = {"celex": "32016R0679", "title": "GDPR Regulation", "type": "REG", "date": "2016-04-27"}
        with patch("law_mcp.server.eurlex.get_document_by_celex", AsyncMock(return_value=doc)):
            result = await mcp.call_tool("read_eu_document", {"celex": "32016R0679"})
            text = _text(result)
            assert "32016R0679" in text
            assert "GDPR" in text

    @pytest.mark.anyio
    async def test_not_found(self):
        from law_mcp.eurlex import APIError

        mock = AsyncMock(side_effect=APIError("No document found for CELEX: INVALID", 404))
        with patch("law_mcp.server.eurlex.get_document_by_celex", mock):
            result = await mcp.call_tool("read_eu_document", {"celex": "INVALID"})
            text = _text(result)
            assert "Error" in text


class TestSearchLegislativeProcessTool:
    @pytest.mark.anyio
    async def test_returns_results(self, sejm_process_search_response):
        mock = AsyncMock(return_value=sejm_process_search_response)
        with patch("law_mcp.server.sejm.search_processes", mock):
            result = await mcp.call_tool("search_legislative_process", {"title": "kodeks"})
            text = _text(result)
            assert "Found 1 legislative processes" in text
            assert "Rządowy projekt" in text

    @pytest.mark.anyio
    async def test_api_error(self):
        from law_mcp.sejm import APIError

        mock = AsyncMock(side_effect=APIError("Sejm API returned 503", 503))
        with patch("law_mcp.server.sejm.search_processes", mock):
            result = await mcp.call_tool("search_legislative_process", {"title": "test"})
            text = _text(result)
            assert "Error" in text


class TestToolListing:
    @pytest.mark.anyio
    async def test_all_tools_registered(self):
        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        assert names == {
            "search_legislation",
            "read_act",
            "search_case_law",
            "read_judgment",
            "read_eu_document",
            "search_legislative_process",
        }
