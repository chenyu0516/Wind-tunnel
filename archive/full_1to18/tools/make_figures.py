#!/usr/bin/env python3
"""Draw the human-facing figures (Traditional Chinese labels) from spec/geometry.json.

Run:  python3 tools/make_figures.py      -> writes figures/zh-TW/*.svg
Geometry comes only from geometry.json and airflow_calc.py; do not hard-code plan numbers here.
Orange dashed items mark values the plan leaves 'tbd'.
"""
import math
import pathlib
import sys
from xml.sax.saxutils import escape

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import airflow_calc as ac  # noqa: E402

G = ac.G
OUT = ac.ROOT / "figures" / "zh-TW"

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


def con_half(s, which):
    con = G["contraction"]
    i = 0 if which == "w" else 1
    return ac.contraction_dim(s, con["inlet"][i], con["exit"][i], con["length"]) / 2


def duct_outline(svg, vw, which):
    """Draw the duct walls (which='z' side view, 'y' top view). Returns nothing."""
    axis = G["frame"]["duct_axis_z"] if which == "z" else 0.0
    sc, con, ts, di, bell = G["settling"], G["contraction"], G["test_section"], G["diffuser"], G["inlet_bell"]
    half_sc = (sc["height"] if which == "z" else sc["width"]) / 2
    half_ts = (ts["height"] if which == "z" else ts["width"]) / 2
    r_out = di["outlet_d"] / 2
    R = bell["lip_radius_min"]
    xb = bell["x0"]
    for sgn in (1, -1):
        top = axis + sgn * half_sc
        # bell: straight then quarter arc flaring outward to the inlet plane
        x_arc = xb + R
        p0 = vw.P(sc["x0"], top)
        p1 = vw.P(x_arc, top)
        p2 = vw.P(xb, top + sgn * R)
        sweep = 0 if sgn > 0 else 1
        svg.path(f"M{p0[0]:.1f},{p0[1]:.1f} L{p1[0]:.1f},{p1[1]:.1f} A{R*vw.s:.1f},{R*vw.s:.1f} 0 0 {sweep} {p2[0]:.1f},{p2[1]:.1f}", "shell0")
        svg.line(*vw.P(sc["x0"], top), *vw.P(con["x0"], top), "shell0")
        pts = [vw.P(con["x0"] + s, axis + sgn * con_half(s, "w" if which == "y" else "h")) for s in range(0, con["length"] + 1, 10)]
        svg.poly(pts, "shell0")
        svg.line(*vw.P(0, axis + sgn * half_ts), *vw.P(ts["length"], axis + sgn * half_ts), "shell0")
        svg.line(*vw.P(di["x0"], axis + sgn * half_ts), *vw.P(di["x0"] + di["length"], axis + sgn * r_out), "shell0")
    # flanges / joints
    for x, h in ((sc["x0"], half_sc), (con["x0"], half_sc), (0, half_ts), (ts["length"], half_ts), (di["x0"] + di["length"], r_out)):
        svg.line(*vw.P(x, axis + h + 25), *vw.P(x, axis + h), "thin")
        svg.line(*vw.P(x, axis - h - 25), *vw.P(x, axis - h), "thin")


# ---------------------------------------------------------------- A1
def fig_airpath():
    svg = Svg(1400, 960, "氣流通道總覽", "側視與俯視，依比例，單位 mm。標示各模組長度、截面與 15 m/s 時各段平均風速。")
    svg.header("圖 A1　氣流通道總覽（依比例）", "上：側視　下：俯視　單位 mm　藍色箭頭為氣流方向；橘色虛線為計畫尚未決定的項目")
    s = 0.24
    side = View(170, 330, s, -1600, G["frame"]["duct_axis_z"])
    top = View(170, 700, s, -1600, 0)
    sc, con, ts, di, fan = G["settling"], G["contraction"], G["test_section"], G["diffuser"], G["fan"]
    cond = G["conditioning"]
    gp = G["ground_plate"]
    for vw, which in ((side, "z"), (top, "y")):
        duct_outline(svg, vw, which)
        axis = G["frame"]["duct_axis_z"] if which == "z" else 0
        half_sc = (sc["height"] if which == "z" else sc["width"]) / 2
        hcx = cond["honeycomb"]["x_upstream_face"]
        svg.rect(vw.X(hcx), vw.V(axis + half_sc), cond["honeycomb"]["depth"] * s, half_sc * 2 * s, "hc")
        for xs in cond["screens_x"]:
            svg.line(vw.X(xs), vw.V(axis + half_sc), vw.X(xs), vw.V(axis - half_sc), "scr")
        r_out = di["outlet_d"] / 2
        xm = G["diffuser"]["safety_mesh_x"]
        svg.line(vw.X(xm), vw.V(axis + r_out), vw.X(xm), vw.V(axis - r_out), "scr")
        svg.rect(vw.X(fan["x0"]), vw.V(axis + r_out), fan["length_approx"] * s, 2 * r_out * s, "tbdf")
        svg.text(vw.X(fan["x0"] + fan["length_approx"] / 2), vw.V(axis) + 4, "風扇（依選型）", "w", "middle")
        svg.line(vw.X(-1600), vw.V(axis), vw.X(2800), vw.V(axis), "cl")
        svg.flow(vw.X(-1800), vw.V(axis), vw.X(-1620), vw.V(axis))
        svg.flow(vw.X(2820), vw.V(axis), vw.X(2980), vw.V(axis))
    # test-section contents (side view)
    pz = gp["z_underside"]
    svg.rect(side.X(gp["x_le"]), side.V(pz + gp["thickness"]), gp["length"] * s, max(2, gp["thickness"] * s), "solid")
    car = G["car"]
    svg.rect(side.X(car["x_nose"]), side.V(pz + 6 + 80), car["length"] * s, 75 * s, "car", 'rx="3"')
    # labels
    svg.text(40, 300, "側視圖", "l")
    svg.text(40, 680, "俯視圖", "l")
    names = [("入口喇叭口", G["inlet_bell"]), ("穩定段", sc), ("收縮段", con), ("測試段", ts), ("擴散段", di)]
    y_dim = 175
    for name, d in names:
        x0, x1 = d["x0"], d["x0"] + d["length"]
        svg.hdim(side.X(x0), side.X(x1), y_dim, f"{d['length']:,}")
        svg.text(side.X((x0 + x1) / 2), y_dim - 22, name, "l", "middle")
    svg.hdim(side.X(fan["x0"]), side.X(fan["x0"] + fan["length_approx"]), y_dim, f"約 {fan['length_approx']}", "w")
    svg.text(side.X(fan["x0"] + fan["length_approx"] / 2), y_dim - 22, "風扇", "l", "middle")
    total = fan["x0"] + fan["length_approx"] - G["inlet_bell"]["x0"]
    svg.hdim(side.X(-1600), side.X(2800), 112, f"風管全長 {total:,}")
    # section sizes
    ax = G["frame"]["duct_axis_z"]
    svg.text(side.X(sc["x0"] + 275), side.V(ax) - 8, f"高 {sc['height']}", "d", "middle", True)
    svg.text(side.X(150), side.V(ax) + 4, f"高 {ts['height']}", "d", "middle", True)
    svg.text(side.X(1900), side.V(ax) - 8, f"出口 Ø{di['outlet_d']}", "d", "middle", True)
    svg.text(top.X(sc["x0"] + 275), top.V(0) - 8, f"寬 {sc['width']}", "d", "middle", True)
    svg.text(top.X(400), top.V(0) - 8, f"寬 {ts['width']}", "d", "middle", True)
    svg.text(top.X(1900), top.V(0) - 8, f"出口 Ø{di['outlet_d']}", "d", "middle", True)
    # velocities at 15 m/s
    cr = ac.contraction_ratio()
    ar = ac.diffuser_geometry()["area_ratio"]
    for x, u in ((sc["x0"] + 275, 15 / cr), (400, 15), (1950, 15 / ar)):
        svg.text(top.X(x), top.V(0) + 20, f"{u:.1f} m/s", "d", "middle", True)
    svg.text(top.X(-1600), 860, "平均風速以測試段 15 m/s 計", "n")
    # small callouts
    svg.text(side.X(-1150), side.V(ax + 367.5) - 10, "蜂巢 + 2 片網", "n", "middle", True)
    svg.text(side.X(2200), side.V(ax + 315) - 10, "安全網", "n", "middle", True)
    svg.text(side.X(425), side.V(gp["z_underside"]) + 26, "地面板 + 車模", "n", "middle", True)
    svg.text(side.X(-1600), side.V(ax + 467.5) - 6, f"唇口 R ≥ {G['inlet_bell']['lip_radius_min']}", "n", "start", True)
    # clear air
    ca = G["clear_air"]
    svg.text(40, 900, f"← 進氣端淨空 ≥ {ca['intake_min']:,}", "l")
    svg.text(1360, 900, f"排氣端淨空 ≥ {ca['exhaust_min']:,} →", "l", "end")
    svg.text(700, 900, f"風管 {total:,} + 淨空 {ca['intake_min'] + ca['exhaust_min']:,} = {total + ca['intake_min'] + ca['exhaust_min']:,}（場地需約 7.5 m 直線）", "l", "middle")
    svg.text(700, 926, "上下游各段假設與測試段同軸（計畫未明訂）", "w", "middle")
    svg.save("A1-airpath.svg")


