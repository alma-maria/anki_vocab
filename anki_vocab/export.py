"""Write cards as a CSV file that Anki (2.1.55+) imports without extra setup.

The leading "#key:value" lines are Anki file headers: they tell the importer
the separator, that fields contain HTML, the column names and the tags.
"""

import csv


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
