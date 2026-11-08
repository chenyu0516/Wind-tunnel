#!/usr/bin/env python3
"""Figures for the mini class-project tunnel (spec/mini.json), Traditional Chinese labels.

Run:  python3 tools/make_mini_figures.py      -> figures/*.svg
"""
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mini_calc as mc  # noqa: E402  (must come first: selects spec/mini.json)
import svg_kit as kit  # noqa: E402
from svg_kit import Svg, View  # noqa: E402

ac = mc.ac
G = mc.G
kit.OUT = ac.ROOT / "figures"
UMAX = G["speeds_m_s"]["max_target"]


def con_half(s, which):
    con = G["contraction"]
    i = 0 if which == "w" else 1
    return ac.contraction_dim(s, con["inlet"][i], con["exit"][i], con["length"]) / 2


def rect_mm(svg, vw, x0, x1, v_top, v_bot, cls="shell", extra=""):
    svg.rect(vw.X(x0), vw.V(v_top), (x1 - x0) * vw.s, (v_top - v_bot) * vw.s, cls, extra)


def duct(svg, vw, which):
    """Walls of the whole duct; which='z' side view, 'y' top view."""
    axis = G["frame"]["duct_axis_z"] if which == "z" else 0.0
    sc, con, ts, di, bell, fan = G["settling"], G["contraction"], G["test_section"], G["diffuser"], G["inlet_bell"], G["fan"]
    i = 1 if which == "z" else 0
    h_sc = (sc["height"], sc["width"])[1 - i] / 2 if False else (sc["height"] if which == "z" else sc["width"]) / 2
    h_ts = (ts["height"] if which == "z" else ts["width"]) / 2
    h_out = di["outlet"][1 if which == "z" else 0] / 2
    R = bell["lip_radius_min"]
    for sgn in (1, -1):
        p0, p1, p2 = vw.P(sc["x0"], axis + sgn * h_sc), vw.P(bell["x0"] + R, axis + sgn * h_sc), vw.P(bell["x0"], axis + sgn * (h_sc + R))
        sweep = 0 if sgn > 0 else 1
        svg.path(f"M{p0[0]:.1f},{p0[1]:.1f} L{p1[0]:.1f},{p1[1]:.1f} A{R*vw.s:.1f},{R*vw.s:.1f} 0 0 {sweep} {p2[0]:.1f},{p2[1]:.1f}", "shell0")
        svg.line(*vw.P(sc["x0"], axis + sgn * h_sc), *vw.P(con["x0"], axis + sgn * h_sc), "shell0")
        svg.poly([vw.P(con["x0"] + s, axis + sgn * con_half(s, "h" if which == "z" else "w")) for s in range(0, con["length"] + 1, 4)], "shell0")
        svg.line(*vw.P(0, axis + sgn * h_ts), *vw.P(ts["length"], axis + sgn * h_ts), "shell0", 'style="stroke-width:2.5"')
        svg.line(*vw.P(di["x0"], axis + sgn * h_ts), *vw.P(di["x0"] + di["length"], axis + sgn * h_out), "shell0")
    for x, h in ((sc["x0"], h_sc), (con["x0"], h_sc), (0, h_ts), (ts["length"], h_ts), (di["x0"] + di["length"], h_out)):
        svg.line(*vw.P(x, axis + h + 12), *vw.P(x, axis + h), "thin")
        svg.line(*vw.P(x, axis - h - 12), *vw.P(x, axis - h), "thin")
    # honeycomb, screens, mesh, fan array
    hc = G["conditioning"]["honeycomb"]
    rect_mm(svg, vw, hc["x_upstream_face"], hc["x_upstream_face"] + hc["depth"], axis + h_sc, axis - h_sc, "hc")
    for xs in G["conditioning"]["screens_x"]:
        svg.line(*vw.P(xs, axis + h_sc), *vw.P(xs, axis - h_sc), "scr")
    svg.line(*vw.P(di["safety_mesh_x"], axis + h_out), *vw.P(di["safety_mesh_x"], axis - h_out), "scr")
    rect_mm(svg, vw, fan["x0"], fan["x0"] + fan["length"], axis + h_out, axis - h_out, "solid")
    for c in (-1, 1):
        cz = axis + c * fan["size"] / 2
        svg.circle(vw.X(fan["x0"] + fan["depth"] / 2), vw.V(cz), fan["size"] / 2 * vw.s * 0.9, "thin")
    svg.line(*vw.P(bell["x0"], axis), *vw.P(fan["x0"] + fan["length"], axis), "cl")


# ---------------------------------------------------------------- M1
def fig_airpath():
    svg = Svg(1400, 900, "迷你風洞總覽", "迷你版（1:43）氣流通道側視與俯視，依比例。")
    svg.header("圖 M1　迷你風洞總覽（1:43，依比例）", "上：側視　下：俯視　單位 mm　藍色箭頭為氣流方向　各段風速以測試段 14 m/s 計")
    s = 0.62
    ax = G["frame"]["duct_axis_z"]
    side = View(170, 330, s, G["inlet_bell"]["x0"], ax)
    top = View(170, 680, s, G["inlet_bell"]["x0"], 0)
    duct(svg, side, "z")
    duct(svg, top, "y")
    for vw, a in ((side, ax), (top, 0)):
        svg.flow(vw.X(-800), vw.V(a), vw.X(-706), vw.V(a))
        svg.flow(vw.X(1056), vw.V(a), vw.X(1150), vw.V(a))
    gp, car = G["ground_plate"], G["car"]
    zt = gp["z_underside"] + gp["thickness"]
    rect_mm(svg, side, gp["x_le"], gp["x_te"], zt, gp["z_underside"], "solid")
    rect_mm(svg, side, car["x_nose"], car["x_tail"], zt + 36, zt + 3, "car", 'rx="2"')
    svg.text(40, 300, "側視圖", "l")
    svg.text(40, 660, "俯視圖", "l")
    mods = [("喇叭口", G["inlet_bell"]), ("穩定段", G["settling"]), ("收縮段", G["contraction"]), ("測試段", G["test_section"]), ("擴散段", G["diffuser"]), ("風扇", G["fan"])]
    for i, (name, d) in enumerate(mods):
        x0, x1 = d["x0"], d["x0"] + d["length"]
        svg.hdim(side.X(x0), side.X(x1), 175, f"{d['length']}")
        svg.text(side.X((x0 + x1) / 2), 153 - (14 if name in ("喇叭口", "風扇") else 0), name, "l", "middle")
    total = G["fan"]["x0"] + G["fan"]["length"] - G["inlet_bell"]["x0"]
    svg.hdim(side.X(G["inlet_bell"]["x0"]), side.X(G["fan"]["x0"] + G["fan"]["length"]), 112, f"風管全長 {total:,}")
    sc, ts, di = G["settling"], G["test_section"], G["diffuser"]
    svg.text(side.X(sc["x0"] + 170), side.V(ax) - 6, f"高 {sc['height']}", "d", "middle", True)
    svg.text(side.X(60), side.V(ax) + 4, f"高 {ts['height']}", "d", "middle", True)
    svg.text(side.X(800), side.V(ax) - 6, f"出口 {di['outlet'][0]}×{di['outlet'][1]}", "d", "middle", True)
    svg.text(top.X(sc["x0"] + 170), top.V(0) - 8, f"寬 {sc['width']}", "d", "middle", True)
    svg.text(top.X(170), top.V(0) - 8, f"寬 {ts['width']}", "d", "middle", True)
    svg.text(top.X(800), top.V(0) - 8, f"出口 {di['outlet'][0]}×{di['outlet'][1]}", "d", "middle", True)
    cr, ar = ac.contraction_ratio(), ac.diffuser_geometry()["area_ratio"]
    for x, u in ((sc["x0"] + 170, UMAX / cr), (170, UMAX), (760, UMAX / ar)):
        svg.text(top.X(x), top.V(0) + 22, f"{u:.1f} m/s", "d", "middle", True)
    svg.text(side.X(-560), side.V(ax + 154.5) - 10, "吸管蜂巢 + 2 片網", "n", "middle", True)
    svg.text(side.X(1016), side.V(ax + 120) - 10, "4 × 120 mm 風扇", "n", "middle", True)
    svg.text(side.X(986), side.V(ax - 120) + 18, "安全網", "n", "end", True)
    svg.text(side.X(168), side.V(gp["z_underside"]) + 30, "地面板 + 1:43 車模", "n", "middle", True)
    ca = G["clear_air"]
    svg.text(40, 850, f"← 進氣端淨空 ≥ {ca['intake_min']}", "l")
    svg.text(1360, 850, f"排氣端淨空 ≥ {ca['exhaust_min']} →", "l", "end")
    svg.text(700, 850, f"風管 {total:,} + 淨空 {ca['intake_min'] + ca['exhaust_min']:,} ≈ {(total + ca['intake_min'] + ca['exhaust_min'])/1000:.1f} m（約兩張課桌長）", "l", "middle")
    svg.save("M1-airpath.svg")


