import csv
import sqlite3
import zipfile

import pytest

from anki_vocab import patterns
from anki_vocab.card import Card, highlight_term
from anki_vocab.cli import main, read_words, safe_dir_name
from anki_vocab.export import write_anki_csv, write_apkg
from anki_vocab.sources import cambridge, synonyms, translate

GREEN = '<span style="color: #359B28">'
SALMON = '<span style="color: #ee7e68">'


def test_read_words_splits_dedupes_and_skips_comments():
    text = "Hearth, timid\n# comment\n\nzilch; hearth  \nsneer # trailing note\n"
    assert read_words(text) == ["hearth", "timid", "zilch", "sneer"]


# --- patterns ---------------------------------------------------------------

@pytest.mark.parametrize("term, name", [
    ("dazed", "green_word"),
    ("deterrent", "green_word"),
    ("uncalled-for", "salmon_phrase"),
    ("take a stab at", "salmon_phrase"),
    ("steer clear of someone/something", "salmon_phrase"),
])
def test_pattern_for(term, name):
    assert patterns.pattern_for(term).name == name


def test_get_unknown_pattern_lists_known_names():
    with pytest.raises(KeyError, match="green_word"):
        patterns.get("purple")


def test_green_word_back_matches_april_2026_markup():
    card = Card("dazed", translation="ошеломлённый, оглушённый",
                definition="unable to think clearly because you are shocked, tired, or injured",
                examples=["He looked dazed after the fall.", "She was still Dazed by the sudden news."],
                synonyms=["stunned", "confused", "bewildered"])
    assert card.back() == (
        'ошеломлённый, оглушённый<br>'
        '<p style="color: #359B28"><b>unable to think clearly because you are shocked, tired, or injured</b></p><br>'
        f'<i>He looked {GREEN}dazed</span> after the fall.<br>'
        f'She was still {GREEN}Dazed</span> by the sudden news.</i><br><br>'
        'Synonyms: stunned, confused, bewildered<br><br>'
    )


def test_salmon_phrase_highlights_without_placeholders():
    card = Card("steer clear of someone/something", definition="to avoid someone",
                examples=["I try to steer  clear of drama."])
    back = card.back()
    assert '<p style="color: #ee7e68">' in back
    assert f"I try to {SALMON}steer  clear of</span> drama." in back


def test_highlight_only_whole_words_and_missing_term_left_alone():
    card = Card("tip", examples=["Tipping is optional.", "No hints here."])
    assert GREEN not in card.back()


def test_back_skips_empty_parts_and_escapes():
    back = Card("timid", definition="shy & nervous").back()
    assert back == '<p style="color: #359B28"><b>shy &amp; nervous</b></p><br>'


def test_highlight_term():
    assert highlight_term("steer clear of someone/something") == "steer clear of"
    assert highlight_term("get on sb's nerves") == "get on sb's nerves"
    assert highlight_term("take a stab at") == "take a stab at"


def test_more_field():
    assert Card("toady", short="A toady flatters.", long="From toad-eater.").more() == \
        "A toady flatters.<br>From toad-eater."
    assert Card("toady").more() == ""


def test_card_with_only_echoed_translation_is_empty():
    assert not Card("qwxzplk", translation="qwxzplk").has_content()
    assert Card("timid", translation="робкий").has_content()


# --- sources ----------------------------------------------------------------

def test_cambridge_parse():
    html = """
      <div class="def ddef_d db">feeling <a>shy</a> and nervous:</div>
      <div class="examp dexamp">ex <a>one</a> .</div><div class="examp dexamp">ex two</div>
      <div class="examp dexamp">ex three</div>"""
    assert cambridge.parse(html) == {"definition": "feeling shy and nervous", "examples": ["ex one.", "ex two"]}


def test_cambridge_parse_missing_entry():
    with pytest.raises(LookupError):
        cambridge.parse("<html></html>")


def test_synonyms_parse_skips_word_and_duplicates():
    data = [{"word": "Dazed"}, {"word": "stunned"}, {"word": "stunned"}, {"word": "confused"},
            {"word": "groggy"}, {"word": "foggy"}]
    assert synonyms.parse(data, "dazed") == ["stunned", "confused", "groggy"]


class FakeSession:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def get(self, url, params, timeout):
        relation = next(k for k in params if k != "max")
        self.calls.append(relation)
        answer = self.answers[relation]

        class Response:
            def raise_for_status(self): pass
            def json(self): return answer
        return Response()


