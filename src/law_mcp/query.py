import re

_STOP_WORDS = frozenset({
    # Polish
    "i", "w", "z", "na", "do", "za", "od", "po", "nie", "się", "jest",
    "to", "że", "jak", "ale", "lub", "dla", "przy", "przez", "jako", "ich",
    "tym", "tej", "ten", "tego", "które", "która", "który", "oraz", "tak",
    "już", "tylko", "czy", "też", "może", "co", "gdy", "tego", "być",
    # English
    "the", "and", "or", "in", "on", "of", "for", "to", "is", "are",
    "was", "were", "be", "been", "have", "has", "had", "with", "at",
    "by", "from", "as", "into", "about", "between", "through", "an",
})

MIN_WORD_LEN = 3
MAX_TOKENS = 6


def tokenize(text: str | None) -> list[str]:
    """Split text into meaningful search tokens.

    Removes stop words and very short words. Returns at most MAX_TOKENS words,
    lowercased and deduplicated while preserving order.
    """
    if not text:
        return []
    words = re.findall(r"\w+", text.lower(), re.UNICODE)
    seen: set[str] = set()
    tokens: list[str] = []
    for w in words:
        if len(w) >= MIN_WORD_LEN and w not in _STOP_WORDS and w not in seen:
            seen.add(w)
            tokens.append(w)
        if len(tokens) >= MAX_TOKENS:
            break
    return tokens
