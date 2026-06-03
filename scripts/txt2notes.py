#!/usr/bin/env python3
"""
Convert Welcome_to_my_Andron converted txt files → Hugo notes.
Preserves original text verbatim (body is the exact source text).

Usage:
    python scripts/txt2notes.py

Reads from: Welcome_to_my_Andron/converted/
Writes to:  content/el/notes/   (overwrites existing files)
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

SOURCES = [
    {
        "file": "Μαλάκι για blog.txt",
        "slug": "cave-survey-malaki",
        "date": "2008-09-15",
        "title": "Σπηλαιολογική έρευνα στο Μαλάκι",
        "tags": ["σπηλαιολογία", "βάραθρο", "κρήτη", "πεδίο"],
        "keywords": ["Μαλάκι", "Νικηφόρος Φωκάς", "Ε.Σ.Ε", "βάραθρα", "Ηράκλειο"],
    },
    {
        "file": "Blog 4pss Zwniana.txt",
        "slug": "speleology-symposium-2008",
        "date": "2008-11-01",
        "title": "4ο Παγκρήτιο Σπηλαιολογικό Συμπόσιο",
        "tags": ["σπηλαιολογία", "συνέδριο", "κρήτη", "παρουσίαση"],
        "keywords": ["Ζωνιανά", "Ε.Σ.Ε", "Σίτανο", "Σητεία"],
    },
    {
        "file": "Το Καμαραϊκό.txt",
        "slug": "canyon-kamaraiko",
        "date": "2008-11-11",
        "title": "Το Καμαραϊκό",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "ψηλορείτης"],
        "keywords": ["Καμαραϊκό", "Καμάρες", "Ψηλορείτης"],
    },
    {
        "file": "Το Ψηστράκι.txt",
        "slug": "psistrakis-cave",
        "date": "2008-11-14",
        "title": "Το Ψηστράκι",
        "tags": ["σπηλαιολογία", "βάραθρο", "κρήτη", "ηράκλειο"],
        "keywords": ["Ψηστράκι", "Γωνιές", "Μαλεβίζι", "Ε.Σ.Ε"],
    },
    {
        "file": "Γιατί unonoctium.txt",
        "slug": "why-unonoctium",
        "date": "2008-11-28",
        "title": "Γιατί unonoctium;",
        "tags": ["σκέψεις", "unonoctium", "χημεία"],
        "keywords": ["unonoctium", "ununoctium", "στοιχείο 118", "περιοδικός πίνακας"],
    },
    {
        "file": "blog wetlands euvoia.txt",
        "slug": "wetlands-euboea",
        "date": "2008-12-14",
        "title": "Υγρότοποι Εύβοιας — WWF αποστολή",
        "tags": ["οικολογία", "υγρότοποι", "φύση", "εθελοντισμός"],
        "keywords": ["υγρότοποι", "Εύβοια", "WWF", "Μύτη", "Μερούθι"],
    },
    {
        "file": "faNTAXOSPILIARA.txt",
        "slug": "fantaxospiliara",
        "date": "2008-12-21",
        "title": "Φανταξοσπηλιάρα",
        "tags": ["σπηλαιολογία", "σπήλαιο", "κρήτη", "ρέθυμνο"],
        "keywords": ["Φανταξοσπηλιάρα", "Ρέθυμνο", "νυχτερίδες", "Ε.Σ.Ε"],
    },
    {
        "file": "Sτο φαράγγι της  Άρβης.txt",
        "slug": "canyon-arvi",
        "date": "2008-12-27",
        "title": "Φαράγγι Άρβης",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "ηράκλειο"],
        "keywords": ["Άρβη", "Κερατόκαμπος", "Δίκτη"],
    },
    {
        "file": "Το φαράγγι Χα.txt",
        "slug": "canyon-ha",
        "date": "2009-01-13",
        "title": "Φαράγγι Χα",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "λασίθι"],
        "keywords": ["Χα", "Ιεράπετρα", "Θρυπτή", "Μάστορας"],
    },
    {
        "file": "Το φαράγγι Καβουσίου.txt",
        "slug": "canyon-kavousi",
        "date": "2009-01-21",
        "title": "Φαράγγι Καβουσίου",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "λασίθι"],
        "keywords": ["Καβούσι", "Κερατόκαμπος", "Βιάννος", "Δίκτη"],
    },
    {
        "file": "Φαράγγι Πορτέλα.txt",
        "slug": "canyon-portela",
        "date": "2009-02-11",
        "title": "Φαράγγι Πορτέλα",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "ηράκλειο"],
        "keywords": ["Πορτέλα", "Χόντρος", "Κερατόκαμπος", "Δίκτη"],
    },
    {
        "file": "Το φαράγγι Λάπαθος ή αλλιώς των Αγίων Αποστόλων.txt",
        "slug": "canyon-lapathos",
        "date": "2009-03-11",
        "title": "Φαράγγι Λάπαθος",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "λασίθι"],
        "keywords": ["Λάπαθος", "Άγιοι Απόστολοι", "Δίκτη", "γύπες"],
    },
    {
        "file": "Ψηστράκι Νεο.txt",
        "slug": "psistrakis-new-visit",
        "date": "2009-04-16",
        "title": "Ψηστράκι — νέα επίσκεψη",
        "tags": ["σπηλαιολογία", "βάραθρο", "κρήτη", "περιβάλλον"],
        "keywords": ["Ψηστράκι", "Γωνιές", "χύτρες", "ρύπανση"],
    },
    {
        "file": "Το βάραθρο Άκολη Ψαρής στα βαθύτερα σπήλαια της Ελλάδας.txt",
        "slug": "expedition-akolie-psaris",
        "date": "2009-08-08",
        "title": "Αποστολή Ψαρή 2009 — Άκολη Ψαρής −442m",
        "tags": ["σπηλαιολογία", "αποστολή", "βάραθρο", "κρήτη", "χανιά"],
        "keywords": ["Άκολη Ψαρής", "Ψαρή 2009", "Λευκά Όρη", "Χανιά"],
    },
    {
        "file": "Ethiano canyon 13.09.2009.txt",
        "slug": "canyon-ethiano",
        "date": "2009-09-15",
        "title": "Φαράγγι Εθιανό",
        "tags": ["canyoning", "φαράγγι", "κρήτη", "αστερούσια"],
        "keywords": ["Εθιανό", "Εθιά", "Ροτάσι", "Αστερούσια"],
    },
    {
        "file": "Στο βάραθρο Ψηστράκι με το Γιάννη Σκοντινάκη και το Γιάννη Μπρομοιράκη στις 13.txt",
        "slug": "psistrakis-memories",
        "date": "2009-09-16",
        "title": "Ψηστράκι και αναμνήσεις",
        "tags": ["σπηλαιολογία", "αναμνήσεις", "φιλία", "κρήτη"],
        "keywords": ["Ψηστράκι", "Γιάννης Μπρομοιράκης", "φιλία"],
    },
    {
        "file": "Arvi.txt",
        "slug": None,  # already covered by the .doc version
        "date": None,
    },
]


def tags_yaml(tags):
    return ", ".join(f'"{t}"' for t in tags)


def write_note(src_text, slug, date, title, tags, keywords):
    el_path = REPO / "content" / "el" / "notes" / f"{slug}.md"
    front = f"""---
title: "{title}"
date: {date}
tags: [{tags_yaml(tags)}]
keywords: [{tags_yaml(keywords)}]
---

"""
    el_path.write_text(front + src_text.strip() + "\n", encoding="utf-8")
    print(f"  updated: {el_path.name}")


def main():
    converted_dir = REPO / "Welcome_to_my_Andron" / "converted"
    if not converted_dir.exists():
        print(f"ERROR: {converted_dir} not found. Run textutil conversions first.")
        sys.exit(1)

    for entry in SOURCES:
        if entry.get("slug") is None:
            continue
        src_file = converted_dir / entry["file"]
        if not src_file.exists():
            print(f"  MISSING: {entry['file']}")
            continue
        src_text = src_file.read_text(encoding="utf-8")
        write_note(
            src_text,
            entry["slug"],
            entry["date"],
            entry["title"],
            entry["tags"],
            entry.get("keywords", []),
        )


if __name__ == "__main__":
    main()
