#!/usr/bin/env python3
"""Verify contrast by reading the REAL tokens out of src/assets/site.css.

This theme has TWO surfaces running in OPPOSITE polarity on the rose theme:
    page   --bg    #d95763 rose  -> dark text  (--fg)
    panels --panel #663931 cocoa -> light text (--panel-fg)
so every check below states which surface it is on, and panel checks use
--panel-fg / --panel-accent rather than the page tokens. A single-polarity
audit would silently pass things that render dark-on-dark.

Resolves var() chains from the stylesheet so the audit cannot drift from
the CSS. Exit 0 = both themes pass WCAG AA.
"""
import re
import sys
from pathlib import Path

from contrast_audit import blend, grade, ratio, scanline

CSS = Path(__file__).parent.parent / "src" / "assets" / "site.css"


def strip_comments(s):
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def block(name):
    src = strip_comments(CSS.read_text())
    m = re.search(re.escape(name) + r"\s*\{(.*?)\}", src, re.S)
    if not m:
        sys.exit(f"could not find {name} in {CSS}")
    out = {}
    for decl in m.group(1).split(";"):
        if ":" in decl:
            k, v = decl.split(":", 1)
            k = k.strip()
            if k.startswith("--"):
                out[k[2:]] = v.strip()
    return out


def resolve(tokens, key, depth=0):
    if depth > 10:
        sys.exit(f"var() cycle resolving --{key}")
    v = tokens.get(key)
    if v is None:
        return None
    m = re.fullmatch(r"var\(\s*--([\w-]+)\s*\)", v)
    if m:
        return resolve(tokens, m.group(1), depth + 1)
    return v


NEEDED = ["bg", "fg", "panel", "accent", "ink", "code-str", "bark", "tan",
          "accent-contrast", "dim-soft", "dim-page", "title-shadow",
          "rose", "brand", "panel-fg", "panel-accent", "panel-accent-contrast", "panel-line", "panel-shadow",
          "paper"]

root = block(":root")
night = {**root, **block('[data-theme="night"]')}


def theme(tokens):
    return {k: resolve(tokens, k) for k in NEEDED}


