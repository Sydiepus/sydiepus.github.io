"""Shared HTML shell helpers for generated pages."""

from __future__ import annotations

import html
from datetime import date


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_navigation(site: dict, prefix: str = "", active: str = "",
                      anchor_prefix: str = "") -> str:
    links = []
    for item in site["navigation"]:
        href = item["href"]
        if prefix and href == "blog.html":
            href = prefix + href
        elif href.startswith("#"):
            href = prefix + anchor_prefix + href

        classes = []
        if item.get("key") == active:
            classes.append("active")
        if item.get("hide_small"):
            classes.append("hide-sm")
        class_attr = f' class="{" ".join(classes)}"' if classes else ""
        current = ' aria-current="page"' if item.get("key") == active else ""
        links.append(
            f'      <a href="{esc(href)}"{class_attr}{current}>{esc(item["label"])}</a>'
        )
    return "\n".join(links)


def render_head(site: dict, title: str, desc: str, depth: int = 0,
                active: str = "home", page_type: str = "website",
                canonical: str | None = None, brand_href: str | None = None,
                body_class: str = "") -> str:
    up = "../" * depth
    anchor_prefix = "" if depth else ("index.html" if active in {"blog", "photos"} else "")
    nav = render_navigation(site, up, active, anchor_prefix)
    meta = site["site"]
    canonical_tag = (
        f'<link rel="canonical" href="{esc(canonical)}">\n'
        if canonical else ""
    )
    brand_target = brand_href or f"{up}index.html"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{esc(meta["author"])}">
{canonical_tag}
<meta property="og:type" content="{esc(page_type)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{esc(meta["og_image"])}">
<meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Silkscreen:wght@400;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="icon" href="{up}assets/potato-32.png">
<link rel="stylesheet" href="{up}assets/site.css">
<script>try{{if(localStorage.getItem("px-theme")==="night")document.documentElement.setAttribute("data-theme","night")}}catch(e){{}}</script>
<script src="{up}assets/site.js" defer></script>
<noscript><style>.reveal{{opacity:1!important;transform:none!important}}</style></noscript>
</head>
<body class="{esc(body_class)}">
<header>
  <div class="wrap nav">
    <a class="brand" href="{esc(brand_target)}">
      <img src="{up}assets/potato.png" alt="" aria-hidden="true" width="36" height="36">
      <span class="brand-name">{esc(meta["name"])}</span>
    </a>
    <nav class="nav-links" id="siteNav">
{nav}
      <button class="toggle" id="themeToggle" type="button" aria-label="Switch to dark theme" aria-pressed="false" data-icon="moon"></button>
    </nav>
    <button class="menu-toggle" id="menuToggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="siteNav">Menu</button>
  </div>
</header>
"""


def render_footer(site: dict, depth: int = 0) -> str:
    up = "../" * depth
    return f"""
<footer class="wrap">
  <span class="micro dim">&copy; <span id="year">{date.today().year}</span> <span>{esc(site["site"]["name"])}</span></span>
  <img src="{up}assets/potato.png" alt="" aria-hidden="true" width="24" height="24">
  <span class="micro dim">{esc(site["footer"]["text"])}</span>
</footer>
"""
