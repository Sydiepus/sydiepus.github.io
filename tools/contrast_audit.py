#!/usr/bin/env python3
"""Throwaway: WCAG contrast audit of the rose vs night themes."""


def lum(hexs):
    h = hexs.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def blend(fg, bg, alpha):
    """CSS opacity on text = simple src-over composite against bg."""
    f, b = fg.lstrip("#"), bg.lstrip("#")
    out = []
    for i in (0, 2, 4):
        fv, bv = int(f[i:i + 2], 16), int(b[i:i + 2], 16)
        out.append(round(fv * alpha + bv * (1 - alpha)))
    return "#%02x%02x%02x" % tuple(out)


def scanline(bg):
    """body::before = rgba(0,0,0,.13) at opacity .55 over half the rows.
    Averaged effective darkening = .13 * .55 / 2 per pixel column pair."""
    return blend("#000000", bg, 0.13 * 0.55 / 2)


ROSE = {
    "bg": "#d95763", "fg": "#fff3ee", "panel": "#663931",
    "accent": "#ffd166", "ink": "#2b1b1c", "code-str": "#f2c48a",
    "bark": "#8f563b",
}
NIGHT = {
    "bg": "#2b1b1c", "fg": "#f6e5d8", "panel": "#3d2626",
    "accent": "#d9a066", "ink": "#2b1b1c", "code-str": "#f2c48a",
    "bark": "#8f563b",
}


def grade(r, large=False):
    need = 3.0 if large else 4.5
    if r >= 7.0:
        return "AAA"
    if r >= need:
        return "AA "
    if r >= 3.0:
        return "aa-large" if not large else "AA "
    return "FAIL"


CASES = [
    # (label, fg token, bg token, opacity, is_large_text)
    ("body text",                "fg",       "bg",    1.0,  False),
    ("body text .dim (.75)",     "fg",       "bg",    0.75, False),
    ("hero h1 (large)",          "fg",       "bg",    1.0,  True),
    ("hero h1 accent span",      "accent",   "bg",    1.0,  True),
    ("nav links",                "fg",       "bg",    1.0,  False),
    ("nav hover arrow",          "accent",   "bg",    1.0,  False),
    ("footer .micro.dim",        "fg",       "bg",    0.75, False),
    ("--- panel surfaces ---",   None,       None,    1.0,  False),
    ("work-title on panel",      "fg",       "panel", 1.0,  True),
    ("work-desc on panel(.85)",  "fg",       "panel", 0.85, False),
    ("work-num accent/panel",    "accent",   "panel", 1.0,  False),
    ("work tags (.8)",           "fg",       "panel", 0.8,  False),
    ("ticker text on panel",     "fg",       "panel", 1.0,  False),
    ("card h3 accent/panel",     "accent",   "panel", 1.0,  False),
    ("stat-note (.6)",           "fg",       "panel", 0.6,  False),
    ("--- on rose bg ---",       None,       None,    1.0,  False),
    ("up-proj accent/bg",        "accent",   "bg",    1.0,  False),
    ("up-what (.85)",            "fg",       "bg",    0.85, False),
    ("up-ref (.55)",             "fg",       "bg",    0.55, False),
    ("links a::before accent",   "accent",   "bg",    1.0,  False),
    ("post-date accent/bg",      "accent",   "bg",    1.0,  False),
    ("post-title",               "fg",       "bg",    1.0,  True),
    ("post-sum (.85)",           "fg",       "bg",    0.85, False),
    ("post-tags (.8)",           "fg",       "bg",    0.8,  False),
    ("article-meta accent/bg",   "accent",   "bg",    1.0,  False),
    ("article body text",        "fg",       "bg",    1.0,  False),
    ("article link accent",      "accent",   "bg",    1.0,  False),
    ("article strong accent",    "accent",   "bg",    1.0,  False),
    ("article h3 (.9)",          "fg",       "bg",    0.9,  True),
    ("footnote (.8)",            "fg",       "bg",    0.8,  False),
    ("--- code block ---",       None,       None,    1.0,  False),
    ("code text on panel",       "fg",       "panel", 1.0,  False),
    ("comment (.72)",            "fg",       "panel", 0.72, False),
    ("keyword accent/panel",     "accent",   "panel", 1.0,  False),
    ("string code-str/panel",    "code-str", "panel", 1.0,  False),
    ("punctuation (.7)",         "fg",       "panel", 0.7,  False),
    ("--- buttons ---",          None,       None,    1.0,  False),
    ("btn: bg-on-fg",            "bg",       "fg",    1.0,  False),
    ("btn hover: ink-on-accent", "ink",      "accent", 1.0, False),
]


def run(name, T):
    print(f"\n{'=' * 64}\n  {name.upper()} THEME   bg={T['bg']}  fg={T['fg']}  accent={T['accent']}\n{'=' * 64}")
    print(f"{'element':<28}{'ratio':>8}  {'grade':<9}{'ratio+CRT':>10}")
    print("-" * 64)
    fails = 0
    for label, f, b, alpha, large in CASES:
        if f is None:
            print(f"{label}")
            continue
        bg_hex = T[b]
        fg_hex = blend(T[f], bg_hex, alpha) if alpha < 1 else T[f]
        r = ratio(fg_hex, bg_hex)
        # with the CRT scanline + dither overlay sitting on top of both
        r_crt = ratio(scanline(fg_hex), scanline(bg_hex))
        g = grade(r, large)
        if g == "FAIL" or (g == "aa-large" and not large):
            fails += 1
        mark = "  <-- " + ("FAIL" if g == "FAIL" else "under AA") if g in ("FAIL", "aa-large") and not large else ""
        print(f"{label:<28}{r:>8.2f}  {g:<9}{r_crt:>10.2f}{mark}")
    print("-" * 64)
    print(f"{fails} of {len([c for c in CASES if c[1]])} checks below their WCAG AA threshold")
    return fails


if __name__ == "__main__":
    run("rose", ROSE)
    run("night", NIGHT)
