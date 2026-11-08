#!/usr/bin/env python3
"""Consistency tests for spec/mini.json (mini class-project tunnel).

Run:  python3 tools/test_mini.py      (or: pytest tools/test_mini.py)
WATCH items print a warning instead of failing.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mini_calc as mc  # noqa: E402  (sets WT_SPEC before importing airflow_calc)

ac = mc.ac
G = mc.G
WARNINGS = []


def watch(cond, msg):
    if not cond:
        WARNINGS.append(msg)


# ---- layout ----
def test_modules_are_contiguous():
    mods = ac.module_chain()
    for (n0, _, x1), (n1, x0, _) in zip(mods, mods[1:]):
        assert x1 == x0, f"{n0} ends at {x1} but {n1} starts at {x0}"


def test_fits_classroom():
    mods = ac.module_chain()
    duct = mods[-1][2] - mods[0][1]
    ca = G["clear_air"]
    assert duct <= 1800, f"duct {duct} mm longer than two desks"
    assert duct + ca["intake_min"] + ca["exhaust_min"] <= ca["room_straight_run_approx"]


def test_scaled_from_full_design():
    k = G["scale_factor"]
    ts = G["test_section"]
    assert abs(ts["width"] - 400 * k) <= 1 and abs(ts["height"] - 300 * k) <= 1 and abs(ts["length"] - 800 * k) <= 1


def test_contraction_ratio_and_aspect():
    assert abs(ac.contraction_ratio() - 6.0) < 0.05
    sc, ts = G["settling"], G["test_section"]
    assert abs(sc["width"] / sc["height"] - ts["width"] / ts["height"]) < 0.01
    assert G["contraction"]["inlet"] == [sc["width"], sc["height"]]
    assert G["contraction"]["exit"] == [ts["width"], ts["height"]]


def test_conditioning_spacing_and_rules():
    c = G["conditioning"]
    hc = c["honeycomb"]
    assert hc["x_upstream_face"] >= G["settling"]["x0"]
    elems = [hc["x_upstream_face"] + hc["depth"]] + c["screens_x"]
    for a, b in zip(elems, elems[1:]):
        assert b - a >= c["min_gap_between_elements"]
    assert G["contraction"]["x0"] - c["screens_x"][-1] >= c["min_gap_last_screen_to_contraction"]
    assert 6 <= hc["depth"] / hc["cell"] <= 8
    assert min(c["screen_open_area"]) >= 0.57
    re_w = G["speeds_m_s"]["max_target"] / ac.contraction_ratio() * c["screen_wire_d_max"] / 1000 / ac.NU
    assert re_w < 40, f"screen wire Re {re_w:.0f}"
    x = G["pressure_taps"]["settling_ring"]["x"]
    assert c["screens_x"][-1] < x < G["contraction"]["x0"]


def test_diffuser():
    d = ac.diffuser_geometry()
    assert d["half_angle_deg"] <= 5.0
    assert d["wall_angle_w_deg"] <= 5.0 and d["wall_angle_h_deg"] <= 5.05
    f = G["fan"]
    side = 2 * f["size"]
    assert G["diffuser"]["outlet"] == [side, side], "diffuser exit must match the 2x2 fan array"
    assert abs(1 / d["area_ratio"] ** 2 - ac.PLAN_K["fan_plane_q"]) < 0.005
    assert abs(0.2 * (1 - 1 / d["area_ratio"] ** 2) - ac.PLAN_K["diffuser"]) < 0.005


# ---- test section ----
def test_items_inside_test_section():
    ts, gp, car = G["test_section"], G["ground_plate"], G["car"]
    assert 0 < gp["x_le"] < car["x_nose"] < car["x_tail"] < gp["x_te"] <= ts["length"]
    assert car["x_tail"] - car["x_nose"] == car["length"]
    assert all(car["x_nose"] < a < car["x_tail"] for a in car["axle_x"])
    assert abs(car["axle_x"][1] - car["axle_x"][0] - car["wheelbase"]) <= 1
    pit = G["probes"]["pitot_nose"]
    zt = gp["z_underside"] + gp["thickness"]
    assert 0 < pit["x"] < car["x_nose"] and abs(pit["y"]) < ts["width"] / 2
    assert zt + pit["z_above_plate"] < ts["height"]
    for z in G["survey"]["heights_above_plate"]:
        assert zt + z < ts["height"]
    for y in G["survey"]["holes_y"]:
        assert abs(y) < ts["width"] / 2
    assert zt < G["pressure_taps"]["side_wall_taps"]["z"] < ts["height"]


def test_blockage():
    assert G["car"]["frontal_area_m2"] / ac.ts_area_m2() <= 0.06


def test_wells_and_posts_fit():
    gp, w, post = G["ground_plate"], G["wheel_wells"], G["post"]
    assert w["depth_max"] < gp["z_underside"]
    assert post["shroud_tube_d"] > post["bare_size_w_by_len"][0]
    assert post["bare_size_w_by_len"][1] == gp["z_underside"]


def test_plenum_covers_axles():
    pl, car = G["plenum"], G["car"]
    assert all(pl["x"][0] < a < pl["x"][1] for a in car["axle_x"])
    assert pl["y"][0] < -car["track"] / 2 and car["track"] / 2 < pl["y"][1]
    assert pl["x"][0] < G["pressure_taps"]["plenum_vent_tap"]["x"] < pl["x"][1]


def test_panels_and_shim():
    ts = G["test_section"]
    dep = ac.depression_at_ts(G["speeds_m_s"]["max_target"])
    assert ac.strip_deflection_mm(dep, ts["width"], ts["roof_t_min"]) <= 0.3
    lo, hi = ts["roof_shim_at_exit"]
    assert lo <= ac.roof_shim_mm(ac.PLAN_K["ts_walls"] + ac.PLAN_K["ground_plate"]) <= hi


# ---- fan and speed ----
def test_fans_reach_target_speed():
    op = mc.operating_point(1.0)
    assert op["U"] >= G["speeds_m_s"]["max_target"], f"top speed {op['U']:.1f} m/s"
    watch(op["U"] >= 1.1 * G["speeds_m_s"]["max_target"],
          f"WATCH top speed {op['U']:.1f} m/s has < 10 % margin over target; fan curve is a linear estimate")


def test_min_speed_controllable():
    d = mc.duty_for(G["speeds_m_s"]["min"])
    assert d is not None and d >= 0.2, "5 m/s needs a duty below typical PWM fan minimum (~20 %)"


def test_resolution_at_coefficient_speed():
    f = mc.forces_mN(G["speeds_m_s"]["coefficient_grade_min"])
    assert G["force_resolution_mN"] / f["drag"] <= 0.03


# ---- balance ----
def test_saddle_holds_drag():
    sd = mc.saddle()
    W = G["car"]["mass_kg"][0] * mc.G_ACC
    drag = mc.forces_mN(G["speeds_m_s"]["max_target"])["drag"] / 1000
    assert sd["liftoff"] * W > 5 * drag, "saddle lift-off margin below 5x max drag for the lightest car"
    watch(sd["sink_mm"] <= 0.2, f"WATCH tyre sits {sd['sink_mm']:.2f} mm below saddle contacts -> ride height ~{min(G['car']['ride_height'])} mm loses ~{sd['sink_mm']/min(G['car']['ride_height'])*100:.0f} %")


def test_drag_stage():
    ds = mc.drag_stage()
    assert ds["defl_um_at_max"] < 1000 * min(G["ground_plate"]["wheel_openings"]["clearance"])
    assert ds["cell_share"] >= 0.7
    rot_min_hz = 5500 / 60 * (mc.duty_for(G["speeds_m_s"]["min"]) or 0.3)
    watch(ds["f_Hz"] < 0.8 * rot_min_hz, f"WATCH balance {ds['f_Hz']:.0f} Hz close to fan rotation >= {rot_min_hz:.0f} Hz")


def test_vertical_cell_capacity():
    bal, car = G["balance"], G["car"]
    assert car["mass_kg"][1] < bal["moving_mass_max_kg"] <= 0.8 * bal["vertical_cell"]["capacity_kg"]


# ---- electronics and budget ----
def test_uno_pins():
    pins = G["electronics"]["pins"]
    assert len(pins) == len(set(pins)), "duplicate pin"
    assert "fan PWM" in pins["D9"], "fan PWM must be on a Timer1 pin (D9/D10) for 25 kHz"
    assert "tach" in pins["D2"] and "tach" in pins["D3"], "tach inputs must use interrupt pins D2/D3"
    assert "SDA" in pins["A4"] and "SCL" in pins["A5"]
    assert "D10" not in pins, "D10 shares Timer1 with the fan PWM; leave it free"


def test_speed_sensor_A_bell():
    b = mc.bell()
    assert b["load_max_g"] <= 0.8 * b["cap_g"], f"bell load {b['load_max_g']:.0f} g too close to the {b['cap_g']:.0f} g cell"
    assert b["net_g"] > 0, "bell must hang in tension (net weight > 0)"
    assert b["immersion"] >= 1.5 * b["dh_max_mm"], "rim not deep enough: liquid inside the bell moves by the full dp"
    assert b["tip_mm"] >= b["dh_max_mm"] + 10, "snorkel tip would be flooded at max dp"
    assert b["tip_mm"] <= b["headroom_mm"] - 5, "snorkel tip must stay below the bell top"
    assert b["liquid_depth"] >= b["immersion"] + b["rim_gap"], "dish too shallow for the immersion"
    assert mc.speed_error(G["speeds_m_s"]["min"], "A") <= 0.02, "bell resolution too coarse at minimum speed"


def test_speed_sensor_B_backup():
    ss = G["electronics"]["speed_sensor"]
    e = mc.baro_pair_error_pa()
    assert mc.speed_error(G["speeds_m_s"]["coefficient_grade_min"], "B") <= 0.02
    addr = ss["B_barometer_pair"]["i2c_addresses"] + ["0x27"]
    assert len(addr) == len(set(addr)), "I2C address clash"
    e_min = mc.speed_error(G["speeds_m_s"]["min"], "B")
    watch(e_min <= 0.03, f"WATCH backup sensor B: +-{e:.1f} Pa after zeroing -> +-{e_min*100:.1f} % speed at {G['speeds_m_s']['min']} m/s")


def test_speed_sensor_pins():
    pins = G["electronics"]["pins"]
    assert "HX711 #3" in pins["A0"] and "HX711 #3" in pins["A1"]


def test_power_supply():
    pc = mc.psu_current()
    assert pc["rated"] <= G["electronics"]["psu"]["current_a_min"]
    assert G["electronics"]["fuse_a"] >= pc["rated"]


def test_budget():
    b = mc.budget()
    assert b["low"] <= b["cap"], f"cheapest path NT${b['low']} exceeds cap"
    watch(b["high"] <= b["cap"], f"WATCH budget upper estimate NT${b['high']:,} exceeds cap NT${b['cap']:,}; see first_cut_if_over")


def _run():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    for w in WARNINGS:
        print(w)
    print(f"\n{len(tests) - failed}/{len(tests)} passed, {len(WARNINGS)} watch items")
    return failed


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
