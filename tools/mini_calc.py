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


def fan_array_flow(p, duty=1.0):
    """Flow (m3/h) of the whole array at static pressure p, linear curve, fan laws for PWM duty (speed ~ duty)."""
    f = G["fan"]
    qmax = f["count"] * f["q_max_m3h_each"] * duty
    pmax = f["p_max_pa"] * duty**2
    return max(0.0, qmax * (1 - p / pmax))


def operating_point(duty=1.0):
    """Test-section speed where the fan curve meets the system curve."""
    lo, hi = 0.0, 60.0
    for _ in range(80):
        U = (lo + hi) / 2
        if fan_array_flow(system_dp(U), duty) > ac.flow_m3h(U):
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
    b = G["balance"]["drag_blades"]
    E = 200e9
    k_blade = E * (b["w"] / 1000) * (b["t"] / 1000) ** 3 / (b["free_len"] / 1000) ** 3  # guided-guided
    k_blades = b["count"] * k_blade
    c = G["balance"]["drag_cell"]
    k_cell = c["capacity_kg"] * G_ACC / (c["rated_defl_mm_assumed"] / 1000)
    m = G["balance"]["moving_mass_max_kg"]
    k = k_blades + k_cell
    return {"k_blades": k_blades, "k_cell": k_cell, "cell_share": k_cell / k, "f_Hz": math.sqrt(k / m) / (2 * math.pi),
            "defl_um_at_max": forces_mN(G["speeds_m_s"]["max_target"])["drag"] / 1000 / k * 1e6}


def max_sensor_dp():
    """Largest pressure difference the speed sensors see: q at full fan speed plus contraction loss (wall-ring use)."""
    return ac.q_of(operating_point(1.0)["U"]) * (1 + ac.PLAN_K["contraction"])


def bell():
    """Bell manometer (speed sensor A): geometry, loads and resolution."""
    A_ = G["electronics"]["speed_sensor"]["A_bell_manometer"]
    b, liq = A_["bell"], A_["liquid"]
    ri, t, h = b["inner_d"] / 2, b["wall_t"], b["height"]
    ro = ri + t
    area_in = math.pi * ri ** 2 * 1e-6                       # m2
    area_eff = math.pi * ((ri + ro) / 2) ** 2 * 1e-6         # mid-wall, planning value
    vol_mm3 = math.pi * (ro ** 2 - ri ** 2) * h + math.pi * ro ** 2 * t
    mass_g = vol_mm3 / 1000 * b["density_g_cm3"]
    buoy_g = math.pi * (ro ** 2 - ri ** 2) * A_["immersion"] / 1000 * liq["density_kg_m3"] / 1000
    dp_max = max_sensor_dp()
    f_max_g = dp_max * area_eff / G_ACC * 1000
    dh_max = dp_max / (liq["density_kg_m3"] * G_ACC) * 1000  # mm of liquid
    res_pa = G["force_resolution_mN"] / 1000 / area_eff
    return {"area_in_m2": area_in, "area_eff_m2": area_eff, "mass_g": mass_g, "net_g": mass_g - buoy_g,
            "dp_max": dp_max, "f_max_g": f_max_g, "load_max_g": mass_g - buoy_g + f_max_g,
            "cap_g": A_["load_cell_kg"] * 1000, "dh_max_mm": dh_max, "res_pa": res_pa,
            "headroom_mm": b["height"] - A_["immersion"], "tip_mm": A_["snorkel"]["tip_above_rest_level"],
            "immersion": A_["immersion"], "liquid_depth": liq["depth"], "rim_gap": A_["rim_above_dish_floor"]}


def baro_pair_error_pa():
    """Speed sensor B after zeroing: averaged noise of the difference plus temperature drift between the sensors."""
    B = G["electronics"]["speed_sensor"]["B_barometer_pair"]
    n = B["samples_per_s"] * B["average_s"]
    noise = math.sqrt(2) * B["noise_pa_per_sample"] / math.sqrt(n)
    drift = math.sqrt(2) * B["tco_pa_per_k"] * B["run_temp_drift_k"]
    return math.hypot(noise, drift)


def speed_error(U, sensor="A"):
    """Fractional speed error at U for sensor A (bell, resolution-limited) or B (barometer pair)."""
    e = bell()["res_pa"] if sensor == "A" else baro_pair_error_pa()
    return 0.5 * e / ac.q_of(U)


