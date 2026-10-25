"""Definition and example sentences from the Cambridge Dictionary."""

import re

import requests
from bs4 import BeautifulSoup

URL = "https://dictionary.cambridge.org/dictionary/english/{word}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/141.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def lookup(word, max_examples=2, session=None):
    """Return {"definition": str, "examples": [str, ...]}.

    Raises LookupError if Cambridge has no entry for the word.
    """
    http = session or requests
    response = http.get(URL.format(word=word), headers=HEADERS, timeout=15)
    response.raise_for_status()
    return parse(response.text, max_examples)


def parse(html, max_examples=2):
    soup = BeautifulSoup(html, "html.parser")
    definition = soup.select_one("div.def.ddef_d")
    if definition is None:
        raise LookupError("no entry on Cambridge")
    examples = [_clean(ex.get_text(" ", strip=True)) for ex in soup.select("div.examp.dexamp")]
    return {
        # Cambridge definitions end with a colon that introduces the examples.
        "definition": _clean(definition.get_text(" ", strip=True)).rstrip(" :"),
        "examples": examples[:max_examples],
    }


def _clean(text):
    # Joining the inner <a>/<span> tags with spaces leaves gaps before punctuation.
    return re.sub(r"\s+([.,;:!?)])", r"\1", " ".join(text.split()))
