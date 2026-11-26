"""Draw the figures of the Concepts page as SVG snippets.

Run from the repository root:

    uv run python scripts/concept_figures.py

Writes includes/figures/*.svg. docs/concepts.md inlines them with pymdownx.snippets
(`--8<-- "figures/<name>.svg"`), so they follow the site's light/dark toggle: colours
are CSS classes (t-*, f-*, s-*) styled inside each SVG from the --wsf-* tokens of
docs/assets/stylesheets/extra.css, with light fallbacks for a file opened on its own.
The Dirichlet panels are an illustration (seed 42), not the exact hands-on split.
"""

import math
import os
import re
import sys

import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join("includes", "figures")
os.makedirs(OUT, exist_ok=True)

# Colours: the site defines the --wsf-* tokens in extra.css (light and dark). The
# fallbacks are the light colours, so a file opened on its own still looks right.
TOKENS = {
    "ink": "#1c2b28", "muted": "#5d6b67", "panel": "#f5f8f7", "line": "#dde6e2",
    "node": "#ffffff", "node-line": "#c3d3ce", "strong": "#1f3d37", "on": "#ffffff",
    "accent": "#2f8a72", "accent-soft": "#d8eee7", "warn": "#c0661a", "warn-soft": "#fbeadb",
}
RULES = [("t-ink", "fill", "ink"), ("t-muted", "fill", "muted"), ("t-on", "fill", "on"),
         ("t-on-soft", "fill", "on"), ("t-accent", "fill", "accent"),
         ("f-panel", "fill", "panel"), ("f-node", "fill", "node"), ("f-line", "fill", "line"),
         ("f-strong", "fill", "strong"), ("f-on", "fill", "on"), ("f-ink", "fill", "ink"),
         ("f-accent", "fill", "accent"), ("f-accent-soft", "fill", "accent-soft"),
         ("f-warn", "fill", "warn"), ("f-warn-soft", "fill", "warn-soft"),
         ("s-line", "stroke", "line"), ("s-node", "stroke", "node-line"), ("s-ink", "stroke", "ink"),
         ("s-on", "stroke", "on"), ("s-accent", "stroke", "accent"), ("s-warn", "stroke", "warn")]
STYLE = ("<style>"
         + "".join(f".wsf .{c}{{{prop}:var(--wsf-{tok},{TOKENS[tok]})}}" for c, prop, tok in RULES)
         + ".wsf .t-on-soft{opacity:.8}"
         + ".wsf circle.f-accent:hover{fill:var(--wsf-strong,#1f3d37)}"
         + ".wsf text{font-family:var(--md-text-font-family,Inter,system-ui,sans-serif)}"
         + "</style>")


def svg(name, w, h, label, body, defs=""):
    s = (f'<svg class="wsf" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
         f'aria-label="{label}" xmlns="http://www.w3.org/2000/svg">\n<title>{label}</title>\n{STYLE}\n')
    if defs:
        s += f"<defs>{defs}</defs>\n"
    s += body + "\n</svg>\n"
    # Same colours as presentation attributes, for viewers that ignore <style>.
    # Any CSS rule wins over them, so the site's light/dark tokens still apply.
    rule = {c: (prop, TOKENS[tok]) for c, prop, tok in RULES}

    def paint(m):
        attrs = "".join(f' {rule[c][0]}="{rule[c][1]}"' for c in m.group(1).split() if c in rule)
        return m.group(0) + attrs
    s = re.sub(r'(?<!svg) class="([^"]+)"', paint, s)
    # no blank lines: the snippet sits inside a raw HTML block
    s = "\n".join(l for l in s.splitlines() if l.strip()) + "\n"
    open(os.path.join(OUT, name), "w").write(s)