# ---------------------------------------------------------------- M2
def fig_contraction():
    con = G["contraction"]
    L = con["length"]
    svg = Svg(1250, 760, "迷你收縮段曲線", "迷你風洞收縮段五次多項式曲線，依比例。")
    svg.header("圖 M2　收縮段壁面曲線（依比例）", "上半：寬度方向壁（俯視）　下半：高度方向壁（側視）　s 自收縮段入口起算，單位 mm")
    vw = View(110, 400, 1.35, 0, 0)
    svg.line(vw.X(-25), vw.V(0), vw.X(L + 30), vw.V(0), "cl")
    svg.poly([vw.P(s, con_half(s, "w")) for s in range(0, L + 1, 2)], "c1")
    svg.poly([vw.P(s, -con_half(s, "h")) for s in range(0, L + 1, 2)], "c2")
    for s in con["plan_table_s"]:
        w, h = 2 * con_half(s, "w"), 2 * con_half(s, "h")
        svg.line(vw.X(s), vw.V(w / 2), vw.X(s), vw.V(-h / 2), "guide")
        svg.text(vw.X(s), vw.V(w / 2) - 8, f"{w:.0f}", "d", "middle", True)
        svg.text(vw.X(s), vw.V(-h / 2) + 18, f"{h:.0f}", "d", "middle", True)
        svg.text(vw.X(s), vw.V(-154.5) + 52, f"{s}", "d", "middle")
    svg.text(vw.X(L / 2), vw.V(-154.5) + 72, "s（mm）", "n", "middle")
    svg.text(vw.X(-25), vw.V(-154.5) + 96, "標示值為全寬（上）與全高（下）＝肋板外形尺寸", "n")
    rx = 760
    svg.text(rx, 130, "曲線公式（與完整版相同）", "l")
    svg.lines(rx, 156, ["h(s) = hᵢ − (hᵢ − hₑ)·(6t⁵ − 15t⁴ + 10t³)", f"t = s / L，L = {L}", "兩端斜率 = 0、曲率 = 0 → 平順銜接"], "d", 19)
    for name, y, hi, he in (("寬度方向壁", 240, con["inlet"][0], con["exit"][0]), ("高度方向壁", 300, con["inlet"][1], con["exit"][1])):
        smax = max(abs(ac.contraction_wall_slope(s, hi, he, L)) for s in range(L + 1))
        kmax = max(abs(ac.contraction_wall_curvature(s, hi, he, L)) for s in range(L + 1))
        svg.lines(rx, y, [f"{name}：最大斜角 {math.degrees(math.atan(smax)):.1f}°，最小彎曲半徑 {1/kmax:.0f} mm"], "d")
    svg.text(rx, 360, "製作", "l")
    svg.lines(rx, 386, ["每面壁只單向彎曲：0.5–1 mm PET／PC 薄板", "彎貼在夾板或 MDF 肋板上（上表站位即肋板）", "四角用熱熔膠或膠帶從外側密封",
                        f"出口段差 ≤ {con['exit_step_max']} mm，只能是後向台階"], "d", 19)
    svg.save("M2-contraction.svg")


