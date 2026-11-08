# Agent spec

Audience: coding/CAD agents (Onshape FeatureScript, calculation and drawing scripts). People should read the Chinese documents with figures instead:

- [build_plan.zh-TW.md](../build_plan.zh-TW.md): the plan, with geometry shown as figures
- [airflow_design.zh-TW.md](../airflow_design.zh-TW.md): why the air path looks like this, and its calculations

This folder is the archived 1:18 reference design. The active class-project design is the mini tunnel at the repository root (`../../spec/mini.json`). Run the tools below from `archive/full_1to18/`.

For the 1:18 reference design, the English [build_plan.md](../build_plan.md) remains the source of truth. If anything here disagrees with it, the plan wins; report the mismatch.

## Files

| File | Role |
| --- | --- |
| `spec/geometry.json` | Single source of geometry. Every number a model or figure needs. |
| `tools/airflow_calc.py` | Calculations (flow, losses, pressures, deflection, cradle geometry). Prints a report. |
| `tools/test_geometry.py` | 23 consistency tests plus WATCH warnings. Run after any edit to `geometry.json`. |
| `tools/make_figures.py` | Draws `figures/zh-TW/*.svg` from the JSON. Never hard-code plan numbers in it. |

```sh
python3 tools/test_geometry.py   # must print 23/23 passed
python3 tools/airflow_calc.py    # numbers quoted in airflow_design.zh-TW.md
python3 tools/make_figures.py    # regenerate figures after any geometry change
```

## Conventions in geometry.json

- Units are mm unless the key names another unit (`_kg`, `_m2`, `_m_s`, `_N`).
- Frame: x = 0 at the contraction exit, +x downstream; y = 0 on the centreline, +y to the left looking downstream; z = 0 on the test-section floor's inner surface, +z up.
- `"tbd"`: the plan leaves this open. Do not invent a value. In CAD, expose it as a parameter and flag it to the user.
- `"assumed"` (in a note): a modelling assumption the plan does not state. Currently only the coaxial duct axis at z = 150.
- `proposals`: not adopted. Use only when the user explicitly asks to model a proposal, and label the result as such.

## Rules that are not numbers

These are in the plan as prose. Keep them when modelling.

- The contraction uses the same quintic law for width and height; each wall curves in one direction only.
- Any residual step at the contraction exit must be backward-facing (downstream wall recessed outward), at most 0.5 mm.
- The roof hinges at x = 0 and is shimmed at x = 800.
- The ground plate spans the full width; its leading edge is a 4:1 ellipse; its trailing edge carries an adjustable flap.
- Plate inserts keep 1–2 mm clearance to everything on the balance through its full travel.
- Wheel wells hang from the plate, not from the balance; shroud tubes are fixed to the tunnel, not the balance.
- Roller tops stay below the plate top. Pitch is set by cradle height only, never by tilting the moving frame.
- The plenum encloses the whole moving frame. Its only link to the pedestal is a flexible neoprene skirt.
- The fog wand and hose mount on the tunnel frame, never on the balance.
- Safety mesh sits at the diffuser exit (lowest speed).

## Open items an agent will hit

| Item | Status |
| --- | --- |
| Fan model, length, flange | tbd (proposal: CHC MD-24, Ø620) |
| Module flange design | tbd |
| Test-section floor thickness | tbd |
| Side-wall tap height and side | tbd |
| Car axle positions, track, height | tbd until the model is measured |
| Plenum size | tbd (proposal 500 × 400 × 250) |
| Contraction rib count and spacing | tbd |
| Roller length | tbd |

## WATCH items (from test_geometry.py)

Five margins the plan does not enforce: blockage above the plate (6.7%), cradle ride-height loss (1.85 mm), screen wire Re at 20 m/s (44), 6 mm roof deflection vs plan text, and roof-shim range when plate loss is included (12 mm). See §8 of airflow_design.zh-TW.md. Do not "fix" these in the JSON; they are decisions for the user.
