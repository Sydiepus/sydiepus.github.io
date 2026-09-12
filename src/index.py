#!/usr/bin/env python3
"""Render the homepage from ``data/site.json``.

The homepage is assembled as one document instead of being patched into a
hand-written HTML file.  This keeps the JSON content and the generated markup
in one place and means the build never needs to locate sections with regexes.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from .page import esc, render_footer, render_head

ROOT = Path(__file__).parent.parent.resolve()
SITE_JSON = ROOT / "src" / "data" / "site.json"
HOME = ROOT / "build" / "index.html"


def render_projects(projects: list[dict]) -> str:
    rows = []
    for number, project in enumerate(projects, 1):
        tags = "".join(f"<i>{esc(tag)}</i>" for tag in project["tags"])
        description = esc(project["description"])
        if project.get("code"):
            description += f" <code>{esc(project['code'])}</code>"
        body = f"""        <span class="work-num">{number:02d}</span>
        <span class="work-body">
          <span class="work-title">{esc(project["name"])}</span>
          <span class="work-desc">{description}</span>
          <span class="work-tags">{tags}</span>
        </span>
        <span class="go">{esc(project["status"])}</span>"""
        if project.get("url"):
            rows.append(
                f'      <a class="work reveal" href="{esc(project["url"])}" '
                'target="_blank" rel="noopener">\n' + body + "\n      </a>"
            )
        else:
            rows.append(f'      <div class="work reveal">\n{body}\n      </div>')
    return "\n\n".join(rows)


def render_upstream(upstream: dict) -> str:
    rows = []
    for entry in upstream["entries"]:
        what = esc(entry["what"])
        if entry.get("code"):
            code = esc(entry["code"])
            what = what.replace(code, f"<code>{code}</code>")
        row = f"""        <span class="up-proj">{esc(entry["project"])}</span>
        <span class="up-what">{what}</span>
        <span class="up-ref">{esc(entry["ref"])}</span>"""
        if entry.get("url"):
            rows.append(
                f'      <a class="up reveal" href="{esc(entry["url"])}" '
                f'target="_blank" rel="noopener">\n{row}\n      </a>'
            )
        else:
            rows.append(f'      <div class="up up-plain reveal">\n{row}\n      </div>')
    return "\n\n".join(rows)


def render_about(about: dict) -> str:
    paragraphs = "\n".join(
        f"        <p>{esc(paragraph)}</p>" for paragraph in about["paragraphs"]
    )
    stats = "\n".join(
        f"""        <div class="stat">
          <div class="stat-top"><span>{esc(stat["label"])}</span><span data-out>0</span></div>
          <div class="bar"><i data-level="{int(stat["value"])}"></i></div>
        </div>"""
        for stat in about["stats"]
    )
    links = "\n".join(
        f'          <a href="{esc(link["url"])}" target="_blank" rel="noopener">{esc(link["label"])}</a>'
        for link in about["links"]
    )
    stats_note = (
        f'        <p class="stat-note">{esc(about["stats_note"])}</p>'
        if about.get("stats_note", "").strip()
        else ""
    )
    return f"""    <div class="sec-head reveal">
      <h2>{esc(about["heading"])}</h2>
      <span class="micro dim" data-role>{esc(about["label"])}</span>
    </div>
    <div class="about">
      <div class="reveal">
{paragraphs}
      </div>
      <div class="card pbox reveal">
        <h3>&#9670; {esc(about["stats_heading"])}</h3>
{stats_note}
{stats}
        <div class="links">
{links}
        </div>
      </div>
    </div>"""


def render_homepage(site: dict) -> str:
    meta = site["site"]
    hero = site["hero"]
    contact = site["contact"]
    upstream = site["upstream"]
    projects = site["projects"]
    project_rows = render_projects(projects)
    upstream_rows = render_upstream(upstream)
    about = render_about(site["about"])
    shell = render_head(
        site,
        meta["title"],
        meta["description"],
        active="home",
        canonical=meta["canonical"],
        brand_href="#top",
    )
    return shell + f"""
<main id="top">
  <section class="wrap hero">
    <div>
      <p class="micro dim">&#9654; {esc(hero["eyebrow"])} <span class="blink">_</span></p>
      <h1>{esc(hero["title_before"])}<span>{esc(hero["title_accent"])}</span></h1>
      <p class="hero-sub">{esc(hero["subtitle"])}</p>
      <div class="cta-row">
        <a class="btn" href="#work">{esc(hero["projects_label"])} &#9654;</a>
        <a class="btn btn-ghost" href="{esc(hero["github_url"])}" target="_blank" rel="noopener">{esc(hero["github_label"])}</a>
      </div>
    </div>
    <figure class="hero-art">
      <img src="assets/potato.png" alt="Pixel-art potato avatar" width="320" height="320">
    </figure>
  </section>
  <section class="wrap" id="work">
    <div class="sec-head reveal">
      <h2>Projects</h2>
      <span class="micro dim">{len(projects):02d} entries</span>
    </div>
    <div class="work-list">
{project_rows}
    </div>
  </section>
  <section class="wrap" id="upstream">
    <div class="sec-head reveal">
      <h2>{esc(upstream["heading"])}</h2>
      <span class="micro dim">{esc(upstream["label"])}</span>
    </div>
    <div class="up-list">
{upstream_rows}
    </div>
  </section>
  <section class="wrap" id="about">
{about}
  </section>
  <section class="wrap contact" id="contact">
    <p class="micro dim reveal">&#9654; {esc(contact["intro"])}</p>
    <h2 class="reveal">{esc(contact["heading_before"])}<span>{esc(contact["heading_accent"])}</span></h2>
    <div class="contact-sub reveal">
      <a class="btn" href="{esc(contact["github_url"])}" target="_blank" rel="noopener">GitHub &#9654;</a>
      <a class="btn btn-ghost" href="mailto:{esc(contact["email"])}" data-email>{esc(contact["email"])}</a>
    </div>
  </section>
{render_footer(site)}
</main>
</body>
</html>
"""


def main() -> None:
    site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    HOME.write_text(render_homepage(site), encoding="utf-8")


if __name__ == "__main__":
    main()
