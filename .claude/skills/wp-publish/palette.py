# /// script
# requires-python = ">=3.11"
# ///
"""Derive a site palette from a butterfly, and the CSS that carries it.

    uv run --script palette.py admiral --harmony triad --ground light \
        --tint specimen --css out.css --json out.json

Same maths as the picker at https://claude.ai/artifact/MMZUy9NdjNobyWahefgPqH,
so a configuration named there reproduces here exactly.

Five slots, because that is what a Twenty Twenty-Three style variation holds:
`base` and `contrast` are the page, and `primary`/`secondary`/`tertiary` are
the harmony. Every accent is lifted until it clears 4.5:1 on the ground --
hue and saturation untouched, so it stays recognisably the specimen's.

The CSS covers three systems from the one palette: Pygments for posts
published since highlighting moved into this script, SyntaxHighlighter for
the posts that predate it, and inline code everywhere.
"""

import argparse
import json

SPECIMENS = {
    "morpho":     ("Morpho",      "peleides",   "Blue Morpho",         "#1B6CA8", "#4FA8DE", "#14161C", "#0E1014", "#D9CBA8"),
    "monarch":    ("Danaus",      "plexippus",  "Monarch",             "#D9661E", "#E8903A", "#17120F", "#17120F", "#F2EDE4"),
    "ulysses":    ("Papilio",     "ulysses",    "Ulysses Swallowtail", "#1E7FD4", "#35A7F0", "#0D0F14", "#0D0F14", "#6FC5F5"),
    "glasswing":  ("Greta",       "oto",        "Glasswing",           "#C87A3E", "#E8E9E4", "#2A2521", "#2A2521", "#8C5A34"),
    "admiral":    ("Vanessa",     "atalanta",   "Red Admiral",         "#C4331F", "#E0603F", "#1A1614", "#1A1614", "#EDE8E0"),
    "hairstreak": ("Callophrys",  "rubi",       "Green Hairstreak",    "#4E7A3A", "#7BA05B", "#3A3122", "#6B5A43", "#C9CBA3"),
    "emperor":    ("Apatura",     "iris",       "Purple Emperor",      "#4B3B8F", "#7A6BC4", "#2B2320", "#2B2320", "#E5E0D8"),
    "malachite":  ("Siproeta",    "stelenes",   "Malachite",           "#8FB870", "#C3D9A8", "#241F1B", "#241F1B", "#F0EEE4"),
    "orangetip":  ("Anthocharis", "cardamines", "Orange Tip",          "#E08A2E", "#F0EEE7", "#7D8A5E", "#4A4F3A", "#7D8A5E"),
    "buckeye":    ("Junonia",     "coenia",     "Common Buckeye",      "#7A6248", "#D8C9A8", "#201B17", "#201B17", "#3D4C8C"),
}
ROT = {"triad": (0, 120, 240), "split": (0, 150, 210),
       "analog": (0, 30, -30), "tetrad": (0, 90, 180)}
TINT_SAT = {"neutral": 0.0, "faint": 0.055, "specimen": None}


# --- colour -----------------------------------------------------------------

def clamp(v, a, b):
    return max(a, min(b, v))


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(r, g, b):
    return "#" + "".join(f"{clamp(round(v), 0, 255):02X}" for v in (r, g, b))


def rgb2hsl(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn
    lightness = (mx + mn) / 2
    s = 0 if d == 0 else d / (1 - abs(2 * lightness - 1))
    if d == 0:
        h = 0.0
    elif mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    h *= 60
    return (h + 360 if h < 0 else h), s, lightness


def hsl2hex(h, s, lightness):
    h, s, lightness = h % 360, clamp(s, 0, 1), clamp(lightness, 0, 1)
    c = (1 - abs(2 * lightness - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = lightness - c / 2
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x), (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60)]
    return rgb2hex((r + m) * 255, (g + m) * 255, (b + m) * 255)


hex2hsl = lambda h: rgb2hsl(*hex2rgb(h))  # noqa: E731


def lum(hx):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in hex2rgb(hx))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def grade(r):
    return "AAA" if r >= 7 else "AA" if r >= 4.5 else "AA-large" if r >= 3 else "FAIL"


def fit_on(col, bg, target):
    """Raise or lower lightness until `col` clears `target` on `bg`."""
    if ratio(col, bg) >= target:
        return col
    h, s, lightness = hex2hsl(col)
    up = lum(bg) < 0.5
    best, best_r = col, ratio(col, bg)
    for i in range(1, 101):
        nl = clamp(lightness + (i * 0.01 if up else -i * 0.01), 0, 1)
        c = hsl2hex(h, s, nl)
        r = ratio(c, bg)
        if r > best_r:
            best, best_r = c, r
        if r >= target:
            return c
        if nl in (0.0, 1.0):
            break
    return best


