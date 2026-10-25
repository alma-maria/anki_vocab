"""Command line entry point: words in, Anki CSV out.

    python -m anki_vocab words.txt -o output/deck.csv
"""

import argparse
import re
import sys
from contextlib import nullcontext
from pathlib import Path

import requests

from anki_vocab.card import Card
from anki_vocab.export import write_anki_csv, write_apkg, write_errors
from anki_vocab.sources import cambridge, translate
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


def build_cards(words, use_vocab=True, use_cambridge=True, use_translate=True, headless=False, log=print):
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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="anki_vocab", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="text file with words (one per line or comma-separated); '-' for stdin")
    parser.add_argument("-o", "--output", default="output/cards.csv",
                        help="output file: .csv for Anki's text import, .apkg for a ready deck (default: %(default)s)")
    parser.add_argument("--deck", help="deck name for .apkg output (default: the output file name)")
    parser.add_argument("--tags", default="vocab", help="Anki tags for every card (space-separated)")
    parser.add_argument("--no-vocabulary", action="store_true", help="skip vocabulary.com (no browser needed)")
    parser.add_argument("--no-cambridge", action="store_true", help="skip Cambridge Dictionary")
    parser.add_argument("--no-translate", action="store_true", help="skip Russian translation")
    parser.add_argument("--headless", action="store_true", help="run Chrome without a window")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    words = read_words(text)
    if not words:
        parser.error("no words found in input")
    if len(words) > MAX_WORDS:
        parser.error(f"{len(words)} words given; the limit is {MAX_WORDS}")

    cards, errors = build_cards(
        words,
        use_vocab=not args.no_vocabulary,
        use_cambridge=not args.no_cambridge,
        use_translate=not args.no_translate,
        headless=args.headless,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() == ".apkg":
        write_apkg(cards, out, deck_name=args.deck or out.stem, tags=args.tags)
    else:
        write_anki_csv(cards, out, tags=args.tags)
    print(f"\n{len(cards)}/{len(words)} cards written to {out}")
    if errors:
        err_path = out.with_name(out.stem + "_errors.csv")
        write_errors(errors, err_path)
        print(f"{len(errors)} lookup problems logged to {err_path}")
    return 0