def budget():
    items = G["budget_ntd"]["items"]
    return {"low": sum(i["low"] for i in items), "high": sum(i["high"] for i in items), "cap": G["budget_ntd"]["cap"]}


def psu_current():
    f = G["fan"]
    return {"rated": f["count"] * f["current_a_max_each"], "measured_high": f["count"] * f["current_a_measured_each"][1]}


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
    p("\n## Fan array operating points (linear fan curve, speed ~ PWM duty)")
    for d in (1.0, 0.8, 0.6, 0.4, 0.3):
        op = operating_point(d)
        f = forces_mN(op["U"])
        p(f"- duty {d*100:.0f} %: U {op['U']:.1f} m/s, Q {op['Q_m3h']:.0f} m3/h, dp {op['dp']:.0f} Pa, drag {f['drag']:.1f} mN, lift {f['lift']:.1f} mN")
    for U in (5, 10, 12, 14):
        d = duty_for(U)
        p(f"- duty for {U} m/s: {'n/a' if d is None else f'{d*100:.0f} %'}")
    p("\n## Forces and resolution")
    res = G["force_resolution_mN"]
    for U in (5, 10, 12, 14):
        f = forces_mN(U)
        p(f"- U {U}: drag {f['drag']:.1f} mN ({f['drag']/G_ACC:.2f} gf), {res} mN = {res/f['drag']*100:.1f} % of drag; Re_L {U*G['car']['length']/1000/ac.NU:.1e}")
    p("\n## Speed sensors (A bell manometer, B BMP280 pair)")
    bl = bell()
    p(f"- max sensor dp {bl['dp_max']:.0f} Pa; bell area {bl['area_eff_m2']*1e6:.0f} mm2 (mid-wall), mass {bl['mass_g']:.0f} g, net {bl['net_g']:.0f} g")
    p(f"- bell load at max {bl['load_max_g']:.0f} g of {bl['cap_g']:.0f} g cell; liquid shift {bl['dh_max_mm']:.0f} mm; resolution {bl['res_pa']:.2f} Pa")
    p(f"- barometer pair error after zeroing {baro_pair_error_pa():.2f} Pa")
    for U in (5, 7.5, 10, 12, 14):
        p(f"- U {U}: q {ac.q_of(U):.0f} Pa, bell force {ac.q_of(U)*bl['area_eff_m2']/G_ACC*1000:.1f} g; speed error A +-{speed_error(U,'A')*100:.1f} %, B +-{speed_error(U,'B')*100:.1f} %")
    p("\n## Suction and panels")
    Um = G["speeds_m_s"]["max_target"]
    dep = ac.depression_at_ts(Um)
    p(f"- depression at {Um} m/s: {dep:.0f} Pa, leak speed {ac.leak_speed(dep):.1f} m/s")
    p(f"- 3 mm PC roof (span {ts['width']}): {ac.strip_deflection_mm(dep, ts['width'], ts['roof_t_min']):.2f} mm; side (span {ts['height']}): {ac.strip_deflection_mm(dep, ts['height'], ts['side_wall_t']):.2f} mm")
    p(f"- roof shim for walls {ac.roof_shim_mm(ac.PLAN_K['ts_walls']):.1f} mm, walls+plate {ac.roof_shim_mm(ac.PLAN_K['ts_walls'] + ac.PLAN_K['ground_plate']):.1f} mm")
    usc = Um / ac.contraction_ratio()
    p(f"- settling speed {usc:.2f} m/s, screen wire Re {usc*G['conditioning']['screen_wire_d_max']/1000/ac.NU:.0f}")
    p("\n## Balance")
    sd = saddle()
    p(f"- saddle lift-off H/W {sd['liftoff']:.2f}; tyre sits {sd['sink_mm']:.2f} mm below contact points")
    ds = drag_stage()
    p(f"- blades {ds['k_blades']:.0f} N/m + cell {ds['k_cell']:.0f} N/m; cell share {ds['cell_share']*100:.0f} %; f {ds['f_Hz']:.1f} Hz; travel at max drag {ds['defl_um_at_max']:.1f} um")
    p("\n## Power and budget")
    pc = psu_current()
    p(f"- fan current: rated {pc['rated']:.1f} A, measured-high {pc['measured_high']:.1f} A; PSU >= {G['electronics']['psu']['current_a_min']} A")
    b = budget()
    p(f"- budget NT${b['low']:,}-{b['high']:,} vs cap NT${b['cap']:,}")
    return "\n".join(out)


if __name__ == "__main__":
    print(report())