# ---------------------------------------------------------------- M3
def fig_test_section():
    svg = Svg(1400, 1240, "迷你測試段配置", "迷你測試段側視與俯視：地面板、車模、皮托管、靜壓孔、量測點、靜壓箱。")
    svg.header("圖 M3　測試段配置（依比例）", "上：側視（從 −y 側看）　下：俯視（+y 在上）　x 自收縮段出口起算；z 自測試段地板起算；單位 mm")
    s = 2.6
    side = View(90, 150 + 140 * s, s, -25, 0)
    top = View(90, 700 + 95 * s, s, -25, 0)
    ts, gp, car, pr = G["test_section"], G["ground_plate"], G["car"], G["probes"]
    zt = gp["z_underside"] + gp["thickness"]
    ticks = sorted({0, G["pressure_taps"]["entrance_ring"]["x"], gp["x_le"], pr["pitot_nose"]["x"], pr["fog_outlet"]["x_approx"],
                    car["x_nose"], G["pressure_taps"]["plenum_vent_tap"]["x"], car["x_tail"], gp["x_te"], ts["length"]})
    ry = 118
    svg.line(side.X(0), ry, side.X(ts["length"]), ry, "axis")
    for i, x in enumerate(ticks):
        svg.line(side.X(x), ry - 5, side.X(x), ry + 5, "axis")
        svg.text(side.X(x), ry - 9 - (12 if i % 2 else 0), f"{x}", "d", "middle")
        svg.line(side.X(x), ry + 6, side.X(x), top.V(-92), "guide")
    svg.text(side.X(-25), ry + 4, "x", "l")
    # side view shell
    rect_mm(svg, side, 0, ts["length"], 0, -ts["floor_t"], "solid")
    svg.line(side.X(0), side.V(ts["height"]), side.X(ts["length"]), side.V(ts["height"]), "shell0", 'style="stroke-width:3"')
    svg.line(side.X(0), side.V(ts["height"]), side.X(ts["length"]), side.V(ts["height"] + ts["roof_shim_at_exit"][1]), "tbd")
    svg.circle(side.X(0), side.V(ts["height"]), 5, "shell")
    svg.text(side.X(3), side.V(ts["height"]) - 10, "頂板鉸鏈", "n", "start", True)
    svg.text(side.X(ts["length"]), side.V(ts["height"] + 6) - 6, f"出口墊高 0–{ts['roof_shim_at_exit'][1]}", "w", "end", True)
    for z in (0, ts["height"]):
        svg.line(side.X(-25), side.V(z), side.X(0), side.V(z), "shell0")
    k = (G["diffuser"]["outlet"][1] - ts["height"]) / 2 / G["diffuser"]["length"]
    svg.line(side.X(ts["length"]), side.V(ts["height"]), side.X(ts["length"] + 24), side.V(ts["height"] + 24 * k), "shell0")
    svg.line(side.X(ts["length"]), side.V(0), side.X(ts["length"] + 24), side.V(-24 * k), "shell0")
    xr = G["pressure_taps"]["entrance_ring"]["x"]
    for z in (0, ts["height"]):
        svg.circle(side.X(xr), side.V(z), 4, "shell", 'style="fill:#187c91"')
    svg.text(side.X(xr) + 6, side.V(ts["height"]) + 16, "入口靜壓環 ×4", "n", "start", True)
    ow = gp["wheel_openings"]["approx_size_x_by_y"][0]
    xs = [gp["x_le"]] + sum([[a - ow / 2, a + ow / 2] for a in car["axle_x"]], []) + [gp["x_te"]]
    for a, b in zip(xs[::2], xs[1::2]):
        rect_mm(svg, side, a, b, zt, gp["z_underside"], "solid")
    svg.line(side.X(gp["x_te"]), side.V(zt - 1.5), side.X(gp["x_te"] + 16), side.V(zt - 4), "shell0", 'style="stroke-width:3"')
    svg.text(side.X(gp["x_te"] + 17), side.V(zt - 5) + 4, "可調襟翼", "n", "start", True)
    svg.text(side.X(gp["x_le"]) - 4, side.V(zt) - 8, "4:1 橢圓前緣", "n", "end", True)
    w, post = G["wheel_wells"], G["post"]
    zf = gp["z_underside"] - w["depth_max"]
    for a in car["axle_x"]:
        rect_mm(svg, side, a - 13, a + 13, gp["z_underside"], zf, "shell")
        rect_mm(svg, side, a - post["shroud_tube_d"] / 2, a + post["shroud_tube_d"] / 2, zf, 0, "shell")
        svg.line(side.X(a), side.V(zf + 3), side.X(a), side.V(-40), "dark", 'style="stroke-width:3;stroke:#4b5563"')
    pl = G["plenum"]
    rect_mm(svg, side, pl["x"][0], pl["x"][1], -ts["floor_t"], -40, "pc", 'style="fill:#eef6f9"')
    svg.text(side.X(sum(pl["x"]) / 2), side.V(-26), f"密封靜壓箱 {pl['x'][1]-pl['x'][0]}×{pl['y'][1]-pl['y'][0]}×{pl['depth']}（見圖 M4）", "l", "middle", True)
    # car
    rect_mm(svg, side, car["x_nose"], car["x_tail"], zt + 3.3 + 30, zt + 3.3, "car", 'rx="12"')
    R = car["tyre_d_planning"] / 2
    for a in car["axle_x"]:
        svg.circle(side.X(a), side.V(zt - 0.8 + R), R * s, "dark")
    svg.text(side.X((car["x_nose"] + car["x_tail"]) / 2), side.V(zt + 22), f"1:43 車模 {car['length']}（示意）", "l", "middle", True)
    # pitot
    p = pr["pitot_nose"]
    zp = zt + p["z_above_plate"]
    svg.line(side.X(p["x"]), side.V(zp), side.X(p["x"] + 16), side.V(zp), "dark", 'style="stroke-width:4;stroke:#1f2937"')
    svg.line(side.X(p["x"] + 16), side.V(zp), side.X(p["x"] + 16), side.V(ts["height"]), "dark", 'style="stroke-width:4;stroke:#1f2937"')
    svg.text(side.X(p["x"]) - 6, side.V(zp) + 4, f"皮托管 Ø{p['tube_d']}", "l", "end", True)
    taps = G["pressure_taps"]
    for x in taps["side_wall_taps"]["x"]:
        svg.circle(side.X(x), side.V(taps["side_wall_taps"]["z"]), 4, "shell")
    vx = taps["plenum_vent_tap"]["x"]
    svg.circle(side.X(vx), side.V(taps["plenum_vent_tap"]["z"]), 5, "shell", 'style="fill:#187c91"')
    svg.text(side.X(taps["side_wall_taps"]["x"][-1]) + 8, side.V(taps["side_wall_taps"]["z"]) + 4, "側壁靜壓孔 Ø1（−y 側）", "n", "start", True)
    svg.path(f"M{side.X(vx):.1f},{side.V(taps['plenum_vent_tap']['z']):.1f} L{side.X(vx):.1f},{side.V(taps['plenum_vent_tap']['z']) - 0:.1f}", "thin")
    svg.text(side.X(vx), side.V(taps["plenum_vent_tap"]["z"]) - 10, f"平衡孔 → Ø{pl['vent_line_d']} 管通靜壓箱", "n", "middle", True)
    xd = side.X(ts["length"]) + 70
    svg.vdim(xd, side.V(0), side.V(gp["z_underside"]), f"板下 {gp['z_underside']}")
    svg.vdim(xd, side.V(zt), side.V(zp), f"{p['z_above_plate']}（皮托管高於地面板）")
    svg.vdim(xd + 200, side.V(0), side.V(ts["height"]), f"{ts['height']}")
    svg.text(xd + 4, side.V(zt) - 2, f"板厚 {gp['thickness']}", "d", "start", True)
    svg.hdim(side.X(car["x_tail"]), side.X(ts["length"]), side.V(108), f"近尾流 {ts['length'] - car['x_tail']}")
    svg.text(side.X(-24), side.V(-34), f"井深 ≤ {w['depth_max']}；護套管 Ø{post['shroud_tube_d']}；支柱 Ø{post['bare_size_w_by_len'][0]}", "n")
    # top view
    hw = ts["width"] / 2
    for sgn in (1, -1):
        svg.line(top.X(-25), top.V(sgn * hw), top.X(ts["length"]), top.V(sgn * hw), "shell0", 'style="stroke-width:3"')
        kd = (G["diffuser"]["outlet"][0] - ts["width"]) / 2 / G["diffuser"]["length"]
        svg.line(top.X(ts["length"]), top.V(sgn * hw), top.X(ts["length"] + 24), top.V(sgn * (hw + 24 * kd)), "shell0")
        svg.circle(top.X(xr), top.V(sgn * hw), 4, "shell", 'style="fill:#187c91"')
    rect_mm(svg, top, gp["x_le"], gp["x_te"], hw, -hw, "pc", 'style="fill:#eef2f6;stroke-width:1"')
    rect_mm(svg, top, car["x_nose"], car["x_tail"], 22, -22, "car", 'rx="14"')
    for a in car["axle_x"]:
        for sgn in (1, -1):
            rect_mm(svg, top, a - ow / 2, a + ow / 2, sgn * car["track"] / 2 + 5, sgn * car["track"] / 2 - 5, "shell", 'style="fill:#ffffff"')
    svg.text(top.X((car["x_nose"] + car["x_tail"]) / 2), top.V(0) + 4, "車模（示意）", "l", "middle", True)
    svg.text(top.X(car["x_tail"]) + 6, top.V(-car["track"] / 2) + 30, f"開口 {ow}×{gp['wheel_openings']['approx_size_x_by_y'][1]} ×4，依實測軸距 {car['wheelbase']}、輪距 {car['track']} 調整", "n", "start", True)
    svg.circle(top.X(p["x"]), top.V(p["y"]), 4, "dark")
    svg.line(top.X(p["x"]), top.V(p["y"]), top.X(p["x"] + 16), top.V(p["y"]), "dark", 'style="stroke-width:4;stroke:#1f2937"')
    svg.text(top.X(p["x"]) - 6, top.V(p["y"]) + 4, f"皮托管 y = +{p['y']}", "l", "end", True)
    fx = pr["fog_outlet"]["x_approx"]
    svg.line(top.X(fx - 25), top.V(-30), top.X(fx), top.V(-30), "tbd", 'marker-end="url(#o)"')
    svg.text(top.X(fx - 27), top.V(-30) + 4, "霧氣出口（選配）", "w", "end", True)
    for xs_ in G["survey"]["stations_x"]:
        for y in G["survey"]["holes_y"]:
            svg.circle(top.X(xs_), top.V(y), 3.5, "shell", 'style="fill:#ffffff"')
    svg.text(top.X(G["survey"]["stations_x"][1]) + 8, top.V(G["survey"]["holes_y"][-1]) - 6, "量測頂板孔 ×5／站（間隔 21）", "n", "start", True)
    for x in taps["side_wall_taps"]["x"]:
        svg.circle(top.X(x), top.V(-hw), 4, "shell")
    svg.circle(top.X(vx), top.V(-hw), 5, "shell", 'style="fill:#187c91"')
    svg.vdim(top.X(ts["length"]) + 70, top.V(hw), top.V(-hw), f"{ts['width']}")
    svg.text(top.X(-24), top.V(hw) - 10, "+y（順流向看的左側）", "n")
    sh = G["survey"]["heights_above_plate"]
    svg.text(32, 1196, f"面板：{ts['side_wall_t']} mm 實心透明 PC（{UMAX} m/s 時頂板撓度約 {ac.strip_deflection_mm(ac.depression_at_ts(UMAX), ts['width'], ts['roof_t_min']):.2f} mm）", "n")
    svg.text(32, 1216, f"流場量測：移除車模，於 x = {G['survey']['stations_x'][0]} 與 {G['survey']['stations_x'][1]}、地面板上方 z = {', '.join(map(str, sh))} 各點（共 50 點）", "n")
    svg.save("M3-test-section.svg")


