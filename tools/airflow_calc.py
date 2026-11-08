#!/usr/bin/env python3
"""Generic airflow-path calculations shared by the tunnel tools.

Loads the spec named by WT_SPEC (default spec/mini.json). mini_calc.py builds the mini report on top of it.
The report() at the bottom was written for the 1:18 reference design (archive/full_1to18).
Other tools import the functions below; keep them free of side effects.
"""
import json
import math
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Set WT_SPEC to another spec file (e.g. spec/mini.json) before importing to use a different design.
SPEC_PATH = ROOT / os.environ.get("WT_SPEC", "spec/mini.json")
G = json.loads(SPEC_PATH.read_text())

RHO = G["air"]["rho_kg_m3"]
NU = G["air"]["nu_m2_s"]

# Loss coefficients from build_plan.md A5, referred to test-section q.
PLAN_K = G.get("losses_K") or {
    "inlet_conditioning": 0.13,
    "contraction": 0.03,
    "ts_walls": 0.05,
    "ground_plate": 0.03,
    "model_supports": 0.03,
    "diffuser": 0.17,
    "safety_screen": 0.15,
    "fan_plane_q": 0.15,
}
PLAN_K = {k: v for k, v in PLAN_K.items() if not k.startswith("_")}
DESIGN_MARGIN = 1.5
FAN_EFFICIENCY = 0.40


# ---------- geometry helpers ----------
def ts_area_m2():
    ts = G["test_section"]
    return ts["width"] * ts["height"] / 1e6


def settling_area_m2():
    sc = G["settling"]
    return sc["width"] * sc["height"] / 1e6


def contraction_ratio():
    return settling_area_m2() / ts_area_m2()


def smooth_step(t):
    return 6 * t**5 - 15 * t**4 + 10 * t**3


def contraction_dim(s, hi, he, L):
    """Full dimension (height or width) at distance s from the contraction inlet."""
    return hi - (hi - he) * smooth_step(s / L)


def contraction_wall_slope(s, hi, he, L):
    """Slope of one wall (= half the dimension change), dz/ds."""
    t = s / L
    return -(hi - he) / 2 * 30 * t**2 * (1 - t) ** 2 / L


def contraction_wall_curvature(s, hi, he, L):
    t = s / L
    return -(hi - he) / 2 * (60 * t - 180 * t**2 + 120 * t**3) / L**2


def module_chain():
    """(name, x0, x1) for each module along the duct."""
    m = []
    for key in ("inlet_bell", "settling", "contraction", "test_section", "diffuser"):
        d = G[key]
        m.append((key, d["x0"], d["x0"] + d["length"]))
    f = G["fan"]
    m.append(("fan", f["x0"], f["x0"] + f.get("length", f.get("length_approx"))))
    return m


def diffuser_geometry():
    """Round (outlet_d) or rectangular (outlet [w, h]) diffuser exit; angle from equivalent diameters."""
    d = G["diffuser"]
    a_in = d["inlet"][0] * d["inlet"][1] / 1e6
    if "outlet_d" in d:
        a_out = math.pi * (d["outlet_d"] / 1000) ** 2 / 4
    else:
        a_out = d["outlet"][0] * d["outlet"][1] / 1e6
    d_eq_in = math.sqrt(4 * a_in / math.pi)
    d_eq_out = math.sqrt(4 * a_out / math.pi)
    half_angle = math.degrees(math.atan((d_eq_out - d_eq_in) / 2 / (d["length"] / 1000)))
    out = {"area_in": a_in, "area_out": a_out, "area_ratio": a_out / a_in,
           "d_eq_in_mm": d_eq_in * 1000, "d_eq_out_mm": d_eq_out * 1000, "half_angle_deg": half_angle}
    if "outlet" in d:
        L = d["length"]
        out["wall_angle_w_deg"] = math.degrees(math.atan((d["outlet"][0] - d["inlet"][0]) / 2 / L))
        out["wall_angle_h_deg"] = math.degrees(math.atan((d["outlet"][1] - d["inlet"][1]) / 2 / L))
    return out


# ---------- flow helpers ----------
def q_of(U):
    return 0.5 * RHO * U**2


def flow_m3h(U):
    return U * ts_area_m2() * 3600


def system_K():
    return sum(PLAN_K.values())


def fan_duty(U):
    q = q_of(U)
    dp = q * system_K()
    Q = U * ts_area_m2()
    return {"U": U, "q": q, "Q_m3h": Q * 3600, "dp_calc": dp, "dp_margin": dp * DESIGN_MARGIN,
            "P_elec_W": Q * dp * DESIGN_MARGIN / FAN_EFFICIENCY}


