from law_mcp.query import tokenize


class TestTokenize:
    def test_basic_split(self):
        assert tokenize("Digital Services Act") == ["digital", "services", "act"]

    def test_removes_stop_words_polish(self):
        result = tokenize("ustawa o ochronie danych")
        assert result == ["ustawa", "ochronie", "danych"]

    def test_removes_stop_words_english(self):
        result = tokenize("regulation of the European Parliament")
        assert result == ["regulation", "european", "parliament"]

    def test_removes_short_words(self):
        result = tokenize("ab cd efg")
        assert result == ["efg"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_none(self):
        assert tokenize(None) == []

    def test_single_word(self):
        assert tokenize("kodeks") == ["kodeks"]

    def test_max_tokens_cap(self):
        result = tokenize("one two three four five six seven eight nine ten")
        assert len(result) <= 6

    def test_unicode_polish(self):
        result = tokenize("kodeks postępowania administracyjnego")
        assert "kodeks" in result
        assert "postępowania" in result
        assert "administracyjnego" in result

    def test_deduplicates(self):
        result = tokenize("test test test other")
        assert result == ["test", "other"]

    def test_all_stop_words_returns_empty(self):
        assert tokenize("i w z na do") == []

    def test_mixed_case(self):
        result = tokenize("GDPR Regulation")
        assert result == ["gdpr", "regulation"]