# ---------------------------------------------------------------- M4
def fig_saddle_balance():
    svg = Svg(1400, 1180, "車輪托座與天平", "上：單一車輪 V 形托座剖面（依比例）；下：密封靜壓箱與天平堆疊（示意）。")
    svg.header("圖 M4　車輪 V 形托座與天平（剖面）", "上半依比例（單一車輪，側視）；下半為示意、未依比例　單位 mm")
    s = 11.0
    vw = View(80, 110 + 46 * s, s, -26, 0)
    gp, w, post, car = G["ground_plate"], G["wheel_wells"], G["post"], G["car"]
    zt = gp["z_underside"] + gp["thickness"]
    ow = gp["wheel_openings"]["approx_size_x_by_y"][0]
    R = car["tyre_d_planning"] / 2
    phi = math.radians(G["cradle"]["contact_angle_deg"])
    zc_contact = zt - 0.3
    zc = zc_contact + R * math.cos(phi)
    xc = R * math.sin(phi)
    sink = mc.saddle()["sink_mm"]
    for x0, x1 in ((-26, -ow / 2), (ow / 2, 26)):
        rect_mm(svg, vw, x0, x1, zt, gp["z_underside"], "solid")
    rect_mm(svg, vw, -26, 26, 46, zt + 3.3, "car")
    svg.circle(vw.X(0), vw.V(zc), R * s, "dark", 'style="fill:#4b5563;opacity:0.85"')
    svg.text(vw.X(0), vw.V(zc) + 5, f"輪胎 Ø{car['tyre_d_planning']}", "l", "middle", extra='style="fill:#ffffff"')
    t = math.tan(phi)
    xe = 5.5
    ze = zc_contact + (xe - xc) * t
    zb = zc_contact - 6
    pts = [(-xe, ze), (-xc, zc_contact), (0, zc_contact - xc * t), (xc, zc_contact), (xe, ze), (xe, zb), (-xe, zb)]
    svg.poly([vw.P(x, z) for x, z in pts], "shell", True, 'style="fill:#cbd5df"')
    for sx in (-xc, xc):
        svg.circle(vw.X(sx), vw.V(zc_contact), 4, "shell", 'style="fill:#7c3aed"')
        svg.line(vw.X(sx), vw.V(zc_contact), vw.X(0), vw.V(zc), "guide", 'style="stroke:#7c3aed;stroke-width:1.5;stroke-dasharray:6 4"')
    zf = gp["z_underside"] - w["depth_max"]
    svg.path(f"M{vw.X(-13):.1f},{vw.V(gp['z_underside']):.1f} L{vw.X(-13):.1f},{vw.V(zf):.1f} L{vw.X(-post['shroud_tube_d']/2):.1f},{vw.V(zf):.1f} "
             f"M{vw.X(post['shroud_tube_d']/2):.1f},{vw.V(zf):.1f} L{vw.X(13):.1f},{vw.V(zf):.1f} L{vw.X(13):.1f},{vw.V(gp['z_underside']):.1f}", "shell0", 'style="stroke-width:2.5"')
    d5 = post["shroud_tube_d"] / 2
    rect_mm(svg, vw, -d5, -d5 + 0.5, zf, 0, "solid")
    rect_mm(svg, vw, d5 - 0.5, d5, zf, 0, "solid")
    d3 = post["bare_size_w_by_len"][0] / 2
    rect_mm(svg, vw, -d3, d3, zb, -5, "solid", 'style="fill:#94a3b8"')
    rect_mm(svg, vw, -26, -d5 - 0.5, 0, -G["test_section"]["floor_t"], "solid")
    rect_mm(svg, vw, d5 + 0.5, 26, 0, -G["test_section"]["floor_t"], "solid")
    xd = vw.X(26) + 14
    svg.vdim(xd, vw.V(0), vw.V(gp["z_underside"]), f"板下 {gp['z_underside']}")
    svg.vdim(xd + 110, vw.V(zf), vw.V(gp["z_underside"]), f"輪井 ≤ {w['depth_max']}")
    svg.vdim(xd + 110, vw.V(0), vw.V(zf), f"護套 {zf}")
    svg.text(xd + 4, vw.V(zt) - 2, f"地面板 {gp['thickness']}", "d", "start", True)
    svg.text(vw.X(-xe) - 8, vw.V(zb - 1.5), "V 形托座", "l", "end", True)
    svg.text(vw.X(-13) - 6, vw.V(zf + 5), "封底輪井", "l", "end", True)
    svg.text(vw.X(-d5) - 6, vw.V(4), f"護套管 Ø{post['shroud_tube_d']}（固定在風洞）", "n", "end", True)
    svg.text(vw.X(d3) + 8, vw.V(-3), f"支柱 Ø{post['bare_size_w_by_len'][0]}（屬天平）", "n", "start", True)
    nx = 860
    svg.text(nx, 140, "托座幾何", "l")
    svg.lines(nx, 166, [f"兩個接觸面與水平夾 {G['cradle']['contact_angle_deg']}°（接觸力與垂直夾同角）",
                        f"脫出條件：水平力 / 重量 = tan φ = {mc.saddle()['liftoff']:.2f}",
                        f"輪胎最低點比接觸點低 {sink:.2f} mm",
                        "規則：接觸點低於地面板頂；俯仰只用托座墊片調",
                        "托座可 3D 列印（PETG）或鋁塊銑 V 槽"], "d", 20)
    svg.lines(nx, 290, [f"待確認：車身離地會少約 {sink:.1f} mm", f"（1:43 車高約 {min(car['ride_height'])} mm，約 {sink/min(car['ride_height'])*100:.0f}%）",
                        "量測時記錄實際車高即可"], "w", 19)
    # lower schematic
    y0 = 700
    svg.line(40, y0 - 14, 1360, y0 - 14, "guide")
    svg.text(40, y0 + 6, "以下為示意，未依比例：測試段地板下方", "w")
    bx0, bx1, by0, by1 = 140, 720, y0 + 40, y0 + 340
    svg.path(f"M380,{by1} L{bx0},{by1} L{bx0},{by0} L{bx1},{by0} L{bx1},{by1} L480,{by1}", "shell0", 'style="stroke-width:4"')
    pl = G["plenum"]
    svg.text(bx0 + 8, by0 + 22, f"密封靜壓箱 {pl['x'][1]-pl['x'][0]}×{pl['y'][1]-pl['y'][0]}×{pl['depth']}（3 mm PC 或壓克力）", "l")
    svg.rect(bx1 - 4, by0 + 90, 8, 100, "solid", 'style="fill:#187c91"')
    svg.text(bx1 + 12, by0 + 140, "檢修蓋（泡棉膠條密封）", "n")
    svg.circle(bx1, by0 + 230, 6, "shell")
    svg.text(bx1 + 12, by0 + 234, "線材孔（熱熔膠封）→ HX711 ×2 在箱外", "n")
    svg.line(bx1, by0 + 40, bx1 + 80, by0 + 40, "scr")
    svg.text(bx1 + 86, by0 + 44, f"Ø{pl['vent_line_d']} 平衡管 → 側壁平衡孔（x = {G['pressure_taps']['plenum_vent_tap']['x']}）", "n")
    for px in (260, 600):
        svg.line(px, by0 - 30, px, by0 + 70, "dark", 'style="stroke-width:5;stroke:#94a3b8"')
    svg.text(608, by0 - 18, "支柱 ×4", "n")
    svg.rect(230, by0 + 70, 400, 14, "solid")
    svg.text(640, by0 + 82, "共用框架（鋁條或 3 mm 板）", "n")
    svg.rect(330, by0 + 100, 200, 12, "solid")
    for px in (340, 520):
        svg.line(px, by0 + 112, px, by0 + 160, "shell0", 'style="stroke-width:2;stroke:#7c3aed"')
    b = G["balance"]["drag_blades"]
    svg.text(540, by0 + 140, f"厚薄規鋼片 ×{b['count']}（{b['t']} × {b['w']} × {b['free_len']}）", "n")
    svg.rect(330, by0 + 160, 200, 12, "solid")
    svg.rect(390, by0 + 128, 60, 18, "shell", 'style="fill:#fde68a"')
    svg.text(380, by0 + 141, f"阻力荷重元 {int(G['balance']['drag_cell']['capacity_kg']*1000)} g（水平）", "n", "end")
    svg.rect(360, by0 + 190, 140, 22, "shell", 'style="fill:#fde68a"')
    svg.text(350, by0 + 205, f"垂直荷重元 {G['balance']['vertical_cell']['capacity_kg']:.0f} kg", "n", "end")
    svg.line(430, by0 + 172, 430, by0 + 190, "shell0", 'style="stroke-width:4"')
    svg.rect(405, by0 + 212, 50, by1 - by0 - 212 + 40, "solid")
    svg.path(f"M380,{by1} q4,8 12,10 q8,4 13,12 M480,{by1} q-4,8 -12,10 q-8,4 -13,12", "shell0", 'style="stroke:#7c3aed;stroke-width:2"')
    svg.text(490, by1 + 26, "薄橡膠裙邊（手套或氣球膜）", "n")
    svg.rect(340, by1 + 40, 180, 30, "solid", 'style="fill:#9ca3af"')
    svg.text(530, by1 + 60, f"底座 + 配重約 {pl['pedestal_added_mass_kg']} kg（磚塊或書）", "n")
    svg.rect(60, by1 + 70, 1280, 12, "solid", 'style="fill:url(#hatch)"')
    svg.text(70, by1 + 66, "桌面或地板（不要放在風洞框架上）", "n")
    ds = mc.drag_stage()
    st = G["balance"]["stops"]
    svg.lines(960, by0 + 210, [f"限位：阻力 {st['drag_N']} N、垂直 {st['vertical_kg']} kg", f"活動質量 ≤ {G['balance']['moving_mass_max_kg']} kg",
                               f"阻力方向自然頻率約 {ds['f_Hz']:.0f} Hz", f"荷重元承受約 {ds['cell_share']*100:.0f}% 阻力（校正扣除）"], "n", 18)
    svg.save("M4-saddle-and-balance.svg")