def static_profile(U):
    """Static pressure relative to the room (Pa) and mean speed (m/s) at key stations."""
    q = q_of(U)
    cr = contraction_ratio()
    ar = diffuser_geometry()["area_ratio"]
    K = PLAN_K
    st = []
    st.append(("room", -2600, 0.0, 0.0))
    st.append(("settling (after screens)", -1000, -q / cr**2 - K["inlet_conditioning"] * q, U / cr))
    k_up = K["inlet_conditioning"] + K["contraction"]
    st.append(("test-section entrance", 0, -q - k_up * q, U))
    k_ts = k_up + K["ts_walls"] + K["ground_plate"] + K["model_supports"]
    st.append(("test-section exit (no shim)", 800, -q - k_ts * q, U))
    k_d = k_ts + K["diffuser"]
    st.append(("diffuser exit, before mesh", 2200, -q / ar**2 - k_d * q, U / ar))
    k_m = k_d + K["safety_screen"]
    st.append(("fan inlet, after mesh", 2200, -q / ar**2 - k_m * q, U / ar))
    return st


def depression_at_ts(U):
    q = q_of(U)
    return q * (1 + PLAN_K["inlet_conditioning"] + PLAN_K["contraction"])


def leak_speed(dp):
    return math.sqrt(2 * dp / RHO)


def roof_shim_mm(k_gradient):
    """Area growth that keeps static pressure constant against a distributed loss k (referred to q).
    q ~ 1/A^2, so dA/A = k/2; roof height grows by that fraction."""
    return G["test_section"]["height"] * k_gradient / 2


def strip_deflection_mm(p_pa, span_mm, t_mm, E=2.35e9, nu=0.37, clamped=False):
    """Mid-span deflection of a long plate strip under uniform pressure."""
    D = E * (t_mm / 1000) ** 3 / (12 * (1 - nu**2))
    b = span_mm / 1000
    coef = 1 if clamped else 5
    return coef * p_pa * b**4 / (384 * D) * 1000


def blasius_bl_mm(x_mm, U):
    rex = U * x_mm / 1000 / NU
    return 5 * x_mm / math.sqrt(rex)


def turbulent_bl_mm(x_mm, U):
    rex = U * x_mm / 1000 / NU
    return 0.37 * x_mm / rex**0.2


def screen_K_wieghardt(beta, re_w):
    """Wieghardt correlation for woven screens, local K."""
    return 6.5 * (1 - beta) / beta**2 * re_w ** (-1 / 3)


def friction_factor_smooth(re):
    return 0.25 / math.log10(5.74 / re**0.9) ** 2


def roller_top_above_tyre_bottom(tyre_d, roller_d, centres):
    """Height of the roller tops above the lowest point of the tyre (mm)."""
    R, r, a = tyre_d / 2, roller_d / 2, centres / 2
    drop = math.sqrt((R + r) ** 2 - a**2)  # tyre centre to roller centre, vertical
    return R + r - drop


def cradle_contact_angle_deg(tyre_d, roller_d, centres):
    """Angle of each tyre-roller contact normal from vertical."""
    R, r, a = tyre_d / 2, roller_d / 2, centres / 2
    return math.degrees(math.asin(a / (R + r)))


def liftoff_ratio(tyre_d, roller_d, centres):
    """Horizontal/vertical load ratio at which the upstream roller unloads (wheel starts to climb)."""
    return math.tan(math.radians(cradle_contact_angle_deg(tyre_d, roller_d, centres)))


def drag_stage(blade_k=2000.0, cell_capacity_kg=0.3, cell_defl_mm=0.3, moving_kg=2.5, drag_N=0.3):
    """Blades and drag cell act as parallel springs between the moving frame and the base."""
    k_cell = cell_capacity_kg * 9.81 / (cell_defl_mm / 1000)
    k_tot = k_cell + blade_k
    return {"k_cell": k_cell, "k_blades": blade_k, "cell_share": k_cell / k_tot,
            "defl_um": drag_N / k_tot * 1e6, "f_Hz": math.sqrt(k_tot / moving_kg) / (2 * math.pi)}


