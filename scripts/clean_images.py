#!/usr/bin/env python3
"""
Clean up the Blogger Takeout image dump under static/img/field/.

The Takeout export drops three messy directories with Greek/spaced names,
one .json sidecar per image, and many (1)/(2)/(3) duplicates.

This script:
  - Copies the handful of *recognizable* images (whose filenames map to a
    specific note) into static/img/field/ with clean, web-safe slugs.
  - Moves every other real image into static/img/field/archive/ with a
    slugified name (Greek transliterated, lowercased, de-collided).
  - Drops all .json sidecars, .bmp files, and (N) duplicates.
  - Removes the now-empty Takeout directories.

Idempotent-ish: safe to re-run; it skips files already placed.

Usage:
    pixi run python scripts/clean_images.py [--dry-run]
"""

import argparse
import re
import shutil
import sys
import unicodedata
from pathlib import Path


def nfc(s: str) -> str:
    """Normalise to NFC so NFD disk names (macOS) match NFC literals."""
    return unicodedata.normalize("NFC", s)

REPO  = Path(__file__).parent.parent
FIELD = REPO / "static/img/field"
ARCHIVE = FIELD / "archive"

# Messy Takeout source directories to clean out
SRC_DIRS = [
    FIELD / "Καλωσορίσατε στο Άντρο μου",
    FIELD / "Εικόνες Blogger",
    FIELD / "Einstein",
]

# Recognizable images → clean destination filename (placed directly in field/)
# These are linked into notes by link_images step.
RECOGNIZABLE = {
    "ΣΙΤΑΝΟΣ_107.jpg":            "sitanos-cave-survey.jpg",
    "Βάραθρο Ψ207gr_csmall.jpg":  "akoli-psaris-pothole.jpg",
    "avussos.jpg":                "akoli-psaris-avyssos.jpg",
    "χαρτογραφηση Αμπα.jpg":       "ampas-canyon-map.jpg",
    "diorhtoshKalamiI.jpg":       "kalami-bolting.jpg",
    "Σαββας ΧΑΥΓΑΣ-ΧΑ 175.jpg":   "ha-canyon-havgas.jpg",
}

RECOGNIZABLE_NFC = {nfc(k): v for k, v in RECOGNIZABLE.items()}

IMG_EXT = {".jpg", ".jpeg", ".png"}

# Greek → ASCII transliteration for archive slugs
GREEK = [
    ("ά","a"),("έ","e"),("ή","i"),("ί","i"),("ό","o"),("ύ","u"),("ώ","o"),
    ("α","a"),("β","b"),("γ","g"),("δ","d"),("ε","e"),("ζ","z"),("η","i"),
    ("θ","th"),("ι","i"),("κ","k"),("λ","l"),("μ","m"),("ν","n"),("ξ","x"),
    ("ο","o"),("π","p"),("ρ","r"),("σ","s"),("ς","s"),("τ","t"),("υ","u"),
    ("φ","f"),("χ","h"),("ψ","ps"),("ω","o"),("ϊ","i"),("ϋ","u"),
]


def slugify(name: str) -> str:
    stem = Path(name).stem.lower()
    for g, l in GREEK:
        stem = stem.replace(g, l)
    stem = re.sub(r"[^\w-]", "-", stem)
    stem = re.sub(r"-+", "-", stem).strip("-")
    return stem or "image"


def is_duplicate(name: str) -> bool:
    # Blogger duplicate suffix like name(1).jpg
    return bool(re.search(r"\(\d+\)\.[^.]+$", name))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run:
        ARCHIVE.mkdir(parents=True, exist_ok=True)

    placed_recognizable = 0
    archived = 0
    dropped = 0
    used_slugs: set[str] = set()

    for src_dir in SRC_DIRS:
        if not src_dir.exists():
            continue
        for f in sorted(src_dir.iterdir()):
            if not f.is_file():
                continue
            ext = f.suffix.lower()

            # Drop sidecars, bmp, duplicates
            if ext == ".json" or ext == ".bmp" or is_duplicate(f.name):
                dropped += 1
                if not args.dry_run:
                    f.unlink()
                continue

            # Not an image we keep (e.g. .mp4) → drop
            if ext not in IMG_EXT:
                dropped += 1
                if not args.dry_run:
                    f.unlink()
                continue

            # Recognizable → clean name in field/ (NFC-normalise for macOS NFD names)
            if nfc(f.name) in RECOGNIZABLE_NFC:
                dest = FIELD / RECOGNIZABLE_NFC[nfc(f.name)]
                print(f"  LINKABLE  {f.name}  →  {dest.name}")
                if not args.dry_run:
                    shutil.copy2(f, dest)
                    f.unlink()
                placed_recognizable += 1
                continue

            # Everything else → archive/ with slug
            slug = slugify(f.name)
            candidate = f"{slug}{ext}"
            i = 2
            while candidate in used_slugs:
                candidate = f"{slug}-{i}{ext}"
                i += 1
            used_slugs.add(candidate)
            dest = ARCHIVE / candidate
            if not args.dry_run:
                shutil.move(str(f), str(dest))
            archived += 1

    # Remove now-empty source dirs
    for src_dir in SRC_DIRS:
        if src_dir.exists() and not args.dry_run:
            shutil.rmtree(src_dir)

    print(f"\nRecognizable placed in field/: {placed_recognizable}")
    print(f"Archived to field/archive/:    {archived}")
    print(f"Dropped (json/bmp/dupes/mp4):  {dropped}")
    if args.dry_run:
        print("\n(dry run — nothing written)")


if __name__ == "__main__":
    main()