# ---------------------------------------------------------------- M5
def fig_wiring():
    svg = Svg(1400, 960, "Arduino Uno 接線", "Uno 接 4 個 PWM 風扇、3 組 HX711（阻力、垂直、鐘罩壓力計）、兩顆 BMP280、安全開關與選配輸出。")
    svg.header("圖 M5　Arduino Uno 接線圖", "紅：12 V　黑：GND　藍：訊號　綠：I²C　所有 GND 必須共地；風扇電源不可取自 Uno")
    ux, uy, uw, uh = 600, 150, 240, 600
    svg.rect(ux, uy, uw, uh, "shell", 'rx="10" style="fill:#e0f2fe"')
    svg.text(ux + uw / 2, uy + 30, "Arduino Uno R3", "t", "middle")
    ly = {"D9": 225, "D2": 330, "D3": 425, "D8": 600}
    right = ["D4", "D5", "D6", "D7", "A0", "A1", "D11", "D12", "A4", "A5"]
    ry = {p_: uy + 70 + i * 50 for i, p_ in enumerate(right)}
    for p_, y in ly.items():
        svg.text(ux + 12, y + 4, p_, "l")
    for p_, y in ry.items():
        svg.text(ux + uw - 12, y + 4, p_, "l", "end")
    svg.text(ux + uw / 2, uy + uh - 40, "5V / GND → 感測器", "n", "middle")
    svg.text(ux + uw / 2, uy + uh - 20, "USB → 筆電（供電 + CSV）", "n", "middle")
    red = 'style="stroke:#dc2626;stroke-width:3"'
    blk = 'style="stroke:#111827;stroke-width:3"'
    blu = 'style="stroke:#2563eb;stroke-width:2"'
    grn = 'style="stroke:#16a34a;stroke-width:2.5"'
    # power chain
    svg.rect(40, 120, 150, 60, "solid", 'rx="6"')
    svg.text(115, 148, "12 V 電源", "l", "middle")
    svg.text(115, 166, f"≥ {G['electronics']['psu']['current_a_min']} A（可用舊 ATX）", "n", "middle")
    svg.rect(220, 130, 80, 40, "shell", 'rx="6" style="fill:#fee2e2"')
    svg.text(260, 155, f"保險絲 {G['electronics']['fuse_a']} A", "n", "middle")
    svg.rect(330, 130, 90, 40, "shell", 'rx="6" style="fill:#fecaca"')
    svg.text(375, 155, "緊急停止", "l", "middle")
    svg.line(190, 150, 220, 150, "thin", red)
    svg.line(300, 150, 330, 150, "thin", red)
    svg.line(420, 150, 460, 150, "thin", red)
    fy0, step = 260, 95
    for i in range(4):
        fy = fy0 + i * step
        svg.rect(60, fy, 200, 70, "shell", 'rx="8"')
        svg.circle(95, fy + 35, 26, "thin")
        svg.text(170, fy + 30, f"風扇 {i+1}（4 線 PWM）", "l", "middle")
        svg.text(170, fy + 50, "12V · GND · 轉速 · PWM", "n", "middle")
        svg.line(260, fy + 8, 460, fy + 8, "thin", red)
        svg.line(260, fy + 60, 300, fy + 60, "thin", blu)
    svg.line(460, 150, 460, fy0 + 3 * step + 8, "thin", red)
    svg.text(468, 200, "12 V", "n")
    svg.line(300, ly["D9"], 300, fy0 + 3 * step + 60, "thin", blu)
    svg.line(300, ly["D9"], ux, ly["D9"], "thin", blu)
    svg.text(312, ly["D9"] - 6, "PWM 25 kHz（4 條並聯）", "n")
    svg.path(f"M260,{fy0+36} L280,{fy0+36} L280,{ly['D2']} L{ux},{ly['D2']}", "thin", blu)
    svg.path(f"M260,{fy0+step+36} L270,{fy0+step+36} L270,{ly['D3']} L{ux},{ly['D3']}", "thin", blu)
    svg.text(480, ly["D2"] - 6, "轉速 1 → D2", "n")
    svg.text(480, ly["D3"] - 6, "轉速 2 → D3", "n")
    svg.rect(470, 640, 110, 40, "shell", 'rx="6"')
    svg.text(525, 665, "艙蓋安全開關", "n", "middle")
    svg.path(f"M525,640 L525,{ly['D8']} L{ux},{ly['D8']}", "thin", blu)
    svg.line(60, 800, 860, 800, "thin", blk)
    svg.text(70, 790, "GND：12 V 電源 GND、風扇 GND、Uno GND 接在一起（共地）", "n")
    svg.text(70, 822, "急停切斷的是 12 V（硬體），不依賴 Uno 程式", "w")
    # right side devices
    dx = 940
    for name, sub, a, b in (("HX711（阻力）", "→ 100 g 荷重元", "D4", "D5"), ("HX711（垂直）", "→ 1 kg 荷重元", "D6", "D7"), ("HX711 #3（風速 A）", "→ 鐘罩壓力計 100 g", "A0", "A1")):
        svg.rect(dx, ry[a] - 22, 210, 82, "shell", 'rx="6" style="fill:#fef9c3"')
        svg.text(dx + 105, ry[a] + 4, name, "l", "middle")
        svg.text(dx + 105, ry[a] + 24, f"DT={a}  SCK={b}", "n", "middle")
        svg.text(dx + 105, ry[a] + 44, sub, "n", "middle")
        svg.line(ux + uw, ry[a], dx, ry[a], "thin", blu)
        svg.line(ux + uw, ry[b], dx, ry[b], "thin", blu)
    for p_, label in (("D11", "MOSFET → 霧化器（選配）"), ("D12", "MOSFET → 12 V LED 燈條（選配）")):
        svg.line(ux + uw, ry[p_], dx, ry[p_], "thin", blu)
        svg.text(dx + 8, ry[p_] + 4, label, "n")
    bx_sda, bx_scl = 880, 900
    svg.path(f"M{ux+uw},{ry['A4']} L{bx_sda},{ry['A4']} L{bx_sda},{ry['A4']+250}", "thin", grn)
    svg.path(f"M{ux+uw},{ry['A5']} L{bx_scl},{ry['A5']} L{bx_scl},{ry['A4']+250}", "thin", grn)
    svg.text(bx_sda - 4, ry["A4"] - 6, "SDA", "n", "end")
    svg.text(bx_scl + 4, ry["A5"] - 6, "SCL", "n")
    for i, (name, sub) in enumerate((("BMP280 × 2（風速 B）", "I²C 0x76 低壓、0x77 高壓"), ("LCD 1602（選配）", "I²C 0x27 · 顯示風速與力"))):
        y = ry["A5"] + 50 + i * 100
        svg.rect(dx, y, 240, 70, "shell", 'rx="6" style="fill:#dcfce7"')
        svg.text(dx + 120, y + 28, name, "l", "middle")
        svg.text(dx + 120, y + 50, sub, "n", "middle")
        svg.line(bx_sda, y + 22, dx, y + 22, "thin", grn)
        svg.line(bx_scl, y + 46, dx, y + 46, "thin", grn)
    y = ry["A5"] + 50
    svg.lines(dx + 250, y + 10, ["選 5 V 可用的模組", "（板上有穩壓與電平轉換）", "管路見圖 M7", "每次開風扇前先歸零"], "n", 18)
    svg.text(40, 880, "D10 保留不用（與 D9 共用 Timer1）；D13 板上狀態燈", "n")
    svg.text(40, 906, "程式：讀 q → PID 調 PWM 定速；自動跑「歸零 → 升速 → 穩定 60 s → 擷取 30 s → 停機 → 再歸零」；每筆 CSV 經 USB 傳到筆電", "n")
    svg.save("M5-uno-wiring.svg")