def test_synonyms_fall_back_to_means_like():
    session = FakeSession({"rel_syn": [], "ml": [{"word": "avoid"}, {"word": "evade"}]})
    assert synonyms.lookup("steer clear of", session=session) == ["avoid", "evade"]
    assert session.calls == ["rel_syn", "ml"]


def test_synonyms_not_found():
    with pytest.raises(LookupError):
        synonyms.lookup("qwxzplk", session=FakeSession({"rel_syn": [], "ml": []}))


def test_mymemory_pick_skips_transliteration_and_weak_matches():
    # Real MyMemory answers for "dazed" and "uncalled-for".
    dazed = [{"translation": "SOZNANIIA SPUTANNOST&apos;", "quality": "0", "match": 0.99},
             {"translation": "Изумленный", "quality": "74", "match": 0.98}]
    uncalled = [{"translation": "uncalled-for", "quality": 70, "match": 0.85},
                {"translation": "Это было неприелимо.", "quality": "74", "match": 0.71}]
    assert translate.pick_match(dazed) == "Изумленный"
    assert translate.pick_match(uncalled) is None


# --- export -----------------------------------------------------------------

def test_anki_csv_has_headers_and_rows(tmp_path):
    path = tmp_path / "deck.csv"
    write_anki_csv([Card("timid", short='He said "hi", softly'), Card("take a stab at")],
                   path, tags="vocab test")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[:4] == ["#separator:Comma", "#html:true", "#columns:Front,Back,More,Tags", "#tags column:4"]
    rows = list(csv.reader(lines[4:]))
    assert rows == [["timid", "", 'He said "hi", softly', "vocab test word"],
                    ["take a stab at", "", "", "vocab test phrase"]]


def _apkg(path, tmp_path):
    with zipfile.ZipFile(path) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    try:
        return db.execute("select guid, flds, tags from notes order by id").fetchall()
    finally:
        db.close()


def test_apkg_has_three_fields_and_pattern_tags(tmp_path):
    path = tmp_path / "deck.apkg"
    write_apkg([Card("timid", translation="робкий", short="Shy."), Card("uncalled-for", definition="rude")],
               path, deck_name="Test", tags="vocab book1")
    notes = _apkg(path, tmp_path)
    fields = [n[1].split("\x1f") for n in notes]
    assert fields[0] == ["timid", "робкий<br>", "Shy."]
    assert fields[1][0] == "uncalled-for" and "#ee7e68" in fields[1][1]
    assert notes[0][2].split() == ["vocab", "book1", "word"]
    assert notes[1][2].split() == ["vocab", "book1", "phrase"]


def test_apkg_guid_is_stable_per_word(tmp_path):
    a, b = tmp_path / "a.apkg", tmp_path / "b.apkg"
    write_apkg([Card("timid", short="v1")], a)
    write_apkg([Card("timid", short="v2")], b)
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    assert _apkg(a, tmp_path / "a")[0][0] == _apkg(b, tmp_path / "b")[0][0]


# --- cli --------------------------------------------------------------------

OFFLINE = ["--no-vocabulary", "--no-cambridge", "--no-translate", "--no-synonyms"]


def test_word_limit(tmp_path):
    words = tmp_path / "words.txt"
    words.write_text("\n".join(f"w{i}" for i in range(101)))
    with pytest.raises(SystemExit):
        main([str(words), *OFFLINE])


def test_each_deck_gets_its_own_folder(tmp_path):
    words = tmp_path / "april.txt"
    words.write_text("Timid, zilch\n")
    out = tmp_path / "out"
    main([str(words), "--deck", "test", "--out-dir", str(out), "--format", "both", *OFFLINE])
    assert sorted(p.name for p in (out / "test").iterdir()) == ["test.apkg", "test.csv", "words.txt"]
    assert (out / "test" / "words.txt").read_text() == "timid\nzilch\n"

    main([str(words), "--out-dir", str(out), *OFFLINE])  # deck name defaults to the file name
    assert (out / "april" / "april.apkg").exists()


def test_safe_dir_name():
    assert safe_dir_name("Book 1: ch/2") == "Book 1_ ch_2"
    assert safe_dir_name(" .. ") == "deck"


def test_list_patterns(capsys):
    assert main(["--list-patterns"]) == 0
    out = capsys.readouterr().out
    assert "green_word" in out and "#ee7e68" in out
