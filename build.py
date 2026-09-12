#!/usr/bin/env python3
"""Build the site and markdown posts into pixel-themed HTML pages.

    uv run build.py            # build everything
    uv run build.py --serve    # build, then serve on :8899
    uv run build.py --new "My post title"

Reads src/data/site.json and src/posts/*.md -> writes the complete deployable
site to build/.

Every page links assets/site.css and assets/site.js, so the blog can never
drift from index.html — there is exactly one stylesheet for the whole site.

Front matter (YAML, between --- fences) is optional except `title`:

    ---
    title: Reading a binary config format
    date: 2026-08-28
    summary: One or two lines shown on the blog index.
    tags: [python, reverse engineering]
    draft: false
    ---
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import markdown
import yaml

from src.index import render_homepage
from src.blog import render_index, render_post
from src.photos import load_photos, render_photos

ROOT = Path(__file__).parent.resolve()
SRC_DIR = ROOT / "src"
POSTS_DIR = SRC_DIR / "posts"
BUILD_DIR = ROOT / "build"
BLOG_DIR = BUILD_DIR / "blog"
INDEX = BUILD_DIR / "blog.html"
SITE_JSON = SRC_DIR / "data" / "site.json"
PHOTOS_JSON = SRC_DIR / "data" / "photos.json"
PHOTOS_HTML = BUILD_DIR / "photos.html"

def slugify(text: str) -> str:
    """ASCII slug. Keeps filenames predictable so URLs never change."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text or "post"


