# Design and Calibration of a Low-Cost Miniature Wind Tunnel for 1:43 Vehicle Aerodynamics: A Proposed Experimental Methodology

## Abstract

This paper presents a proposed design and experimental methodology for a low-cost miniature wind tunnel intended to measure the drag and downforce of 1:43 vehicle models under controlled classroom conditions. The proposed facility uses an open-return circuit with a downstream array of four 12 V fans, a 168 × 126 mm test section, and an operating range of approximately 5–14 m/s. An Arduino Uno controls fan speed in closed loop on measured dynamic pressure and acquires force and pressure data. A geometrically documented Ahmed body at 1:10 of its standard size will be used for facility characterization before testing a 1:43 vehicle model. The methodology integrates force-balance calibration, differential-pressure calibration, spatial flow surveys, repeatability assessment, and systematic evaluation of ground and support effects. The experimental program comprises Reynolds-number sweeps, ground-condition sensitivity studies, and comparisons of vehicle configurations. Data reduction will emphasize model-scale forces, nondimensional coefficients, and measurement uncertainty. Reynolds-number mismatch, stationary-ground effects, blockage, and geometric fidelity are treated as limitations on extrapolation to full-scale vehicles. The facility is constrained to a material cost of NT$5,000. The proposed dimensions and acceptance criteria are preliminary design targets; no experimental performance results are reported. The intended outcome is a characterized facility capable of resolving repeatable aerodynamic differences within a documented operating envelope.

**Keywords:** vehicle aerodynamics; miniature wind tunnel; Arduino; force-balance calibration; Reynolds-number similarity; ground effect; measurement uncertainty

## 1. Introduction

Model-scale wind-tunnel experiments provide a means of examining how vehicle geometry influences aerodynamic forces. Their interpretation requires consideration of the relationship between model and full-scale flow, the quality of the incoming stream, and the influence of the measurement apparatus. Geometric similarity alone is insufficient to establish aerodynamic equivalence because the governing nondimensional parameters and boundary conditions may differ between the model and the full-scale vehicle. These principles underpin conventional aerodynamic analysis and low-speed wind-tunnel testing. [[1]][ref1], [[12]][ref12], [[13]][ref13]

The present work proposes a compact, low-cost facility for measuring drag and downforce on 1:43 vehicle models, built as a general-education course project in which an Arduino microcontroller performs all control and data acquisition. Its objectives are to establish calibrated force and flow measurements, characterize coefficient variation over the accessible Reynolds-number range, quantify sensitivity to ground and mounting conditions, and compare selected vehicle configurations. The primary outputs will be model-scale forces, aerodynamic coefficients, repeatability statistics, and uncertainty estimates. Any full-scale force estimates will be reported separately as conditional extrapolations.

The experimental sequence begins with a simplified reference body and proceeds to a 1:43 diecast vehicle model. This sequence is intended to distinguish limitations of the facility and measurement system from the additional complexity introduced by vehicle geometry. Quantitative validation against published results will depend on the availability of a dataset with sufficiently comparable geometry, Reynolds number, and boundary conditions; at this scale such overlap is unlikely, as discussed in Section 4.1.

This paper describes a proposed apparatus and measurement protocol. Dimensions, operating conditions, acquisition durations, and acceptance criteria remain subject to verification during design and commissioning. The construction plan is given in [build_plan_mini.zh-TW.md](build_plan_mini.zh-TW.md), and all dimensions are held in [spec/mini.json](spec/mini.json).

## 2. Theoretical Framework

### 2.1. Governing equations and aerodynamic forces

The proposed operating regime is described using the incompressible Navier–Stokes equations for a Newtonian fluid. Neglecting gravity in the aerodynamic momentum balance, conservation of mass and momentum are expressed as

$$
\nabla\cdot\mathbf{u}=0,
\tag{1}
$$

$$
\rho\left(\frac{\partial\mathbf{u}}{\partial t}+\mathbf{u}\cdot\nabla\mathbf{u}\right)
=-\nabla p+\mu\nabla^2\mathbf{u},
\tag{2}
$$