# ---------------------------------------------------------------- M6
def fig_fan_curve():
    svg = Svg(1240, 640, "風扇曲線與系統曲線", "4 個 120 mm 風扇在不同 PWM 下的估計曲線，與迷你風洞系統曲線的交點。")
    svg.header("圖 M6　風扇陣列 vs 風洞系統曲線（估計）", "直線：4 個風扇並聯，依官方最大風量與最大靜壓連線（實際曲線待量測）　藍色拋物線：風洞需要的壓力")
    x0, y0, w, h = 90, 560, 700, 440
    qmax, pmax = 1800, 360
    X = lambda q: x0 + q / qmax * w
    Y = lambda p: y0 - p / pmax * h
    for q in range(0, qmax + 1, 300):
        svg.line(X(q), y0, X(q), y0 - h, "grid")
        svg.text(X(q), y0 + 18, f"{q:,}", "d", "middle")
    for p in range(0, pmax + 1, 60):
        svg.line(x0, Y(p), x0 + w, Y(p), "grid")
        svg.text(x0 - 8, Y(p) + 4, f"{p}", "d", "end")
    svg.line(x0, y0, x0 + w, y0, "axis")
    svg.line(x0, y0, x0, y0 - h, "axis")
    svg.text(x0 + w / 2, y0 + 40, "流量 Q（m³/h）", "l", "middle")
    svg.text(x0 - 60, y0 - h - 14, "Δp（Pa）", "l")
    pts = []
    for i in range(0, 101):
        Q = qmax * i / 100
        U = Q / 3600 / ac.ts_area_m2()
        dp = mc.system_dp(U)
        if dp <= pmax:
            pts.append((X(Q), Y(dp)))
    svg.poly(pts, "c1")
    f = G["fan"]
    for d in (1.0, 0.8, 0.6, 0.4):
        q0 = f["count"] * f["q_max_m3h_each"] * d
        p0 = f["p_max_pa"] * d * d
        svg.line(X(0), Y(min(p0, pmax)) if p0 <= pmax else Y(pmax), X(q0), Y(0), "c2") if p0 <= pmax else \
            svg.line(X(q0 * (1 - pmax / p0)), Y(pmax), X(q0), Y(0), "c2")
        op = mc.operating_point(d)
        svg.circle(X(op["Q_m3h"]), Y(op["dp"]), 5, "shell", 'style="fill:#187c91"')
        svg.text(X(op["Q_m3h"]) + 8, Y(op["dp"]) - 8, f"PWM {d*100:.0f}% → {op['U']:.1f} m/s", "d", "start", True)
    rx = 850
    svg.text(rx, 130, "怎麼讀", "l")
    svg.lines(rx, 156, ["紫線：風扇能給的壓力（轉速越低越往左下）", "藍線：風洞在各流量下需要的壓力", "交點：實際會跑到的風速",
                        "", f"5 m/s 約需 PWM {mc.duty_for(5)*100:.0f}%", f"10 m/s 約需 PWM {mc.duty_for(10)*100:.0f}%（課堂展示）",
                        f"{UMAX} m/s 約需 PWM {mc.duty_for(UMAX)*100:.0f}%", "", "PWM 只是起點：Arduino 會讀壓差、",
                        "用 PID 自動調到目標風速", "", "直線只是粗估，真實曲線可能較低；", "裝好後用 PWM 掃描實測一次"], "d", 21)
    svg.save("M6-fan-curve.svg")