def parse_date(value, fallback: dt.date) -> dt.date:
    """PyYAML already returns a date for unquoted 2026-08-28."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value.strip():
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return dt.datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        warn(f"unrecognised date {value!r}, using file mtime")
    return fallback


def warn(msg: str) -> None:
    print(f"  \033[33mwarning:\033[0m {msg}", file=sys.stderr)


def die(msg: str) -> None:
    print(f"\033[31merror:\033[0m {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_projects(site: dict) -> list[dict]:
    projects = site.get("projects")
    if not isinstance(projects, list) or not projects:
        die("site projects must be a non-empty array")

    required = {"name", "description", "tags", "status"}
    names = set()
    for i, project in enumerate(projects, 1):
        if not isinstance(project, dict):
            die(f"project {i} must be an object")
        missing = required - project.keys()
        if missing:
            die(f"project {i} is missing: {', '.join(sorted(missing))}")
        if not all(isinstance(project[key], str) and project[key].strip()
                   for key in ("name", "description", "status")):
            die(f"project {i} name, description, and status must be non-empty strings")
        if not isinstance(project["tags"], list) or not all(
            isinstance(tag, str) and tag.strip() for tag in project["tags"]
        ):
            die(f"project {i} tags must be an array of non-empty strings")
        if project["name"] in names:
            die(f"duplicate project name {project['name']!r}")
        names.add(project["name"])
        if "url" in project and (
            not isinstance(project["url"], str)
            or not re.match(r"^https://", project["url"])
        ):
            die(f"project {project['name']!r} url must be an https URL")
        if "code" in project and (
            not isinstance(project["code"], str) or not project["code"].strip()
        ):
            die(f"project {project['name']!r} code must be a non-empty string")
    return projects


def load_site() -> dict:
    if not SITE_JSON.exists():
        die(f"missing {SITE_JSON.relative_to(ROOT)}")
    try:
        site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{SITE_JSON.relative_to(ROOT)}: invalid JSON\n{e}")
        return {}
    if not isinstance(site, dict):
        die(f"{SITE_JSON.relative_to(ROOT)} must contain an object")
        return {}
    required = {
        "site", "blog", "navigation", "hero", "projects", "upstream",
        "about", "contact", "footer",
    }
    missing = required - site.keys()
    if missing:
        die(f"{SITE_JSON.relative_to(ROOT)} is missing: {', '.join(sorted(missing))}")
    if not isinstance(site["navigation"], list) or not site["navigation"]:
        die("site navigation must be a non-empty array")
    if not isinstance(site["blog"], dict):
        die("site blog must be an object")
    blog_required = {
        "title", "description", "all_posts_label", "home_label",
        "empty_message", "reading_time_suffix", "post_count_label",
        "posts_count_label",
    }
    blog_missing = blog_required - site["blog"].keys()
    if blog_missing:
        die(f"site blog is missing: {', '.join(sorted(blog_missing))}")
    if not all(
        isinstance(site["blog"][key], str) and site["blog"][key].strip()
        for key in blog_required
    ):
        die("site blog labels and messages must be non-empty strings")
    for i, item in enumerate(site["navigation"], 1):
        if not isinstance(item, dict) or not item.get("label") or not item.get("href"):
            die(f"navigation item {i} needs label and href")
    if not isinstance(site["upstream"].get("entries"), list):
        die("site upstream.entries must be an array")
    if not isinstance(site["about"].get("paragraphs"), list):
        die("site about.paragraphs must be an array")
    if not isinstance(site["about"].get("stats"), list):
        die("site about.stats must be an array")
    load_projects(site)
    return site


class Post:
    __slots__ = ("src", "meta", "body_md", "html", "slug", "date",
                 "title", "summary", "tags", "draft", "reading_min")

    def __init__(self, path: Path):
        self.src = path
        raw = path.read_text(encoding="utf-8")

        meta: dict = {}
        lines = raw.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            try:
                end = next(index for index, line in enumerate(lines[1:], 1)
                           if line.strip() == "---")
            except StopIteration:
                die(f"{path.name}: front matter is missing its closing ---")
            front_matter = "".join(lines[1:end])
            try:
                meta = yaml.safe_load(front_matter) or {}
            except yaml.YAMLError as e:
                die(f"{path.name}: bad YAML front matter\n{e}")
            if not isinstance(meta, dict):
                die(f"{path.name}: front matter must be a mapping")
            body = "".join(lines[end + 1:])
        else:
            body = raw
            warn(f"{path.name}: no front matter, deriving title from filename")

        self.meta = meta
        self.body_md = body
        mtime = dt.date.fromtimestamp(path.stat().st_mtime)

        self.title = str(meta.get("title") or path.stem.replace("-", " ").title())
        self.date = parse_date(meta.get("date"), mtime)
        self.slug = slugify(str(meta.get("slug") or path.stem))
        self.draft = bool(meta.get("draft", False))

        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        self.tags = [str(t).strip() for t in tags if str(t).strip()]

        md = markdown.Markdown(
            extensions=[
                "extra",          # tables, fenced code, footnotes, attr_list
                "codehilite",     # pygments; styled via .article-body .highlight
                "sane_lists",
                "smarty",
                "toc",
            ],
            extension_configs={
                "codehilite": {"guess_lang": False, "css_class": "highlight"},
                "smarty": {"smart_dashes": True, "smart_quotes": True},
            },
            output_format="html5",
        )
        self.html = md.convert(body)

        words = len(re.findall(r"\w+", re.sub(r"```.*?```", "", body, flags=re.S)))
        self.reading_min = max(1, round(words / 200))

        summary = meta.get("summary") or meta.get("description")
        if not summary:
            text = re.sub(r"<[^>]+>", "", self.html)
            text = " ".join(text.split())
            summary = (text[:180].rsplit(" ", 1)[0] + "…") if len(text) > 180 else text
            if not summary:
                warn(f"{path.name}: empty post body")
        self.summary = str(summary)

    @property
    def url(self) -> str:
        return f"blog/{self.slug}.html"

    @property
    def iso(self) -> str:
        return self.date.isoformat()

    @property
    def pretty(self) -> str:
        return self.date.strftime("%d %b %Y").upper()


def build() -> int:
    site = load_site()
    projects = load_projects(site)
    photos = load_photos()

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)
    shutil.copytree(SRC_DIR / "assets", BUILD_DIR / "assets")
    (BUILD_DIR / ".nojekyll").touch()

    (BUILD_DIR / "index.html").write_text(render_homepage(site), encoding="utf-8")
    PHOTOS_HTML.write_text(render_photos(site, photos), encoding="utf-8")

    if not POSTS_DIR.exists():
        POSTS_DIR.mkdir(parents=True)
        print(f"created {POSTS_DIR.relative_to(ROOT)}/")

    sources = sorted(POSTS_DIR.glob("*.md"))
    posts, drafts = [], 0
    for src in sources:
        p = Post(src)
        if p.draft:
            drafts += 1
            print(f"  skip  {src.name} (draft)")
            continue
        posts.append(p)

    seen: dict[str, str] = {}
    for p in posts:
        if p.slug in seen:
            die(f"duplicate slug {p.slug!r} from {p.src.name} and {seen[p.slug]}")
        seen[p.slug] = p.src.name

    posts.sort(key=lambda p: (p.date, p.title), reverse=True)

    if BLOG_DIR.exists():
        shutil.rmtree(BLOG_DIR)
    BLOG_DIR.mkdir(parents=True)

    for p in posts:
        out = BLOG_DIR / f"{p.slug}.html"
        out.write_text(render_post(p, site), encoding="utf-8")
        print(f"  ok    {p.src.name} -> {out.relative_to(ROOT)}")

    INDEX.write_text(render_index(posts, site), encoding="utf-8")

    n = len(posts)
    extra = f", {drafts} draft{'s' if drafts != 1 else ''} skipped" if drafts else ""
    print(
        f"built {n} post{'s' if n != 1 else ''}{extra};\n"
        f"updated {len(projects)} projects -> build/index.html;\n"
        f"updated {len(photos['entries'])} photo{'s' if len(photos['entries']) != 1 else ''} -> build/photos.html"
    )
    return n


def new_post(title: str) -> Path:
    POSTS_DIR.mkdir(exist_ok=True)
    slug = slugify(title)
    path = POSTS_DIR / f"{slug}.md"
    if path.exists():
        die(f"{path.relative_to(ROOT)} already exists")
    path.write_text(
        f"""---
title: {title}
date: {dt.date.today().isoformat()}
summary:
tags: []
draft: true
---

Write here. Set `draft: false` when it's ready to publish.
""",
        encoding="utf-8",
    )
    print(f"created {path.relative_to(ROOT)}")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Build markdown posts into the pixel site.")
    ap.add_argument("--new", metavar="TITLE", help="scaffold a new draft post")
    ap.add_argument("--serve", action="store_true", help="serve on :8899 after building")
    args = ap.parse_args()

    if args.new:
        new_post(args.new)
        return

    build()

    if args.serve:
        print("\nserving http://localhost:8899  (ctrl-c to stop)")
        try:
            subprocess.run(
                [sys.executable, "-m", "http.server", "8899"], cwd=BUILD_DIR, check=False
            )
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