def build_cases(T):
    """(label, fg, bg, alpha, is_large). Grouped by which surface it sits on."""
    page, panel = T["bg"], T["panel"]
    fg, pfg = T["fg"], T["panel-fg"]
    acc, pacc = T["accent"], T["panel-accent"]
    dpage, dsoft = float(T["dim-page"]), float(T["dim-soft"])
    return [
        ("== PAGE SURFACE ==", None, None, 1.0, False),
        ("body text",               fg,  page, 1.0,   False),
        ("body text .dim",          fg,  page, dpage, False),
        ("hero h1",                 fg,  page, 1.0,   True),
        ("hero h1 brand span",      T["brand"], page, 1.0, True),
        ("contact h2 brand span",   T["brand"], page, 1.0, True),
        ("nav links",               fg,  page, 1.0,   False),
        ("nav hover arrow",         acc, page, 1.0,   False),
        ("footer micro dim",        fg,  page, dpage, False),
        ("sec-head h2",             fg,  page, 1.0,   True),
        ("up-proj accent",          acc, page, 1.0,   False),
        ("up-what",                 fg,  page, dpage, False),
        ("up-ref",                  fg,  page, dpage, False),
        ("links a::before",         acc, page, 1.0,   False),
        ("post-date accent",        acc, page, 1.0,   False),
        ("post-title",              fg,  page, 1.0,   True),
        ("post-sum",                fg,  page, dpage, False),
        ("post-tags",               fg,  page, dpage, False),
        ("article-meta accent",     acc, page, 1.0,   False),
        ("article body text",       fg,  page, 1.0,   False),
        ("article link accent",     acc, page, 1.0,   False),
        ("article strong accent",   acc, page, 1.0,   False),
        ("article h3",              fg,  page, dpage, True),
        ("article th accent",       acc, page, 1.0,   False),
        ("footnote",                fg,  page, dpage, False),

        ("== PANEL SURFACE (opposite polarity) ==", None, None, 1.0, False),
        ("panel text",              pfg,  panel, 1.0,   False),
        ("work-title",              pfg,  panel, 1.0,   True),
        ("work-desc",               pfg,  panel, 0.85,  False),
        ("work-num accent",         pacc, panel, 1.0,   False),
        ("work tags",               pfg,  panel, 0.8,   False),
        ("work .go accent",         pacc, panel, 1.0,   False),
        ("div.work .go private",    pfg,  panel, dsoft, False),
        ("ticker text",             pfg,  panel, 1.0,   False),
        ("ticker diamond",          pacc, panel, 1.0,   False),
        ("card h3 accent",          pacc, panel, 1.0,   False),
        ("stat-note",               pfg,  panel, dsoft, False),
        ("blockquote text",         pfg,  panel, 1.0,   False),
        ("inline code",             pfg,  panel, 1.0,   False),

        ("== CODE BLOCK (dark panel) ==", None, None, 1.0, False),
        ("code text",               pfg,  panel, 1.0,  False),
        ("comment",                 pfg,  panel, 0.72, False),
        ("keyword",                 pacc, panel, 1.0,  False),
        ("string",                  T["code-str"], panel, 1.0, False),
        ("function name",           pfg,  panel, 1.0,  False),
        ("punctuation",             pfg,  panel, 0.7,  False),

        ("== BUTTONS / INVERTED ==", None, None, 1.0, False),
        ("btn rest",                page, fg,    1.0,  False),
        ("btn hover",   T["accent-contrast"], acc, 1.0, False),
        ("toggle hover", T["accent-contrast"], acc, 1.0, False),
        ("work:hover title",        T["panel-accent-contrast"], T["panel-accent"], 1.0, True),
        ("work:hover desc",         T["panel-accent-contrast"], T["panel-accent"], 0.85, False),
        ("work:hover num/go", T["panel-accent-contrast"], T["panel-accent"], 1.0, False),
    ]


def report(name, T):
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"  page {T['bg']} + {T['fg']}    panel {T['panel']} + {T['panel-fg']}")
    print(f"{'=' * 70}")
    print(f"{'element':<28}{'ratio':>8}  {'grade':<9}{'+CRT':>8}")
    print("-" * 70)
    fails = []
    for label, f, b, alpha, large in build_cases(T):
        if f is None:
            print(label)
            continue
        fg_hex = blend(f, b, alpha) if alpha < 1 else f
        r = ratio(fg_hex, b)
        r_crt = ratio(scanline(fg_hex), scanline(b))
        bad = r < (3.0 if large else 4.5)
        if bad:
            fails.append((label, r))
        print(f"{label:<28}{r:>8.2f}  {grade(r, large):<9}{r_crt:>8.2f}"
              + ("   <-- UNDER AA" if bad else ""))

    # decorative: must be visible, not legible
    ts = ratio(T["title-shadow"], T["fg"])
    print(f"{'title shadow vs fg':<28}{ts:>8.2f}  "
          f"{'visible' if ts >= 1.5 else 'INVISIBLE'}")
    if ts < 1.5:
        fails.append(("title shadow invisible", ts))

    print("-" * 70)
    if fails:
        print(f"FAIL: {len(fails)} below threshold")
        for lbl, r in fails:
            print(f"   {lbl}  {r:.2f}")
    else:
        print("PASS: every measured pair meets WCAG AA")
    return len(fails)