where $\mathbf{u}$ is velocity, $p$ is pressure, $\rho$ is density, and $\mu$ is dynamic viscosity. The relevant boundary conditions are determined by the model geometry, incoming flow, surface condition, ground motion, and tunnel walls.

The resultant aerodynamic force is obtained by integrating pressure and viscous traction over the body surface:

$$
\mathbf{F}_{\mathrm{aero}}
=\oint_S\left[-(p-p_\infty)\mathbf{n}
+\boldsymbol{\tau}\cdot\mathbf{n}\right]\,\mathrm{d}S,
\tag{3}
$$

where $S$ denotes the body surface, $\mathbf{n}$ is the unit normal directed from the body into the fluid, $p_\infty$ is the reference pressure, and $\boldsymbol{\tau}$ is the viscous stress tensor. Pressure and viscous stresses contribute to the total aerodynamic load; their moment integrals also determine the aerodynamic moments. [[2]][ref2], [[3]][ref3]

The coordinate system is defined with positive $x$ in the direction of the incoming flow and positive $z$ vertically upward. Drag and downforce are consequently defined as $D=F_x$ and $F_{\mathrm{down}}=-F_z$, respectively. This convention assigns a positive value to a downward aerodynamic force.

### 2.2. Pressure-based velocity measurement

For steady, incompressible flow brought to rest with negligible loss, the total pressure $p_t$, static pressure $p_s$, and dynamic pressure $q$ satisfy

$$
p_t=p_s+\frac{1}{2}\rho U^2,
\qquad
q=p_t-p_s=\frac{1}{2}\rho U^2.
\tag{4}
$$

A Pitot-static probe measures total pressure through an upstream-facing opening and static pressure through separate side openings. Static pressure represents the local pressure in the flowing air and is distinct from a wind-off pressure measurement; it need not equal room atmospheric pressure. [[4]][ref4] The local velocity is calculated as

$$
U=\sqrt{\frac{2q}{\rho}}.
\tag{5}
$$

In routine operation the reference dynamic pressure will be taken from wall static-pressure rings at the settling chamber and the test-section entrance, which leave nothing in the airstream. The Pitot probe will be used to calibrate this wall-ring reference, positioned upstream of the model and outside the floor boundary layer. Its suitability will be assessed through spatial flow surveys and checks for alignment error, leakage, and disturbances caused by installation of the model.

### 2.3. Aerodynamic coefficients

Drag and downforce coefficients are defined by

$$
C_D=\frac{D}{q_\infty A_{\mathrm{ref}}},
\qquad
C_{\mathrm{DF}}=\frac{F_{\mathrm{down}}}{q_\infty A_{\mathrm{ref}}},
\tag{6}
$$

where $q_\infty$ is the measured reference dynamic pressure and $A_{\mathrm{ref}}$ is the specified reference area. For a constant coefficient and density, force varies approximately with the square of velocity. The coefficients themselves may vary with Reynolds number and other flow conditions. [[5]][ref5]

The reference area will be documented and held fixed across configuration comparisons. Comparisons with published data will use the reference-area convention of the selected dataset, with any conversion explicitly stated.

### 2.4. Reynolds-number similarity

The Reynolds number based on characteristic length $L$ is

$$
Re_L=\frac{\rho UL}{\mu}=\frac{UL}{\nu},
\tag{7}
$$

where $\nu=\mu/\rho$ is the kinematic viscosity. For geometrically similar bodies at a 1:43 scale ratio and equal fluid properties,

$$
\frac{Re_m}{Re_f}=\frac{U_m}{43\,U_f},
\tag{8}
$$

where subscripts $m$ and $f$ denote model and full scale. Reynolds-number matching therefore requires $U_m=43\,U_f$. A full-scale speed of approximately 55.6 m/s would require a model speed of approximately 2,390 m/s under this scaling relation, about seven times the speed of sound and incompatible with the proposed low-speed experiment. [[1]][ref1], [[5]][ref5] At 14 m/s, a 105 mm model reaches $Re_L\approx9.8\times10^4$, roughly 1/170 of the full-scale value at highway speed.

The experimental program will therefore characterize coefficient dependence over the accessible Reynolds-number range. A coefficient plateau within that range would indicate locally weak Reynolds-number dependence, but would not by itself establish equivalence to full-scale conditions.

