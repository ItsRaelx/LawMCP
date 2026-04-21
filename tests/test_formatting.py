from law_mcp.formatting import (
    format_act_detail,
    format_act_search_results,
    format_combined_case_law,
    format_combined_legislation,
    format_eu_case_law_results,
    format_eu_document_detail,
    format_eu_legislation_results,
    format_full_act,
    format_judgment_detail,
    format_judgment_search_results,
    format_legislative_process_results,
    html_to_text,
    pdf_to_text,
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


class TestPdfToText:
    def test_extracts_text(self):
        import pymupdf

        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Art. 1. Przepisy ogólne")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = pdf_to_text(pdf_bytes)
        assert "Art. 1. Przepisy ogólne" in result

    def test_multiple_pages(self):
        import pymupdf

        doc = pymupdf.open()
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Page one content")
        page2 = doc.new_page()
        page2.insert_text((72, 72), "Page two content")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = pdf_to_text(pdf_bytes)
        assert "Page one content" in result
        assert "Page two content" in result


class TestFormatFullAct:
    def test_includes_text(self, isap_act_detail, isap_references):
        result = format_full_act(isap_act_detail, isap_references, "<p>Art. 1. Przepisy ogólne</p>")
        assert "Kodeks" in result
        assert "References:" in result
        assert "--- Full text ---" in result
        assert "Art. 1. Przepisy ogólne" in result

    def test_without_text(self, isap_act_detail):
        result = format_full_act(isap_act_detail, None, "")
        assert "Kodeks" in result
        assert "--- Full text ---" not in result


class TestFormatEuLegislationResults:
    def test_formats_results(self):
        results = [
            {"celex": "32016R0679", "title": "GDPR Regulation", "date": "2016-04-27", "type": "REG"},
        ]
        output = format_eu_legislation_results(results)
        assert "Found 1 EU legislative acts" in output
        assert "32016R0679" in output
        assert "GDPR" in output
        assert "REG" in output

    def test_empty_results(self):
        assert "No EU legislation found" in format_eu_legislation_results([])


class TestFormatEuCaseLawResults:
    def test_formats_results(self):
        results = [
            {
                "celex": "62014CJ0362",
                "title": "Schrems v DPC",
                "date": "2015-10-06",
                "ecli": "ECLI:EU:C:2015:650",
            },
        ]
        output = format_eu_case_law_results(results)
        assert "Found 1 CJEU judgments" in output
        assert "62014CJ0362" in output
        assert "Schrems" in output
        assert "ECLI:EU:C:2015:650" in output

    def test_empty_results(self):
        assert "No EU case law found" in format_eu_case_law_results([])


class TestFormatEuDocumentDetail:
    def test_formats_detail(self):
        data = {
            "celex": "32016R0679",
            "title": "GDPR Regulation",
            "date": "2016-04-27",
            "type": "REG",
            "inForce": "INFORCE",
        }
        output = format_eu_document_detail(data)
        assert "32016R0679" in output
        assert "GDPR" in output
        assert "INFORCE" in output


class TestFormatLegislativeProcessResults:
    def test_formats_results(self, sejm_process_search_response):
        output = format_legislative_process_results(sejm_process_search_response)
        assert "Found 1 legislative processes" in output
        assert "Rządowy projekt" in output
        assert "2024-03-01" in output

    def test_empty_results(self):
        assert "No legislative processes found" in format_legislative_process_results([])


class TestFormatCombinedLegislation:
    def test_both_sources(self, isap_search_response):
        eu_data = [{"celex": "32016R0679", "title": "GDPR", "date": "2016-04-27", "type": "REG"}]
        output = format_combined_legislation(isap_search_response, eu_data)
        assert "Polish Legislation (ISAP)" in output
        assert "EU Legislation (EUR-Lex)" in output
        assert "Kodeks" in output
        assert "GDPR" in output

    def test_pl_only(self, isap_search_response):
        output = format_combined_legislation(isap_search_response, None)
        assert "Polish Legislation (ISAP)" in output
        assert "EU Legislation" not in output

    def test_eu_only(self):
        eu_data = [{"celex": "32016R0679", "title": "GDPR", "date": "2016-04-27", "type": "REG"}]
        output = format_combined_legislation(None, eu_data)
        assert "EU Legislation (EUR-Lex)" in output
        assert "Polish Legislation" not in output

    def test_with_errors(self, isap_search_response):
        output = format_combined_legislation(isap_search_response, None, ["EUR-Lex: timeout"])
        assert "Warnings:" in output
        assert "EUR-Lex: timeout" in output

    def test_no_results(self):
        output = format_combined_legislation(None, None)
        assert "No legislation found" in output

    def test_errors_only_shows_warnings(self):
        output = format_combined_legislation(None, None, ["EUR-Lex: timed out after 30s"])
        assert "Warnings:" in output
        assert "timed out" in output
        assert "No legislation found" in output


class TestFormatCombinedCaseLaw:
    def test_both_sources(self, saos_search_response):
        eu_data = [{"celex": "62014CJ0362", "title": "Schrems", "date": "2015-10-06", "ecli": "ECLI:EU:C:2015:650"}]
        output = format_combined_case_law(saos_search_response, eu_data)
        assert "Polish Case Law (SAOS)" in output
        assert "EU Case Law (CJEU)" in output

    def test_no_results(self):
        output = format_combined_case_law(None, None)
        assert "No case law found" in output

    def test_errors_only_shows_warnings(self):
        output = format_combined_case_law(None, None, ["CJEU: timed out after 30s"])
        assert "Warnings:" in output
        assert "timed out" in output
        assert "No case law found" in output