# ---------------------------------------------------------------- M7
def fig_speed_sensors():
    ss = G["electronics"]["speed_sensor"]
    A_, B_ = ss["A_bell_manometer"], ss["B_barometer_pair"]
    b, liq = A_["bell"], A_["liquid"]
    bl = mc.bell()
    svg = Svg(1400, 980, "自製風速感測器", "主感測器 A：鐘罩壓力計吊在 100 g 荷重元下；備援 B：兩顆 BMP280 氣壓計；兩者用三通接同一組量測孔。")
    svg.header("圖 M7　自製風速感測器：A 鐘罩壓力計（主）＋ B 兩顆氣壓計（備援）",
               "剖面依比例（mm）；低壓接鐘罩內部，高壓接盒內空氣 → 壓差把鐘罩往下拉，荷重元讀數隨 q 增加")
    s_ = 2.9
    vw = View(300, 840, s_)                      # x = mm from box inner left wall, v = mm above box floor
    box_w, box_h = 170, 175
    dish_d, dish_h, dish_x0, dish_z0 = A_["dish_inner_d_min"], liq["depth"] + 12, 20, 8
    cx = dish_x0 + dish_d / 2
    lz = dish_z0 + liq["depth"]                  # liquid rest level
    rim = dish_z0 + A_["rim_above_dish_floor"]
    top = rim + b["height"]
    ri, ro = b["inner_d"] / 2, b["inner_d"] / 2 + b["wall_t"]
    svg.rect(vw.X(0), vw.V(box_h), box_w * s_, box_h * s_, "shell0", 'rx="10" style="stroke-width:3"')
    svg.text(vw.X(box_w) - 8, vw.V(box_h) + 20, "密封保鮮盒（≥ 1.5 L）", "l", "end")
    svg.text(vw.X(box_w) - 8, vw.V(box_h) + 38, "電線出口用熱熔膠封死", "n", "end")
    svg.rect(vw.X(dish_x0), vw.V(dish_z0 + dish_h), dish_d * s_, dish_h * s_, "shell0")
    svg.rect(vw.X(dish_x0), vw.V(lz), dish_d * s_, liq["depth"] * s_, "pc", 'style="fill:#fde68a;stroke:none;opacity:0.7"')
    svg.rect(vw.X(dish_x0 - 6), vw.V(dish_z0), (dish_d + 12) * s_, 3 * s_, "solid")
    for x_ in (cx - ro, cx + ri):
        svg.rect(vw.X(x_), vw.V(top), b["wall_t"] * s_, b["height"] * s_, "dark")
    svg.rect(vw.X(cx - ro), vw.V(top), 2 * ro * s_, b["wall_t"] * s_, "dark")
    svg.line(vw.X(cx - ri), vw.V(lz + bl["dh_max_mm"]), vw.X(cx + ri), vw.V(lz + bl["dh_max_mm"]), "tbd")
    svg.text(vw.X(cx + ri) - 6, vw.V(lz + bl["dh_max_mm"]) - 6, "最大時液面", "w", "end", halo=True)
    tip = lz + A_["snorkel"]["tip_above_rest_level"]
    sx_out, sx_in, sz_low = cx - ro - 8, cx - ri + 8, dish_z0 + 4
    svg.poly([vw.P(0, 120), vw.P(sx_out, 120), vw.P(sx_out, sz_low), vw.P(sx_in, sz_low), vw.P(sx_in, tip)], "c2")
    svg.circle(*vw.P(sx_in, tip), 3, "c2")
    svg.text(vw.X(sx_in) + 8, vw.V(tip) - 4, "通氣管口", "n", halo=True)
    svg.vdim(vw.X(sx_in) + 18, vw.V(tip), vw.V(lz), f"{A_['snorkel']['tip_above_rest_level']}")
    lc_z = top + 30
    br_x = cx + 75
    svg.rect(vw.X(br_x), vw.V(lc_z), 10 * s_, (lc_z - dish_z0) * s_, "solid")
    svg.rect(vw.X(cx - 10), vw.V(lc_z + 12.7), (br_x + 10 - (cx - 10)) * s_, 12.7 * s_, "pc", 'style="fill:#e5e7eb"')
    svg.text(vw.X((cx + br_x) / 2), vw.V(lc_z + 12.7) - 8, "100 g 荷重元 → HX711 #3（A0/A1）", "l", "middle", halo=True)
    svg.line(vw.X(cx), vw.V(lc_z), vw.X(cx), vw.V(top), "thin", 'style="stroke-width:1.5"')
    svg.text(vw.X(cx) + 6, vw.V(lc_z) + 18, "細線吊掛", "n", halo=True)
    svg.lines(vw.X(br_x) - 6, vw.V(dish_z0 + dish_h + 30), ["硬支架", "黏盒底", "不黏盒蓋"], "n", 16, "end")
    svg.rect(vw.X(-8), vw.V(122), 8 * s_, 4 * s_, "solid")
    svg.lines(vw.X(-30), vw.V(120) - 4, ["低壓", "皮托管靜壓／入口環", "→ 鐘罩內"], "w", 16, "end")
    svg.rect(vw.X(-8), vw.V(160), 8 * s_, 4 * s_, "solid")
    svg.lines(vw.X(-30), vw.V(158) - 4, ["高壓", "皮托管總壓／穩定段環", "→ 盒內空氣"], "w", 16, "end")
    svg.hdim(vw.X(cx - ri), vw.X(cx + ri), vw.V(top) - 22, f"內徑 {b['inner_d']}")
    svg.vdim(vw.X(cx + ro) + 22, vw.V(top), vw.V(rim), f"高 {b['height']}")
    svg.vdim(vw.X(cx - ro) - 16, vw.V(lz), vw.V(rim), f"浸入 {A_['immersion']}", left=True)
    svg.vdim(vw.X(dish_x0 + dish_d) + 10, vw.V(lz), vw.V(dish_z0), f"油深 {liq['depth']}")
    svg.vdim(vw.X(cx + ri) - 12, vw.V(rim), vw.V(dish_z0), f"{A_['rim_above_dish_floor']}", left=True)
    svg.hdim(vw.X(dish_x0), vw.X(dish_x0 + dish_d), vw.V(dish_z0) + 30, f"碗內徑 ≥ {dish_d}", below=True)
    svg.lines(40, 900, [f"鐘罩：3D 列印 PETG 直筒（不要用錐形杯），壁厚 {b['wall_t']} mm，約 {bl['mass_g']:.0f} g；液體：嬰兒油（不易蒸發、不導電）；通氣管：4 mm 黃銅管彎 U 形，從鐘罩口下方繞進去",
                        f"有效面積約 {bl['area_eff_m2']*1e6:.0f} mm²（校正後以實測為準）：15 Pa ≈ {15*bl['area_eff_m2']/mc.G_ACC*1000:.1f} g，最大 {bl['dp_max']:.0f} Pa ≈ {bl['f_max_g']:.0f} g；荷重元最大負載約 {bl['load_max_g']:.0f} g / {bl['cap_g']:.0f} g；最大時鐘罩內液面升高約 {bl['dh_max_mm']:.0f} mm",
                        f"解析度：天平 1 mN ÷ 面積 ≈ {bl['res_pa']:.2f} Pa → 5 m/s 風速誤差約 ±{mc.speed_error(5,'A')*100:.1f}%"], "n", 18)
    # right: backup B
    rx = 820
    svg.text(rx, 130, "B　備援：兩顆 BMP280（I²C 0x76、0x77）", "l")
    for i, (lab, addr) in enumerate((("B 高壓", "0x77"), ("B 低壓", "0x76"))):
        x_ = rx + 20 + i * 150
        svg.rect(x_, 170, 110, 120, "shell", 'rx="14"')
        svg.rect(x_ + 30, 215, 50, 30, "solid")
        svg.text(x_ + 55, 235, "BMP280", "n", "middle")
        svg.text(x_ + 55, 160, f"{lab}（{addr}）", "n", "middle")
        svg.rect(x_ + 48, 290, 14, 22, "solid")
        svg.text(x_ + 55, 330, "接管嘴", "n", "middle")
    svg.rect(rx + 8, 180, 285, 100, "tbd", 'rx="6" style="fill:none"')
    svg.lines(rx + 320, 190, ["底片盒或小密封盒", "各裝一顆、只留一個管嘴", "兩盒膠帶綁在一起、包泡棉", "→ 溫度相同，漂移較小", "電線孔用熱熔膠封"], "n", 18)
    svg.lines(rx, 370, [f"歸零後誤差約 ±{mc.baro_pair_error_pa():.1f} Pa（雜訊平均 1 s ＋ 兩顆溫差 {B_['run_temp_drift_k']} K）",
                        f"→ 12 m/s 風速誤差 ±{mc.speed_error(12,'B')*100:.1f}%，5 m/s 約 ±{mc.speed_error(5,'B')*100:.1f}%",
                        "兩顆出廠差約 ±12 Pa：每次開風扇前一定要歸零", "另外提供室內氣壓與溫度（算空氣密度）"], "n", 18)
    # plumbing
    py = 520
    svg.text(rx, py, "管路：A、B 用三通接在同一組量測孔", "l")
    svg.rect(rx, py + 30, 150, 60, "shell", 'rx="6"')
    svg.lines(rx + 75, py + 55, ["皮托管", "或壁面靜壓環"], "n", 18, "middle")
    for lab, col, yy, ya, yb in (("高壓（總壓）", "c1", py + 45, py + 15, py + 90), ("低壓（靜壓）", "c2", py + 80, py + 35, py + 110)):
        svg.line(rx + 150, yy, rx + 300, yy, col)
        svg.text(rx + 158, yy - 6, lab, "n")
        svg.circle(rx + 300, yy, 6, col)
        svg.line(rx + 300, yy, rx + 380, ya, col)
        svg.line(rx + 300, yy, rx + 380, yb, col)
    svg.rect(rx + 380, py + 0, 160, 50, "shell", 'rx="6" style="fill:#fef9c3"')
    svg.text(rx + 460, py + 30, "A 鐘罩壓力計", "l", "middle")
    svg.rect(rx + 380, py + 75, 160, 50, "shell", 'rx="6" style="fill:#dcfce7"')
    svg.text(rx + 460, py + 105, "B 氣壓計對", "l", "middle")
    svg.lines(rx, py + 170, ["高壓 → A 的盒內空氣、B 高壓盒；低壓 → A 的鐘罩內、B 低壓盒",
                             "平時接壁面靜壓環（穩定段 − 測試段入口）控制風速；",
                             "校正 k 時：A 接壁面環、B 接皮托管，同時量 → 不用換管",
                             "A、B 讀數差 > 1 Pa 或 2% → 先查漏氣，再決定用哪一個（見計畫書）"], "n", 18)
    svg.save("M7-speed-sensors.svg")


