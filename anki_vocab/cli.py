"""Command line entry point: words in, Anki deck out.

    python -m anki_vocab words.txt --deck test      ->  output/test/test.apkg
"""

import argparse
import re
import sys
from contextlib import nullcontext
from pathlib import Path

import requests

from anki_vocab.card import Card
from anki_vocab.export import write_anki_csv, write_apkg, write_errors
from anki_vocab.patterns import PATTERNS
from anki_vocab.sources import cambridge, synonyms, translate
from anki_vocab.sources.vocabulary_com import VocabularyCom

MAX_WORDS = 100


def read_words(text):
    """Split on newlines/commas/semicolons, drop blanks and '#' comments, dedupe keeping order."""
    words = []
    for line in text.splitlines():
        line = line.split("#", 1)[0]
        for raw in re.split(r"[,;]", line):
            word = raw.strip().lower()
            if word and word not in words:
                words.append(word)
    return words


def build_cards(words, use_vocab=True, use_cambridge=True, use_translate=True, use_synonyms=True,
                headless=False, log=print):
    cards, errors = [], []
    scraper = VocabularyCom(headless=headless) if use_vocab else nullcontext()
    session = requests.Session()

    with scraper:
        for i, word in enumerate(words, 1):
            log(f"[{i}/{len(words)}] {word}")
            card = Card(word)

            if use_translate:
                try:
                    card.translation = translate.lookup(word)
                except Exception as e:
                    errors.append((word, "translate", _msg(e)))
            if use_cambridge:
                try:
                    found = cambridge.lookup(word, session=session)
                    card.definition, card.examples = found["definition"], found["examples"]
                except Exception as e:
                    errors.append((word, "cambridge", _msg(e)))
            if use_synonyms:
                try:
                    card.synonyms = synonyms.lookup(word, session=session)
                except Exception as e:
                    errors.append((word, "synonyms", _msg(e)))
            if use_vocab:
                try:
                    found = scraper.lookup(word)
                    card.short, card.long = found["short"], found["long"]
                except Exception as e:
                    errors.append((word, "vocabulary.com", _msg(e)))

            if card.has_content():
                cards.append(card)
            else:
                log("    skipped: nothing found")
    return cards, errors


def _msg(exc):
    # Selenium messages carry a long stacktrace after the first line.
    return str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__


def safe_dir_name(name):
    """Deck name -> folder name: replace characters macOS/Windows/Linux don't allow."""
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")
    return cleaned or "deck"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="anki_vocab", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", help="text file with words (one per line or comma-separated); '-' for stdin")
    parser.add_argument("--deck", help="deck name; also the output folder name (default: the input file name)")
    parser.add_argument("--out-dir", default="output", help="parent folder for deck folders (default: %(default)s)")
    parser.add_argument("--format", choices=["apkg", "csv", "both"], default="apkg",
                        help="apkg = ready deck, csv = Anki text import (default: %(default)s)")
    parser.add_argument("--tags", default="vocab", help="Anki tags for every card (space-separated)")
    parser.add_argument("--no-vocabulary", action="store_true", help="skip vocabulary.com (no browser needed)")
    parser.add_argument("--no-cambridge", action="store_true", help="skip Cambridge Dictionary")
    parser.add_argument("--no-translate", action="store_true", help="skip Russian translation")
    parser.add_argument("--no-synonyms", action="store_true", help="skip Datamuse synonyms")
    parser.add_argument("--headless", action="store_true", help="run Chrome without a window")
    parser.add_argument("--list-patterns", action="store_true", help="show the card color patterns and exit")
    args = parser.parse_args(argv)

    if args.list_patterns:
        for p in PATTERNS:
            print(f"{p.name:<16} {p.color}  tag: {p.tag}")
        return 0
    if args.input is None:
        parser.error("the input file is required")

    text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    words = read_words(text)
    if not words:
        parser.error("no words found in input")
    if len(words) > MAX_WORDS:
        parser.error(f"{len(words)} words given; the limit is {MAX_WORDS}")

    deck = args.deck or ("cards" if args.input == "-" else Path(args.input).stem)
    folder = Path(args.out_dir) / safe_dir_name(deck)
    folder.mkdir(parents=True, exist_ok=True)

    cards, errors = build_cards(
        words,
        use_vocab=not args.no_vocabulary,
        use_cambridge=not args.no_cambridge,
        use_translate=not args.no_translate,
        use_synonyms=not args.no_synonyms,
        headless=args.headless,
    )

    written = []
    if args.format in ("apkg", "both"):
        written.append(folder / f"{safe_dir_name(deck)}.apkg")
        write_apkg(cards, written[-1], deck_name=deck, tags=args.tags)
    if args.format in ("csv", "both"):
        written.append(folder / f"{safe_dir_name(deck)}.csv")
        write_anki_csv(cards, written[-1], tags=args.tags)
    (folder / "words.txt").write_text("\n".join(words) + "\n", encoding="utf-8")

    err_path = folder / "errors.csv"
    if errors:
        write_errors(errors, err_path)
    elif err_path.exists():
        err_path.unlink()  # stale from a previous run of this deck

    print(f"\n{len(cards)}/{len(words)} cards written to {', '.join(map(str, written))}")
    if errors:
        print(f"{len(errors)} lookup problems logged to {err_path}")
    return 0