def mix(a, b, t):
    A, B = hex2rgb(a), hex2rgb(b)
    return rgb2hex(*(A[i] + (B[i] - A[i]) * t for i in range(3)))


# --- derivation -------------------------------------------------------------

def derive(key, harmony, ground, tint, force_aa=True):
    genus, species, common, wing, wing2, edge, body, spot = SPECIMENS[key]
    ordered = sorted([wing, wing2, spot, edge, body], key=lum)
    darkest, lightest = ordered[0], ordered[-1]
    light = ground == "light"
    anchor_h, anchor_s, anchor_l = hex2hsl(wing)
    sat = TINT_SAT[tint]

    if sat is None:
        base = mix(lightest, "#FFFFFF", 0.55) if light else mix(darkest, "#000000", 0.35)
        contrast = mix(darkest, "#000000", 0.35) if light else mix(lightest, "#FFFFFF", 0.62)
    else:
        base = hsl2hex(anchor_h, sat, 0.975 if light else 0.072)
        contrast = hsl2hex(anchor_h, min(sat * 1.5, 0.10), 0.105 if light else 0.935)
    contrast = fit_on(contrast, base, 12)

    if harmony == "asfound":
        accents = [wing, wing2, spot]
    else:
        s = clamp(0.42 if anchor_s < 0.28 else anchor_s, 0.3, 0.86)
        accents = [hsl2hex(anchor_h + d, s,
                           clamp(anchor_l + (-0.04 if i == 1 else 0.05 if i == 2 else 0), 0.24, 0.66))
                   for i, d in enumerate(ROT[harmony])]
    if force_aa:
        accents = [fit_on(c, base, 4.5) for c in accents]

    return {"key": key, "genus": genus, "species": species, "common": common,
            "anchor": round(anchor_h), "base": base, "contrast": contrast,
            "primary": accents[0], "secondary": accents[1], "tertiary": accents[2]}


# --- output -----------------------------------------------------------------

def variation_json(p):
    return json.dumps({
        "$schema": "https://schemas.wp.org/trunk/theme.json",
        "version": 2,
        "title": p["common"],
        "settings": {"color": {"palette": [
            {"slug": s, "color": p[s], "name": s.capitalize()}
            for s in ("base", "contrast", "primary", "secondary", "tertiary")
        ]}},
    }, indent=2)