# ---------------------------------------------------------------- A2
def fig_conditioning():
    svg = Svg(1300, 900, "穩定段與整流元件", "穩定段側視放大圖：入口喇叭口、蜂巢、兩片整流網、靜壓環與間距。")
    svg.header("圖 A2　穩定段與整流元件（側視，依比例）", "單位 mm　x 自收縮段出口起算（負值在上游）　藍色虛線為整流網")
    s = 0.72
    ax = G["frame"]["duct_axis_z"]
    vw = View(80, 120 + (617.5 - ax) * s, s, -1620, ax)
    sc, cond, bell = G["settling"], G["conditioning"], G["inlet_bell"]
    hs = sc["height"] / 2
    R = bell["lip_radius_min"]
    for sgn in (1, -1):
        top = ax + sgn * hs
        p0, p1, p2 = vw.P(-860, top), vw.P(bell["x0"] + R, top), vw.P(bell["x0"], top + sgn * R)
        sweep = 0 if sgn > 0 else 1
        svg.path(f"M{p0[0]:.1f},{p0[1]:.1f} L{p1[0]:.1f},{p1[1]:.1f} A{R*s:.1f},{R*s:.1f} 0 0 {sweep} {p2[0]:.1f},{p2[1]:.1f}", "shell0")
    for x in (sc["x0"], G["contraction"]["x0"]):
        svg.line(vw.X(x), vw.V(ax + hs + 30), vw.X(x), vw.V(ax - hs - 30), "thin")
    hc = cond["honeycomb"]
    svg.rect(vw.X(hc["x_upstream_face"]), vw.V(ax + hs), hc["depth"] * s, 2 * hs * s, "hc")
    for xs in cond["screens_x"]:
        svg.line(vw.X(xs), vw.V(ax + hs + 28), vw.X(xs), vw.V(ax - hs), "scr")
        svg.rect(vw.X(xs) - 6, vw.V(ax + hs + 28), 12, 28 * s + 2, "solid")
    svg.rect(vw.X(hc["x_upstream_face"]) - 3, vw.V(ax + hs + 28), hc["depth"] * s + 6, 28 * s + 2, "solid")
    svg.text(vw.X(-1220), vw.V(ax + hs + 28) - 10, "可抽出框架（加墊片密封）", "n", "middle", True)
    ring = G["pressure_taps"]["settling_ring"]["x"]
    for sgn in (1, -1):
        svg.circle(vw.X(ring), vw.V(ax + sgn * hs), 5, "shell", 'style="fill:#187c91"')
    svg.text(vw.X(ring) + 10, vw.V(ax - hs) + 22, f"穩定段靜壓環 ×4（x = {ring}，每面壁一孔）", "n", "start", True)
    svg.line(vw.X(-1620), vw.V(ax), vw.X(-860), vw.V(ax), "cl")
    svg.flow(vw.X(-1700), vw.V(ax), vw.X(-1625), vw.V(ax))
    svg.flow(vw.X(-930), vw.V(ax), vw.X(-865), vw.V(ax))
    svg.text(vw.X(-905), vw.V(ax) + 22, "→ 收縮段", "n", "end", True)
    svg.text(vw.X(bell["x0"]) + 4, vw.V(ax + hs + R) - 8, f"唇口 R ≥ {R}", "n", "start", True)
    svg.vdim(vw.X(-860) + 14, vw.V(ax + hs), vw.V(ax - hs), f"高 {sc['height']}（寬 {sc['width']}）")
    # chain dims
    xs = [bell["x0"], sc["x0"], hc["x_upstream_face"], hc["x_upstream_face"] + hc["depth"]] + cond["screens_x"] + [G["contraction"]["x0"]]
    labs = ["喇叭口 150", "40", "40", "≥150", "≥150", "≥170"]
    svg.text(vw.X(hc["x_upstream_face"] + hc["depth"] / 2), vw.V(ax - hs) + 20, "蜂巢", "n", "middle", True)
    yb = vw.V(ax - hs - R) + 32
    for (a, b), lab in zip(zip(xs, xs[1:]), labs):
        svg.hdim(vw.X(a), vw.X(b), yb, lab, below=False)
        svg.line(vw.X(a), yb - 4, vw.X(a), vw.V(ax - hs), "ext")
    svg.line(vw.X(xs[-1]), yb - 4, vw.X(xs[-1]), vw.V(ax - hs), "ext")
    svg.hdim(vw.X(sc["x0"]), vw.X(G["contraction"]["x0"]), yb + 34, f"穩定段 {sc['length']}")
    svg.text(vw.X(-1600), yb + 64, "蜂巢與網的 x 位置為一種符合間距規則的排法；計畫只規定間距。", "w")
    # insets
    ix, iy = 760, 140
    svg.text(ix, iy, "蜂巢整流格（放大）", "l")
    hx = 8
    for row in range(3):
        for col in range(5):
            cx = ix + 30 + col * hx * 6 * math.sqrt(3) / 2 * 1.0 + (row % 2) * hx * 6 * math.sqrt(3) / 4
            cy = iy + 40 + row * hx * 6 * 0.75
            r = hx * 6 / 2 / math.cos(math.pi / 6) * 0.5
            pts = [(cx + r * math.cos(math.pi / 6 + k * math.pi / 3), cy + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
            svg.poly(pts, "thin", True)
    cells = ac.settling_area_m2() * 1e6 / (math.sqrt(3) / 2 * hc["cell"] ** 2)
    svg.lines(ix, iy + 150, [f"格孔 {hc['cell']} mm、深 {hc['depth']} mm", f"深/孔徑 L/D = {hc['depth']/hc['cell']:.1f}（建議 6–8）",
                             f"整面約 {cells:,.0f} 格 → 買成品板"], "d", 19)
    iy2 = 420
    svg.text(ix, iy2, "整流網（放大）", "l")
    for k in range(9):
        svg.line(ix + 20 + k * 14, iy2 + 20, ix + 20 + k * 14, iy2 + 132, "thin")
        svg.line(ix + 20, iy2 + 20 + k * 14, ix + 132, iy2 + 20 + k * 14, "thin")
    usc = 15 / ac.contraction_ratio()
    re_w = usc * cond["screen_wire_d_max"] / 1000 / ac.NU
    svg.lines(ix + 160, iy2 + 40, ["不鏽鋼網，兩片", f"線徑 ≤ {cond['screen_wire_d_max']} mm", "開孔率 60–70%（≥ 57%）",
                                     f"15 m/s 時此處風速 {usc:.1f} m/s", f"線徑雷諾數 ≈ {re_w:.0f}（< 40 不渦流脫落）", "紗窗網須先確認開孔率"], "d", 19)
    svg.save("A2-conditioning.svg")


# ---------------------------------------------------------------- A3
def fig_contraction():
    svg = Svg(1300, 820, "收縮段曲線", "收縮段五次多項式壁面曲線；上半為寬度方向壁，下半為高度方向壁，依比例。")
    svg.header("圖 A3　收縮段壁面曲線（依比例）", "上半：寬度方向壁（俯視）　下半：高度方向壁（側視）　s 自收縮段入口起算，單位 mm")
    con = G["contraction"]
    L = con["length"]
    s_ = 0.62
    vw = View(110, 430, s_, 0, 0)
    svg.line(vw.X(-40), vw.V(0), vw.X(L + 60), vw.V(0), "cl")
    up = [vw.P(s, con_half(s, "w")) for s in range(0, L + 1, 5)]
    dn = [vw.P(s, -con_half(s, "h")) for s in range(0, L + 1, 5)]
    svg.poly(up, "c1")
    svg.poly(dn, "c2")
    svg.line(vw.X(-40), vw.V(con["inlet"][0] / 2), vw.X(0), vw.V(con["inlet"][0] / 2), "c1")
    svg.line(vw.X(L), vw.V(con["exit"][0] / 2), vw.X(L + 60), vw.V(con["exit"][0] / 2), "c1")
    svg.line(vw.X(-40), vw.V(-con["inlet"][1] / 2), vw.X(0), vw.V(-con["inlet"][1] / 2), "c2")
    svg.line(vw.X(L), vw.V(-con["exit"][1] / 2), vw.X(L + 60), vw.V(-con["exit"][1] / 2), "c2")
    for s, h, w in zip(con["plan_table_s"], con["plan_table_height"], con["plan_table_width"]):
        svg.line(vw.X(s), vw.V(w / 2), vw.X(s), vw.V(-h / 2), "guide")
        svg.text(vw.X(s), vw.V(w / 2) - 8, f"{w}", "d", "middle", True)
        svg.text(vw.X(s), vw.V(-h / 2) + 18, f"{h}", "d", "middle", True)
        svg.text(vw.X(s), vw.V(-367.5) + 52, f"{s}", "d", "middle")
    svg.text(vw.X(L / 2), vw.V(-367.5) + 72, "s（mm）", "n", "middle")
    svg.text(vw.X(-40), vw.V(490) - 30, "標示值為全寬（上）與全高（下）", "n")
    svg.flow(vw.X(L * 0.35), vw.V(0) - 10, vw.X(L * 0.55), vw.V(0) - 10)
    svg.text(vw.X(30), vw.V(0) - 8, "中心線", "n")
    for which, cls_y, name, hi, he in (("w", 230, "寬度方向壁", con["inlet"][0], con["exit"][0]), ("h", 610, "高度方向壁", con["inlet"][1], con["exit"][1])):
        smax = max(abs(ac.contraction_wall_slope(s, hi, he, L)) for s in range(L + 1))
        kmax = max(abs(ac.contraction_wall_curvature(s, hi, he, L)) for s in range(L + 1))
        svg.lines(vw.X(L) - 20, cls_y, [name, f"最大斜角 {math.degrees(math.atan(smax)):.1f}°", f"最小彎曲半徑 {1/kmax:.0f} mm"], "d", 17, "end")
    rx = 820
    svg.text(rx, 130, "曲線公式", "l")
    svg.lines(rx, 156, ["h(s) = hᵢ − (hᵢ − hₑ)·(6t⁵ − 15t⁴ + 10t³)", "t = s / L，L = 900", "寬與高使用同一公式",
                        "", "兩端：斜率 = 0、曲率 = 0", "→ 與穩定段、測試段平順銜接，", "   不會在接縫處產生壓力尖峰"], "d", 19)
    svg.text(rx, 330, "製作", "l")
    svg.lines(rx, 356, [f"每面壁只單向彎曲 → 用 {con['wall_sheet_t'][0]}–{con['wall_sheet_t'][1]} mm 平板", "彎貼在 CNC 肋板上；四角從外側修順、密封",
                        "肋板數量與間距：計畫未定"], "d", 19)
    svg.text(rx, 440, "出口接縫（放大示意）", "l")
    bx, by = rx + 10, 470
    svg.line(bx, by + 40, bx + 120, by + 40, "shell0")
    svg.line(bx + 120, by + 40, bx + 120, by + 46, "shell0")
    svg.line(bx + 120, by + 46, bx + 260, by + 46, "shell0")
    svg.text(bx + 60, by + 30, "收縮段", "n", "middle")
    svg.text(bx + 190, by + 36, "測試段壁", "n", "middle")
    svg.flow(bx + 20, by + 80, bx + 100, by + 80)
    svg.lines(bx, by + 110, [f"段差 ≤ {con['exit_step_max']} mm", "若有段差：下游壁略往外退（後向台階）", "不可做成迎風凸台"], "d", 19)
    svg.text(bx + 120, by + 64, "← 下游壁外退", "w", "start")
    svg.save("A3-contraction.svg")


# ---------------------------------------------------------------- A4
def fig_test_section():
    svg = Svg(1400, 1240, "測試段配置", "測試段側視與俯視：地面板、車模、皮托管、靜壓孔、量測點、靜壓箱位置。")
    svg.header("圖 A4　測試段配置（依比例）", "上：側視（從 −y 側看）　下：俯視（+y 在上）　x 自收縮段出口起算；z 自測試段地板起算；單位 mm")
    s = 1.1
    side = View(90, 150 + 330 * s, s, -60, 0)
    top = View(90, 680 + 230 * s, s, -60, 0)
    ts, gp, car, pr = G["test_section"], G["ground_plate"], G["car"], G["probes"]
    z_pt = gp["z_underside"] + gp["thickness"]
    # ruler
    ry = 120
    svg.line(side.X(0), ry, side.X(ts["length"]), ry, "axis")
    ticks = sorted({0, G["pressure_taps"]["entrance_ring"]["x"], gp["x_le"], pr["pitot_nose"]["x"], pr["fog_outlet"]["x_approx"],
                    car["x_nose"], car["x_tail"], gp["x_te"], ts["length"]})
    for i, x in enumerate(ticks):
        svg.line(side.X(x), ry - 5, side.X(x), ry + 5, "axis")
        svg.text(side.X(x), ry - 9 - (12 if i % 2 else 0), f"{x}", "d", "middle")
        svg.line(side.X(x), ry + 6, side.X(x), top.V(-215), "guide")
    svg.text(side.X(-60), ry + 4, "x", "l")
    # ---- side view ----
    svg.rect(side.X(0), side.V(0), ts["length"] * s, 6 * s, "solid")
    svg.line(side.X(0), side.V(ts["height"]), side.X(ts["length"]), side.V(ts["height"]), "shell0", 'style="stroke-width:3"')
    svg.line(side.X(0), side.V(ts["height"]), side.X(ts["length"]), side.V(ts["height"] + 10), "tbd")
    svg.circle(side.X(0), side.V(ts["height"]), 5, "shell")
    svg.text(side.X(4), side.V(ts["height"]) - 10, "頂板鉸鏈", "n", "start", True)
    svg.text(side.X(ts["length"]), side.V(ts["height"] + 10) - 8, "出口墊高 0–10", "w", "end", True)
    for x0, x1, zt, zb in ((-60, 0, ts["height"], 0), (ts["length"], ts["length"] + 60, None, None)):
        if zt is not None:
            svg.line(side.X(x0), side.V(zt), side.X(x1), side.V(zt), "shell0")
            svg.line(side.X(x0), side.V(zb), side.X(x1), side.V(zb), "shell0")
    k = (G["diffuser"]["outlet_d"] / 2 - ts["height"] / 2) / G["diffuser"]["length"]
    svg.line(side.X(800), side.V(300), side.X(860), side.V(300 + 60 * k), "shell0")
    svg.line(side.X(800), side.V(0), side.X(860), side.V(-60 * k), "shell0")
    svg.text(side.X(-55), side.V(150), "收縮段", "n")
    svg.text(side.X(805), side.V(150), "擴散段", "n")
    xr = G["pressure_taps"]["entrance_ring"]["x"]
    for z in (0, ts["height"]):
        svg.circle(side.X(xr), side.V(z), 4, "shell", 'style="fill:#187c91"')
    svg.text(side.X(xr) + 6, side.V(ts["height"]) + 16, "入口靜壓環 ×4", "n", "start", True)
    # plate with openings
    axles = [car["x_nose"] + 50, car["x_tail"] - 50]
    ow = G["ground_plate"]["wheel_openings"]["approx_size_x_by_y"][0]
    xs = [gp["x_le"]] + sum([[a - ow / 2, a + ow / 2] for a in axles], []) + [gp["x_te"]]
    for a, b in zip(xs[::2], xs[1::2]):
        svg.rect(side.X(a), side.V(z_pt), (b - a) * s, gp["thickness"] * s, "solid")
    svg.path(f"M{side.X(gp['x_le']):.1f},{side.V(z_pt):.1f} Q{side.X(gp['x_le'] - 12):.1f},{side.V(z_pt - 3):.1f} {side.X(gp['x_le']):.1f},{side.V(gp['z_underside']):.1f}", "solid")
    svg.line(side.X(gp["x_te"]), side.V(z_pt - 3), side.X(gp["x_te"] + 40), side.V(z_pt - 10), "shell0", 'style="stroke-width:3"')
    svg.text(side.X(gp["x_te"] + 42), side.V(z_pt - 12) + 4, "可調襟翼", "n", "start", True)
    svg.text(side.X(gp["x_le"]) - 4, side.V(z_pt) - 8, "4:1 橢圓前緣", "n", "end", True)
    # wells, shrouds, plenum
    for a in axles:
        svg.rect(side.X(a - 30), side.V(gp["z_underside"]), 60 * s, G["wheel_wells"]["depth_max"] * s, "shell")
        zf = gp["z_underside"] - G["wheel_wells"]["depth_max"]
        svg.rect(side.X(a - 6), side.V(zf), 12 * s, zf * s, "shell")
        svg.line(side.X(a), side.V(zf), side.X(a), side.V(-55), "dark", 'style="stroke-width:3;stroke:#4b5563"')
    svg.rect(side.X(car["x_nose"] - 80), side.V(-8), (car["length"] + 160) * s, 50 * s, "tbdf")
    svg.text(side.X(car["x_nose"] + car["length"] / 2), side.V(-8) + 30, "密封靜壓箱（尺寸待定，見圖 A5）", "w", "middle")
    # car
    svg.rect(side.X(car["x_nose"]), side.V(z_pt + 7.5 + 75), car["length"] * s, 75 * s, "car", 'rx="10"')
    for a in axles:
        svg.circle(side.X(a), side.V(z_pt - 2 + 20), 20 * s, "dark")
    svg.text(side.X(car["x_nose"] + 125), side.V(z_pt + 45), f"1:18 車模 {car['length']}（示意）", "l", "middle", True)
    svg.text(side.X(car["x_nose"] + 125), side.V(z_pt + 45) + 18, "軸位、車高 7–8 待第 1 週量測", "w", "middle", True)
    # pitot
    p = pr["pitot_nose"]
    zp = z_pt + p["z_above_plate"]
    svg.line(side.X(p["x"]), side.V(zp), side.X(p["x"] + 40), side.V(zp), "dark", 'style="stroke-width:3;stroke:#1f2937"')
    svg.line(side.X(p["x"] + 40), side.V(zp), side.X(p["x"] + 40), side.V(ts["height"]), "dark", 'style="stroke-width:3;stroke:#1f2937"')
    svg.text(side.X(p["x"]) - 6, side.V(zp) + 4, "皮托管", "l", "end", True)
    # side taps
    for x in G["pressure_taps"]["side_wall_taps"]["x"]:
        svg.circle(side.X(x), side.V(190), 4, "tbd")
    svg.text(side.X(700) + 8, side.V(190) + 4, "側壁靜壓孔 Ø1（高度待定）", "w", "start", True)
    # vent line
    svg.path(f"M{side.X(560):.1f},{side.V(-8):.1f} L{side.X(560):.1f},{side.V(-30):.1f} L{side.X(650):.1f},{side.V(-30):.1f}", "scr")
    svg.text(side.X(655), side.V(-30) + 4, "Ø6 平衡管 → 車身中段附近的側壁靜壓孔", "n", "start", True)
    # z dims
    xd = side.X(ts["length"]) + 75
    svg.vdim(xd, side.V(0), side.V(gp["z_underside"]), f"板下 {gp['z_underside']}")
    svg.vdim(xd, side.V(z_pt), side.V(zp), f"{p['z_above_plate']}（皮托管高於地面板）")
    svg.vdim(xd + 190, side.V(0), side.V(ts["height"]), f"{ts['height']}")
    svg.text(xd + 4, side.V(z_pt) + 2, f"板厚 {gp['thickness']}", "d", "start", True)
    svg.hdim(side.X(car["x_tail"]), side.X(ts["length"]), side.V(260), f"近尾流 {ts['length'] - car['x_tail']}")
    svg.text(side.X(-55), side.V(-40), "井深 ≤ 30；護套管 Ø12", "n")
    # ---- top view ----
    hw = ts["width"] / 2
    for sgn in (1, -1):
        svg.line(top.X(-60), top.V(sgn * hw), top.X(ts["length"]), top.V(sgn * hw), "shell0", 'style="stroke-width:3"')
        kd = (G["diffuser"]["outlet_d"] / 2 - hw) / G["diffuser"]["length"]
        svg.line(top.X(800), top.V(sgn * hw), top.X(860), top.V(sgn * (hw + 60 * kd)), "shell0")
        svg.circle(top.X(xr), top.V(sgn * hw), 4, "shell", 'style="fill:#187c91"')
    svg.rect(top.X(gp["x_le"]), top.V(hw), gp["length"] * s, ts["width"] * s, "pc", 'style="fill:#eef2f6;stroke-width:1"')
    svg.rect(top.X(car["x_nose"]), top.V(50), car["length"] * s, 100 * s, "car", 'rx="18"')
    for a in axles:
        for sgn in (1, -1):
            svg.rect(top.X(a - ow / 2), top.V(sgn * 45 + 10), ow * s, 20 * s, "tbdf")
    svg.text(top.X(car["x_nose"] + 125), top.V(0) + 4, "車模（示意）", "l", "middle", True)
    svg.text(top.X(car["x_tail"]) + 6, top.V(-45) + 26, "開口 45×20 ×4（位置依實測輪距）", "w", "start", True)
    svg.circle(top.X(p["x"]), top.V(p["y"]), 4, "dark")
    svg.line(top.X(p["x"]), top.V(p["y"]), top.X(p["x"] + 40), top.V(p["y"]), "dark", 'style="stroke-width:3;stroke:#1f2937"')
    svg.text(top.X(p["x"]) - 6, top.V(p["y"]) + 4, f"皮托管 y = +{p['y']}", "l", "end", True)
    fx = pr["fog_outlet"]["x_approx"]
    svg.line(top.X(fx - 60), top.V(-90), top.X(fx), top.V(-90), "tbd", 'marker-end="url(#o)"')
    svg.text(top.X(fx - 62), top.V(-90) + 4, "霧氣出口 x≈220（橫向可調，與皮托管錯開）", "w", "end", True)
    for xs_ in G["survey"]["stations_x"]:
        for y in G["survey"]["holes_y"]:
            svg.circle(top.X(xs_), top.V(y), 3.5, "shell", 'style="fill:#ffffff"')
    svg.text(top.X(G["survey"]["stations_x"][1]) + 8, top.V(100) - 6, "量測頂板孔 y = −100…+100（間隔 50）", "n", "start", True)
    for x in G["pressure_taps"]["side_wall_taps"]["x"]:
        svg.circle(top.X(x), top.V(-hw), 4, "tbd")
    svg.text(top.X(100), top.V(-hw) + 20, "側壁靜壓孔：側別待定", "w", "start", True)
    svg.vdim(top.X(ts["length"]) + 75, top.V(hw), top.V(-hw), f"{ts['width']}")
    svg.text(top.X(-55), top.V(hw) - 10, "+y（順流向看的左側）", "n")
    sh = G["survey"]["heights_above_plate"]
    svg.text(32, 1204, f"面板：側壁 {ts['side_wall_t']} mm PC、頂板 ≥ {ts['roof_t_min']} mm PC（157 Pa 下中心撓度約 0.3／0.4 mm）；地板厚度待定", "n")
    svg.text(32, 1222, f"流場量測：移除車模，於 x = 300 與 550 兩站、地面板上方 z = {', '.join(map(str, sh))} 各點量測（共 50 點）", "n")
    svg.save("A4-test-section.svg")


# ---------------------------------------------------------------- A5
def fig_balance():
    svg = Svg(1400, 1120, "車輪支撐與天平剖面", "單一車輪處的剖面：地面板開口、滾輪托架、輪井、護套管與下方密封靜壓箱和天平堆疊。")
    svg.header("圖 A5　車輪支撐與天平（剖面）", "上半依比例（單一車輪，側視）；下半為示意、未依比例　單位 mm")
    s = 5.0
    vw = View(80, 110 + 100 * s, s, -55, 0)
    gp, well, post, cr = G["ground_plate"], G["wheel_wells"], G["post"], G["cradle"]
    z_pt = gp["z_underside"] + gp["thickness"]
    ow = gp["wheel_openings"]["approx_size_x_by_y"][0]
    tyre = G["car"]["tyre_d_planning"]
    R, r, a = tyre / 2, cr["roller_d"] / 2, cr["roller_centres"] / 2
    sink = ac.roller_top_above_tyre_bottom(tyre, cr["roller_d"], cr["roller_centres"])
    roller_top = z_pt - 0.3
    tyre_bot = roller_top - sink
    zc = tyre_bot + R
    zr = zc - math.sqrt((R + r) ** 2 - a ** 2)
    # body and plate
    svg.rect(vw.X(-55), vw.V(100), 110 * s, (100 - (z_pt + 7.5)) * s, "car")
    svg.text(vw.X(-50), vw.V(95), "車身", "n")
    for x0, x1 in ((-55, -ow / 2), (ow / 2, 55)):
        svg.rect(vw.X(x0), vw.V(z_pt), (x1 - x0) * s, gp["thickness"] * s, "solid")
    svg.circle(vw.X(0), vw.V(zc), R * s, "dark", 'style="fill:#4b5563;opacity:0.85"')
    svg.text(vw.X(0), vw.V(zc) + 4, f"輪胎 Ø{tyre}", "l", "middle", extra='style="fill:#ffffff"')
    for sx in (-a, a):
        svg.circle(vw.X(sx), vw.V(zr), r * s, "shell", 'style="fill:#cbd5df"')
        svg.circle(vw.X(sx), vw.V(zr), 3.5 * s, "thin")
        svg.circle(vw.X(sx), vw.V(zr), 1.5 * s, "dark")
    zb = zr - r - 3
    for sx in (-a - r - 2, a + r + 2):
        svg.line(vw.X(sx), vw.V(zr), vw.X(sx), vw.V(zb), "shell0", 'style="stroke-width:3"')
    svg.line(vw.X(-a - r - 2), vw.V(zb), vw.X(a + r + 2), vw.V(zb), "shell0", 'style="stroke-width:3"')
    zf = gp["z_underside"] - well["depth_max"]
    svg.path(f"M{vw.X(-30):.1f},{vw.V(gp['z_underside']):.1f} L{vw.X(-30):.1f},{vw.V(zf):.1f} L{vw.X(-6):.1f},{vw.V(zf):.1f} "
             f"M{vw.X(6):.1f},{vw.V(zf):.1f} L{vw.X(30):.1f},{vw.V(zf):.1f} L{vw.X(30):.1f},{vw.V(gp['z_underside']):.1f}", "shell0", 'style="stroke-width:2.5"')
    svg.rect(vw.X(-6), vw.V(zf), 1 * s, zf * s, "solid")
    svg.rect(vw.X(5), vw.V(zf), 1 * s, zf * s, "solid")
    svg.rect(vw.X(-4), vw.V(zb), 8 * s, (zb + 12) * s, "solid", 'style="fill:#94a3b8"')
    svg.rect(vw.X(-55), vw.V(0), 49 * s, 8 * s, "tbdf")
    svg.rect(vw.X(6), vw.V(0), 49 * s, 8 * s, "tbdf")
    svg.text(vw.X(-50), vw.V(-4) + 4, "測試段地板（厚度待定）", "w")
    # dims
    xd = vw.X(55) + 14
    svg.vdim(xd, vw.V(0), vw.V(gp["z_underside"]), f"板下淨空 {gp['z_underside']}")
    svg.vdim(xd + 120, vw.V(zf), vw.V(gp["z_underside"]), f"輪井深 ≤ {well['depth_max']}")
    svg.vdim(xd + 120, vw.V(0), vw.V(zf), f"護套跨距 {zf:.0f}")
    svg.text(xd + 4, vw.V(z_pt) + 2, f"地面板 {gp['thickness']}", "d", "start", True)
    # labels left
    svg.text(vw.X(-a) - r * s - 8, vw.V(zr) + 4, f"滾輪 Ø{cr['roller_d']}", "l", "end", True)
    svg.text(vw.X(-a) - r * s - 8, vw.V(zr) + 22, "2 × 683ZZ、軸 Ø3", "n", "end", True)
    svg.text(vw.X(-30) - 6, vw.V(zf + 10), "封底輪井", "l", "end", True)
    svg.text(vw.X(-6) - 6, vw.V(8), f"固定護套管 Ø{post['shroud_tube_d']}", "l", "end", True)
    svg.text(vw.X(4) + 8, vw.V(-10), f"支柱 {post['bare_size_w_by_len'][0]} mm（屬天平）", "n", "start", True)
    svg.text(vw.X(0), vw.V(zb) + 16, "托架", "n", "middle", True)
    # zoom note on roller vs tyre
    nx, ny = 960, 150
    svg.text(nx, ny, "滾輪與輪胎的幾何", "l")
    svg.lines(nx, ny + 26, [f"輪胎 Ø{tyre}，滾輪 Ø{cr['roller_d']}，中心距 {cr['roller_centres']}",
                            f"→ 滾輪頂高於輪胎最低點 {sink:.2f} mm（計畫：約 1.9）",
                            "規則：滾輪頂 < 地面板頂；車身俯仰只用托架高度調"], "d", 19)
    svg.lines(nx, ny + 100, ["待確認：滾輪頂在板面以下，", f"輪胎最低點就比地面板頂低 ≥ {sink:.1f} mm，",
                             f"車身離地會比原車模少約 {sink:.1f} mm（車高 7–8 的約 25%）", "見 airflow_design.zh-TW.md §8"], "w", 18)
    # roller front-view inset
    ix, iy = 960, 360
    svg.text(ix, iy, "滾輪正視（示意）", "l")
    k = 7
    rl = 24
    svg.rect(ix + 40, iy + 30, rl * k, cr["roller_d"] * k, "shell")
    for xx in (ix + 40, ix + 40 + rl * k - 3 * k):
        svg.rect(xx, iy + 30 + (cr["roller_d"] - 7) / 2 * k, 3 * k, 7 * k, "solid")
    svg.line(ix + 20, iy + 30 + cr["roller_d"] / 2 * k, ix + 60 + rl * k, iy + 30 + cr["roller_d"] / 2 * k, "dark", 'style="stroke-width:3;stroke:#1f2937"')
    for xx in (ix + 34, ix + 40 + rl * k + 2):
        svg.rect(xx, iy + 20, 4, cr["roller_d"] * k + 20, "solid")
    svg.lines(ix, iy + 170, ["683ZZ（3 × 7 × 3 mm）兩端各一", "Ø3 軸固定在托架側板", "凸緣或側導板做橫向定位", "滾輪長度：計畫未定"], "n", 17)
    svg.text(ix + 40 + rl * k + 10, iy + 30 + cr["roller_d"] * k + 14, "長度待定", "w")
    # lower schematic
    y0 = 680
    svg.line(40, y0 - 14, 1360, y0 - 14, "guide")
    svg.text(40, y0 + 6, "以下為示意，未依比例：測試段地板下方", "w")
    bx0, bx1, by0, by1 = 140, 720, y0 + 30, y0 + 330
    svg.path(f"M380,{by1} L{bx0},{by1} L{bx0},{by0} L{bx1},{by0} L{bx1},{by1} L480,{by1}", "shell0", 'style="stroke-width:4"')
    svg.text(bx0 + 8, by0 + 22, "密封靜壓箱（整個活動框架都在箱內）", "l")
    svg.rect(bx1 - 4, by0 + 90, 8, 100, "solid", 'style="fill:#187c91"')
    svg.text(bx1 + 12, by0 + 140, "檢修門（加墊片）", "n")
    svg.circle(bx1, by0 + 230, 6, "shell")
    svg.text(bx1 + 12, by0 + 234, "線材格蘭頭", "n")
    svg.line(bx1, by0 + 40, bx1 + 80, by0 + 40, "scr")
    svg.text(bx1 + 86, by0 + 44, "Ø6 平衡管 → 車身中段附近的側壁靜壓孔", "n")
    svg.text(bx1 + 86, by0 + 62, "靜壓箱與地面板壓差 ≤ 1 Pa", "n")
    for px in (260, 600):
        svg.line(px, by0 - 30, px, by0 + 70, "dark", 'style="stroke-width:5;stroke:#94a3b8"')
    svg.text(608, by0 - 18, "支柱 ×4（穿過護套管）", "n")
    svg.rect(230, by0 + 70, 400, 14, "solid")
    svg.text(640, by0 + 82, "共用框架", "n")
    svg.rect(330, by0 + 100, 200, 12, "solid")
    for px in (340, 520):
        svg.line(px, by0 + 112, px, by0 + 160, "shell0", 'style="stroke-width:2;stroke:#7c3aed"')
    svg.text(540, by0 + 140, "彈簧鋼片 ×4（0.2 × 20 × 40）", "n")
    svg.rect(330, by0 + 160, 200, 12, "solid")
    svg.rect(390, by0 + 128, 60, 18, "shell", 'style="fill:#fde68a"')
    svg.text(380, by0 + 141, "阻力荷重元 300 g（水平）", "n", "end")
    svg.rect(360, by0 + 190, 140, 22, "shell", 'style="fill:#fde68a"')
    svg.text(350, by0 + 205, "垂直荷重元 3 kg", "n", "end")
    svg.line(430, by0 + 172, 430, by0 + 190, "shell0", 'style="stroke-width:4"')
    svg.rect(405, by0 + 212, 50, by1 - by0 - 212 + 40, "solid")
    svg.path(f"M380,{by1} q4,8 12,10 q8,4 13,12 M480,{by1} q-4,8 -12,10 q-8,4 -13,12", "shell0", 'style="stroke:#7c3aed;stroke-width:2"')
    svg.text(490, by1 + 26, "氯丁橡膠裙邊（柔性密封）", "n")
    svg.rect(340, by1 + 40, 180, 30, "solid", 'style="fill:#9ca3af"')
    svg.text(530, by1 + 60, "落地底座 + 配重約 30 kg", "n")
    svg.rect(60, by1 + 70, 1280, 12, "solid", 'style="fill:url(#hatch)"')
    svg.text(70, by1 + 66, "剛性樓板", "n")
    svg.lines(960, by0 + 250, ["限位：阻力約 2 N、垂直 < 4.5 kg", "換車時鎖上運輸鎖", "活動質量 ≤ 2.6 kg（垂直荷重元容量 3 kg）"], "n", 18)
    svg.save("A5-wheel-and-balance.svg")


# ---------------------------------------------------------------- A6
def fig_drag_path():
    svg = Svg(1400, 800, "阻力如何被量到", "左：輪胎坐在兩個滾輪之間時，水平力如何傳到托架；右：阻力與重量在天平中的兩條路徑。")
    svg.header("圖 A6　水平力（阻力）如何被量到", "左：單一車輪，依比例　右：天平堆疊，示意　氣流由左向右，阻力方向 +x")
    cr = G["cradle"]
    tyre = G["car"]["tyre_d_planning"]
    R, r, a = tyre / 2, cr["roller_d"] / 2, cr["roller_centres"] / 2
    phi = ac.cradle_contact_angle_deg(tyre, cr["roller_d"], cr["roller_centres"])
    lr = ac.liftoff_ratio(tyre, cr["roller_d"], cr["roller_centres"])
    s = 6.0
    vw = View(330, 250, s, 0, 0)
    dz = math.sqrt((R + r) ** 2 - a ** 2)
    svg.circle(vw.X(0), vw.V(0), R * s, "dark", 'style="fill:#4b5563;opacity:0.85"')
    for sx in (-a, a):
        svg.circle(vw.X(sx), vw.V(-dz), r * s, "shell", 'style="fill:#cbd5df"')
        svg.circle(vw.X(sx), vw.V(-dz), 1.5 * s, "dark")
        svg.line(vw.X(sx), vw.V(-dz), vw.X(0), vw.V(0), "guide", 'style="stroke:#7c3aed;stroke-width:1.5;stroke-dasharray:6 4"')
    svg.line(vw.X(-a - r - 2), vw.V(-dz - r - 3), vw.X(a + r + 2), vw.V(-dz - r - 3), "shell0", 'style="stroke-width:4"')
    for sx in (-a - r - 2, a + r + 2):
        svg.line(vw.X(sx), vw.V(-dz), vw.X(sx), vw.V(-dz - r - 3), "shell0", 'style="stroke-width:4"')
    svg.text(vw.X(0), vw.V(-dz - r - 3) + 22, "托架（固定在共用框架上）", "n", "middle")
    cx, cy = vw.X(0), vw.V(0)
    svg.line(cx, cy, cx, cy + 80, "air", 'style="stroke:#1f2937;stroke-width:3" marker-end="url(#a)"')
    svg.text(cx + 8, cy + 76, "重量 W", "l", "start", True)
    svg.line(cx, cy, cx + 160, cy, "air", 'style="stroke-width:3" marker-end="url(#f)"')
    svg.text(cx + 164, cy + 5, "阻力 D", "l", "start", True)
    for sgn, name in ((-1, "N₁（上游）"), (1, "N₂（下游）")):
        px, py = vw.X(sgn * a * R / (R + r)), vw.V(-dz * R / (R + r))
        ux, uy = -sgn * math.sin(math.radians(phi)), -math.cos(math.radians(phi))
        L = 70 if sgn > 0 else 45
        svg.line(px - ux * L, py + uy * L, px, py, "air", 'style="stroke:#7c3aed;stroke-width:3"')
        svg.text(px - ux * L + sgn * 8, py + uy * L + 18, name, "l", "start" if sgn > 0 else "end", True)
    svg.text(vw.X(a) + 30, vw.V(-dz) - 4, f"φ = {phi:.1f}°", "d", "start", True)
    svg.lines(40, 580, [
        "接觸力永遠沿著「滾輪中心 → 輪胎中心」的方向（紫色虛線）。",
        f"兩條線都斜 φ = {phi:.1f}°，所以接觸力有水平分量：D = (N₂ − N₁)·sin φ",
        "阻力只是把重量多分一點給下游滾輪，托架照樣把水平力接住。",
        "滾輪與輪胎轉動不會讓輪胎平移：要平移，輪胎中心必須先爬高。",
        f"爬出條件：N₁ = 0，即 D/W = tan φ = {lr:.2f}，整車約 {lr*12:.1f} N；15 m/s 阻力只有約 0.3 N。",
        "量測時仍鎖住滾輪（計畫 B3），排除任何滾動或晃動。"], "d", 21)
    # right: balance stack
    ox = 760
    ds = ac.drag_stage()
    svg.rect(ox + 60, 120, 400, 26, "solid")
    svg.text(ox + 260, 138, "共用框架（4 個托架都鎖在上面）", "n", "middle")
    for px in (ox + 120, ox + 400):
        svg.rect(px - 18, 92, 36, 28, "shell", 'style="fill:#cbd5df"')
    svg.text(ox + 260, 104, "托架 ×4", "n", "middle")
    svg.rect(ox + 110, 170, 300, 16, "solid")
    svg.text(ox + 420, 182, "上板", "n")
    svg.line(ox + 260, 146, ox + 260, 170, "shell0", 'style="stroke-width:5"')
    for px in (ox + 130, ox + 390):
        svg.line(px, 186, px, 286, "shell0", 'style="stroke:#7c3aed;stroke-width:3"')
    svg.rect(ox + 110, 286, 300, 16, "solid")
    svg.text(ox + 420, 298, "底板", "n")
    svg.rect(ox + 220, 222, 70, 26, "shell", 'style="fill:#fde68a"')
    svg.line(ox + 200, 186, ox + 200, 235, "shell0", 'style="stroke-width:4"')
    svg.line(ox + 200, 235, ox + 220, 235, "shell0", 'style="stroke-width:4"')
    svg.line(ox + 290, 235, ox + 320, 235, "shell0", 'style="stroke-width:4"')
    svg.line(ox + 320, 235, ox + 320, 286, "shell0", 'style="stroke-width:4"')
    svg.text(ox + 255, 215, "阻力荷重元", "n", "middle")
    svg.text(ox + 120, 270, "鋼片", "n", "end")
    svg.line(ox + 260, 302, ox + 260, 330, "shell0", 'style="stroke-width:5"')
    svg.rect(ox + 170, 330, 180, 26, "shell", 'style="fill:#fde68a"')
    svg.text(ox + 260, 348, "垂直荷重元", "n", "middle")
    svg.rect(ox + 225, 356, 70, 70, "solid")
    svg.text(ox + 305, 400, "落地底座", "n")
    # paths
    svg.path(f"M{ox+40},{105} L{ox+40},{178} L{ox+180},{178} L{ox+180},{235}", "c1", 'marker-end="url(#f)"')
    svg.text(ox + 30, 100, "阻力路徑", "l", "end", True)
    svg.path(f"M{ox+490},{105} L{ox+490},{240} L{ox+440},{240} L{ox+440},{343} L{ox+355},{343}", "c2", 'marker-end="url(#a)"')
    svg.text(ox + 498, 100, "重量路徑", "l", "start", True)
    svg.lines(ox - 30, 470, [
        "兩個平台疊在一起，不是滾輪自己去動：",
        "• 托架鎖死在共用框架上，整個框架一起動。",
        "• 鋼片把上板吊在底板上：垂直方向極硬（直接承重），",
        f"  水平方向很軟（約 {ds['k_blades']:,.0f} N/m），讓上板能前後移動。",
        "• 上板前後移動時只能推阻力荷重元 → 讀到阻力。",
        "• 整個阻力平台再坐在垂直荷重元上 → 讀到重量 + 下壓力。",
        "",
        f"阻力荷重元剛性約 {ds['k_cell']:,.0f} N/m（假設滿載變形 0.3 mm），",
        f"與鋼片並聯 → 荷重元承受約 {ds['cell_share']*100:.0f}%，其餘由鋼片承受；",
        "這個比例固定，組裝後的力校正（F1）會一併扣除。",
        f"0.3 N 阻力只讓框架水平移動約 {ds['defl_um']:.0f} µm（間隙 1–2 mm）。",
        f"同一組彈簧也決定阻力方向自然頻率約 {ds['f_Hz']:.0f} Hz（計畫 C4）。"], "d", 21)
    svg.save("A6-drag-path.svg")


# ---------------------------------------------------------------- B1
def fig_system_curve():
    svg = Svg(1240, 620, "系統曲線與損失分配", "風扇所需壓力對流量的系統曲線，以及各組件損失係數。")
    svg.header("圖 B1　系統曲線與損失分配", "左：風扇需提供的壓力 Δp = q·ΣK（含 50% 餘裕的虛線）　右：各組件 K（以測試段 q 為基準）")
    x0, y0, w, h = 90, 540, 560, 420
    qmax, pmax = 10000, 300
    X = lambda q: x0 + q / qmax * w
    Y = lambda p: y0 - p / pmax * h
    for q in range(0, qmax + 1, 2000):
        svg.line(X(q), y0, X(q), y0 - h, "grid")
        svg.text(X(q), y0 + 18, f"{q:,}", "d", "middle")
    for p in range(0, pmax + 1, 50):
        svg.line(x0, Y(p), x0 + w, Y(p), "grid")
        svg.text(x0 - 8, Y(p) + 4, f"{p}", "d", "end")
    svg.line(x0, y0, x0 + w, y0, "axis")
    svg.line(x0, y0, x0, y0 - h, "axis")
    svg.text(x0 + w / 2, y0 + 40, "流量 Q（m³/h）", "l", "middle")
    svg.text(x0 - 60, y0 - h - 14, "Δp（Pa）", "l")
    K = ac.system_K()
    A = ac.ts_area_m2()
    curve = []
    curve_m = []
    for i in range(0, 101):
        Q = qmax * i / 100
        U = Q / 3600 / A
        dp = ac.q_of(U) * K
        curve.append((X(Q), Y(dp)))
        if dp * 1.5 <= pmax:
            curve_m.append((X(Q), Y(dp * 1.5)))
    svg.poly(curve, "c1")
    svg.poly(curve_m, "c3")
    for U in (5, 10, 15, 20):
        d = ac.fan_duty(U)
        svg.line(X(d["Q_m3h"]), y0 - h, X(d["Q_m3h"]), y0 - h - 6, "axis")
        svg.text(X(d["Q_m3h"]), y0 - h - 10, f"{U} m/s", "d", "middle")
    for U in (15, 20):
        d = ac.fan_duty(U)
        svg.circle(X(d["Q_m3h"]), Y(d["dp_calc"]), 5, "shell", 'style="fill:#187c91"')
        svg.circle(X(d["Q_m3h"]), Y(d["dp_margin"]), 5, "shell", 'style="fill:#ffffff;stroke:#187c91"')
        svg.text(X(d["Q_m3h"]) - 8, Y(d["dp_calc"]) + 18, f"{d['dp_calc']:.0f} Pa", "d", "end", True)
        svg.text(X(d["Q_m3h"]) - 8, Y(d["dp_margin"]) - 6, f"{d['dp_margin']:.0f} Pa", "d", "end", True)
    pf = G["proposals"]["fan"]
    svg.circle(X(9000), Y(196), 6, "tbd")
    svg.text(X(9000) + 8, Y(196) + 20, "MD-24 額定點", "w", "start", True)
    svg.text(X(9000) + 8, Y(196) + 36, "（提案，未採用）", "w", "start", True)
    svg.text(X(1000), Y(270), f"實線：ΣK = {K:.2f}（表列值相加）", "d", "start", True)
    svg.text(X(1000), Y(250), "虛線：再加 50% 餘裕", "d", "start", True)
    svg.text(X(1000), Y(230), f"15 m/s：{ac.fan_duty(15)['Q_m3h']:,.0f} m³/h，電功率約 {ac.fan_duty(15)['P_elec_W']/1000:.1f} kW", "d", "start", True)
    # bars
    names = {"inlet_conditioning": "入口 + 蜂巢 + 2 片網", "contraction": "收縮段", "ts_walls": "測試段壁面摩擦", "ground_plate": "地面板",
             "model_supports": "車模與支撐", "diffuser": "擴散段（效率 80%）", "safety_screen": "安全網", "fan_plane_q": "出口動壓（風扇面）"}
    items = sorted(ac.PLAN_K.items(), key=lambda kv: -kv[1])
    bx, by = 900, 130
    bw = 280
    for i, (k_, v) in enumerate(items):
        yy = by + i * 46
        svg.text(bx - 10, yy + 16, names[k_], "d", "end")
        svg.rect(bx, yy, v / 0.2 * bw, 22, "bar")
        svg.text(bx + v / 0.2 * bw + 6, yy + 16, f"{v:.2f}", "d")
    svg.lines(bx - 200, by + 8 * 46 + 20, [f"表列值相加 = {K:.2f}（計畫寫 0.73，為進位前的合計）", "擴散段、安全網、出口動壓三項合計 0.47，約佔 64%"], "n", 18)
    svg.save("B1-system-curve.svg")


# ---------------------------------------------------------------- B2
def duct_area_at(x):
    """Flow area (m2) along the duct, for the velocity/pressure plot."""
    sc, con, ts, di = G["settling"], G["contraction"], G["test_section"], G["diffuser"]
    if x < con["x0"]:
        return sc["width"] * sc["height"] / 1e6
    if x < 0:
        s = x - con["x0"]
        return ac.contraction_dim(s, con["inlet"][0], con["exit"][0], con["length"]) * ac.contraction_dim(s, con["inlet"][1], con["exit"][1], con["length"]) / 1e6
    if x <= ts["length"]:
        return ac.ts_area_m2()
    if x <= di["x0"] + di["length"]:
        dg = ac.diffuser_geometry()
        d = dg["d_eq_in_mm"] + (di["outlet_d"] - dg["d_eq_in_mm"]) * (x - di["x0"]) / di["length"]
        return math.pi * (d / 1000) ** 2 / 4
    return math.pi * (di["outlet_d"] / 1000) ** 2 / 4


def loss_before(x, q):
    """Cumulative total-pressure loss (Pa) upstream of x, spreading each K over where it happens."""
    K = ac.PLAN_K
    cond = G["conditioning"]
    hc = cond["honeycomb"]["x_upstream_face"] + cond["honeycomb"]["depth"]
    steps = [(hc, 0.03), (cond["screens_x"][0], 0.05), (cond["screens_x"][1], K["inlet_conditioning"] - 0.08), (G["diffuser"]["safety_mesh_x"], K["safety_screen"])]
    spreads = [(G["contraction"]["x0"], 0, K["contraction"]), (0, 800, K["ts_walls"] + K["ground_plate"]), (300, 550, K["model_supports"]),
               (G["diffuser"]["x0"], G["diffuser"]["x0"] + G["diffuser"]["length"], K["diffuser"])]
    k = sum(v for xs, v in steps if x >= xs)
    for a, b, v in spreads:
        k += v * min(1, max(0, (x - a) / (b - a)))
    return k * q


def fig_pressure_profile():
    U = 15
    svg = Svg(1400, 820, "風速與靜壓沿風管分布", "15 m/s 時沿風管的平均風速與相對室內的靜壓，說明為何測試段為負壓，以及各段的作用。")
    svg.header("圖 B2　沿風管的風速與靜壓（15 m/s）", "x 與圖 A1 對齊　靜壓為相對室內大氣的值　風扇段以虛線示意")
    s = 0.24
    sil = View(170, 175, s, -1600, G["frame"]["duct_axis_z"])
    sil.s = s
    # thin silhouette using half vertical scale
    vs = View(170, 175, s, -1600, G["frame"]["duct_axis_z"])
    vs.V = lambda v: 175 - (v - G["frame"]["duct_axis_z"]) * s * 0.35
    duct_outline(svg, vs, "z")
    fan = G["fan"]
    r_out = G["diffuser"]["outlet_d"] / 2
    svg.rect(vs.X(fan["x0"]), vs.V(150 + r_out), fan["length_approx"] * s, 2 * r_out * s * 0.35, "tbdf")
    # velocity panel
    q = ac.q_of(U)
    Qv = U * ac.ts_area_m2()
    X = lambda x: 170 + (x + 1600) * s
    vy0, vh = 410, 150
    VY = lambda u: vy0 - u / 16 * vh
    py0, ph = 760, 300
    PY = lambda p: py0 - (p + 180) / 180 * ph
    for u in (0, 5, 10, 15):
        svg.line(X(-1600), VY(u), X(2800), VY(u), "grid")
        svg.text(X(-1600) - 8, VY(u) + 4, f"{u}", "d", "end")
    svg.text(40, vy0 - vh - 8, "平均風速 U（m/s）", "l")
    for p in range(-180, 1, 30):
        svg.line(X(-1600), PY(p), X(2800), PY(p), "grid")
        svg.text(X(-1600) - 8, PY(p) + 4, f"{p}", "d", "end")
    svg.text(40, py0 - ph - 14, "靜壓 p − p室內（Pa）", "l")
    xs = list(range(-1600, 2201, 10))
    upts, ppts = [], []
    for x in xs:
        u = Qv / duct_area_at(x)
        if x < G["settling"]["x0"]:
            u *= max(0.0, (x + 1700) / 250)
        ql = 0.5 * ac.RHO * u**2
        upts.append((X(x), VY(u)))
        ppts.append((X(x), PY(-ql - loss_before(x, q))))
    svg.poly(upts, "c1")
    svg.poly(ppts, "c2")
    pf = ppts[-1][1]
    svg.line(X(2200), pf, X(2800), PY(0), "c2", 'style="stroke-dasharray:6 4"')
    svg.line(X(2200), VY(Qv / duct_area_at(2200)), X(2800), VY(Qv / duct_area_at(2200)), "c1", 'style="stroke-dasharray:6 4"')
    for x in (G["settling"]["x0"], G["contraction"]["x0"], 0, 800, 2200, 2800):
        svg.line(X(x), 120, X(x), py0, "guide")
    # annotations
    dep = ac.depression_at_ts(U)
    p_exit = -q - loss_before(799, q)
    p_dexit = -q / ac.diffuser_geometry()["area_ratio"] ** 2 - loss_before(2199, q)
    k_ts = ac.PLAN_K["ts_walls"] + ac.PLAN_K["ground_plate"] + ac.PLAN_K["model_supports"]
    wall_drop = ac.PLAN_K["ts_walls"] * q
    svg.circle(X(0), PY(-dep), 11, "shell", 'style="fill:#ffffff;stroke:#c2410c"')
    svg.text(X(0), PY(-dep) + 4, "1", "w", "middle")
    svg.circle(X(800), PY(p_exit), 11, "shell", 'style="fill:#ffffff;stroke:#c2410c"')
    svg.text(X(800), PY(p_exit) + 4, "2", "w", "middle")
    svg.lines(X(1180), PY(-140), [f"1  測試段入口 {-dep:.0f} Pa → 地板縫隙漏氣約 {ac.leak_speed(dep):.0f} m/s（所以天平要密封）",
                                  f"2  測試段內再降 {k_ts*q:.0f} Pa：壁面 {wall_drop:.1f} + 地面板 {ac.PLAN_K['ground_plate']*q:.1f} + 車模 {ac.PLAN_K['model_supports']*q:.1f}",
                                  f"    壁面摩擦造成 {wall_drop/0.8:.1f} Pa/m 的梯度 → 頂板出口墊高約 {ac.roof_shim_mm(ac.PLAN_K['ts_walls']):.1f} mm 可抵銷"], "w", 18)
    svg.text(X(1500), PY(p_dexit) - 40, f"擴散段把動壓轉回靜壓：回升 {p_dexit - p_exit:.0f} Pa", "d", "middle", True)
    svg.text(X(2500), PY(-50), f"風扇補回 ≈ {ac.fan_duty(U)['dp_calc']:.0f} Pa", "d", "middle", True)
    svg.text(X(-1200), PY(-40), f"穩定段 {15/ac.contraction_ratio():.1f} m/s：", "d", "middle", True)
    svg.text(X(-1200), PY(-40) + 16, "網在低速處，損失小", "d", "middle", True)
    svg.text(X(400), VY(15) - 8, "15 m/s", "d", "middle", True)
    svg.text(X(1500), VY(9) - 8, "擴散段減速", "d", "middle", True)
    svg.text(X(-450), VY(9) - 8, "收縮段加速 6 倍", "d", "middle", True)
    svg.save("B2-pressure-along-duct.svg")


if __name__ == "__main__":
    fig_airpath()
    fig_conditioning()
    fig_contraction()
    fig_test_section()
    fig_balance()
    fig_drag_path()
    fig_system_curve()
    fig_pressure_profile()
