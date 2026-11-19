#!/usr/bin/env python3
"""Calculations for the mini class-project tunnel (spec/mini.json).

Run:  python3 tools/mini_calc.py
Reuses the generic functions in airflow_calc.py, loaded with WT_SPEC=spec/mini.json.
"""
import math
import os
import pathlib
import sys

os.environ["WT_SPEC"] = "spec/mini.json"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import airflow_calc as ac  # noqa: E402

G = ac.G
assert ac.SPEC_PATH.name == "mini.json", "airflow_calc was imported earlier with another spec"
G_ACC = 9.81


def system_dp(U):
    return ac.q_of(U) * ac.system_K()


def fan_flow_each(p):
    """Flow (m3/h) of one fan at full speed and static pressure p, from the datasheet P-Q points."""
    pts = G["fan"]["pq_curve_each"]
    if p <= 0:
        return pts[-1][0]
    if p >= pts[0][1]:
        return 0.0
    for (q1, p1), (q2, p2) in zip(pts, pts[1:]):
        if p2 <= p <= p1:
            return q1 + (q2 - q1) * (p1 - p) / (p1 - p2)
    return 0.0


def series_factor(case="design"):
    lo, hi = G["fan"]["series_factor"]
    return 1.0 if G["fan"]["layers"] == 1 else (lo if case == "design" else hi)


def fan_array_flow(p, duty=1.0, case="design", layers=None):
    """Flow (m3/h) of the whole array at static pressure p.

    Parallel stacks of fans in series: each stack gives series_factor x one fan's pressure at the same flow.
    Fan laws for PWM duty d (speed ~ d): Q ~ d, p ~ d^2.
    """
    f = G["fan"]
    sf = series_factor(case) if layers is None else (1.0 if layers == 1 else series_factor(case))
    if duty <= 0:
        return 0.0
    return f["parallel"] * duty * fan_flow_each(p / (sf * duty**2))


def operating_point(duty=1.0, case="design", layers=None):
    """Test-section speed where the fan curve meets the system curve."""
    lo, hi = 0.0, 60.0
    for _ in range(80):
        U = (lo + hi) / 2
        if fan_array_flow(system_dp(U), duty, case, layers) > ac.flow_m3h(U):
            lo = U
        else:
            hi = U
    U = (lo + hi) / 2
    return {"duty": duty, "U": U, "Q_m3h": ac.flow_m3h(U), "dp": system_dp(U)}


def duty_for(U_target):
    lo, hi = 0.05, 1.0
    if operating_point(1.0)["U"] < U_target:
        return None
    for _ in range(60):
        d = (lo + hi) / 2
        if operating_point(d)["U"] < U_target:
            lo = d
        else:
            hi = d
    return hi


def forces_mN(U, cd=0.35, cl=0.30):
    q = ac.q_of(U)
    am = G["car"]["frontal_area_m2"]
    return {"drag": cd * q * am * 1000, "lift": cl * q * am * 1000}


def saddle():
    phi = math.radians(G["cradle"]["contact_angle_deg"])
    R = G["car"]["tyre_d_planning"] / 2
    return {"liftoff": math.tan(phi), "sink_mm": R * (1 - math.cos(phi))}


def drag_stage():
    """Drag direction of the series balance: no slide or blades, so the drag cell carries all the drag."""
    c = G["balance"]["drag_cell"]
    k_cell = c["capacity_kg"] * G_ACC / (c["rated_defl_mm_assumed"] / 1000)
    m = G["balance"]["moving_mass_max_kg"]
    return {"k_cell": k_cell, "cell_share": 1.0, "f_Hz": math.sqrt(k_cell / m) / (2 * math.pi),
            "defl_um_at_max": forces_mN(G["speeds_m_s"]["max_target"])["drag"] / 1000 / k_cell * 1e6}


def max_sensor_dp():
    """Largest pressure difference the speed sensor sees: q at full fan speed plus contraction loss (wall-ring use)."""
    return ac.q_of(operating_point(1.0)["U"]) * (1 + ac.PLAN_K["contraction"])


def baro_pair_error_pa():
    """Speed sensor (BMP280 pair) after zeroing: averaged noise of the difference plus temperature drift between the sensors."""
    B = G["electronics"]["speed_sensor"]["barometer_pair"]
    n = B["samples_per_s"] * B["average_s"]
    noise = math.sqrt(2) * B["noise_pa_per_sample"] / math.sqrt(n)
    drift = math.sqrt(2) * B["tco_pa_per_k"] * B["run_temp_drift_k"]
    return math.hypot(noise, drift)


def speed_error(U):
    """Fractional speed error at U from the barometer pair's pressure error (U ~ sqrt(q))."""
    return 0.5 * baro_pair_error_pa() / ac.q_of(U)


def budget():
    items = G["budget_ntd"]["items"]
    return {"low": sum(i["low"] for i in items), "high": sum(i["high"] for i in items), "cap": G["budget_ntd"]["cap"]}


def psu_current():
    f = G["fan"]
    return {"rated": f["count"] * f["current_a_each"], "max": f["count"] * f["current_a_max_each"]}