### 2.5. Ground boundary conditions

In the vehicle-fixed reference frame, both the incoming air and the road move rearward. A moving belt can reproduce road motion more faithfully than a stationary floor, as illustrated by full-scale automotive wind-tunnel practice. [[6]][ref6] The proposed facility will use a stationary raised plate.

A stationary surface develops a boundary layer that may alter the underbody inflow. A raised plate establishes a new boundary layer near its leading edge but retains this limitation, which is proportionally more severe at this scale: the model's ride height is only about 3 mm. Ride height, model pitch, wheel clearance, wheel state, and plate geometry will therefore be controlled and documented as experimental boundary conditions.

## 3. Proposed Experimental Facility

### 3.1. Tunnel configuration

The proposed facility is an open-return wind tunnel driven by a downstream array of fans. Air will pass through a settling chamber containing a honeycomb and two removable screens, followed by a 6:1 contraction, test section, diffuser, fan array, and exhaust. This arrangement follows the general component sequence used in educational wind tunnels; component dimensions are a 0.42 scaling of a previously designed 1:18 facility, adapted to commercially available 120 mm fans. [[9]][ref9]

**Table 1. Preliminary wind-tunnel design parameters.**

| Parameter | Proposed specification |
| --- | --- |
| Circuit | Open-return with downstream suction fans |
| Test-section cross-section | 168 × 126 mm |
| Test-section length | 336 mm |
| Overall duct length | Approximately 1.7 m |
| Velocity range | Approximately 5–14 m/s |
| Drive | Four 120 × 120 × 38 mm 12 V PWM fans in a 2 × 2 array |
| Control and acquisition | Arduino Uno; closed-loop speed control on measured $q$ |
| Ground representation | Removable raised plate |
| Flow conditioning | Settling chamber, honeycomb, and two removable screens |
| Optical and physical access | Transparent 3 mm polycarbonate panels |
| Material budget | At most NT$5,000 |

The exhaust will be positioned to limit recirculation into the intake. Removable model mounts, ground plates, and test-section panels will support alignment, maintenance, and controlled changes to the experimental configuration.

### 3.2. Flow-rate and power requirements

For a mean test-section velocity $U$ and cross-sectional area $A_t$, the required volumetric flow rate is

$$
Q=UA_t.
\tag{9}
$$

The nominal test-section area is $A_t=0.0212\ \mathrm{m^2}$. Corresponding flow-rate requirements are listed in Table 2.

**Table 2. Nominal volumetric flow requirements.**

| Mean velocity (m/s) | Flow rate (m³/s) | Flow rate (m³/h) |
| --- | --- | --- |
| 5 | 0.106 | 381 |
| 10 | 0.212 | 762 |
| 14 | 0.296 | 1,067 |

Fan selection will be based on the intersection of the fan pressure–flow characteristic and the estimated system resistance. The approximate electrical power requirement is

$$
P_{\mathrm{electrical}}
\approx\frac{Q\Delta p_{\mathrm{system}}}{\eta_{\mathrm{overall}}},
\tag{10}
$$

where $\Delta p_{\mathrm{system}}$ is the system pressure loss and $\eta_{\mathrm{overall}}$ is the overall efficiency. The resistance estimate will include losses associated with the screens, honeycomb, contraction, diffuser, and outlet. Published tunnel-design methods provide a basis for this assessment, although the cited closed-loop design differs from the proposed open-return circuit. [[10]][ref10] With a summed loss coefficient of about 0.71 referred to test-section dynamic pressure, the system requires about 84 Pa at 14 m/s. A linear approximation between the published maximum flow and maximum static pressure of the selected fans predicts a top speed of about 15.8 m/s; this estimate will be replaced by a measured fan-array characteristic during commissioning. Free-air flow ratings and motor power alone are insufficient to establish the achievable test-section velocity.

### 3.3. Instrumentation and mechanical load path

