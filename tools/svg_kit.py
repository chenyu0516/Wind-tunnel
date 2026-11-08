#!/usr/bin/env python3
"""Small SVG drawing kit shared by the figure scripts (no plan numbers here).

Set svg_kit.OUT to the output folder before calling Svg.save().
"""
import pathlib
from xml.sax.saxutils import escape

OUT = pathlib.Path(__file__).resolve().parent.parent / "figures"

FONT = "'PingFang TC','Heiti TC','Noto Sans TC','Microsoft JhengHei',sans-serif"
STYLE = f"""
text{{font-family:{FONT};fill:#183344}}
.t{{font-size:24px;font-weight:700}} .st{{font-size:14px;fill:#526b7b}}
.l{{font-size:14px;font-weight:600}} .n{{font-size:12px;fill:#526b7b}} .d{{font-size:12px;fill:#374151}}
.w{{font-size:12px;fill:#c2410c;font-weight:600}}
.halo{{paint-order:stroke;stroke:#ffffff;stroke-width:4px;stroke-linejoin:round}}
.shell{{stroke:#32566b;stroke-width:2;fill:#edf3f6}}
.shell0{{stroke:#32566b;stroke-width:2;fill:none}}
.thin{{stroke:#32566b;stroke-width:1;fill:none}}
.pc{{stroke:#32566b;stroke-width:2;fill:#e3f1f7}}
.solid{{stroke:#32566b;stroke-width:1.2;fill:#cbd5df}}
.dark{{stroke:#1f2937;stroke-width:1;fill:#4b5563}}
.car{{stroke:#475569;stroke-width:1.2;fill:#e2e8f0}}
.air{{stroke:#187c91;stroke-width:2;fill:none}}
.airf{{fill:#187c91}}
.scr{{stroke:#187c91;stroke-width:2;stroke-dasharray:6 4;fill:none}}
.dim{{stroke:#6b7280;stroke-width:1;fill:none}}
.ext{{stroke:#9ca3af;stroke-width:0.8;fill:none}}
.guide{{stroke:#cbd5e1;stroke-width:0.8;stroke-dasharray:3 4;fill:none}}
.tbd{{stroke:#c2410c;stroke-width:1.4;stroke-dasharray:5 3;fill:none}}
.tbdf{{stroke:#c2410c;stroke-width:1.4;stroke-dasharray:5 3;fill:#fff7ed}}
.cl{{stroke:#94a3b8;stroke-width:1;stroke-dasharray:14 4 2 4;fill:none}}
.grid{{stroke:#e5e7eb;stroke-width:1;fill:none}}
.axis{{stroke:#374151;stroke-width:1.2;fill:none}}
.c1{{stroke:#187c91;stroke-width:2.5;fill:none}} .c2{{stroke:#7c3aed;stroke-width:2.5;fill:none}}
.c3{{stroke:#187c91;stroke-width:2;stroke-dasharray:6 4;fill:none}}
.bar{{fill:#187c91}} .bar2{{fill:#94a3b8}}
.hc{{fill:url(#hc);stroke:#32566b;stroke-width:1}}
"""
DEFS = """
<marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="#6b7280"/></marker>
<marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#187c91"/></marker>
<marker id="o" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#c2410c"/></marker>
<pattern id="hc" width="5" height="8" patternUnits="userSpaceOnUse"><path d="M0 0V8 M0 4H5" stroke="#8aa4b2" stroke-width="0.8"/></pattern>
<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V6" stroke="#94a3b8" stroke-width="1"/></pattern>
"""


class Svg:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.items = []

    def add(self, s):
        self.items.append(s)

    def line(self, x1, y1, x2, y2, cls="thin", extra=""):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}" {extra}/>')

    def rect(self, x, y, w, h, cls="shell", extra=""):
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" class="{cls}" {extra}/>')

    def poly(self, pts, cls="thin", closed=False, extra=""):
        tag = "polygon" if closed else "polyline"
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.add(f'<{tag} points="{p}" class="{cls}" {extra}/>')

    def path(self, d, cls="thin", extra=""):
        self.add(f'<path d="{d}" class="{cls}" {extra}/>')

    def circle(self, cx, cy, r, cls="thin", extra=""):
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" class="{cls}" {extra}/>')

    def text(self, x, y, s, cls="l", anchor="start", halo=False, extra=""):
        c = cls + (" halo" if halo else "")
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{c}" text-anchor="{anchor}" {extra}>{escape(s)}</text>')

    def lines(self, x, y, rows, cls="n", dy=17, anchor="start", halo=False):
        for i, r in enumerate(rows):
            self.text(x, y + i * dy, r, cls, anchor, halo)

    def hdim(self, x1, x2, y, label, cls="d", below=False):
        self.line(x1, y, x2, y, "dim", 'marker-start="url(#a)" marker-end="url(#a)"')
        self.text((x1 + x2) / 2, y + (14 if below else -5), label, cls, "middle", halo=True)

    def vdim(self, x, y1, y2, label, cls="d", left=False):
        self.line(x, y1, x, y2, "dim", 'marker-start="url(#a)" marker-end="url(#a)"')
        self.text(x + (-6 if left else 6), (y1 + y2) / 2 + 4, label, cls, "end" if left else "start", halo=True)

    def flow(self, x1, y1, x2, y2):
        self.line(x1, y1, x2, y2, "air", 'marker-end="url(#f)"')

    def header(self, title, sub):
        self.text(32, 42, title, "t")
        self.text(32, 66, sub, "st")

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        body = "\n".join(self.items)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="title desc">\n'
               f'<title id="title">{escape(self.title)}</title>\n<desc id="desc">{escape(self.desc)}</desc>\n'
               f'<defs>{DEFS}<style>{STYLE}</style></defs>\n'
               f'<rect width="{self.w}" height="{self.h}" rx="14" fill="#fafcfd"/>\n{body}\n</svg>\n')
        (OUT / name).write_text(svg, encoding="utf-8")
        print("wrote", OUT / name)


class View:
    """Maps plan mm (x, v) to page px. v is z (side view) or y (top view); up on the page is +v."""

    def __init__(self, ox, oy, s, x0=0.0, v0=0.0):
        self.ox, self.oy, self.s, self.x0, self.v0 = ox, oy, s, x0, v0

    def X(self, x):
        return self.ox + (x - self.x0) * self.s

    def V(self, v):
        return self.oy - (v - self.v0) * self.s

    def P(self, x, v):
        return (self.X(x), self.V(v))
