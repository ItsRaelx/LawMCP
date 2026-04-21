from law_mcp.formatting import (
    format_act_detail,
    format_act_search_results,
    format_judgment_detail,
    format_judgment_search_results,
    html_to_text,
    truncate,
)


class TestHtmlToText:
    def test_strips_tags(self):
        assert html_to_text("<p>hello</p>") == "hello"

    def test_br_becomes_newline(self):
        assert "hello\nworld" in html_to_text("hello<br>world")

    def test_br_self_closing(self):
        assert "hello\nworld" in html_to_text("hello<br/>world")

    def test_p_closing_becomes_double_newline(self):
        result = html_to_text("<p>first</p><p>second</p>")
        assert "first" in result
        assert "second" in result

    def test_unescapes_entities(self):
        assert html_to_text("&amp; &lt; &gt;") == "& < >"

    def test_collapses_whitespace(self):
        result = html_to_text("<p>  lots   of   spaces  </p>")
        assert "  " not in result

    def test_empty_string(self):
        assert html_to_text("") == ""

    def test_nested_tags(self):
        result = html_to_text("<div><p><b>bold</b> text</p></div>")
        assert "bold text" in result


class TestTruncate:
    def test_short_text_unchanged(self):
        assert truncate("hello", 100) == "hello"

    def test_long_text_truncated(self):
        result = truncate("a" * 200, 50)
        assert len(result) == 50
        assert result.endswith("[...truncated...]")

    def test_exact_length_unchanged(self):
        text = "a" * 50
        assert truncate(text, 50) == text

    def test_custom_suffix(self):
        result = truncate("a" * 100, 20, suffix="...")
        assert result.endswith("...")
        assert len(result) == 20


class TestFormatJudgmentSearchResults:
    def test_formats_results(self, saos_search_response):
        result = format_judgment_search_results(saos_search_response)
        assert "Found 1 judgments" in result
        assert "12345" in result
        assert "II K 123/24" in result
        assert "2024-03-15" in result
        assert "COMMON" in result

    def test_empty_results(self):
        data = {"items": [], "info": {"totalResults": 0}}
        result = format_judgment_search_results(data)
        assert "No judgments found" in result


class TestFormatJudgmentDetail:
    def test_formats_detail(self, saos_judgment_detail):
        data = saos_judgment_detail["data"]
        result = format_judgment_detail(data)
        assert "II K 123/24" in result
        assert "2024-03-15" in result
        assert "Jan Kowalski" in result
        assert "PRESIDING_JUDGE" in result
        assert "Anna Nowak" in result
        assert "art. 278" in result
        assert "Kodeks karny" in result
        assert "WYROK" in result

    def test_minimal_data(self):
        result = format_judgment_detail({"judgmentDate": "2024-01-01"})
        assert "2024-01-01" in result


class TestFormatActSearchResults:
    def test_formats_results(self, isap_search_response):
        result = format_act_search_results(isap_search_response)
        assert "Found 1 legal acts" in result
        assert "Kodeks" in result
        assert "Dz.U. 2024 poz. 1673" in result
        assert "obowiązujący" in result

    def test_empty_results(self):
        data = {"count": 0, "items": [], "offset": 0}
        result = format_act_search_results(data)
        assert "No legal acts found" in result


class TestFormatActDetail:
    def test_formats_detail(self, isap_act_detail):
        result = format_act_detail(isap_act_detail)
        assert "Kodeks" in result
        assert "Ustawa" in result
        assert "obowiązujący" in result
        assert "DU/2024/1673" in result

    def test_with_references(self, isap_act_detail, isap_references):
        result = format_act_detail(isap_act_detail, isap_references)
        assert "References:" in result
        assert "Zmienia" in result
        assert "Zmieniony przez" in result

    def test_without_references(self, isap_act_detail):
        result = format_act_detail(isap_act_detail, None)
        assert "References:" not in result
