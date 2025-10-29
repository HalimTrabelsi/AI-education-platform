import re
from typing import Iterable

BAD_WORDS = {
    "merde",
    "putain",
    "connard",
    "idiot",
    "stupide",
    "fuck",
    "shit",
}

_BAD_WORDS_PATTERN = None


def _compile_pattern():
    global _BAD_WORDS_PATTERN
    if not BAD_WORDS:
        _BAD_WORDS_PATTERN = None
        return
    escaped = [re.escape(word) for word in BAD_WORDS if word]
    if not escaped:
        _BAD_WORDS_PATTERN = None
        return
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    _BAD_WORDS_PATTERN = re.compile(pattern, flags=re.IGNORECASE)


def mask_bad_words(message: str) -> str:
    """Replace each bad word by a masked variant (first letter + *)."""
    global _BAD_WORDS_PATTERN
    if _BAD_WORDS_PATTERN is None:
        _compile_pattern()
    if not _BAD_WORDS_PATTERN:
        return message

    def _replace(match: re.Match) -> str:
        token = match.group(0)
        if len(token) <= 2:
            return "*" * len(token)
        return token[0] + "*" * (len(token) - 2) + token[-1]

    return _BAD_WORDS_PATTERN.sub(_replace, message)


def extend_bad_words(words: Iterable[str]) -> None:
    """Allow dynamic extension of the bad words list."""
    global BAD_WORDS
    cleaned = {word.strip().lower() for word in words if word and word.strip()}
    if not cleaned:
        return
    BAD_WORDS.update(cleaned)
    _compile_pattern()