The measurement system will include separate calibrated vertical-force and drag channels, two home-made differential-pressure sensors teed to the same taps — a liquid-sealed bell manometer hung from a 100 g load cell (primary; about 0.34 Pa resolution) and a pair of BMP280 barometers (backup and cross-check) — bench-calibrated against a 1:10 inclined water manometer and zeroed with the fans off before every run, connected to the wall-ring reference and, for calibration, to a Pitot-static probe. Inlet temperature and atmospheric pressure will be recorded with each run. Fan rotational speed will be logged as an operating parameter from the fans' tachometer outputs. Ride height and pitch will be measured independently.

An Arduino Uno will drive all four fans from one 25 kHz PWM signal and will adjust the duty cycle with a proportional–integral–derivative loop to hold a target dynamic pressure. It will read the two force channels through 24-bit HX711 load-cell amplifiers at 10 samples/s, read the pressure transducer over I²C, and stream timestamped records as comma-separated values to a laptop. A predefined run sequence (wind-off zero, ramp, stabilization, acquisition, shutdown, and post-run zero) will be executed by the microcontroller to standardize procedure.

Force-sensor capacity will account for model weight, aerodynamic loading, and handling loads: a 100 g single-point load cell for drag and a 1 kg cell for vertical force, with a moving-mass limit of 0.6 kg. Installed measurement performance will be determined through calibration and stability testing rather than inferred from analog-to-digital converter resolution.

The model support will transmit all measured loads through the instrumented balance. Each wheel will rest in a fixed V-shaped saddle; the four saddles are carried by a common frame mounted on a flexure-guided drag stage, which in turn rests on the vertical load cell. The balance will be enclosed in a sealed plenum vented to the test-section static pressure so that air cannot enter through the wheel openings in the ground plate. Wheel contact with the fixed ground plate and parasitic loads from cables, seals, or friction will be prevented. Fan and balance structures will be separated, and drag-to-vertical cross-talk will be quantified. Support loading and aerodynamic interference will be characterized independently.

The initial reported quantities will be total drag and downforce. Individual support reactions will not be treated as aerodynamic axle loads.

### 3.4. Operational provisions

The facility operates from a fused 12 V supply, so no mains wiring is required beyond a certified power supply. The design will incorporate metal fan guards, a hardware emergency stop that removes fan power independently of the microcontroller, a test-section hatch interlock monitored by the microcontroller, secured ducting, and model restraint. Commissioning will include a noise assessment, since four high-speed fans may exceed 70 dBA at full speed, and a loose-part inspection procedure.

## 4. Test Models and Reference-Data Selection

### 4.1. Reference body

A geometrically documented Ahmed body will precede testing of the vehicle model. Previous experimental and computational studies of this body provide a basis for selecting reference conditions and examining Reynolds-number effects. [[7]][ref7] The preliminary model specification is summarized in Table 3.

**Table 3. Preliminary reference-body specification.**

| Parameter | Proposed specification |
| --- | --- |
| Rear slant angle | 25° |
| Body length | Approximately 105 mm (1:10 of the standard body) |
| Construction | 3D-printed, sanded, dimensionally inspected |
| Ground clearance | Adjustable and reported as a dimensionless ratio |
| Mounting | Four stilts seated in the wheel saddles of the force balance |

A single published experimental dataset will be selected before fabrication. The associated geometry will define front rounding, body proportions, supports, ground clearance, and rear slant. Dimensions and test conditions from different datasets will not be combined into a nominal benchmark.

Commonly cited standard Ahmed-body dimensions are approximately 1044 mm in length, 389 mm in width, and 288 mm in body height. At 1:10 these become about 104 × 39 × 29 mm, giving a frontal area close to that of the 1:43 vehicle model and a similar blockage of about 5%. The square-back study of Zeidan et al. provides related context but is not a validation dataset for the proposed slanted-body configuration. [[7]][ref7], [[8]][ref8]

Reference comparisons will account for the characteristic length used to define Reynolds number. In particular, $Re_L=UL/\nu$ and $Re_H=UH/\nu$, where $H$ is body height, are distinct quantities. Published Ahmed-body measurements are typically at Reynolds numbers one to two orders of magnitude above the $Re_L\approx10^5$ attainable here. Reference area, ground treatment, blockage, support geometry, and incoming-flow conditions will also be compared. If adequate overlap cannot be established, which is the expected outcome at this scale, the reference body will support repeatability and sensitivity characterization without a claim of quantitative aerodynamic validation.

