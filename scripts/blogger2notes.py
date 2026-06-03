#!/usr/bin/env python3
"""
Migrate Blogger Takeout export → Hugo notes.

Usage:
    python scripts/blogger2notes.py [--dry-run] [--all]

Source:
    Welcome_to_my_Andron/Takeout-20260603/Blogger/Blogs/
        Καλωσορίσατε στο Άντρο μου/feed.atom
    Welcome_to_my_Andron/Takeout-20260603/Blogger/Albums/
        Καλωσορίσατε στο Άντρο μου/*.jpg  (images)

Output:
    content/el/notes/<slug>.md   — verbatim original text
    content/en/notes/<slug>.md   — stub marked ai-translated
    static/img/field/<image>     — images extracted from posts (manual step; see below)

Rules:
    - Original Greek text is preserved verbatim (no paraphrasing)
    - English stubs get tag "ai-translated" and a placeholder body
    - Posts already in ALREADY_MIGRATED are skipped
    - Images embedded in posts are listed but NOT copied automatically
      (copy manually; resize to 1600×1067 max 350KB before committing)
    - One git commit per post (run: git add + git commit after each write)

Migration status:
    25 posts migrated from old XML snapshots (see content/el/notes/)
    11 posts remaining in the Takeout feed (2008-2015)
"""

import argparse
import html as _html
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from textwrap import dedent

REPO = Path(__file__).parent.parent
NS   = "http://www.w3.org/2005/Atom"

FEED   = REPO / "Welcome_to_my_Andron/Takeout-20260603/Blogger/Blogs/Καλωσορίσατε στο Άντρο μου/feed.atom"
ALBUMS = REPO / "Welcome_to_my_Andron/Takeout-20260603/Blogger/Albums/Καλωσορίσατε στο Άντρο μου"

EL_NOTES = REPO / "content/el/notes"
EN_NOTES = REPO / "content/en/notes"

# Posts already migrated from earlier XML snapshots — skip these
ALREADY_MIGRATED = {
    "2008-09-10", "2008-09-15", "2008-09-16", "2008-09-29",
    "2008-10-21", "2008-11-01", "2008-11-11", "2008-11-14",
    "2008-11-22", "2008-12-13", "2008-12-27",
    "2009-01-12", "2009-01-21", "2009-02-11", "2009-03-11",
    "2009-04-15", "2009-08-12", "2009-09-16",
    "2010-03-21", "2010-07-12", "2010-08-04",
    "2010-08-08", "2010-08-30", "2010-09-03",
    # also skip the Takeout duplicate of pothole-tapes (1 day earlier)
    "2008-09-09",
}

# Blogger label → Hugo tag mapping
LABEL_MAP = {
    "Φαράγγια - Canyons":                                      "canyoning",
    "Σπήλαια - Caves":                                          "speleology",
    "Πεζοπορίες - Trekking":                                    "trekking",
    "Διορθώσεις αρματώματος φαραγγιών - Bolting improvement in canyons": "rigging",
    "Διάφορα - Other News":                                     "misc",
    "Initiateur EFC":                                           "canyoning",
    "Ανεξερεύνητη Σαμαριά - Unexplored Samaria":               "expedition",
}


# ── HTML → Markdown ──────────────────────────────────────────────────────────

def html_to_md(raw: str) -> str:
    """Convert Blogger HTML to clean Markdown. Preserves all original text."""
    h = _html.unescape(raw or "")
    # Bold / italic
    h = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", h, flags=re.DOTALL)
    h = re.sub(r"<(?:i|em)>(.*?)</(?:i|em)>",         r"*\1*",   h, flags=re.DOTALL)
    # Links
    h = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r"[\2](\1)", h, flags=re.DOTALL)
    # Images — note filename for manual copy, render as comment
    def img_sub(m):
        src = re.search(r'src=["\']([^"\']+)["\']', m.group(0))
        return f"\n<!-- image: {src.group(1) if src else 'unknown'} -->\n"
    h = re.sub(r"<img[^>]+>", img_sub, h)
    # Block structure
    h = re.sub(r"<br\s*/?>",  "\n",   h)
    h = re.sub(r"</p>",       "\n\n", h)
    h = re.sub(r"<p[^>]*>",   "",     h)
    h = re.sub(r"<div[^>]*>", "",     h)
    h = re.sub(r"</div>",     "\n",   h)
    # Strip remaining tags
    h = re.sub(r"<[^>]+>", "", h)
    # Clean whitespace
    h = re.sub(r"[ \t]+\n",  "\n", h)
    h = re.sub(r"\n{3,}",    "\n\n", h)
    return h.strip()


# ── Slug ─────────────────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    t = title.lower()
    # Transliterate Greek → ASCII (1-to-1 mapping only; complex chars drop)
    pairs = [
        ("ά", "a"), ("έ", "e"), ("ή", "i"), ("ί", "i"), ("ό", "o"), ("ύ", "u"), ("ώ", "o"),
        ("α", "a"), ("β", "b"), ("γ", "g"), ("δ", "d"), ("ε", "e"), ("ζ", "z"), ("η", "i"),
        ("θ", "th"), ("ι", "i"), ("κ", "k"), ("λ", "l"), ("μ", "m"), ("ν", "n"), ("ξ", "x"),
        ("ο", "o"), ("π", "p"), ("ρ", "r"), ("σ", "s"), ("ς", "s"), ("τ", "t"), ("υ", "u"),
        ("φ", "f"), ("χ", "h"), ("ψ", "ps"), ("ω", "o"), ("ϊ", "i"), ("ϋ", "u"),
    ]
    for src, dst in pairs:
        t = t.replace(src, dst)
    t = re.sub(r"[^\w\s-]", "",  t)
    t = re.sub(r"[\s_]+",   "-", t)
    t = t.strip("-")[:60]
    return t or "note"


