"""Synonyms from the Datamuse API (free, no key).

`rel_syn` gives true synonyms but is empty for multi-word phrases, so
`ml` ("means like") is used as a fallback: "steer clear of" -> avoid, evade, shun.
"""

import requests

URL = "https://api.datamuse.com/words"


def lookup(word, max_results=3, session=None):
    http = session or requests
    for relation in ("rel_syn", "ml"):
        response = http.get(URL, params={relation: word, "max": max_results + 5}, timeout=15)
        response.raise_for_status()
        found = parse(response.json(), word, max_results)
        if found:
            return found
    raise LookupError("no synonyms on Datamuse")


def parse(data, word, max_results=3):
    results = []
    for item in data:
        candidate = item.get("word", "").strip()
        if candidate and candidate.lower() != word.lower() and candidate not in results:
            results.append(candidate)
    return results[:max_results]