### 4.2. Vehicle model

Following reference-body testing, the facility will be used to investigate a closed-body 1:43 diecast vehicle model of approximately 105 mm length. Its dimensions, frontal area, underbody geometry, ride height, pitch, wheel clearance, surface finish, and mounting arrangement will be measured and documented after purchase. Geometric fidelity of an inexpensive diecast model and ground representation will remain explicit limitations on the interpretation of its measured coefficients.

## 5. Calibration and Facility Characterization

### 5.1. Force-balance calibration

Known vertical and horizontal loads will be applied across the intended measurement range. Small masses (coins or hardware) will be weighed on a 0.01 g balance and used as calibration loads; horizontal loads will be applied through a fine thread over a low-friction pulley, from both directions so that averaging cancels pulley friction. Calibration will assess zero stability, loading and unloading hysteresis, repeatability, load-position sensitivity, cross-axis sensitivity, combined loading, and the installed response. This approach is consistent with the emphasis on sensor calibration and experimental validation in low-force wind-tunnel measurements. [[11]][ref11]

The initial calibration model is

$$
\begin{bmatrix}r_z\\r_x\end{bmatrix}
=\mathbf{K}\begin{bmatrix}F_{\mathrm{down}}\\D\end{bmatrix}
+\mathbf{b},
\tag{11}
$$

where $r_z$ and $r_x$ are the measured channel responses, $\mathbf{K}$ is the sensitivity matrix, and $\mathbf{b}$ is the offset vector. Off-diagonal terms represent cross-axis sensitivity. The fitted calibration will be evaluated using independent validation loads. Additional terms will be introduced only where supported by systematic residual behavior, and each dataset will retain the applicable calibration version.

The preliminary target for drift and repeatability is approximately 0.1 g mass-equivalent or less, corresponding to approximately 0.001 N, over the relevant acquisition period. With an expected drag of about 47 mN at 14 m/s, this corresponds to about 2% of the signal. This target will be assessed on the installed apparatus.

### 5.2. Pressure-system calibration

The differential-pressure transducer will be compared with a suitable reference over the intended operating range, either a borrowed calibrated manometer or, where none is available, an inclined water manometer with its reading uncertainty stated. Tests will evaluate zero offset, scale factor, hysteresis, leakage, temperature response, and measurement uncertainty.

For an illustrative air density of $\rho=1.20\ \mathrm{kg/m^3}$, Equation (4) gives

$$
q(5\ \mathrm{m/s})=15\ \mathrm{Pa},
\qquad
q(14\ \mathrm{m/s})=118\ \mathrm{Pa}.
\tag{12}
$$

These low differential pressures require particular attention to sensor range and uncertainty near the lower end of the operating envelope. [[4]][ref4]

### 5.3. Flow uniformity and temporal stability

The intended model envelope will be traversed at multiple operating conditions to map mean velocity and dynamic pressure, using five probe heights at each of two survey stations. Temporal stability will be recorded at each condition, and the survey will be repeated with the ground plate installed. Additional checks will determine whether installation of the model affects the reference reading.

**Table 4. Preliminary characterization targets.**

| Metric | Initial target |
| --- | --- |
| Mean velocity uniformity over the model envelope | Approximately ±2% |
| Mean dynamic-pressure stability under closed-loop control | Approximately ±1% |
| Coefficient variation between repeated setups | Approximately 3%, where the force signal is adequate (above about 12 m/s) |

The spatial domain, averaging interval, and statistical definition associated with each target will be specified in the commissioning procedure. A mean-flow survey does not establish turbulence intensity. Any reported turbulence level will require suitable measurements of velocity fluctuations.

### 5.4. Support interference and blockage

Support-only aerodynamic loading will be measured as a function of dynamic pressure. These measurements will inform tare corrections, while the uncertainty assessment will recognize that interactions between the model and support prevent exact correction by subtraction alone.

Geometric blockage will be evaluated using the actual model frontal area and usable test-section area, accounting for exposed supports and space occupied by the ground arrangement. The planning estimate is about 5.4% of the full section. Any correction will be justified for the relevant geometry and flow conditions using established wind-tunnel methods rather than a universal continuity-based multiplier. [[12]][ref12]

