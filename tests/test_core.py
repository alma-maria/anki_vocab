import csv

import pytest

from anki_vocab.card import Card
from anki_vocab.cli import main, read_words
from anki_vocab.export import write_anki_csv
from anki_vocab.sources import cambridge


def test_read_words_splits_dedupes_and_skips_comments():
    text = "Hearth, timid\n# comment\n\nzilch; hearth  \nsneer # trailing note\n"
    assert read_words(text) == ["hearth", "timid", "zilch", "sneer"]


def test_card_back_escapes_and_skips_empty_parts():
    card = Card("timid", translation="робкий", definition="shy & nervous", examples=["a <timid> child"])
    back = card.back()
    assert "робкий" in back
    assert "shy &amp; nervous" in back
    assert "a &lt;timid&gt; child" in back
    assert "teal" not in back  # no long description given


def test_anki_csv_has_headers_and_rows(tmp_path):
    path = tmp_path / "deck.csv"
    write_anki_csv([Card("timid", short='He said "hi", softly')], path, tags="vocab test")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[:4] == ["#separator:Comma", "#html:true", "#columns:Front,Back", "#tags:vocab test"]
    rows = list(csv.reader(lines[4:]))
    assert rows == [["timid", '<p>He said "hi", softly</p>']]


def test_cambridge_parse():
    html = """
      <div class="def ddef_d db">feeling <a>shy</a> and nervous:</div>
      <div class="examp dexamp">ex <a>one</a> .</div><div class="examp dexamp">ex two</div>
      <div class="examp dexamp">ex three</div>"""
    assert cambridge.parse(html) == {"definition": "feeling shy and nervous", "examples": ["ex one.", "ex two"]}


def test_card_with_only_echoed_translation_is_empty():
    assert not Card("qwxzplk", translation="qwxzplk").has_content()
    assert Card("timid", translation="робкий").has_content()


def test_cambridge_parse_missing_entry():
    with pytest.raises(LookupError):
        cambridge.parse("<html></html>")


def test_word_limit(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("\n".join(f"w{i}" for i in range(101)))
    with pytest.raises(SystemExit):
        main([str(words), "--no-vocabulary", "--no-cambridge", "--no-translate"])
