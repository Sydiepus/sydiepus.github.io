#!/usr/bin/env python3
"""Can the exact GitHub avatar rose #d95763 be the accent on the paper surface?

Splits accent usages by WCAG text-size class, because large text only needs
3:1 while small text needs 4.5:1 — and almost every accent usage on this
site is SMALL (Press Start 2P at --t-micro/--t-label).
"""
import colorsys

from contrast_audit import grade, ratio

ROSE = "#d95763"          # exact, sampled from the avatar
PAPER = "#fff3ee"
FG = "#3d2220"
PANEL = "#f7ddd2"

r = ratio(ROSE, PAPER)
print(f"exact avatar rose {ROSE} on paper {PAPER}: {r:.2f}:1  {grade(r)}")
print(f"  small text needs 4.5  -> {'PASS' if r >= 4.5 else 'FAIL'}")
print(f"  large text needs 3.0  -> {'PASS' if r >= 3.0 else 'FAIL'}")
print(f"  non-text/UI needs 3.0 -> {'PASS' if r >= 3.0 else 'FAIL'}")

print("\nWhere --accent is actually used, by computed size:")
USES = [
    # (selector, font-size token, min px at smallest viewport, is_text)
    (".hero h1 span",        "--t-hero",  1.35 * 16, True),
    (".contact h2 span",     "--t-mega",  1.50 * 16, True),
    (".nav-links a::before", "--t-micro", 0.50 * 16, True),
    (".work-num",            "--t-label", 0.55 * 16, True),
    (".card h3",             "--t-label", 0.55 * 16, True),
    (".up-proj",             "--t-label", 0.55 * 16, True),
    (".links a::before",     "--t-micro", 0.50 * 16, True),
    (".post-date",           "--t-micro", 0.50 * 16, True),
    (".article-meta",        "--t-micro", 0.50 * 16, True),
    (".article-body a",      "--t-lead",  1.15 * 16, True),
    (".article-body strong", "--t-lead",  1.15 * 16, True),
    (".article-body th",     "--t-micro", 0.50 * 16, True),
    ("code .k keyword",      "0.82rem",   0.82 * 16, True),
    (".bar i (XP fill)",     "n/a",       0,         False),
    (":focus-visible outline", "n/a",     0,         False),
    ("title-shadow",         "n/a",       0,         False),
]
big = []
small = []
for sel, tok, px, is_text in USES:
    if not is_text:
        need, cls = 3.0, "non-text"
        big.append(sel)
    elif px >= 24:
        need, cls = 3.0, "large"
        big.append(sel)
    else:
        need, cls = 4.5, "SMALL"
        small.append(sel)
    ok = "ok" if r >= need else "FAIL"
    size = f"{px:.0f}px" if px else "  -  "
    print(f"  {sel:<24}{tok:<11}{size:>7}  {cls:<9}needs {need}  exact-rose {ok}")

print(f"\n{len(big)} usages can carry the exact rose; {len(small)} cannot.")
print("Note: 24px is the WCAG large-text floor for regular weight. --t-hero")
print("only reaches 21.6px at the SMALLEST viewport, so even the hero is")
print("borderline there and grows well past 24px on desktop.")

print("\nMinimal darkening of #d95763 that reaches 4.5:1 on paper,")
print("preserving hue and saturation (HLS lightness sweep):")
rr, gg, bb = (int(ROSE[i:i + 2], 16) / 255 for i in (1, 3, 5))
h, l, s = colorsys.rgb_to_hls(rr, gg, bb)
print(f"  source HLS: h={h * 360:.1f}deg  l={l:.3f}  s={s:.3f}")
best = None
for step in range(0, 1000):
    li = l * (1 - step / 1000)
    nr, ng, nb = colorsys.hls_to_rgb(h, li, s)
    hexc = "#%02x%02x%02x" % (round(nr * 255), round(ng * 255), round(nb * 255))
    cr = ratio(hexc, PAPER)
    if cr >= 4.5:
        best = (hexc, cr, li)
        break
hexc, cr, li = best
print(f"  -> {hexc}  {cr:.2f}:1   (lightness {l:.3f} -> {li:.3f}, hue unchanged)")
print(f"     current --rose-accent #b0313f = {ratio('#b0313f', PAPER):.2f}:1")
print(f"     {hexc} on panel {PANEL} = {ratio(hexc, PANEL):.2f}:1")
