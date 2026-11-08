#!/usr/bin/env python3
"""Consistency tests for spec/geometry.json against the rules in build_plan.md.

Run:  python3 tools/test_geometry.py      (or: pytest tools/test_geometry.py)
Each test names the plan section it guards. Proposals are never checked here.
A test marked WATCH prints a warning instead of failing: it flags a margin the
plan does not enforce but a reviewer should see.
"""
import math
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import airflow_calc as ac  # noqa: E402

G = ac.G
WARNINGS = []


def watch(cond, msg):
    if not cond:
        WARNINGS.append(msg)


# ---- Table 2: module chain ----
def test_modules_are_contiguous():
    mods = ac.module_chain()
    for (n0, _, x1), (n1, x0, _) in zip(mods, mods[1:]):
        assert x1 == x0, f"{n0} ends at {x1} but {n1} starts at {x0}"


def test_room_length_fits():
    mods = ac.module_chain()
    duct = mods[-1][2] - mods[0][1]
    ca = G["clear_air"]
    assert duct + ca["intake_min"] + ca["exhaust_min"] <= ca["room_straight_run_approx"]


# ---- A1/A2: contraction ratio, settling chamber, conditioning ----
def test_contraction_ratio_is_6():
    assert abs(ac.contraction_ratio() - 6.0) < 0.05


def test_settling_keeps_test_section_aspect():
    sc, ts = G["settling"], G["test_section"]
    assert abs(sc["width"] / sc["height"] - ts["width"] / ts["height"]) < 0.01


def test_conditioning_spacing():
    c = G["conditioning"]
    hc = c["honeycomb"]
    sc = G["settling"]
    hc_down = hc["x_upstream_face"] + hc["depth"]
    assert hc["x_upstream_face"] >= sc["x0"], "honeycomb outside settling chamber"
    elems = [hc_down] + c["screens_x"]
    for a, b in zip(elems, elems[1:]):
        assert b - a >= c["min_gap_between_elements"], f"gap {b - a} < {c['min_gap_between_elements']}"
    assert G["contraction"]["x0"] - c["screens_x"][-1] >= c["min_gap_last_screen_to_contraction"]


def test_honeycomb_and_screen_rules():
    c = G["conditioning"]
    ld = c["honeycomb"]["depth"] / c["honeycomb"]["cell"]
    assert 6 <= ld <= 8, f"honeycomb L/D {ld:.1f} outside 6-8"
    assert min(c["screen_open_area"]) >= 0.57, "screen open area below 0.57 (Mehta & Bradshaw)"
    re_w = 15 / ac.contraction_ratio() * c["screen_wire_d_max"] / 1000 / ac.NU
    assert re_w < 40, f"screen wire Re {re_w:.0f} at 15 m/s"
    re_w20 = 20 / ac.contraction_ratio() * c["screen_wire_d_max"] / 1000 / ac.NU
    watch(re_w20 < 40, f"WATCH screen wire Re {re_w20:.0f} at 20 m/s exceeds ~40")


def test_settling_rings_between_screen_and_contraction():
    x = G["pressure_taps"]["settling_ring"]["x"]
    assert G["conditioning"]["screens_x"][-1] < x < G["contraction"]["x0"]


# ---- A2: contraction profile ----
def test_contraction_table_matches_formula():
    con = G["contraction"]
    L = con["length"]
    (wi, hi), (we, he) = con["inlet"], con["exit"]
    for s, h, w in zip(con["plan_table_s"], con["plan_table_height"], con["plan_table_width"]):
        assert abs(ac.contraction_dim(s, hi, he, L) - h) <= 1.0, f"height at s={s}"
        assert abs(ac.contraction_dim(s, wi, we, L) - w) <= 1.0, f"width at s={s}"


def test_contraction_ends_are_smooth():
    con = G["contraction"]
    L = con["length"]
    for hi, he in ((con["inlet"][1], con["exit"][1]), (con["inlet"][0], con["exit"][0])):
        for s in (0, L):
            assert abs(ac.contraction_wall_slope(s, hi, he, L)) < 1e-12
            assert abs(ac.contraction_wall_curvature(s, hi, he, L)) < 1e-12


def test_contraction_inlet_matches_settling():
    assert G["contraction"]["inlet"] == [G["settling"]["width"], G["settling"]["height"]]
    assert G["contraction"]["exit"] == [G["test_section"]["width"], G["test_section"]["height"]]


# ---- A4: diffuser ----
def test_diffuser_angle_and_ratio():
    d = ac.diffuser_geometry()
    assert d["half_angle_deg"] <= 5.0, f"half-angle {d['half_angle_deg']:.2f} deg"
    assert abs(d["area_ratio"] - 2.6) < 0.05


# ---- A3 / Table 3: test-section layout ----
def test_items_inside_test_section():
    ts, gp, car = G["test_section"], G["ground_plate"], G["car"]
    assert 0 < gp["x_le"] < gp["x_te"] <= ts["length"]
    assert gp["x_te"] - gp["x_le"] == gp["length"]
    assert gp["x_le"] < car["x_nose"] < car["x_tail"] < gp["x_te"]
    assert car["x_tail"] - car["x_nose"] == car["length"]
    assert ts["length"] - car["x_tail"] >= 250, "near-wake allowance"
    pit = G["probes"]["pitot_nose"]
    z_plate_top = gp["z_underside"] + gp["thickness"]
    assert 0 < pit["x"] < car["x_nose"]
    assert abs(pit["y"]) < ts["width"] / 2
    assert z_plate_top + pit["z_above_plate"] < ts["height"]
    for y in G["survey"]["holes_y"]:
        assert abs(y) < ts["width"] / 2
    for z in G["survey"]["heights_above_plate"]:
        assert z_plate_top + z < ts["height"]
    for x in G["pressure_taps"]["side_wall_taps"]["x"]:
        assert 0 < x < ts["length"]


