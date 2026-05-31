from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import unicodedata
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "Wiki"
OUT = ROOT / "_site"
REPO = "adarec1994/DragonAgeToolset"

GITHUB_WIKI_PREFIX = f"https://github.com/{REPO}/wiki/"
RAW_PREFIXES = (
    f"https://raw.githubusercontent.com/{REPO}/main/Wiki/assets/",
    f"https://raw.githubusercontent.com/{REPO}/main/assets/",
)

SKIP_PAGES = {"_Sidebar.mediawiki", "_Footer.mediawiki"}
ATTR_RE = re.compile(r'(?P<name>\b(?:href|src))="(?P<value>[^"]*)"')
SRCSET_RE = re.compile(r'(?P<name>\bsrcset)="(?P<value>[^"]*)"')


STYLE_CSS = r"""
:root {
  color-scheme: light;
  --bg: #f3f4f1;
  --surface: #ffffff;
  --panel: #f8fafc;
  --panel-strong: #e8eef5;
  --text: #18202a;
  --muted: #647083;
  --border: #cbd5e1;
  --link: #0b5cad;
  --link-hover: #064681;
  --accent: #7c2d12;
  --code: #eef2f7;
}

html[data-theme="dark"] {
  color-scheme: dark;
  --bg: #111316;
  --surface: #181b20;
  --panel: #20252c;
  --panel-strong: #2b323b;
  --text: #e6edf3;
  --muted: #9aa7b8;
  --border: #39424e;
  --link: #8ab4f8;
  --link-hover: #b8d2ff;
  --accent: #f2a66f;
  --code: #252b33;
}

* {
  box-sizing: border-box;
}

html {
  min-height: 100%;
}

body {
  margin: 0;
  min-height: 100%;
  background: var(--bg);
  color: var(--text);
  font: 14px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

a {
  color: var(--link);
  text-decoration: none;
}

a:hover {
  color: var(--link-hover);
  text-decoration: underline;
}

.site-shell {
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: auto;
  padding: 18px;
  border-right: 1px solid var(--border);
  background: var(--surface);
}

.brand {
  display: block;
  margin-bottom: 18px;
  color: var(--text);
  font-weight: 700;
  font-size: 18px;
}

.controls {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.search {
  width: 100%;
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  color: var(--text);
}

.theme-toggle {
  width: 40px;
  flex: 0 0 40px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--panel);
  color: var(--text);
  cursor: pointer;
}

.nav-title {
  margin: 18px 0 7px;
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}

.nav-list {
  display: grid;
  gap: 2px;
}

.nav-list a,
.search-results a {
  display: block;
  padding: 6px 8px;
  border-radius: 6px;
  color: var(--text);
}

.nav-list a:hover,
.search-results a:hover {
  background: var(--panel);
  text-decoration: none;
}

.content {
  min-width: 0;
  width: 100%;
  padding: 24px clamp(18px, 3vw, 52px) 64px;
}

.page-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.page-header h1 {
  margin: 0;
  font-size: clamp(24px, 2vw, 34px);
  line-height: 1.2;
  letter-spacing: 0;
}

.source-link {
  white-space: nowrap;
  color: var(--muted);
}

.wiki-content {
  max-width: none;
  overflow-wrap: anywhere;
}

.wiki-content p {
  max-width: 92rem;
}

.wiki-content img {
  max-width: 100%;
  height: auto;
}

.wiki-content table {
  max-width: 100%;
  border-collapse: collapse;
}

.wiki-content th,
.wiki-content td {
  border-color: var(--border);
}

.wiki-content pre,
.wiki-content code {
  background: var(--code);
  border-radius: 4px;
}

.wiki-content pre {
  overflow: auto;
  padding: 12px;
}

.wiki-content .gallery {
  display: flex !important;
  flex-wrap: wrap;
  gap: 14px;
  max-width: none !important;
  padding-left: 0;
}

.wiki-content .gallerybox {
  list-style: none;
}

.wiki-content .thumb {
  background: var(--panel);
}

html[data-theme="dark"] .wiki-content [style] {
  color: var(--text) !important;
  border-color: var(--border) !important;
}

html[data-theme="dark"] .wiki-content [style*="background"] {
  background: var(--panel) !important;
}

html[data-theme="dark"] .wiki-content h1 [style],
html[data-theme="dark"] .wiki-content h2 [style],
html[data-theme="dark"] .wiki-content h3 [style] {
  background: var(--panel-strong) !important;
}

@media (max-width: 860px) {
  .site-shell {
    display: block;
  }

  .sidebar {
    position: relative;
    height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--border);
  }

  .content {
    padding: 18px 14px 44px;
  }

  .page-header {
    display: block;
  }

  .source-link {
    display: inline-block;
    margin-top: 8px;
  }
}
""".strip()