def report():
    out = []
    p = out.append
    ts = G["test_section"]
    p("# Mini tunnel calculation report (spec/mini.json)\n")
    mods = ac.module_chain()
    duct = mods[-1][2] - mods[0][1]
    ca = G["clear_air"]
    p(f"- duct length {duct} mm; with clear air {duct + ca['intake_min'] + ca['exhaust_min']} mm")
    p(f"- test section {ts['width']}x{ts['height']}x{ts['length']}; contraction ratio {ac.contraction_ratio():.2f}")
    dg = ac.diffuser_geometry()
    p(f"- diffuser AR {dg['area_ratio']:.2f}, equivalent half-angle {dg['half_angle_deg']:.2f} deg, "
      f"wall angles width {dg['wall_angle_w_deg']:.1f} / height {dg['wall_angle_h_deg']:.1f} deg")
    p(f"- blockage {G['car']['frontal_area_m2']/ac.ts_area_m2()*100:.1f} % of full section")
    p(f"- sum K {ac.system_K():.3f}")
    fa = G["fan"]
    p(f"\n## Fan array operating points ({fa['count']} fans: {fa['parallel']} stacks x {fa['layers']} layers; datasheet P-Q curve; speed ~ PWM duty)")
    if fa["layers"] > 1:
        p(f"- series factor {series_factor('design')} (design) to {series_factor('ideal')} (ideal)")
    for d in (1.0, 0.8, 0.6, 0.4, 0.3):
        op = operating_point(d)
        hi = operating_point(d, "ideal")
        f = forces_mN(op["U"])
        p(f"- duty {d*100:.0f} %: U {op['U']:.1f} m/s (ideal {hi['U']:.1f}), Q {op['Q_m3h']:.0f} m3/h, dp {op['dp']:.0f} Pa, drag {f['drag']:.1f} mN, lift {f['lift']:.1f} mN")
    top = operating_point(1.0)["U"]
    p(f"- top speed {top:.1f} m/s = {(top / G['speeds_m_s']['max_target'] - 1) * 100:.0f} % over the {G['speeds_m_s']['max_target']} m/s target")
    for U in (5, 10, 12, 14):
        d = duty_for(U)
        p(f"- duty for {U} m/s: {'n/a' if d is None else f'{d*100:.0f} %'}")
    p("\n## Forces and resolution")
    res = G["force_resolution_mN"]
    for U in (5, 10, 12, 14):
        f = forces_mN(U)
        p(f"- U {U}: drag {f['drag']:.1f} mN ({f['drag']/G_ACC:.2f} gf), {res} mN = {res/f['drag']*100:.1f} % of drag; Re_L {U*G['car']['length']/1000/ac.NU:.1e}")
    p("\n## Speed sensor (BMP280 pair)")
    p(f"- max sensor dp {max_sensor_dp():.0f} Pa; pair error after zeroing {baro_pair_error_pa():.2f} Pa")
    for U in (5, 7.5, 10, 12, 14):
        p(f"- U {U}: q {ac.q_of(U):.0f} Pa, speed error +-{speed_error(U)*100:.1f} %")
    p("\n## Suction and panels")
    Um = G["speeds_m_s"]["max_target"]
    dep = ac.depression_at_ts(Um)
    p(f"- depression at {Um} m/s: {dep:.0f} Pa, leak speed {ac.leak_speed(dep):.1f} m/s")
    p(f"- 3 mm acrylic roof, PC stiffness as a safe bound (span {ts['width']}): {ac.strip_deflection_mm(dep, ts['width'], ts['roof_t_min']):.2f} mm; side (span {ts['height']}): {ac.strip_deflection_mm(dep, ts['height'], ts['side_wall_t']):.2f} mm")
    p(f"- roof shim for walls {ac.roof_shim_mm(ac.PLAN_K['ts_walls']):.1f} mm, walls+plate {ac.roof_shim_mm(ac.PLAN_K['ts_walls'] + ac.PLAN_K['ground_plate']):.1f} mm")
    usc = Um / ac.contraction_ratio()
    p(f"- settling speed {usc:.2f} m/s, screen wire Re {usc*G['conditioning']['screen_wire_d_max']/1000/ac.NU:.0f}")
    p("\n## Balance")
    sd = saddle()
    p(f"- saddle lift-off H/W {sd['liftoff']:.2f}; tyre sits {sd['sink_mm']:.2f} mm below contact points")
    ds = drag_stage()
    p(f"- drag cell {ds['k_cell']:.0f} N/m carries all the drag (no slide); f {ds['f_Hz']:.1f} Hz; travel at max drag {ds['defl_um_at_max']:.1f} um")
    p("\n## Power and budget")
    pc = psu_current()
    p(f"- fan current: rated {pc['rated']:.1f} A, datasheet max {pc['max']:.1f} A; PSU >= {G['electronics']['psu']['current_a_min']} A, fuse {G['electronics']['fuse_a']} A")
    b = budget()
    p(f"- budget NT${b['low']:,}-{b['high']:,} vs cap NT${b['cap']:,}")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
