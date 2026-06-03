#!/usr/bin/env python3
"""
Convert a Blogger Atom export (feed.atom or Takeout feed.atom) to Hugo notes.

Usage:
    python scripts/blogger2notes.py <feed.atom> <output_dir>

Example:
    python scripts/blogger2notes.py \
        "Welcome_to_my_Andron/Takeout-20260603/Blogger/Blogs/Καλωσορίσατε στο Άντρο μου/feed.atom" \
        content/el/notes

Outputs one .md file per blog post. Preserves original text verbatim.
EN stubs are written to content/en/notes/ automatically.
"""

import sys
import re
import html as html_module
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

NS = "http://www.w3.org/2005/Atom"

ALREADY_MIGRATED = {
    "2008-09-10", "2008-09-15", "2008-09-16", "2008-09-29",
    "2008-10-21", "2008-11-01", "2008-11-11", "2008-11-14",
    "2008-11-22", "2008-12-13", "2008-12-27",
    "2009-01-12", "2009-01-21", "2009-02-11", "2009-03-11",
    "2009-04-15", "2009-08-12", "2009-09-16",
    "2010-03-21", "2010-07-12", "2010-08-04",
    "2010-08-08", "2010-08-30", "2010-09-03",
}


def html_to_markdown(h):
    """Convert simple Blogger HTML to Markdown. Preserves original text."""
    if not h:
        return ""
    h = html_module.unescape(h)
    # Bold
    h = re.sub(r"<b>(.*?)</b>", r"**\1**", h, flags=re.DOTALL)
    h = re.sub(r"<strong>(.*?)</strong>", r"**\1**", h, flags=re.DOTALL)
    # Italic
    h = re.sub(r"<i>(.*?)</i>", r"*\1*", h, flags=re.DOTALL)
    h = re.sub(r"<em>(.*?)</em>", r"*\1*", h, flags=re.DOTALL)
    # Links
    h = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
               r"[\2](\1)", h, flags=re.DOTALL)
    # Line breaks and paragraphs
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"</p>", "\n\n", h)
    h = re.sub(r"<p[^>]*>", "", h)
    # Strip remaining tags
    h = re.sub(r"<[^>]+>", "", h)
    # Clean whitespace
    h = re.sub(r"\n{3,}", "\n\n", h)
    return h.strip()


def slugify(title):
    """Create a URL-safe slug from a title."""
    t = title.lower()
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"[\s_]+", "-", t)
    t = t.strip("-")[:60]
    return t


def parse_feed(feed_path):
    """Parse a Blogger Atom feed and return list of post dicts."""
    tree = ET.parse(feed_path)
    root = tree.getroot()
    posts = []
    for entry in root.iter(f"{{{NS}}}entry"):
        title_el = entry.find(f"{{{NS}}}title")
        if title_el is None or not title_el.text:
            continue
        pub_el = entry.find(f"{{{NS}}}published")
        if pub_el is None:
            continue
        content_el = entry.find(f"{{{NS}}}content")
        date = pub_el.text[:10]
        cats = [
            c.get("term", "").split("/")[-1]
            for c in entry.findall(f"{{{NS}}}category")
            if "kind#" not in c.get("term", "")
        ]
        posts.append({
            "title": title_el.text.strip(),
            "date": date,
            "content_html": content_el.text if content_el is not None else "",
            "tags": cats,
        })
    return sorted(posts, key=lambda p: p["date"])


def write_note(post, out_dir, skip_dates=None):
    """Write a single post as a Hugo note markdown file."""
    skip_dates = skip_dates or ALREADY_MIGRATED
    if post["date"] in skip_dates:
        print(f"  SKIP (already migrated): {post['date']} {post['title'][:50]}")
        return None

    slug = slugify(post["title"])
    if not slug:
        slug = post["date"]

    # Build frontmatter tags from Blogger labels
    raw_tags = []
    for t in post["tags"]:
        # Strip bilingual labels like "Φαράγγια - Canyons" → keep Greek part
        clean = t.split(" - ")[0].strip().lower().replace(" ", "-")
        if clean:
            raw_tags.append(clean)

    tags_yaml = ", ".join(f'"{t}"' for t in raw_tags) if raw_tags else ""
    content_md = html_to_markdown(post["content_html"])

    md = f"""---
title: "{post['title'].replace('"', '\\"')}"
date: {post['date']}
tags: [{tags_yaml}]
---

{content_md}
"""

    out_path = Path(out_dir) / f"{slug}.md"
    # Avoid collisions
    if out_path.exists():
        out_path = Path(out_dir) / f"{post['date']}-{slug}.md"

    out_path.write_text(md, encoding="utf-8")
    print(f"  WROTE: {out_path.name}")
    return out_path


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    feed_path = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Derive EN stub dir
    en_dir = Path(str(out_dir).replace("/el/", "/en/"))
    en_dir.mkdir(parents=True, exist_ok=True)

    posts = parse_feed(feed_path)
    print(f"Found {len(posts)} posts in {feed_path}")

    for post in posts:
        el_path = write_note(post, out_dir)
        if el_path is None:
            continue
        # Write minimal EN stub
        slug = el_path.name
        en_path = en_dir / slug
        en_path.write_text(
            f"""---
title: "{post['title'].replace('"', '\\"')}"
date: {post['date']}
tags: []
---

*(Original in Greek — see [ελληνική έκδοση](/el/notes/{el_path.stem}/))*
""",
            encoding="utf-8",
        )
        print(f"    stub: {en_path.name}")


if __name__ == "__main__":
    main()
