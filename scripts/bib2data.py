#!/usr/bin/env python3
"""Convert publications.bib → data/publications.yaml for Hugo templates."""

import sys
import re
import yaml
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

ENTRY_TYPE_MAP = {
    "article":       "article",
    "inproceedings": "article",
    "proceedings":   "article",
    "phdthesis":     "thesis",
    "mastersthesis": "thesis",
    "book":          "book",
    "incollection":  "book",
    "misc":          "preprint",
    "unpublished":   "preprint",
}

def clean(s):
    if not s:
        return ""
    s = re.sub(r"\{|\}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_authors(raw):
    if not raw:
        return []
    parts = re.split(r"\s+and\s+", raw, flags=re.IGNORECASE)
    return [clean(p) for p in parts]

def entry_to_dict(e):
    etype = ENTRY_TYPE_MAP.get(e.get("ENTRYTYPE", "misc").lower(), "article")
    # treat bioRxiv / EcoEvoRxiv as preprints
    journal = clean(e.get("journal", e.get("booktitle", "")))
    if any(x in journal.lower() for x in ["biorxiv", "ecoevorxiv", "arxiv", "preprint"]):
        etype = "preprint"

    doi = clean(e.get("doi", ""))
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)

    return {
        "key":      e.get("ID", ""),
        "type":     etype,
        "title":    clean(e.get("title", "")),
        "authors":  parse_authors(e.get("author", "")),
        "year":     int(e.get("year", 0) or 0),
        "journal":  journal,
        "doi":      doi,
        "url":      clean(e.get("url", "")),
    }

def main(bib_path, out_path):
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with open(bib_path, encoding="utf-8") as f:
        db = bibtexparser.load(f, parser)

    entries = [entry_to_dict(e) for e in db.entries]
    entries.sort(key=lambda x: x["year"], reverse=True)

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(entries, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"Wrote {len(entries)} entries → {out_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: bib2data.py <input.bib> <output.yaml>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
