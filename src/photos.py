"""Render the photography page from ``data/photos.json``."""

from __future__ import annotations

import json
from pathlib import Path

from .page import esc, render_footer, render_head

ROOT = Path(__file__).parent.parent.resolve()
PHOTOS_JSON = ROOT / "src" / "data" / "photos.json"
PHOTOS_HTML = ROOT / "build" / "photos.html"


def load_photos() -> dict:
    try:
        data = json.loads(PHOTOS_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{PHOTOS_JSON.relative_to(ROOT)}: invalid JSON\n{exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit(f"{PHOTOS_JSON.relative_to(ROOT)} must contain an object")
    required = {"title", "description", "intro", "entries"}
    missing = required - data.keys()
    if missing:
        raise SystemExit(
            f"{PHOTOS_JSON.relative_to(ROOT)} is missing: {', '.join(sorted(missing))}"
        )
    if not isinstance(data["entries"], list):
        raise SystemExit(f"{PHOTOS_JSON.relative_to(ROOT)} entries must be an array")

    entry_required = {"image", "camera", "film"}
    entry_optional = {"title", "place", "alt", "app"}
    for number, entry in enumerate(data["entries"], 1):
        if not isinstance(entry, dict):
            raise SystemExit(f"photo {number} must be an object")
        missing = entry_required - entry.keys()
        if missing:
            raise SystemExit(f"photo {number} is missing: {', '.join(sorted(missing))}")
        if not all(isinstance(entry[key], str) and entry[key].strip()
                   for key in entry_required):
            raise SystemExit(f"photo {number} fields must be non-empty strings")
        if not all(isinstance(entry[key], str) for key in entry_optional if key in entry):
            raise SystemExit(f"photo {number} optional fields must be strings")

    return data


def render_photos(site: dict, photos: dict) -> str:
    entries = []
    for photo in photos["entries"]:
        title = photo.get("title", "").strip()
        place = photo.get("place", "").strip()
        alt = photo.get("alt", "").strip() or title or "Photograph"
        app = photo.get("app", "").strip()
        image = photo["image"]
        if image.lower().endswith(".mp4"):
            media = (
                f'<video src="{esc(image)}" aria-label="{esc(alt)}" '
                'controls loop muted playsinline preload="metadata"></video>'
            )
        else:
            media = (
                f'<a class="photo-open" href="{esc(image)}" '
                f'data-photo-full="{esc(image)}" data-photo-title="{esc(title)}" '
                f'data-photo-place="{esc(place)}" data-photo-camera="{esc(photo["camera"])}" '
                f'data-photo-film="{esc(photo["film"])}" data-photo-app="{esc(app if "app" in photo else "")}" '
                f'aria-label="View {esc(alt)} full size">'
                f'<img src="{esc(image)}" alt="{esc(alt)}" loading="lazy"></a>'
            )
        caption = ""
        if title:
            caption = f'<span class="photo-title">{esc(title)}</span>'
        if place:
            caption += f'<span class="photo-place">{esc(place)}</span>'
        caption_html = f'<div class="photo-caption">{caption}</div>' if caption else ""
        app_html = f'<span class="photo-app">{esc(app)}</span>' if app else ""
        entries.append(f"""      <figure class="photo-card reveal">
        <div class="photo-frame">{media}</div>
        <figcaption>
          {caption_html}
          <div class="photo-meta"><span class="photo-camera">{esc(photo["camera"])}</span><span class="photo-film">{esc(photo["film"])}</span>{app_html}</div>
        </figcaption>
      </figure>""")

    return render_head(
        site,
        photos["title"],
        photos["description"],
        active="photos",
        body_class="photos-page subpage",
    ) + f"""
<main class="wrap" style="padding-block:clamp(28px,5vw,64px)">
  <section>
    <div class="sec-head reveal">
      <h1>{esc(photos["title"])}</h1>
      <span class="micro dim">{len(photos["entries"]):02d} frames</span>
    </div>
    <p class="photo-intro reveal">{esc(photos["intro"])}</p>
    <div class="photo-grid">
{chr(10).join(entries)}
    </div>
  </section>
</main>
<dialog class="photo-lightbox" id="photoLightbox" aria-label="Full-size photo viewer">
  <div class="photo-lightbox-body">
    <img id="photoLightboxImage" src="" alt="">
    <div class="photo-lightbox-caption">
      <div id="photoLightboxTitle"></div>
      <div id="photoLightboxPlace"></div>
      <div class="photo-meta">
        <span class="photo-camera" id="photoLightboxCamera"></span>
        <span class="photo-film" id="photoLightboxFilm"></span>
        <span class="photo-app" id="photoLightboxApp"></span>
      </div>
    </div>
    <div class="photo-lightbox-actions">
      <a class="btn" id="photoDownload" href="" download>Download</a>
      <button class="btn btn-ghost" id="photoClose" type="button">Close</button>
    </div>
  </div>
</dialog>
""" + render_footer(site) + """
</body>
</html>
"""


def main() -> None:
    site = json.loads((ROOT / "src" / "data" / "site.json").read_text(encoding="utf-8"))
    PHOTOS_HTML.write_text(render_photos(site, load_photos()), encoding="utf-8")


if __name__ == "__main__":
    main()
