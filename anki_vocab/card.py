"""Turn the data collected for one word into the front/back of an Anki card."""

from dataclasses import dataclass, field
from html import escape as _escape


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

    def has_content(self):
        # A "translation" that just echoes the word means the translator didn't know it.
        real_translation = self.translation and self.translation.lower() != self.word.lower()
        return bool(real_translation or self.short or self.long or self.definition)

    def front(self):
        return escape(self.word)

    def back(self):
        parts = []
        if self.translation:
            parts.append(f'<div style="color: darkred"><b>{escape(self.translation)}</b></div>')
        if self.definition:
            parts.append(f'<div style="color: darkblue"><b>{escape(self.definition)}</b></div>')
        if self.examples:
            items = "".join(f"<li><i>{escape(ex)}</i></li>" for ex in self.examples)
            parts.append(f"<ul>{items}</ul>")
        if self.short:
            parts.append(f"<p>{escape(self.short)}</p>")
        if self.long:
            parts.append(f'<p style="color: teal">{escape(self.long)}</p>')
        return "".join(parts)
