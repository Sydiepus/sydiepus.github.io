#!/usr/bin/env python3
"""Static check: page-surface tokens used on elements that actually render
inside a PANEL.

Why this is not a pure-CSS check. `.links` is written as a bare selector,
but in index.html it lives inside `.card` — a dark panel. The selector
carries no hint of that, so scanning CSS alone cannot catch it (an earlier
version of this script missed exactly that bug). So: parse the HTML to
learn which classes are rendered inside a panel container, then flag CSS
rules that target those classes with page-only tokens.

Exit 0 = clean.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent.parent
CSS = ROOT / "src" / "assets" / "site.css"

# Class names whose elements render on the PANEL surface.
PANEL_CLASSES = {"pbox", "card", "work", "ticker"}
# Selectors that are panel context by construction (generated markup).
PANEL_SELECTORS = [".article-body pre", ".article-body blockquote",
                   ".article-body code", ".pbox", ".card", ".work", ".ticker"]

# Tokens keyed to the PAGE surface. Illegal on a panel.
PAGE_ONLY = ["--accent", "--brand", "--dim-page"]
# --fg is page-only for TEXT, but legitimately draws the frame and the
# hover invert, so it is checked only on colour-bearing properties.
FG_TEXT_PROPS = {"color", "caret-color", "text-decoration-color"}


class PanelScanner(HTMLParser):
    """Collect every class that appears inside a panel container."""

    def __init__(self):
        super().__init__()
        self.depth_stack = []
        self.inside = 0
        self.found = set()

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "img", "meta", "link", "input", "hr"):
            return
        classes = set()
        for k, v in attrs:
            if k == "class" and v:
                classes = set(v.split())
        opens_panel = bool(classes & PANEL_CLASSES)
        if self.inside and classes:
            self.found |= classes
        self.depth_stack.append(opens_panel)
        if opens_panel:
            self.inside += 1

    def handle_endtag(self, tag):
        if self.depth_stack:
            if self.depth_stack.pop():
                self.inside -= 1


def strip_comments(s):
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def rules(src):
    src = strip_comments(src)
    out, buf, sel, depth = [], "", "", 0
    for c in src:
        if c == "{":
            depth += 1
            if depth == 1:
                sel, buf = buf.strip(), ""
            else:
                buf += c
        elif c == "}":
            depth -= 1
            if depth == 0:
                if sel.startswith("@"):
                    out.extend(rules(buf))
                else:
                    out.append((sel, buf))
                buf, sel = "", ""
            else:
                buf += c
        else:
            buf += c
    return out


def main():
    panel_classes = set()
    for page in (ROOT / "build").glob("*.html"):
        p = PanelScanner()
        p.feed(page.read_text(encoding="utf-8"))
        panel_classes |= p.found
    for page in (ROOT / "build" / "blog").glob("*.html"):
        p = PanelScanner()
        p.feed(page.read_text(encoding="utf-8"))
        panel_classes |= p.found

    print(f"classes rendered inside a panel: {len(panel_classes)}")

    def is_panel_ctx(sel):
        for b in [x.strip() for x in sel.split(",") if x.strip()]:
            if any(s in b for s in PANEL_SELECTORS):
                continue
            hit = re.findall(r"\.([\w-]+)", b)
            if hit and any(h in panel_classes for h in hit):
                continue
            return False
        return True

    problems, checked = [], 0
    for sel, body in rules(CSS.read_text()):
        if not is_panel_ctx(sel):
            continue
        checked += 1
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, val = decl.split(":", 1)
            prop, val = prop.strip(), val.replace(" ", "")
            if prop.startswith("--"):
                continue
            for tok in PAGE_ONLY:
                if f"var({tok})" in val:
                    problems.append((sel, prop, tok))
            if "var(--fg)" in val and prop in FG_TEXT_PROPS:
                problems.append((sel, prop, "--fg"))

    print(f"panel-context rules checked:     {checked}")
    print("-" * 66)
    if problems:
        print(f"FAIL: {len(problems)} page-only token(s) on a panel\n")
        for sel, prop, tok in problems:
            short = sel if len(sel) <= 44 else sel[:41] + "..."
            print(f"  {short}\n      {prop}: var({tok})   <- needs --panel-*")
        print("\nA page token on a panel renders same-on-same. Use")
        print("--panel-fg / --panel-accent / --panel-line / --dim-soft.")
        return 1
    print("PASS: no page-only tokens on panel-rendered elements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