## 6. Experimental Methodology

### 6.1. Repeatability assessment

A fixed reference-body configuration will be tested at three dynamic-pressure levels. Each run will begin with a wind-off zero measurement, followed by establishment of the target dynamic pressure and a stabilization period. Synchronized force and pressure records will then be acquired. A second wind-off zero will be recorded after shutdown to assess drift. Independent repetitions will include model removal and remounting to capture setup variability. The run sequence will be executed automatically by the microcontroller to remove operator timing as a variable.

Initial acquisition periods will be approximately 30 s. The duration will be increased where necessary until mean estimates are stable. Within-run fluctuations and between-run repeatability will be reported separately because they represent different contributions to measurement variability.

### 6.2. Reynolds-number sweep

The reference body will initially be tested at nominal velocities of 5, 7.5, 10, 12, and 14 m/s. Operating conditions will be established using measured dynamic pressure under closed-loop control; fan PWM duty and rotational speed will serve as recorded control parameters rather than substitutes for airflow measurement.

For each condition, $Re_L$, $C_D$, and $C_{\mathrm{DF}}$ will be calculated using the documented characteristic length and reference area. Force will be examined as a function of dynamic pressure, and aerodynamic coefficients will be examined as functions of Reynolds number. Results below about 12 m/s will be reported as force trends because the force signal approaches the resolution target. Comparison with the selected reference dataset will follow an explicit assessment of condition overlap and differences. Drag validation will require the calibrated drag channel and cannot be inferred from vertical-force measurements.

### 6.3. Ground-condition sensitivity

Ground sensitivity will be evaluated at selected low, intermediate, and high operating conditions. Ride height (through saddle shims) and the leading-edge position of the ground plate will be varied individually. Model pitch will be examined in a separate series. Other configuration variables will remain fixed within each series.

Observed systematic changes will be interpreted as sensitivity to the imposed boundary conditions. They will be distinguished from random sensor noise and included in the discussion of facility limitations.

### 6.4. Vehicle-configuration comparisons

The vehicle study will compare a baseline configuration with three modifications: an added rear spoiler (3D-printed or card), a change in spoiler angle, and a change in ride height. At least three independent runs will be performed for each selected condition. Baseline and modified configurations will be alternated to expose drift, while reference area, ground arrangement, and mounting convention will remain fixed, apart from the intended configuration change.

Changes in downforce and drag coefficients will be expressed as

$$
\Delta C_{\mathrm{DF}}
=C_{\mathrm{DF,modified}}-C_{\mathrm{DF,baseline}},
\tag{13}
$$

$$
\Delta C_D=C_{D,\mathrm{modified}}-C_{D,\mathrm{baseline}}.
\tag{14}
$$

These differences will be interpreted as model-scale responses under the documented test conditions. A configuration effect will be reported as inconclusive when it cannot be resolved relative to the associated uncertainty and repeatability.

### 6.5. Qualitative flow visualization

Tufts of fine thread will be used in separate low-speed visualization runs to support qualitative interpretation of the force measurements and for classroom demonstration. Visualization will be separated from quantitative acquisition where it could alter the flow. Patterns observed at lower Reynolds numbers will not be assumed to reproduce the measurement flow at higher speeds. A fog tracer is optional and will be added only if budget allows; fog droplets may deposit on the model and affect force measurements.

## 7. Data Reduction and Uncertainty Analysis

### 7.1. Data records and traceability

Each run will be associated with a unique identifier and a complete record of the model, configuration, geometry version, reference area, and characteristic-length definitions. The record will include ride height, pitch, ground-plate geometry, support arrangement, and wheel state. Raw load-cell counts and pressure readings will be retained with timestamps, inlet temperature, atmospheric pressure, fan PWM duty, fan rotational speed, calibration version, pre-run and post-run zeros, and operator observations.

Processed forces and coefficients will remain traceable to these raw records and the applied calibration. Comparisons will use consistent definitions of reference pressure, reference area, and force sign.

### 7.2. Coefficient uncertainty

For a coefficient of the form $C=F/(qA)$ and approximately independent inputs, first-order propagation gives