# ---------- report ----------
def report():
    out = []
    p = out.append
    ts = G["test_section"]
    A = ts_area_m2()
    cr = contraction_ratio()
    p("# Airflow calculation report (from spec/geometry.json)\n")

    p("## 1. Test section size")
    above_plate_h = ts["height"] - G["ground_plate"]["z_underside"] - G["ground_plate"]["thickness"]
    A_above = ts["width"] * above_plate_h / 1e6
    for label, am in (("plan car", G["car"]["frontal_area_m2"]), ("proposal FL5", G["proposals"]["car"]["frontal_area_m2"])):
        p(f"- blockage {label}: {am/A*100:.1f}% of full section, {am/A_above*100:.1f}% of the {above_plate_h} mm above the plate")
    gp = G["ground_plate"]
    car = G["car"]
    p(f"- length split: 0-{gp['x_le']} settle, {gp['x_le']}-{car['x_nose']} plate run-up, "
      f"{car['x_nose']}-{car['x_tail']} car, {car['x_tail']}-{ts['length']} wake ({ts['length']-car['x_tail']} mm = {(ts['length']-car['x_tail'])/car['length']:.1f} car lengths)")
    for U in (5, 15):
        for x_name, x in (("nose", car["x_nose"] - gp["x_le"]), ("tail", car["x_tail"] - gp["x_le"])):
            p(f"- plate boundary layer at {x_name} (x_plate={x} mm), U={U}: laminar {blasius_bl_mm(x, U):.1f} mm, turbulent {turbulent_bl_mm(x, U):.1f} mm")
    floor_run = car["x_nose"] + 900  # floor BL would start near contraction inlet
    p(f"- for comparison, tunnel-floor boundary layer at the car nose (~{floor_run} mm run, turbulent, 15 m/s): {turbulent_bl_mm(floor_run, 15):.1f} mm")

    p("\n## 2. Contraction ratio and settling chamber")
    sc = G["settling"]
    p(f"- settling {sc['width']}x{sc['height']} = {settling_area_m2():.4f} m2; TS {A:.4f} m2; ratio {cr:.3f}")
    p(f"- sqrt(6) x 400 = {math.sqrt(6)*400:.0f}, sqrt(6) x 300 = {math.sqrt(6)*300:.0f}")
    p(f"- mean-velocity non-uniformity reduced by 1/c^2 = 1/{cr**2:.0f}")
    for U in (15, 20):
        usc = U / cr
        re_w = usc * G["conditioning"]["screen_wire_d_max"] / 1000 / NU
        p(f"- U={U}: settling speed {usc:.2f} m/s, screen wire Re {re_w:.0f}")
    hc = G["conditioning"]["honeycomb"]
    cell_area = math.sqrt(3) / 2 * hc["cell"] ** 2
    p(f"- honeycomb L/D = {hc['depth']/hc['cell']:.1f}; cells ~ {settling_area_m2()*1e6/cell_area:,.0f}")
    c = G["conditioning"]
    gaps = [c["screens_x"][0] - (hc["x_upstream_face"] + hc["depth"]),
            c["screens_x"][1] - c["screens_x"][0],
            G["contraction"]["x0"] - c["screens_x"][1]]
    p(f"- stack gaps: honeycomb->screen1 {gaps[0]}, screen1->screen2 {gaps[1]}, screen2->contraction {gaps[2]}; "
      f"inlet->honeycomb {hc['x_upstream_face']-sc['x0']}")

    p("\n## 3. Contraction shape")
    con = G["contraction"]
    L = con["length"]
    p("| s | height formula | plan | width formula | plan |")
    p("|---|---|---|---|---|")
    for s, hp, wp in zip(con["plan_table_s"], con["plan_table_height"], con["plan_table_width"]):
        p(f"| {s} | {contraction_dim(s, 735, 300, L):.1f} | {hp} | {contraction_dim(s, 980, 400, L):.1f} | {wp} |")
    for name, hi, he in (("height walls", 735, 300), ("width walls", 980, 400)):
        ss = [i for i in range(0, L + 1)]
        smax = max(abs(contraction_wall_slope(s, hi, he, L)) for s in ss)
        kmax = max(abs(contraction_wall_curvature(s, hi, he, L)) for s in ss)
        p(f"- {name}: max wall angle {math.degrees(math.atan(smax)):.1f} deg, tightest radius {1/kmax:.0f} mm")
    hi_eq = 4 * settling_area_m2() / (2 * (sc["width"] + sc["height"]) / 1000)
    p(f"- L / inlet height = {L/sc['height']:.2f}; L / inlet hydraulic diameter = {L/(hi_eq*1000):.2f}")

    p("\n## 4. Diffuser")
    dg = diffuser_geometry()
    p(f"- inlet equivalent diameter {dg['d_eq_in_mm']:.0f} mm, area ratio {dg['area_ratio']:.2f}, equivalent half-angle {dg['half_angle_deg']:.2f} deg")
    cp_ideal = 1 - 1 / dg["area_ratio"] ** 2
    p(f"- ideal pressure recovery 1-1/AR^2 = {cp_ideal:.3f}; at 80 % efficiency loss K = 0.2 x {cp_ideal:.3f} = {0.2*cp_ideal:.3f}")
    p(f"- exit dynamic pressure 1/AR^2 = {1/dg['area_ratio']**2:.3f} q (vs 1.00 q with no diffuser)")
    p(f"- safety mesh K referred to TS q = K_local / AR^2 -> plan 0.15 means K_local = {0.15*dg['area_ratio']**2:.2f}")

    p("\n## 5. Losses and fan duty")
    for k, v in PLAN_K.items():
        p(f"- {k}: {v}")
    p(f"- sum of listed K = {system_K():.2f} (plan prints 0.73 'before rounding'; the listed values are rounded)")
    usc = 15 / cr
    re_w = usc * 0.0002 / NU
    k_scr = screen_K_wieghardt(0.65, re_w)
    re_cell = usc * 0.006 / NU
    k_hc = 64 / re_cell * (40 / 6) + 0.2
    p(f"- check inlet_conditioning: screen K_local {k_scr:.2f} (beta 0.65, Re_w {re_w:.0f}), honeycomb K_local ~{k_hc:.2f}; "
      f"referred to TS: {(2*k_scr + k_hc)/cr**2:.3f} (plan 0.13)")
    dh = 4 * A / (2 * (ts["width"] + ts["height"]) / 1000)
    re_dh = 15 * dh / NU
    f = friction_factor_smooth(re_dh)
    p(f"- check walls: Dh {dh*1000:.0f} mm, Re {re_dh:.2e}, f {f:.4f}, K = fL/Dh = {f*0.8/dh:.3f} (plan 0.05)")
    for U in (5, 10, 15, 20):
        d = fan_duty(U)
        p(f"- U={U}: q {d['q']:.0f} Pa, Q {d['Q_m3h']:,.0f} m3/h, dp {d['dp_calc']:.0f} Pa, with margin {d['dp_margin']:.0f} Pa, electrical {d['P_elec_W']:.0f} W")

    p("\n## 6. Pressure along the duct and its consequences")
    for name, x, ps, u in static_profile(15):
        p(f"- {name} (x={x}): p-p_room {ps:.1f} Pa, U {u:.2f} m/s")
    dep = depression_at_ts(15)
    p(f"- TS depression {dep:.0f} Pa -> leak speed {leak_speed(dep):.1f} m/s")
    for U in (15, 20):
        dep = depression_at_ts(U)
        p(f"- U={U}: roof strip deflection (simply supported, PC E=2.35 GPa): "
          f"side 6 mm {strip_deflection_mm(dep, 300, 6):.2f}, roof 8 mm {strip_deflection_mm(dep, 400, 8):.2f}, roof 6 mm {strip_deflection_mm(dep, 400, 6):.2f} mm")
    k_walls = PLAN_K["ts_walls"]
    grad = k_walls * q_of(15) / (ts["length"] / 1000)
    p(f"- wall friction alone drops static by {k_walls*q_of(15):.1f} Pa over the TS = {grad:.1f} Pa/m (target <= 2)")
    p(f"- roof shim to cancel wall friction: {roof_shim_mm(k_walls):.1f} mm; walls+plate: {roof_shim_mm(k_walls+PLAN_K['ground_plate']):.1f} mm (plan range 0-10)")

    p("\n## 7. Room length")
    mods = module_chain()
    duct = mods[-1][2] - mods[0][1]
    ca = G["clear_air"]
    p(f"- duct {duct} mm; with clear air {duct + ca['intake_min'] + ca['exhaust_min']} mm")

    p("\n## 8. Cradle")
    p(f"- 40 mm tyre on 16 mm rollers at 20 mm: roller tops {roller_top_above_tyre_bottom(40, 16, 20):.2f} mm above tyre bottom")
    p(f"- proposal 35.6 mm tyre: {roller_top_above_tyre_bottom(35.6, 16, 20):.2f} mm")
    phi = cradle_contact_angle_deg(40, 16, 20)
    lr = liftoff_ratio(40, 16, 20)
    W = 12.0
    p(f"- contact normals {phi:.1f} deg from vertical; lift-off at H/W = tan(phi) = {lr:.2f} -> {lr*W:.1f} N for a {W:.0f} N car (drag at 15 m/s ~0.3 N)")
    ds = drag_stage()
    p(f"- drag stage: cell {ds['k_cell']:,.0f} N/m + blades {ds['k_blades']:,.0f} N/m in parallel; cell carries {ds['cell_share']*100:.0f} % of drag; "
      f"0.3 N moves the frame {ds['defl_um']:.0f} um; drag natural frequency {ds['f_Hz']:.1f} Hz (2.5 kg)")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
