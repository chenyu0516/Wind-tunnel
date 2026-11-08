# Agent spec: mini class-project tunnel

Audience: coding/CAD agents (Arduino sketch, Onshape FeatureScript, calculation and drawing scripts). People should read [build_plan_mini.zh-TW.md](../build_plan_mini.zh-TW.md), [model.md](../model.md) and [shopping_list.zh-TW.md](../shopping_list.zh-TW.md) instead.

Design: 1:43 car, the 1:18 reference design scaled by 0.42, Arduino Uno controls everything, budget at most NT$5,000. The 1:18 reference design is archived in [archive/full_1to18/](../archive/full_1to18/) and is not built.

## Files

| File | Role |
| --- | --- |
| `spec/mini.json` | Single source of geometry, fan, electronics pins and budget. |
| `tools/airflow_calc.py` | Generic duct calculations (loads `WT_SPEC`, default `spec/mini.json`). |
| `tools/mini_calc.py` | Mini report: fan operating points, forces, balance, power, budget. |
| `tools/test_mini.py` | 23 consistency tests plus WATCH warnings. Run after any edit to `mini.json`. |
| `tools/make_mini_figures.py` | Draws `figures/M1–M8*.svg` from the JSON (Traditional Chinese labels). |
| `tools/svg_kit.py` | Shared SVG drawing helpers. No plan numbers. |
| `arduino/fan_pwm_test/` | One-fan go/no-go sketch for 2-wire fans switched by a MOSFET (compiles for Uno). |

```sh
python3 tools/test_mini.py          # must print 23/23 passed
python3 tools/mini_calc.py          # numbers quoted in the plan
python3 tools/make_mini_figures.py  # regenerate figures after any spec change
```

## Conventions in mini.json

- Units are mm unless the key names another unit (`_kg`, `_m2`, `_m_s`, `_N`, `_a`, `_pa`, `_m3h`, `ntd`).
- Frame: x = 0 at the contraction exit, +x downstream; y = 0 on the centreline, +y to the left looking downstream; z = 0 on the test-section floor's inner surface, +z up. All modules are coaxial (duct axis z = 63).
- Car values are planning estimates until the purchased 1:43 model is measured; update `car` first, then rerun tests and figures.
- Budget items marked `"basis": "estimate"` are not checked against real listings.

## Rules that are not numbers

- Contraction: same quintic law for width and height; walls bend in one direction only; any exit step must be backward-facing.
- Roof hinges at x = 0 and is shimmed at x = 336.
- Ground plate spans the full width; 4:1 elliptical leading edge; adjustable trailing-edge flap.
- Wells hang from the plate; shroud tubes are fixed to the tunnel, never to the balance.
- Wheels sit in fixed V-saddles; contact points stay below the plate top; pitch is set by saddle shims only.
- The plenum encloses the whole moving frame; its only link to the pedestal is a thin rubber skirt. The pedestal stands on the table/floor, not on the tunnel frame.
- Fans: one shared 25 kHz PWM signal on D9 (Timer1); leave D10 unused. Fan 12 V never comes from the Uno; all grounds common.
- Hardware E-stop cuts 12 V independently of the sketch; the hatch interlock (D8) also forces PWM to 0 in software.
- PWM 0 % does NOT stop 4-wire fans (PFC1212DE idles at 1,550 rpm, ~4.8 m/s) and an open PWM line means full speed: stopping must cut the fans' 12 V (pin assignment pending the fan decision).
- Speed sensors: A (bell manometer, HX711 #3 on A0/A1) is primary; B (2 x BMP280, I2C 0x76/0x77) is teed to the same taps as backup and cross-check; C (buy ABP2) only if both fail. Follow `speed_sensor.fallback_rule`. Zero both with the fans off before every run.
- Bell must be a straight cylinder (a tapered cup changes area as the inner liquid level moves); lower pressure goes inside the bell; load cell bracket on the box floor, never the lid.
- After bench calibration, replace the planning bell area with the measured slope (add `effective_area_m2_measured`).

## WATCH items (from test_mini.py)

- Budget upper estimate (NT$7,750) exceeds the NT$5,000 cap; follow `budget_ntd.first_cut_if_over` and the cheap path in shopping_list.zh-TW.md.
- V-saddle drops the tyre about 0.53 mm, about 18% of a 3 mm ride height; record actual ride height.

Do not "fix" these in the JSON; they are the user's decisions.
