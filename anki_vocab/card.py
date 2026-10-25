"""Turn the data collected for one word into the fields of an Anki card."""

import re
from dataclasses import dataclass, field
from html import escape as _escape

from anki_vocab.patterns import Pattern, pattern_for

# Dictionary placeholders that don't appear in real sentences:
# "steer clear of someone/something" is highlighted as "steer clear of".
PLACEHOLDERS = {"someone", "something", "somebody", "somewhere", "sb", "sth",
                "someone's", "somebody's", "one's"}


def escape(text):
    return _escape(text, quote=False)


@dataclass
class Card:
    word: str
    translation: str = ""
    short: str = ""
    long: str = ""
    definition: str = ""
    examples: list = field(default_factory=list)
    synonyms: list = field(default_factory=list)
    pattern: Pattern = None

    def __post_init__(self):
        if self.pattern is None:
            self.pattern = pattern_for(self.word)

    def has_content(self):
        # A "translation" that just echoes the word means the translator didn't know it.
        real_translation = self.translation and self.translation.lower() != self.word.lower()
        return bool(real_translation or self.short or self.long or self.definition)

    def front(self):
        return escape(self.word)

    def back(self):
        return self.pattern.render(
            translation=escape(self.translation),
            definition=escape(self.definition),
            examples="<br>".join(self._highlight(escape(ex)) for ex in self.examples),
            synonyms=escape(", ".join(self.synonyms)),
        )

    def more(self):
        return "<br>".join(escape(part) for part in (self.short, self.long) if part)

    def _highlight(self, example):
        term = highlight_term(self.word)
        if not term:
            return example
        # Any run of whitespace in the term matches any whitespace in the sentence.
        regex = r"\s+".join(re.escape(escape(w)) for w in term.split())
        return re.sub(rf"(?<!\w)({regex})(?!\w)", lambda m: self.pattern.mark(m.group(1)),
                      example, flags=re.IGNORECASE)


def highlight_term(word):
    """The part of a headword to look for in example sentences (placeholders removed)."""
    kept = [w for w in word.split()
            if not all(part.lower() in PLACEHOLDERS for part in w.split("/"))]
    return " ".join(kept)
