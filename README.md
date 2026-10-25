# anki_vocab

Turns a list of up to 100 English words into a CSV that Anki imports directly.

Each card:
- **Front:** the word
- **Back:** Russian translation, Cambridge definition + 2 examples, vocabulary.com short and long descriptions

## Setup

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Google Chrome must be installed (vocabulary.com is read through a real browser).

## Usage

```sh
.venv/bin/python -m anki_vocab words.txt -o output/deck.csv
.venv/bin/python -m anki_vocab words.txt --headless --tags "vocab book1"
echo "timid, zilch" | .venv/bin/python -m anki_vocab - --no-vocabulary
```

Input: one word per line or comma-separated; `#` starts a comment; duplicates are dropped.
Options: `--no-vocabulary`, `--no-cambridge`, `--no-translate`, `--headless`, `--tags`.

Lookup failures are written to `<output>_errors.csv`. A word is skipped only if no source knows it.

## Importing into Anki

File → Import → pick the CSV. The header lines in the file set the separator,
HTML, field mapping (Front, Back) and tags automatically (Anki 2.1.55+).
Choose the **Basic** note type (or **Basic (and reversed card)**).

## Tests

```sh
.venv/bin/python -m pytest
```