def arrow_marker(mid, cls):
    return (f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M1 1.5 L9 5 L1 8.5 z" class="{cls}"/></marker>')

def t(x, y, s, cls="t-ink", size=13, weight=None, anchor="start", extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}"{w} text-anchor="{anchor}"{extra}>{s}</text>'

def db_icon(x, y, cls="s-ink", s=1.0):
    # database cylinder, 18x22 at scale 1
    return (f'<g transform="translate({x} {y}) scale({s})" class="{cls}" fill="none" stroke-width="1.8">'
            '<ellipse cx="9" cy="4" rx="8" ry="3.2"/>'
            '<path d="M1 4 v14 c0 1.8 3.6 3.2 8 3.2 s8-1.4 8-3.2 v-14"/>'
            '<path d="M1 11 c0 1.8 3.6 3.2 8 3.2 s8-1.4 8-3.2"/></g>')

def net_icon(x, y, cls="s-on", fcls="f-on"):
    # tiny 3-layer network glyph, 24x22
    pts = [(0, 4), (0, 18), (12, 0), (12, 11), (12, 22), (24, 11)]
    edges = [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
    g = f'<g transform="translate({x} {y})">'
    g += "".join(f'<line x1="{pts[a][0]}" y1="{pts[a][1]}" x2="{pts[b][0]}" y2="{pts[b][1]}" class="{cls}" stroke-width="1.2" opacity=".7"/>' for a, b in edges)
    g += "".join(f'<circle cx="{px}" cy="{py}" r="2.8" class="{fcls}"/>' for px, py in pts)
    return g + "</g>"

def lock_badge(cx, cy):
    return (f'<g><circle cx="{cx}" cy="{cy}" r="10" class="f-accent"/>'
            f'<rect x="{cx-4.5}" y="{cy-1}" width="9" height="7" rx="1.5" class="f-on"/>'
            f'<path d="M{cx-2.8} {cy-1} v-2.2 a2.8 2.8 0 0 1 5.6 0 v2.2" fill="none" class="s-on" stroke-width="1.6"/></g>')

def doc_chip(cx, cy):
    return (f'<g><rect x="{cx-11}" y="{cy-10}" width="22" height="20" rx="5" class="f-warn-soft s-warn" stroke-width="1.5"/>'
            + "".join(f'<line x1="{cx-5}" y1="{cy-4+i*4}" x2="{cx+5}" y2="{cy-4+i*4}" class="s-warn" stroke-width="1.6" stroke-linecap="round"/>' for i in range(3))
            + "</g>")

# ---------------------------------------------------------------- figure 1
W1, H1 = 360, 330
SITES = [(60, "Site A"), (180, "Site B"), (300, "Site C")]
SY = 222  # top of site cards

def panel(title, sub):
    return (f'<rect x="1" y="1" width="{W1-2}" height="{H1-2}" rx="16" class="f-panel s-line" stroke-width="1.5"/>'
            + t(20, 34, title, size=16, weight=700) + t(20, 54, sub, "t-muted", 13))

def server(sub, icon):
    return (f'<rect x="105" y="78" width="150" height="58" rx="13" class="f-strong"/>' + icon
            + t(152, 103, "Server", "t-on", 14, 700) + t(152, 121, sub, "t-on-soft", 12))

def site(c, lock=False):
    g = (f'<rect x="{c-50}" y="{SY}" width="100" height="56" rx="12" class="f-node s-node" stroke-width="1.5"/>'
         + db_icon(c - 36, SY + 17, "s-ink"))
    g += t(c + 8, SY + 33, dict((a, b) for a, b in SITES)[c], size=13, weight=600, anchor="middle")
    if lock:
        g += lock_badge(c + 46, SY + 2)
    return g

# centralised
body = panel("Centralised", "The data are copied to one server")
body += server("all the data", db_icon(119, 96, "s-on", 0.95))
for (c, _), tx in zip(SITES, (150, 180, 210)):
    body += f'<path d="M{c} {SY-4} L{tx} 142" class="s-warn" stroke-width="2" fill="none" marker-end="url(#ac-w)"/>'
    body += doc_chip((c + tx) / 2, (SY - 4 + 142) / 2 + 4)
for c, _ in SITES:
    body += site(c)
body += doc_chip(28, 306) + t(46, 311, "raw data leave the sites", "t-muted", 12.5)
svg("centralised.svg", W1, H1, "Centralised learning: every site copies its raw data to one server.",
    body, arrow_marker("ac-w", "f-warn"))

# federated
body = panel("Federated", "Weights travel, the data stay")
body += server("global model", net_icon(117, 96))
for (c, _), tx in zip(SITES, (150, 180, 210)):
    dx, dy = c - tx, (SY - 4) - 142
    L = math.hypot(dx, dy); nx, ny = -dy / L * 6, dx / L * 6
    body += (f'<path d="M{tx+nx:.1f} {142+ny:.1f} L{c+nx:.1f} {SY-4+ny:.1f}" class="s-accent" stroke-width="2" '
             f'fill="none" marker-end="url(#af-m)"/>')
    body += (f'<path d="M{c-nx:.1f} {SY-4-ny:.1f} L{tx-nx:.1f} {142-ny:.1f}" class="s-ink" stroke-width="2" '
             f'stroke-dasharray="5 4" fill="none" marker-end="url(#af-w)"/>')
for c, _ in SITES:
    body += site(c, lock=True)
body += (f'<line x1="18" y1="306" x2="44" y2="306" class="s-accent" stroke-width="2" marker-end="url(#af-m)"/>'
         + t(52, 311, "global weights", "t-muted", 12.5)
         + f'<line x1="162" y1="306" x2="188" y2="306" class="s-ink" stroke-width="2" stroke-dasharray="5 4" marker-end="url(#af-w)"/>'
         + t(196, 311, "updated weights", "t-muted", 12.5))
svg("federated.svg", W1, H1, "Federated learning: the server sends the global weights to each site, and only updated weights come back. The data stay on the sites.",
    body, arrow_marker("af-m", "f-accent") + arrow_marker("af-w", "f-ink"))

# ---------------------------------------------------------------- figure 2
CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Boot"]
PER_CLASS, K = 6000, 5
COLW, ROWH, LABW, TOP = 31, 25, 70, 92
RMAX = 11.5
W2 = LABW + K * COLW + 14
H2 = TOP + len(CLASSES) * ROWH + 86

panels = [(100, "α = 100", "the same mix everywhere", False),
          (1, "α = 1", "uneven shares", False),
          (0.1, "α = 0.1", "a class sits on 1 or 2 clients", True)]
for alpha, title, sub, handson in panels:
    rng = np.random.default_rng(42)
    M = np.array([rng.multinomial(PER_CLASS, rng.dirichlet([alpha] * K)) for _ in CLASSES])  # classes x clients
    tot = M.sum(0)
    b = f'<rect x="1" y="1" width="{W2-2}" height="{H2-2}" rx="16" class="f-panel s-line" stroke-width="1.5"/>'
    b += t(18, 34, title, size=17, weight=700) + t(18, 54, sub, "t-muted", 12.5)
    if handson:
        b += (f'<rect x="{W2-92}" y="18" width="76" height="22" rx="11" class="f-accent-soft"/>'
              + t(W2 - 54, 33, "hands-on", "t-accent", 12, 600, "middle"))
    for j in range(K):
        b += t(LABW + j * COLW + COLW / 2, TOP - 14, f"C{j+1}", "t-muted", 12, 600, "middle")
    for i, cl in enumerate(CLASSES):
        cy = TOP + i * ROWH + ROWH / 2
        b += t(LABW - 10, cy + 4.5, cl, "t-muted", 12, anchor="end")
        for j in range(K):
            cx = LABW + j * COLW + COLW / 2
            n = int(M[i, j]); r = RMAX * math.sqrt(n / PER_CLASS)
            if r < 1.6:
                b += f'<circle cx="{cx}" cy="{cy}" r="1.6" class="f-line"><title>Client {j+1}, {cl}: {n:,} images</title></circle>'
            else:
                b += f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" class="f-accent"><title>Client {j+1}, {cl}: {n:,} images</title></circle>'
    # client sizes
    by = TOP + len(CLASSES) * ROWH + 14
    b += f'<line x1="{LABW}" y1="{by+36}" x2="{LABW+K*COLW}" y2="{by+36}" class="s-line" stroke-width="1.5"/>'
    b += t(LABW - 10, by + 30, "size", "t-muted", 12, anchor="end")
    for j in range(K):
        x = LABW + j * COLW + 6; h = 36 * tot[j] / 32000
        b += (f'<path d="M{x} {by+36} v{-(h-3):.1f} a3 3 0 0 1 3 -3 h{COLW-18} a3 3 0 0 1 3 3 v{h-3:.1f} z" class="f-strong">'
              f'<title>Client {j+1}: {tot[j]:,} images</title></path>')
        b += t(x + (COLW - 12) / 2, by + 54, f"{tot[j]/1000:.0f}k", "t-muted", 11.5, anchor="middle")
    svg(f"alpha-{str(alpha).replace('.', '')}.svg", W2, H2,
        f"Dirichlet partitioning with {title}: each dot is one class on one client, its area is the number of images; {sub}.",
        b)

# ---------------------------------------------------------------- figure 3
W3, H3 = 712, 320
b = f'<rect x="1" y="1" width="{W3-2}" height="{H3-2}" rx="16" class="f-panel s-line" stroke-width="1.5"/>'
b += t(20, 34, "One federation in Flower", size=16, weight=700)
b += t(20, 54, "In the hands-on, you take part in a federation like this one", "t-muted", 13)
# SuperLink
b += '<rect x="256" y="84" width="200" height="56" rx="28" class="f-strong"/>'
b += t(356, 108, "SuperLink", "t-on", 15, 700, "middle") + t(356, 126, "runs the rounds, averages", "t-on-soft", 12, anchor="middle")
# flwr run
b += '<rect x="30" y="84" width="170" height="56" rx="12" class="f-node s-node" stroke-width="1.5"/>'
b += (f'<g transform="translate(44 101)" class="s-ink" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
      '<rect x="0" y="0" width="20" height="16" rx="3"/><path d="M5 6 l3 2.5 -3 2.5 M10 11 h5"/></g>')
b += t(74, 107, "flwr run", size=13, weight=700) + t(74, 125, "submits app + run-config", "t-muted", 11.5)
b += '<path d="M200 112 L250 112" class="s-ink" stroke-width="1.8" fill="none" marker-end="url(#ak)"/>'
# note on the right
b += '<line x1="490" y1="100" x2="490" y2="76" class="s-accent" stroke-width="2" marker-end="url(#ah)"/>'
b += t(504, 92, "Each SuperNode connects", "t-muted", 12) + t(504, 108, "out to the SuperLink.", "t-muted", 12)
b += (t(504, 128, "Global weights down,", "t-muted", 12) + t(504, 144, "updated weights up,", "t-muted", 12)
      + t(504, 160, "on that same connection.", "t-muted", 12))
# clients
labels = ["SuperNode 1", "SuperNode 2", "SuperNode 3", "SuperNode n"]
for i, lab in enumerate(labels):
    x, y = 20 + i * 174, 222
    last = i == 3
    dash = ' stroke-dasharray="5 4"' if last else ""
    if i == 3:
        b += t(x - 12, y + 37, "…", "t-muted", 18, 700, "middle")
    b += f'<rect x="{x}" y="{y}" width="150" height="64" rx="12" class="f-node s-node" stroke-width="1.5"{dash}/>'
    b += db_icon(x + 16, y + 21, "s-accent", 0.95) + t(x + 44, y + 30, lab, size=13, weight=700)
    b += t(x + 44, y + 48, "its own data", "t-muted", 12)
    b += (f'<path d="M{x+75} {y-4} L{311 + i*30} 146" class="s-accent" stroke-width="1.8" fill="none" '
          'marker-end="url(#ah)"/>')
b += t(20, 306, "One SuperNode per client site. Their number depends on the federation.", "t-muted", 12)
svg("hub.svg", W3, H3, "One federation in Flower: flwr run submits the app to the SuperLink; each SuperNode trains on its own data and connects out to the SuperLink.",
    b, arrow_marker("ah", "f-accent") + arrow_marker("ak", "f-ink"))
print(f"Figures written to {OUT}")