# ── Parse feed ───────────────────────────────────────────────────────────────

def parse_posts(skip_all: bool = False) -> list[dict]:
    tree  = ET.parse(FEED)
    posts = []
    for entry in tree.getroot().iter(f"{{{NS}}}entry"):
        t = entry.find(f"{{{NS}}}title")
        if t is None or not t.text:
            continue
        p = entry.find(f"{{{NS}}}published")
        if p is None:
            continue
        date  = p.text[:10]
        skip  = ALREADY_MIGRATED if not skip_all else set()
        if date in skip:
            continue
        content = entry.find(f"{{{NS}}}content")
        body_html = content.text if content is not None else ""
        body_md   = html_to_md(body_html)
        if not body_md.strip():
            continue
        labels = [
            c.get("term", "").split("/")[-1]
            for c in entry.findall(f"{{{NS}}}category")
            if "kind#" not in c.get("term", "")
        ]
        tags = list({LABEL_MAP.get(l, l.split(" - ")[0].lower().replace(" ", "-"))
                     for l in labels if l})
        # Extract image filenames mentioned in the post
        imgs = re.findall(r'<!-- image: ([^\s>]+) -->', body_md)
        posts.append({
            "title":    t.text.strip(),
            "date":     date,
            "tags":     sorted(tags),
            "body":     body_md,
            "images":   imgs,
        })
    posts.sort(key=lambda p: p["date"])
    return posts


# ── Write note files ──────────────────────────────────────────────────────────

def tags_yaml(tags: list[str]) -> str:
    # Clean tag strings: remove problematic characters
    safe = []
    for t in tags:
        # Remove quotes and special chars, keep alphanumeric + spaces/hyphens
        t_clean = t.replace('"', '').replace("'", '')
        t_clean = re.sub(r'[^\w\s-]', '', t_clean)
        t_clean = t_clean.strip()
        if t_clean and len(t_clean) < 50:
            safe.append(t_clean)
    return ", ".join(f'"{t}"' for t in safe) if safe else '""'


def write_el(post: dict, slug: str, dry_run: bool) -> Path:
    path = EL_NOTES / f"{slug}.md"
    content = f"""---
title: "{post['title'].replace('"', '\\"')}"
date: {post['date']}
tags: [{tags_yaml(post['tags'])}]
---

{post['body']}"""
    if dry_run:
        print(f"  [dry] would write {path.relative_to(REPO)}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"  ✓ {path.relative_to(REPO)}")
    return path


def write_en(post: dict, slug: str, dry_run: bool) -> Path:
    path = EN_NOTES / f"{slug}.md"
    content = f"""---
title: "{post['title'].replace('"', '\\"')}"
date: {post['date']}
tags: ["ai-translated"]
---

*(Original in Greek — see [ελληνική έκδοση](/el/notes/{slug}/))*"""
    if dry_run:
        print(f"  [dry] would write {path.relative_to(REPO)}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"  ✓ {path.relative_to(REPO)}")
    return path


def git_commit(files: list[Path], message: str, dry_run: bool):
    if dry_run:
        print(f"  [dry] git commit: {message}")
        return
    rel = [str(f.relative_to(REPO)) for f in files]
    subprocess.run(["git", "add"] + rel, cwd=REPO, check=True)
    # Only commit if there are actual changes
    result = subprocess.run(["git", "commit", "-m", message], cwd=REPO, capture_output=True)
    if result.returncode != 0 and b"nothing to commit" not in result.stdout:
        raise subprocess.CalledProcessError(result.returncode, result.args)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Print what would be done without writing")
    ap.add_argument("--all",     action="store_true", help="Include already-migrated posts (re-generate)")
    args = ap.parse_args()

    if not FEED.exists():
        sys.exit(f"ERROR: feed not found at {FEED}")

    posts = parse_posts(skip_all=args.all)
    print(f"Posts to migrate: {len(posts)}\n")

    for post in posts:
        slug = slugify(post["title"])
        # Avoid collision with existing slug
        el_path = EL_NOTES / f"{slug}.md"
        if el_path.exists() and not args.all:
            slug = f"{post['date']}-{slug}"
        print(f"{'[DRY] ' if args.dry_run else ''}─── {post['date']}  {post['title'][:60]}")
        if post["images"]:
            print(f"  ⚠ images to copy manually → static/img/field/:")
            for img in post["images"]:
                fname = Path(img).name
                src   = ALBUMS / fname
                print(f"    {'✓ found' if src.exists() else '✗ missing'}  {fname}")
        el = write_el(post, slug, args.dry_run)
        en = write_en(post, slug, args.dry_run)
        git_commit([el, en], f"note: {post['title'][:60]} ({post['date']})", args.dry_run)
        print()


if __name__ == "__main__":
    main()
