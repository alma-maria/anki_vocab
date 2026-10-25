"""Write cards as a CSV file that Anki (2.1.55+) imports without extra setup.

The leading "#key:value" lines are Anki file headers: they tell the importer
the separator, that fields contain HTML, the column names and the tags.
"""

import csv
import hashlib

import genanki

# Fixed IDs: Anki identifies note types and decks by ID, so keeping them stable
# means re-importing updates the same note type/deck instead of creating copies.
MODEL_ID = 1735910211

MODEL = genanki.Model(
    MODEL_ID,
    "anki_vocab",
    fields=[{"name": "Front"}, {"name": "Back"}],
    templates=[{
        "name": "Card 1",
        "qfmt": '<div class="word">{{Front}}</div>',
        "afmt": '{{FrontSide}}<hr id="answer">{{Back}}',
    }],
    css=(
        ".card { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 18px;"
        " text-align: left; color: black; background-color: white; }\n"
        ".word { font-size: 28px; text-align: center; }\n"
        ".nightMode .card { color: #eee; background-color: #2f2f31; }"
    ),
)


def _deck_id(name):
    # Same deck name -> same ID, so a re-import lands in the existing deck.
    return int(hashlib.sha1(name.encode()).hexdigest()[:8], 16) | (1 << 31)


def write_apkg(cards, path, deck_name="Vocabulary", tags="vocab"):
    deck = genanki.Deck(_deck_id(deck_name), deck_name)
    tag_list = tags.split() if tags else []
    for card in cards:
        deck.add_note(genanki.Note(
            model=MODEL,
            fields=[card.front(), card.back()],
            tags=tag_list,
            guid=genanki.guid_for(card.word),  # re-import updates instead of duplicating
        ))
    genanki.Package(deck).write_to_file(str(path))


def write_anki_csv(cards, path, tags="vocab"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write("#separator:Comma\n")
        f.write("#html:true\n")
        f.write("#columns:Front,Back\n")
        if tags:
            f.write(f"#tags:{tags}\n")
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for card in cards:
            writer.writerow([card.front(), card.back()])


def write_errors(errors, path):
    """errors: list of (word, source, message)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "source", "error"])
        writer.writerows(errors)