SITE_JS = r"""
(function () {
  const root = window.SITE_ROOT || "";
  const html = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const input = document.getElementById("page-search");
  const results = document.getElementById("search-results");
  const stored = localStorage.getItem("theme");
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;

  function setTheme(theme) {
    html.dataset.theme = theme;
    localStorage.setItem("theme", theme);
    if (toggle) {
      toggle.textContent = theme === "dark" ? "Light" : "Dark";
      toggle.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    }
  }

  setTheme(stored || (prefersDark ? "dark" : "light"));

  if (toggle) {
    toggle.addEventListener("click", function () {
      setTheme(html.dataset.theme === "dark" ? "light" : "dark");
    });
  }

  function renderResults(query) {
    if (!results || !window.WIKI_PAGES) return;
    const q = query.trim().toLowerCase();
    results.textContent = "";
    if (!q) return;

    const matches = window.WIKI_PAGES
      .filter(function (page) {
        return page.title.toLowerCase().includes(q);
      })
      .slice(0, 60);

    for (const page of matches) {
      const link = document.createElement("a");
      link.href = root + page.url;
      link.textContent = page.title;
      results.appendChild(link);
    }

    if (!matches.length) {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "No matching pages";
      results.appendChild(empty);
    }
  }

  if (input) {
    input.addEventListener("input", function () {
      renderResults(input.value);
    });
  }
})();
""".strip()


def normalize_title(title: str) -> str:
    title = urllib.parse.unquote(title).replace("_", " ").replace(":", " - ")
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s+-\s+", " - ", title)
    return title.casefold()


def display_title(path: Path) -> str:
    return path.stem


def slug_base(title: str) -> str:
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_title).strip("-").lower()
    if not slug:
        slug = "page"
    return slug[:90].strip("-") or "page"