$$
\left(\frac{u_C}{|C|}\right)^2
\approx
\left(\frac{u_F}{|F|}\right)^2
+\left(\frac{u_q}{q}\right)^2
+\left(\frac{u_A}{A}\right)^2,
\tag{15}
$$

where $u_C$, $u_F$, $u_q$, and $u_A$ denote the corresponding standard uncertainties. Near zero force, uncertainty will be propagated in absolute form because the relative expression becomes ill-conditioned. Covariance terms will be retained where inputs are correlated.

The analysis will distinguish instrument uncertainty, facility sensitivity, and uncertainty in transfer to full scale. Instrument uncertainty includes calibration, noise, drift, and geometric measurement. Facility sensitivity includes support interference, blockage, and ground conditions. Transfer uncertainty arises from Reynolds-number mismatch and model fidelity. These contributions will be described separately where a common quantitative uncertainty model is not justified.

The uncertainty of a time average will not be assumed to decrease as $1/\sqrt{N}$ when the $N$ acquired samples are correlated. Effective independence will be assessed, or repeat-run and block-based analyses will be used. Comparisons between configurations will also account for shared calibration and reference quantities when evaluating uncertainty in coefficient differences.

## 8. Interpretation and Limitations

### 8.1. Conditional extrapolation to full scale

For a geometric scale ratio $s=L_f/L_m$ (here $s=43$) and corresponding reference areas, the relationship between model and full-scale force is

$$
F_f=F_m s^2\frac{q_f}{q_m}\frac{C_f}{C_m}.
\tag{16}
$$

The assumption $C_f/C_m=1$ produces a conditional full-scale equivalent. Its validity depends on aerodynamic similarity and cannot be established from geometric scale alone. [[5]][ref5] Reynolds-number mismatch, ground simulation, wheel state, and geometric detail may all limit this interpretation, and at a Reynolds-number ratio near 1/170 the equal-coefficient assumption is particularly uncertain.

Results will therefore present measured model forces, coefficients, test conditions, and uncertainty before any full-scale equivalent. Where extrapolated values are included, the equal-coefficient assumption will be stated explicitly. Calibration factors will be established from independent loads rather than adjusted to reproduce a manufacturer-reported force.

### 8.2. Scope of validation

Instrument calibration, repeatability assessment, and aerodynamic validation address different questions. Calibration establishes the response of the measurement system to known inputs. Repeatability characterizes variation under nominally repeated conditions. Aerodynamic validation requires comparison with an independent reference under sufficiently comparable conditions.

A reproducible result may retain systematic bias from the ground arrangement, supports, or tunnel walls. Similarly, agreement at one operating point does not establish validity across the full operating range. The proposed study will therefore define its usable envelope from the combined calibration, flow-characterization, and sensitivity results.

## 9. Implementation and Evaluation Criteria

Development will proceed through the stages in Table 5. Progression will depend on documented evidence that the preceding stage supports the measurements required in the next stage.

**Table 5. Proposed development stages and evaluation criteria.**

| Stage | Principal deliverable | Evaluation criterion |
| --- | --- | --- |
| Electronics and control commissioning | Arduino fan control, load-cell and pressure acquisition, CSV logging | Stable closed-loop speed; bench force drift within about 1 mN |
| Instrument commissioning | Force and pressure calibrations | Adequate range, drift performance, and cross-axis characterization |
| Empty-tunnel characterization | Measured fan-array curve, flow maps, and stability measurements | Documented usable flow envelope |
| Reference-body testing | Repeatability results and Reynolds-number sweep | Scope and limitations of reference comparison established |
| Ground-condition study | Sensitivity measurements | Ground approximation characterized |
| Vehicle testing | Configuration-dependent aerodynamic coefficients | Effects resolved or reported as inconclusive |
| Classroom demonstration | Live force and flow display at a demonstration speed | Configuration differences visible above repeatability |

The primary success criterion is the ability to obtain repeatable aerodynamic comparisons with stated uncertainty under controlled model-scale conditions. Achievement of the preliminary numerical targets will be established experimentally during commissioning.

## 10. Conclusions