def stylesheet(p):
    base, ink = p["base"], p["contrast"]
    primary, secondary, tertiary = p["primary"], p["secondary"], p["tertiary"]
    code_bg = mix(base, ink, 0.045)
    rule = mix(base, ink, 0.18)
    comments = fit_on(mix(ink, base, 0.45), code_bg, 4.5)
    gutter = fit_on(mix(ink, base, 0.55), code_bg, 3)
    faint = mix(ink, code_bg, 0.32)
    inline = fit_on(primary, base, 4.5)
    sh = ".syntaxhighlighter.syntaxhighlighter"

    return f"""/* {p['genus']} {p['species']} ({p['common']}).
   Generated by .claude/skills/wp-publish/palette.py -- edit there, not here.
   Lives in Site Editor > Styles > Additional CSS (wp_global_styles). */

/* ---- Pygments: posts highlighted at publish time ----
   Scoped to .pyg, so no !important and nothing to override. Colour follows
   meaning, which is only possible because Pygments separates a function
   definition from a builtin and a docstring from a comment. */
.pyg {{ background: {code_bg}; color: {ink}; border: 1px solid {rule};
       border-radius: 2px; padding: 1.1rem 1.25rem; overflow-x: auto;
       line-height: 1.7; tab-size: 4; }}
.pyg code {{ white-space: pre; font-size: .875rem; }}

.pyg .c, .pyg .c1, .pyg .cm, .pyg .ch, .pyg .cs, .pyg .cpf,
.pyg .sd                      {{ color: {comments}; font-style: italic; }}
.pyg .cp                      {{ color: {comments}; }}

.pyg .k, .pyg .kd, .pyg .kn, .pyg .kr, .pyg .kp, .pyg .kt,
.pyg .ow                      {{ color: {primary}; font-weight: 600; }}
.pyg .kc                      {{ color: {tertiary}; font-weight: 600; }}

.pyg .nf, .pyg .fm, .pyg .nc, .pyg .nd
                              {{ color: {tertiary}; font-weight: 600; }}
.pyg .nb, .pyg .bp, .pyg .nn  {{ color: {tertiary}; }}
.pyg .na, .pyg .nt            {{ color: {tertiary}; }}
.pyg .n, .pyg .nx, .pyg .nl,
.pyg .nv, .pyg .vi, .pyg .vg  {{ color: {ink}; }}

.pyg .s, .pyg .s1, .pyg .s2, .pyg .sa, .pyg .sb, .pyg .sc, .pyg .se,
.pyg .sh, .pyg .si, .pyg .sx, .pyg .sr, .pyg .ss, .pyg .dl,
.pyg .m, .pyg .mi, .pyg .mf, .pyg .mh, .pyg .mo, .pyg .mb,
.pyg .l                       {{ color: {secondary}; }}

/* Punctuation and operators recede: the most frequent tokens and the least
   informative. SyntaxHighlighter made every `=` a bold keyword. */
.pyg .o, .pyg .p, .pyg .w     {{ color: {faint}; }}

.pyg .gd {{ color: {primary}; }}
.pyg .gi {{ color: {secondary}; }}
.pyg .gh, .pyg .gu {{ color: {comments}; font-weight: 600; }}
.pyg .gs {{ font-weight: 600; }}
.pyg .ge {{ font-style: italic; }}
.pyg .err {{ color: {primary}; border-bottom: 1px dotted {primary}; }}

/* ---- SyntaxHighlighter: posts that predate the change ----
   The class is doubled deliberately. Every bundled theme marks these rules
   !important and the plugin prints its stylesheet on wp_footer, long after
   global styles land in wp_head. At equal specificity the later sheet wins,
   so a single .syntaxhighlighter here is silently overruled. Doubling takes
   the selector to (0,3,0) against the plugin's (0,2,0). */
{sh},
{sh} .line.alt1,
{sh} .line.alt2      {{ background-color: {code_bg} !important; }}
{sh} .gutter         {{ color: {gutter} !important; }}
{sh} .gutter .line   {{ border-right: 3px solid {rule} !important; }}
{sh} .line.highlighted.alt1,
{sh} .line.highlighted.alt2 {{ background-color: {mix(base, primary, 0.16)} !important; }}
{sh} .plain, {sh} .plain a  {{ color: {ink} !important; }}
{sh} .comments, {sh} .comments a
                     {{ color: {comments} !important; font-style: italic !important; }}
{sh} .string, {sh} .string a {{ color: {secondary} !important; }}
{sh} .keyword        {{ color: {primary} !important; }}
{sh} .functions, {sh} .variable, {sh} .value
                     {{ color: {tertiary} !important; }}
{sh} .decorator      {{ color: {tertiary} !important; font-weight: 600 !important; }}
{sh} .constants      {{ color: {secondary} !important; }}
{sh} .preprocessor   {{ color: {comments} !important; }}
{sh} .color1, {sh} .color1 a {{ color: {tertiary} !important; font-weight: 600 !important; }}
{sh} .color2, {sh} .color2 a {{ color: {tertiary} !important; }}
{sh} .color3, {sh} .color3 a {{ color: {primary} !important; }}
{sh}                 {{ overflow-x: auto !important; }}
{sh} .line .content  {{ white-space: pre !important; }}

/* ---- Inline code ----
   `:not(pre) > code` so this can never reach a highlighted block.

   Primary, and no background. Twenty Twenty-Three styles links as
   `contrast` with an underline -- primary is only the button background --
   so primary is the one palette colour that appears nowhere in running
   text. That makes it unambiguous here: in a paragraph, coloured means
   code and underlined means link, and the two never have to compete. */
.entry-content :not(pre) > code {{
  font-family: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .875em;
  color: {inline};
  overflow-wrap: break-word;
}}
/* inside a link the link wins: one object, one colour */
.entry-content a code {{ color: inherit; }}
.entry-content :is(h1,h2,h3,h4,h5,h6) > code {{
  color: inherit; font-size: .9em;   /* headings carry their own weight */
}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("specimen", choices=sorted(SPECIMENS))
    ap.add_argument("--harmony", default="triad", choices=["asfound", *ROT])
    ap.add_argument("--ground", default="light", choices=["light", "dark"])
    ap.add_argument("--tint", default="faint", choices=list(TINT_SAT))
    ap.add_argument("--no-aa", action="store_true", help="skip the 4.5:1 correction")
    ap.add_argument("--css", help="write the stylesheet here")
    ap.add_argument("--json", dest="js", help="write the style variation here")
    args = ap.parse_args()

    p = derive(args.specimen, args.harmony, args.ground, args.tint, not args.no_aa)
    print(f"{p['genus']} {p['species']} ({p['common']}) -- {args.harmony}, "
          f"{args.ground}, {args.tint} tint, anchor {p['anchor']}deg")
    print(f"\n{'slot':10} {'hex':9} {'vs base':>9}  grade")
    for slot in ("base", "contrast", "primary", "secondary", "tertiary"):
        against = p["contrast"] if slot == "base" else p["base"]
        r = ratio(p[slot], against)
        print(f"{slot:10} {p[slot]:9} {r:8.2f}:1  {grade(r)}")

    if args.css:
        open(args.css, "w").write(stylesheet(p))
        print(f"\nwrote {args.css}")
    if args.js:
        open(args.js, "w").write(variation_json(p))
        print(f"wrote {args.js}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