def build_page_maps(page_paths: list[Path]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    used: dict[str, str] = {}
    title_to_slug: dict[str, str] = {}
    norm_to_title: dict[str, str] = {}

    for path in page_paths:
        title = display_title(path)
        norm_to_title.setdefault(normalize_title(title), title)

        if title == "Home":
            title_to_slug[title] = "index"
            used["index"] = title
            continue

        base = slug_base(title)
        slug = base
        if slug in used and used[slug] != title:
            slug = f"{base}-{hashlib.sha1(title.encode('utf-8')).hexdigest()[:8]}"
        used[slug] = title
        title_to_slug[title] = slug

    title_to_url = {
        title: ("index.html" if slug == "index" else f"pages/{slug}.html")
        for title, slug in title_to_slug.items()
    }
    return title_to_slug, title_to_url, norm_to_title


def page_output_path(title: str, title_to_slug: dict[str, str]) -> Path:
    slug = title_to_slug[title]
    if slug == "index":
        return OUT / "index.html"
    return OUT / "pages" / f"{slug}.html"


def rel_url(current_title: str, target_url: str, title_to_url: dict[str, str]) -> str:
    current_url = title_to_url[current_title]
    current_dir = os.path.dirname(current_url) or "."
    return os.path.relpath(target_url, start=current_dir).replace("\\", "/")


def site_root_for(title: str, title_to_url: dict[str, str]) -> str:
    current_url = title_to_url[title]
    current_dir = os.path.dirname(current_url)
    if not current_dir:
        return ""
    depth = len(Path(current_dir).parts)
    return "../" * depth


def resolve_wiki_title(raw_title: str, norm_to_title: dict[str, str]) -> str | None:
    normalized = normalize_title(raw_title)
    return norm_to_title.get(normalized)


def rewrite_url(value: str, current_title: str, title_to_url: dict[str, str], norm_to_title: dict[str, str]) -> str:
    unescaped = html.unescape(value)
    root = site_root_for(current_title, title_to_url)

    for prefix in RAW_PREFIXES:
        if unescaped.startswith(prefix):
            return root + "assets/" + unescaped[len(prefix):]

    if unescaped.startswith(GITHUB_WIKI_PREFIX):
        tail = unescaped[len(GITHUB_WIKI_PREFIX):]
        target, hash_mark, fragment = tail.partition("#")
        target_title = resolve_wiki_title(urllib.parse.unquote(target), norm_to_title)
        if target_title:
            url = rel_url(current_title, title_to_url[target_title], title_to_url)
            if hash_mark:
                url += "#" + fragment
            return url
        return value

    parsed = urllib.parse.urlsplit(unescaped)
    if parsed.netloc.casefold() in {"www.datoolset.net", "datoolset.net"}:
        title = None
        if parsed.path.startswith("/wiki/"):
            title = parsed.path.removeprefix("/wiki/")
        elif parsed.path in {"/wiki/index.php", "/mw/index.php"}:
            query = urllib.parse.parse_qs(parsed.query)
            values = query.get("title") or query.get("amp;title")
            if values:
                title = values[0]
        if title:
            target_title = resolve_wiki_title(title, norm_to_title)
            if target_title:
                url = rel_url(current_title, title_to_url[target_title], title_to_url)
                if parsed.fragment:
                    url += "#" + parsed.fragment
                return url

    return value


def rewrite_srcset(value: str, current_title: str, title_to_url: dict[str, str], norm_to_title: dict[str, str]) -> str:
    rewritten = []
    for part in value.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        pieces = stripped.split(None, 1)
        url = rewrite_url(pieces[0], current_title, title_to_url, norm_to_title)
        rewritten.append(url + (f" {pieces[1]}" if len(pieces) > 1 else ""))
    return ", ".join(rewritten)


def rewrite_content(content: str, current_title: str, title_to_url: dict[str, str], norm_to_title: dict[str, str]) -> str:
    content = ATTR_RE.sub(
        lambda match: f'{match.group("name")}="{rewrite_url(match.group("value"), current_title, title_to_url, norm_to_title)}"',
        content,
    )
    content = SRCSET_RE.sub(
        lambda match: f'{match.group("name")}="{rewrite_srcset(match.group("value"), current_title, title_to_url, norm_to_title)}"',
        content,
    )
    return content


def quick_links(current_title: str, title_to_url: dict[str, str]) -> str:
    titles = [
        "Home",
        "Getting Started",
        "Tutorials",
        "Design",
        "Art",
        "Cinematography",
        "Sound and music",
        "Script",
        "Technical information",
    ]
    links = []
    for title in titles:
        if title in title_to_url:
            href = rel_url(current_title, title_to_url[title], title_to_url)
            links.append(f'<a href="{html.escape(href)}">{html.escape(title)}</a>')
    return "\n".join(links)


def render_page(title: str, content: str, title_to_url: dict[str, str], norm_to_title: dict[str, str]) -> str:
    root = site_root_for(title, title_to_url)
    rewritten = rewrite_content(content, title, title_to_url, norm_to_title)
    source_href = f"https://github.com/{REPO}/blob/main/Wiki/{urllib.parse.quote(title + '.mediawiki')}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - Dragon Age Toolset Wiki</title>
  <link rel="stylesheet" href="{root}assets/site.css">
</head>
<body>
  <script>window.SITE_ROOT = "{root}";</script>
  <div class="site-shell">
    <aside class="sidebar">
      <a class="brand" href="{root}index.html">Dragon Age Toolset Wiki</a>
      <div class="controls">
        <input id="page-search" class="search" type="search" placeholder="Search pages" autocomplete="off">
        <button id="theme-toggle" class="theme-toggle" type="button">Dark</button>
      </div>
      <div class="nav-title">Main Sections</div>
      <nav class="nav-list">{quick_links(title, title_to_url)}</nav>
      <div class="nav-title">Search Results</div>
      <nav id="search-results" class="search-results"></nav>
    </aside>
    <main class="content">
      <header class="page-header">
        <h1>{html.escape(title)}</h1>
        <a class="source-link" href="{source_href}">Source</a>
      </header>
      <article class="wiki-content">
{rewritten}
      </article>
    </main>
  </div>
  <script src="{root}assets/search-index.js"></script>
  <script src="{root}assets/site.js"></script>
</body>
</html>
"""


def copy_assets() -> None:
    source = WIKI / "assets"
    target = OUT / "assets"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    (target / "site.css").write_text(STYLE_CSS + "\n", encoding="utf-8")
    (target / "site.js").write_text(SITE_JS + "\n", encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "pages").mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    page_paths = sorted(
        [path for path in WIKI.glob("*.mediawiki") if path.name not in SKIP_PAGES],
        key=lambda path: display_title(path).casefold(),
    )
    title_to_slug, title_to_url, norm_to_title = build_page_maps(page_paths)

    copy_assets()

    index = []
    for path in page_paths:
        title = display_title(path)
        content = path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff")
        output_path = page_output_path(title, title_to_slug)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_page(title, content, title_to_url, norm_to_title), encoding="utf-8")
        index.append({"title": title, "url": title_to_url[title]})

    search_index = "window.WIKI_PAGES = " + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (OUT / "assets" / "search-index.js").write_text(search_index, encoding="utf-8")

    (OUT / "404.html").write_text(
        render_page(
            "Page not found",
            "<p>The requested page was not found. Use search to find a wiki page.</p>",
            {"Page not found": "404.html", **title_to_url},
            {"page not found": "Page not found", **norm_to_title},
        ),
        encoding="utf-8",
    )

    report = {
        "pages": len(page_paths),
        "assets": len([path for path in (OUT / "assets").rglob("*") if path.is_file()]),
        "output": str(OUT),
    }
    (OUT / "build-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
