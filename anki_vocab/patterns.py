"""Card markup patterns: how the back of a card looks, chosen by the term.

Each pattern has a color, an Anki tag, a rule (`matches`) that decides which
terms it applies to, and a template for the back of the card. The first pattern
in PATTERNS whose rule matches wins; GREEN_WORD matches everything, so it must
stay last.

To add a pattern, define it and put it in PATTERNS above the fallback:

    IDIOM = Pattern(
        name="blue_idiom",
        color="#2b6cb0",
        tag="idiom",
        matches=lambda term: term in KNOWN_IDIOMS,
    )
    PATTERNS = [IDIOM, SALMON_PHRASE, GREEN_WORD]

A pattern can also replace `template` (a different layout) or `highlight`
(how the term is marked inside example sentences).
"""

import re
from dataclasses import dataclass
from typing import Callable

# The back of the card, part by part. A part is rendered only when its value is
# non-empty, so a card without examples doesn't get stray <br> tags.
# Values arrive already HTML-escaped; examples arrive joined with <br> and with
# the term highlighted.
BACK_TEMPLATE = (
    ("translation", "{translation}<br>"),
    ("definition", '<p style="color: {color}"><b>{definition}</b></p><br>'),
    ("examples", "<i>{examples}</i><br><br>"),
    ("synonyms", "Synonyms: {synonyms}<br><br>"),
)

HIGHLIGHT = '<span style="color: {color}">{text}</span>'


@dataclass(frozen=True)
class Pattern:
    name: str
    color: str
    tag: str
    matches: Callable[[str], bool]
    template: tuple = BACK_TEMPLATE
    highlight: str = HIGHLIGHT

    def render(self, **values):
        return "".join(
            fmt.format(color=self.color, **values)
            for key, fmt in self.template
            if values.get(key)
        )

    def mark(self, text):
        return self.highlight.format(color=self.color, text=text)


def is_phrase(term):
    """Multi-word, hyphenated or slashed: 'take a stab at', 'uncalled-for', 'and/or'."""
    return bool(re.search(r"[\s\-/]", term.strip()))


SALMON_PHRASE = Pattern("salmon_phrase", "#ee7e68", "phrase", is_phrase)
GREEN_WORD = Pattern("green_word", "#359B28", "word", lambda term: True)  # fallback

PATTERNS = [SALMON_PHRASE, GREEN_WORD]


def pattern_for(term):
    return next(p for p in PATTERNS if p.matches(term))


def get(name):
    for p in PATTERNS:
        if p.name == name:
            return p
    raise KeyError(f"unknown pattern {name!r}; known: {', '.join(p.name for p in PATTERNS)}")