if __name__ == "__main__":
    L, N = theme(root), theme(night)
    bad = report("ROSE  (rose page / cocoa panels)", L)
    bad += report("NIGHT (dark page / dark panels)", N)

    print(f"\n{'=' * 70}\n  BRAND FIDELITY\n{'=' * 70}")
    avatar = "#d95763"
    problems = []

    if L["rose"].lower() != avatar:
        problems.append(f"--rose is {L['rose']}, avatar sprite is {avatar}")
    else:
        print(f"  --rose {L['rose']} == avatar sprite  OK")

    # --brand must be the EXACT avatar rose wherever the light theme uses it.
    # (The page surface is deliberately NOT the rose: a fully saturated
    # mid-tone red across a whole page is fatiguing, so rose is the brand
    # colour and paper is the surface. See the token comment in site.css.)
    if L["brand"].lower() != avatar:
        problems.append(f"--brand is {L['brand']}, expected the exact "
                        f"avatar rose {avatar}")
    else:
        print(f"  --brand {L['brand']} == exact avatar rose  OK")

    # large-text / non-text bar is 3:1; small-text accent bar is 4.5:1
    r_brand = ratio(L["brand"], L["bg"])
    print(f"  --brand on surface      {r_brand:.2f}:1  "
          f"{'OK (>=3.0 large/non-text)' if r_brand >= 3.0 else 'FAIL'}")
    if r_brand < 3.0:
        problems.append(f"--brand only {r_brand:.2f}:1, needs 3.0 for large text")

    # --accent is a PAGE colour and --panel-accent is a PANEL colour; each
    # is only ever checked against the surface it actually sits on. (They
    # are NOT interchangeable: on the sand theme --accent is 1.54:1 on the
    # cocoa panel, which is exactly why --panel-accent exists.)
    r_acc = ratio(L["accent"], L["bg"])
    print(f"  --accent on page        {r_acc:>5.2f}:1  "
          f"{'OK (>=4.5 small text)' if r_acc >= 4.5 else 'FAIL'}")
    if r_acc < 4.5:
        problems.append(f"--accent {r_acc:.2f}:1 on the page, needs 4.5")

    r_pacc = ratio(L["panel-accent"], L["panel"])
    print(f"  --panel-accent on panel {r_pacc:>5.2f}:1  "
          f"{'OK (>=4.5 small text)' if r_pacc >= 4.5 else 'FAIL'}")
    if r_pacc < 4.5:
        problems.append(f"--panel-accent {r_pacc:.2f}:1 on --panel, needs 4.5")

    # Panel fill and internal borders must remain distinguishable.
    r_fill = ratio(L["panel"], L["bg"])
    print(f"  panel fill vs page      {r_fill:>5.2f}:1")
    r_shadow = ratio(L["panel-shadow"], L["panel"])
    print(f"  panel shadow vs fill    {r_shadow:>5.2f}:1")

    # hairlines drawn inside a panel must be visible on it
    r_line = ratio(L["panel-line"], L["panel"])
    print(f"  --panel-line on panel   {r_line:>5.2f}:1  "
          f"{'OK' if r_line >= 3.0 else 'FAIL'}")
    if r_line < 3.0:
        problems.append(f"--panel-line {r_line:.2f}:1 on --panel, needs 3.0")

    # polarity sanity: --panel-fg must actually read on --panel
    from contrast_audit import lum
    for th, nm in ((L, "rose"), (N, "night")):
        light_panel = lum(th["panel"]) > 0.18
        light_text = lum(th["panel-fg"]) > lum(th["panel"])
        if light_panel and light_text:
            problems.append(f"{nm}: --panel is light but --panel-fg is lighter")
        if not light_panel and not light_text:
            problems.append(f"{nm}: --panel is dark but --panel-fg is darker")
    if not any("panel-fg" in p for p in problems):
        print("  panel polarity consistent in both themes  OK")

    print("-" * 70)
    if problems:
        print(f"FAIL: {len(problems)} brand rule violated")
        for p in problems:
            print(f"   {p}")
        bad += len(problems)
    else:
        print("PASS: brand colour is the exact avatar rose wherever it is legal")

    sys.exit(1 if bad else 0)
