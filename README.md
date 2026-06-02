# unonoctium.gr

Personal academic website for Savvas Paragkamian.  
Stack: Hugo (static site generator) · nginx · Podman · pixi

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| [pixi](https://pixi.sh) | Manages Hugo + Python tools | `curl -fsSL https://pixi.sh/install.sh | sh` |
| [Podman](https://podman.io) | Runs the container locally and in production | `brew install podman` |
| Text editor | Authoring markdown content | any |

After cloning, install all tools once:

```sh
pixi install
```

This installs Hugo 0.162+, Python, bibtexparser, cairosvg, and other scripts.

---

## Development

### Start the live-reload server

```sh
make dev
```

Opens at **http://localhost:1313/en/**. Hugo reloads the browser on every file save. Drafts are visible.

### Build the static site

```sh
make build
```

Output goes to `public/`. This also runs the publications pipeline if `data/publications.bib` is present.

---

## Content authoring

All content lives in `content/en/` (English) and `content/el/` (Greek). Write English first, then translate.

Every content file starts with a YAML frontmatter block followed by markdown:

```markdown
---
title: "Your title"
date: 2026-06-01
description: "One-line summary shown in previews"
---

Your text here. Standard **markdown** works.
```

### Stories (blog)

Stories are longer writing — field notes, reflections, project updates.

```sh
# Create a new story
cat > content/en/stories/my-story.md << 'EOF'
---
title: "My Story"
date: 2026-06-01
description: "A short description"
---

Story text here.
EOF
```

The filename becomes the URL slug: `my-story.md` → `/en/stories/my-story/`.  
Add a matching file in `content/el/stories/` for the Greek version.

### Bits

Short observations, links, or fragments — no summary needed.

```sh
cat > content/en/bits/my-bit.md << 'EOF'
---
title: "An observation"
date: 2026-06-01
---

One or two paragraphs at most.
EOF
```

### Notes

Same format as Bits. Files go in `content/en/notes/`.

### About

Edit `content/en/about.md` directly. It is plain markdown — no special syntax.  
When you have a profile photo, set the `photo` field in the frontmatter:

```yaml
---
title: "About"
photo: "/img/profile/savvas.jpg"
---
```

The page layout switches to two-column automatically.

---

## Updating publications

The publications page is auto-generated from your BibTeX CV. Workflow:

```sh
# 1. Copy the latest bib file from the CV repo
cp /path/to/Curriculum_Vitae/publications.bib data/publications.bib

# 2. Convert to YAML (Hugo reads this)
make pubs

# 3. Rebuild
make build
```

Never edit `data/publications.yaml` by hand — it is regenerated every time.

To sync automatically, consider adding the CV repo as a git submodule:

```sh
git submodule add https://github.com/savvas-paragkamian/Curriculum_Vitae cv-repo
# Then copy: cp cv-repo/publications.bib data/publications.bib
```

---

## Adding photos

| Use | Directory | Size | Format |
|---|---|---|---|
| Profile / headshot | `static/img/profile/` | 800 × 800 px | WebP or JPG |
| Field / exploration | `static/img/field/` | 1600 × 1067 px (3:2) | WebP or JPG |
| Research figures | `static/img/research/` | 1200 × 800 px | WebP or PNG |

**DPI does not matter for web** — only pixel dimensions count.  
Target file sizes: profile < 120 KB, field < 350 KB, research < 300 KB.

Reference in markdown:

```markdown
![Caption text](/img/field/ha-gorge.jpg)
```

---

## Bilingual maintenance

| File | Purpose |
|---|---|
| `i18n/en.yaml` | UI strings: nav labels, section headings, footer links |
| `i18n/el.yaml` | Same keys in Greek |
| `content/en/` | English content (write here first) |
| `content/el/` | Greek content (translate from English) |

The language switcher in the sidebar links `/en/` ↔ `/el/`.

For pages that do not yet have a Greek translation, Hugo falls back to English automatically.

### Regenerating Greek drafts with DeepL

```sh
DEEPL_API_KEY=your_key make translate
```

This runs `scripts/translate.py` which creates draft Greek files for any English page that has no corresponding file in `content/el/`. Always review auto-translated output before publishing.

---

## Deployment (Podman)

### First time

```sh
# Start the Podman VM (macOS only, once per machine restart)
podman machine start

# Build site + container image + start container
make container
```

Site is live at **http://localhost:8080**.

### Routine update (after editing content)

```sh
make build      # rebuilds public/
make container  # rebuilds image and restarts container
```

### Stop the container

```sh
make stop
```

### Production server

On the server, run the same `make container` after pulling the latest code. Point a reverse proxy (Caddy recommended) at port 8080:

```
# /etc/caddy/Caddyfile
unonoctium.gr {
    reverse_proxy localhost:8080
}
```

Caddy handles TLS automatically via Let's Encrypt.

---

## File structure

```
unonoctium_website/
├── Makefile                    ← build, dev, deploy commands
├── Dockerfile                  ← nginx container (no Hugo runtime)
├── nginx.conf                  ← security headers, routing
├── pixi.toml                   ← dev environment (Hugo, Python)
│
├── config/_default/
│   ├── hugo.toml               ← languages, menus, site settings
│   └── params.toml             ← author name, email, social links
│
├── content/
│   ├── en/                     ← English content (write here first)
│   │   ├── _index.md           ← homepage
│   │   ├── about.md
│   │   ├── stories/            ← blog posts
│   │   ├── bits/               ← short fragments
│   │   └── notes/              ← quick notes
│   └── el/                     ← Greek translations (mirror structure)
│
├── assets/css/main.css         ← all styling, no external framework
│
├── layouts/
│   ├── _default/baseof.html    ← page shell (nav, sidebar, footer)
│   ├── index.html              ← homepage template
│   ├── partials/
│   │   ├── head.html
│   │   ├── nav.html
│   │   ├── sidebar.html
│   │   └── footer.html
│   ├── about/single.html       ← about page (two-col when photo set)
│   ├── stories/list.html
│   ├── bits/list.html
│   └── notes/list.html
│
├── static/
│   ├── logo.svg / logo.png     ← the balloon logo
│   └── img/
│       ├── profile/            ← 800×800 headshot
│       ├── field/              ← 1600×1067 explorations
│       └── research/           ← 1200×800 figures
│
├── data/
│   ├── publications.bib        ← source (copy from CV repo)
│   └── publications.yaml       ← generated — do not edit
│
├── i18n/
│   ├── en.yaml                 ← UI strings in English
│   └── el.yaml                 ← UI strings in Greek
│
└── scripts/
    ├── bib2data.py             ← BibTeX → data/publications.yaml
    └── translate.py            ← DeepL auto-translation helper
```

---

## Logo

The balloon logo (`logo.svg` / `logo.png`) was generated by `scripts/make_logo.py`.  
To regenerate after design changes:

```sh
pixi run python scripts/make_logo.py
```

The script writes both `logo.svg` and `logo.png` directly to the repo root.

---

## Browser support

Targets all evergreen browsers (Chrome, Firefox, Safari, Edge) released in the last 3 years.  
Notable compatibility notes:

- `backdrop-filter` (sidebar overlay blur): Chrome 76+, Safari 9+, Firefox 103+. Older Firefox gets a solid white overlay — functional, just no blur.
- `100dvh` (sidebar height on mobile): Safari 15.4+, Chrome 108+, Firefox 101+. Falls back to `100vh` silently.
- `gap` in flexbox: Safari 14.1+, Chrome 84+, Firefox 63+. Items wrap correctly on older Safari — slightly different spacing.
- CSS animations respect `prefers-reduced-motion`.
- Keyboard accessible: skip-link, sidebar toggled by checkbox (no JS required for open/close).
