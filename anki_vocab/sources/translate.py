"""English -> Russian translation.

Google Translate is tried first. It sometimes blocks an IP with a CAPTCHA
(HTTP 429); then MyMemory is used instead (free, ~5000 chars/day).

MyMemory's top answer is often junk (a transliteration like "SOZNANIIA", or the
English word echoed back), so all its candidate matches are ranked instead and
only close, rated, Cyrillic ones are kept: "dazed" -> "изумленный".
"""

import html
import re

import requests
from deep_translator import GoogleTranslator

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
MIN_MATCH = 0.8  # how closely the memory's source text matches the word (0..1)

_google = GoogleTranslator(source="en", target="ru")
_google_blocked = False


def lookup(word, session=None):
    global _google_blocked
    if not _google_blocked:
        try:
            result = _google.translate(word)
            if result and _is_russian(result):
                return result
        except Exception:
            _google_blocked = True  # don't keep hitting a blocked endpoint for every word
    return _mymemory(word, session or requests)


def _mymemory(word, http):
    response = http.get(MYMEMORY_URL, params={"q": word, "langpair": "en|ru"}, timeout=15)
    response.raise_for_status()
    best = pick_match(response.json().get("matches", []))
    if best is None:
        raise LookupError("no reliable translation")
    # Memories are often capitalized sentences; a dictionary word reads better lowercase.
    return best[0].lower() + best[1:] if word.islower() else best


def pick_match(matches):
    candidates = []
    for m in matches:
        text = html.unescape(m.get("translation", "")).strip()
        quality = int(m.get("quality") or 0)
        match = float(m.get("match") or 0)
        if text and quality > 0 and match >= MIN_MATCH and _is_russian(text):
            candidates.append((quality, match, text))
    return max(candidates)[2] if candidates else None


def _is_russian(text):
    return bool(re.search(r"[а-яё]", text, re.IGNORECASE))