A low-cost miniature open-return wind tunnel for 1:43 vehicle models, with Arduino-based control and acquisition, and an associated calibration and experimental methodology have been proposed for drag and downforce measurements. The approach combines a documented reference body, independent force and pressure calibration, flow surveys, and controlled configuration studies. It is intended to establish which aerodynamic differences can be resolved within the facility's operating envelope and budget.

The interpretation framework separates measured model-scale behavior from conditional full-scale extrapolation. Reynolds-number mismatch, stationary-ground effects, support interference, blockage, and model fidelity remain central limitations to be evaluated. Experimental work is required to determine whether the proposed performance targets are achievable with low-cost components.

## References

1. NASA Glenn Research Center. *Similarity Parameters*. [Online resource][ref1].
2. NASA Glenn Research Center. *Aerodynamic Forces*. [Online resource][ref2].
3. Talay, T. A. (1975). *Introduction to the Aerodynamics of Flight*. NASA SP-367. National Aeronautics and Space Administration. [Report][ref3].
4. NASA Glenn Research Center. *Pitot Tube*. [Online resource][ref4].
5. NASA Glenn Research Center. *Lift Coefficient*. [Online resource][ref5].
6. Honda Motor Co., Ltd. *Full-Scale Wind Tunnel: Mastering the Wind with the Air as Our Ally*. [Technical overview][ref6].
7. Bayraktar, I., Landman, D., and Baysal, O. (2001). *Experimental and Computational Investigation of Ahmed Body for Ground Vehicle Aerodynamics*. SAE Technical Paper 2001-01-2742. [doi:10.4271/2001-01-2742][ref7].
8. Zeidan, W., Mazellier, N., Guilmineau, E., Passaggia, P.-Y., and Kourta, A. (2023). A near-wake survey of an Ahmed body comparing low- & high-fidelity numerical models with experiments. *European Journal of Mechanics - B/Fluids*, **101**, 195–208. [doi:10.1016/j.euromechflu.2023.05.002][ref8].
9. NASA Glenn Research Center. *Wandering Wind Tunnel*. [Online resource][ref9].
10. Calautit, J. K., Chaudhry, H. N., Hughes, B. R., and Sim, L. F. (2014). A validated design methodology for a closed-loop subsonic wind tunnel. *Journal of Wind Engineering and Industrial Aerodynamics*, **125**, 180–194. [doi:10.1016/j.jweia.2013.12.010][ref10].
11. Aboelezz, A., Elqudsi, Y., Hassanalian, M., and Desoki, A. (2020). Wind tunnel calibration, corrections and experimental validation for fixed-wing micro air vehicles measurements. *Aviation*, **23**(4), 104–113. [doi:10.3846/aviation.2019.11975][ref11].
12. Barlow, J. B., Rae, W. H., Jr., and Pope, A. (1999). *Low-Speed Wind Tunnel Testing* (3rd ed.). Wiley. ISBN 9780471557746. [Publisher][ref12].
13. Anderson, J. D., Jr. *Fundamentals of Aerodynamics* (4th ed.). McGraw-Hill. [Table of contents][ref13].

[ref1]: https://www.grc.nasa.gov/www/k-12/airplane/airsim.html
[ref2]: https://www.grc.nasa.gov/www/k-12/VirtualAero/BottleRocket/airplane/presar.html
[ref3]: https://ntrs.nasa.gov/citations/19760003955
[ref4]: https://www.grc.nasa.gov/www/k-12/BGP/pitot.html
[ref5]: https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/lift-coefficient/
[ref6]: https://global.honda/en/tech/serial/Hondas_RandD_Facilities_part04/
[ref7]: https://doi.org/10.4271/2001-01-2742
[ref8]: https://doi.org/10.1016/j.euromechflu.2023.05.002
[ref9]: https://www.grc.nasa.gov/www/k-12/WindTunnel/wandering_windtunnel.html
[ref10]: https://doi.org/10.1016/j.jweia.2013.12.010
[ref11]: https://doi.org/10.3846/aviation.2019.11975
[ref12]: https://www.wiley.com/en-it/Low-Speed+Wind+Tunnel+Testing,+3rd+Edition-p-9780471557746
[ref13]: https://catdir.loc.gov/catdir/toc/ecip0513/2005015910.html
