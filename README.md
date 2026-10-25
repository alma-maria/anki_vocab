# anki_vocab

Turns a list of up to 100 English words into an Anki deck: a ready `.apkg` package or a CSV for Anki's text import.

Each card:
- **Front:** the word
- **Back:** Russian translation, Cambridge definition, 2 examples with the word highlighted, 3 synonyms
- **More:** vocabulary.com short and long descriptions (when the site has them)

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Google Chrome must be installed (vocabulary.com is read through a real browser).

## Usage

```sh
.venv/bin/python -m anki_vocab words.txt --deck test          # -> output/test/test.apkg
.venv/bin/python -m anki_vocab words.txt --format both        # -> output/words/words.apkg + words.csv
.venv/bin/python -m anki_vocab words.txt --headless --tags "vocab book1"
echo "timid, zilch" | .venv/bin/python -m anki_vocab - --no-vocabulary
.venv/bin/python -m anki_vocab --list-patterns
```

Input: one word per line or comma-separated; `#` starts a comment; duplicates are dropped.

Each run writes into its own folder, `<out-dir>/<deck>/`:

| File | |
|---|---|
| `<deck>.apkg` / `<deck>.csv` | the deck (`--format apkg`, `csv` or `both`; default `apkg`) |
| `words.txt` | the words used |
| `errors.csv` | lookups that failed (only when there were some) |

Running the same deck name again overwrites that folder's files.

| Option | |
|---|---|
| `--deck NAME` | deck and folder name (default: the input file name, `cards` for stdin) |
| `--out-dir DIR` | parent folder (default: `output`) |
| `--format` | `apkg`, `csv` or `both` |
| `--tags` | tags for every card (space-separated; default `vocab`) |
| `--no-vocabulary`, `--no-cambridge`, `--no-translate`, `--no-synonyms` | skip a source |
| `--headless` | run Chrome without a window |
| `--list-patterns` | show the color patterns |

A word is skipped only if no source knows it.

## Patterns

The term on the front decides the card's color pattern (`anki_vocab/patterns.py`):

| Pattern | Color | Tag | Used for |
|---|---|---|---|
| `salmon_phrase` | `#ee7e68` | `phrase` | terms with a space, `-` or `/`: *take a stab at*, *uncalled-for* |
| `green_word` | `#359B28` | `word` | everything else: *dazed* |

The color is used for the definition and for the term inside the examples.
Placeholders like `someone/something` are ignored when highlighting.

To add a pattern, define it and put it in `PATTERNS` above `GREEN_WORD` (the fallback):

```python
IDIOM = Pattern("blue_idiom", "#2b6cb0", "idiom", matches=lambda term: term in KNOWN_IDIOMS)
PATTERNS = [IDIOM, SALMON_PHRASE, GREEN_WORD]
```

A pattern can also set its own `template` (layout of the back) or `highlight`.

## Sources

- **Translation:** Google Translate; when Google blocks the IP, MyMemory (only close, rated matches are kept)
- **Definition and examples:** Cambridge Dictionary
- **Synonyms:** Datamuse (`rel_syn`, falling back to "means like" for phrases)
- **More:** vocabulary.com

## Importing into Anki

**.apkg:** double-click the file, or File → Import. It creates the deck and an
`anki_vocab` note type (Front / Back / More). Re-importing a regenerated deck updates
existing cards (each note's ID is derived from its word) instead of duplicating them.

**.csv:** File → Import → pick the CSV. The header lines set the separator, HTML,
columns (Front, Back, More, Tags) and the tags column automatically (Anki 2.1.55+).
Pick a note type with three fields.

## Tests

```sh
.venv/bin/python -m pytest
```