# ---------------------------------------------------------------- M8
def fig_sensor_calibration():
    cal = G["electronics"]["speed_sensor"]["calibration"]
    svg = Svg(1400, 760, "風速感測器校正", "用針筒產生壓差，以 1:10 傾斜水柱計為標準，校正鐘罩壓力計與氣壓計對。")
    svg.header("圖 M8　風速感測器桌上校正（不用開風扇）",
               "針筒慢慢抽氣 → 傾斜水柱計讀數 L → Δp = ρ g L / 10 ≈ 0.98 Pa/mm；同時記錄 A、B 讀數")
    # syringe
    svg.rect(60, 250, 200, 50, "shell", 'rx="6"')
    svg.rect(260, 265, 40, 20, "solid")
    svg.rect(20, 262, 60, 26, "solid")
    svg.text(160, 240, "60 mL 針筒（慢慢拉）", "l", "middle")
    svg.circle(380, 275, 7, "c2")
    svg.line(300, 275, 373, 275, "c2")
    svg.text(380, 255, "三通", "n", "middle")
    # to manometer and to sensors low sides
    svg.path("M380,282 L380,420 L470,420", "c2")
    svg.path("M387,275 L700,275", "c2")
    svg.circle(700, 275, 7, "c2")
    svg.path("M700,268 L700,170 L900,170", "c2")
    svg.path("M707,275 L900,275", "c2")
    svg.rect(900, 140, 220, 60, "shell", 'rx="6" style="fill:#fef9c3"')
    svg.text(1010, 176, "A 鐘罩內（低壓口）", "l", "middle")
    svg.rect(900, 245, 220, 60, "shell", 'rx="6" style="fill:#dcfce7"')
    svg.text(1010, 281, "B 低壓盒", "l", "middle")
    svg.lines(1140, 165, ["A 的盒內空氣、B 高壓盒：", "開著通室內（高壓口不接）"], "n", 18)
    # inclined manometer
    x0, y0, L = 470, 600, 560
    import math as _m
    ang = _m.atan(0.1)
    svg.line(x0, y0, x0 + L * _m.cos(ang), y0 - L * _m.sin(ang), "shell0", 'style="stroke-width:10;stroke:#e5e7eb"')
    svg.line(x0, y0, x0 + L * _m.cos(ang), y0 - L * _m.sin(ang), "c1")
    svg.rect(x0 - 40, y0 - 30, 50, 60, "pc", 'style="fill:#bfdbfe"')
    svg.text(x0 - 15, y0 + 50, "水槽", "n", "middle")
    svg.path(f"M470,420 L{x0-15},420 L{x0-15},{y0-30}", "c2")
    svg.line(x0, y0 + 20, x0 + L, y0 + 20, "guide")
    svg.text(x0 + L + 10, y0 - L * _m.sin(ang) + 4, "斜率 1:10", "n")
    for k in range(0, 11):
        xx = x0 + k * L / 10 * _m.cos(ang)
        yy = y0 - k * L / 10 * _m.sin(ang)
        svg.line(xx, yy - 8, xx, yy + 8, "thin")
    svg.text(x0 + L / 2, y0 + 48, "1:10 傾斜水柱計（透明管＋尺，加食用色素）", "l", "middle")
    svg.text(x0 + L / 2, y0 + 68, f"讀數精度 ±{cal['read_mm_along_tube']} mm（沿管）→ ±{cal['read_mm_along_tube']*0.98:.1f} Pa", "n", "middle")
    svg.lines(900, 380, ["步驟", "1. 全部接好，捏住針筒管 60 s：讀數變化須 < " + f"{cal['accept_leak_pa_per_60s']} Pa（漏氣測試）",
                        "2. 垂直水柱 0 → 2 → 5 → 10 → 15 → 20 mm（沿管 0–200 mm）", "   每點停 10 s，記錄 L、A、B；再反向回到 0",
                        "3. 重複 3 次；A 的斜率 = 有效面積（寫回 spec）", "4. 合格：直線誤差 ≤ " + f"{cal['accept_linearity_pa_or_pct'][0]} Pa 或 {cal['accept_linearity_pa_or_pct'][1]}%",
                        f"   遲滯 ≤ {cal['accept_hysteresis_pa']} Pa；A、B 相差 ≤ {cal['accept_A_vs_B_pa_or_pct'][0]} Pa 或 {cal['accept_A_vs_B_pa_or_pct'][1]}%"], "n", 19)
    svg.save("M8-sensor-calibration.svg")


if __name__ == "__main__":
    fig_airpath()
    fig_contraction()
    fig_test_section()
    fig_saddle_balance()
    fig_wiring()
    fig_fan_curve()
    fig_speed_sensors()
    fig_sensor_calibration()
