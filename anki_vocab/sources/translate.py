"""English -> Russian translation.

Google Translate is tried first. It sometimes blocks an IP with a CAPTCHA
(HTTP 429); then MyMemory is used instead (free, lower quality, ~5000 chars/day).
"""

from deep_translator import GoogleTranslator, MyMemoryTranslator

_google = GoogleTranslator(source="en", target="ru")
_mymemory = MyMemoryTranslator(source="en-GB", target="ru-RU")
_google_blocked = False


def lookup(word):
    global _google_blocked
    if not _google_blocked:
        try:
            result = _google.translate(word)
            if result:
                return result
        except Exception:
            _google_blocked = True  # don't keep hitting a blocked endpoint for every word
    result = _mymemory.translate(word)
    if not result:
        raise LookupError("no translation")
    return result