def test_blockage():
    ts, gp = G["test_section"], G["ground_plate"]
    a_full = ac.ts_area_m2()
    am = G["car"]["frontal_area_m2"]
    assert am / a_full < 0.075, "blockage above 7.5 % of the full section"
    above = ts["width"] * (ts["height"] - gp["z_underside"] - gp["thickness"]) / 1e6
    watch(am / above <= 0.05, f"WATCH blockage {am/above*100:.1f}% of the area above the plate (>5 %: apply a blockage correction)")


def test_wells_fit_under_plate():
    gp, w, post = G["ground_plate"], G["wheel_wells"], G["post"]
    assert w["depth_max"] < gp["z_underside"]
    assert post["shroud_tube_d"] > post["bare_size_w_by_len"][0]
    assert post["bare_size_w_by_len"][1] == gp["z_underside"], "bare post length should equal under-plate gap"


# ---- A5: fan duty ----
def test_fan_duty_numbers():
    d15 = ac.fan_duty(15)
    assert abs(d15["Q_m3h"] - 6480) < 1
    assert abs(d15["dp_calc"] - 99) <= 2
    assert abs(d15["dp_margin"] - 150) <= 3
    assert abs(d15["P_elec_W"] - 700) <= 50
    d20 = ac.fan_duty(20)
    assert abs(d20["Q_m3h"] - 8640) < 1
    assert abs(d20["dp_calc"] - 176) <= 3
    assert abs(d20["dp_margin"] - 260) <= 8
    assert abs(d20["P_elec_W"] - 1600) <= 60


def test_diffuser_K_consistent_with_area_ratio():
    d = ac.diffuser_geometry()
    assert abs(0.2 * (1 - 1 / d["area_ratio"] ** 2) - ac.PLAN_K["diffuser"]) < 0.01
    assert abs(1 / d["area_ratio"] ** 2 - ac.PLAN_K["fan_plane_q"]) < 0.01


# ---- Suction consequences ----
def test_depression_and_leak():
    dep = ac.depression_at_ts(15)
    assert abs(dep - 157) <= 2
    assert abs(ac.leak_speed(dep) - 16) <= 0.5


def test_panel_deflection_close_to_plan():
    dep = ac.depression_at_ts(15)
    assert abs(ac.strip_deflection_mm(dep, 300, 6) - 0.3) <= 0.1
    assert abs(ac.strip_deflection_mm(dep, 400, 8) - 0.4) <= 0.1
    watch(abs(ac.strip_deflection_mm(dep, 400, 6) - 0.9) <= 0.1,
          f"WATCH 6 mm roof deflection {ac.strip_deflection_mm(dep, 400, 6):.2f} mm vs plan 0.9 (simply supported, E=2.35 GPa)")


def test_roof_shim_range():
    lo, hi = G["test_section"]["roof_shim_at_exit"]
    walls = ac.roof_shim_mm(ac.PLAN_K["ts_walls"])
    assert lo <= walls <= hi, f"shim for wall friction {walls:.1f} mm outside plan range"
    both = ac.roof_shim_mm(ac.PLAN_K["ts_walls"] + ac.PLAN_K["ground_plate"])
    watch(both <= hi, f"WATCH shim for walls+plate {both:.1f} mm exceeds plan range {hi} mm")


# ---- B3: cradle ----
def test_cradle_roller_height():
    h = ac.roller_top_above_tyre_bottom(G["car"]["tyre_d_planning"], G["cradle"]["roller_d"], G["cradle"]["roller_centres"])
    assert abs(h - 1.9) <= 0.1


def test_cradle_holds_drag():
    # B3: lift-off needs H/W near 0.38, about 4.5 N for the car; drag is ~0.3 N.
    cr = G["cradle"]
    lr = ac.liftoff_ratio(G["car"]["tyre_d_planning"], cr["roller_d"], cr["roller_centres"])
    assert abs(lr - 0.38) <= 0.01
    assert lr * 12.0 > 10 * 0.307, "cradle lift-off margin below 10x the 15 m/s drag"


def test_drag_stage_matches_plan_frequency():
    # C2/C4: blades ~2,000 N/m in parallel with the drag cell give ~11 Hz with 2.5 kg moving.
    ds = ac.drag_stage()
    assert abs(ds["f_Hz"] - 11) <= 0.5
    assert ds["defl_um"] < 1000 * min(G["ground_plate"]["wheel_openings"]["clearance"]), "drag travel exceeds insert clearance"


def test_cradle_ride_height_loss():
    # Roller tops must stay below the plate top, so the tyre bottom sits at least
    # this far below the plate: the car rides lower than on a flat floor.
    sink = ac.roller_top_above_tyre_bottom(G["car"]["tyre_d_planning"], G["cradle"]["roller_d"], G["cradle"]["roller_centres"])
    watch(sink <= 0.5, f"WATCH tyre bottom >= {sink:.2f} mm below plate top -> ride height {min(G['car']['ride_height'])}-{max(G['car']['ride_height'])} mm loses ~{sink/7.5*100:.0f} %")


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
