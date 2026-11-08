# Wind Tunnel Shopping List

For the 400 × 300 mm, 5–15 m/s apparatus in [build_plan.md](build_plan.md). Preferred marketplace: **Shopee Taiwan (蝦皮購物)**. Product sources checked on 3 November 2026. Quantities below are for one tunnel with four two-roller wheel cradles.

**Order the electronics first. Confirm the car dimensions, total supported mass, available mains supply, and tunnel pressure loss before ordering the load cells, cut parts, or fan.** No complete price is quoted because these major items still require sizing and quotations.

## Shopee Taiwan buying options

These product listings appeared in indexed search results. Live stock, selected variants, authenticity, and checkout prices were not verified. Alternatives below replace the corresponding item in the detailed list; do not buy both.

- **2 × SparkFun Qwiic Scale NAU7802** — [物聯汪汪 listing](https://shopee.tw/product/9340697/23287703474). Ask for model **SEN-15242**, as specified below.
- **1 × TCA9548A multiplexer** — [大洋國際電子 listing](https://shopee.tw/product/26482219/2763399875). Alternative to the Adafruit PCA9548 board. Confirm the supplied chip and pinout; use 3.3 V wiring. The generic board requires header wiring rather than direct Qwiic connections.
- **1 × CJMCU-280E BME280, 3.3 V** — [台灣物聯 listing](https://shopee.tw/product/10207300/109950098). Alternative to the Adafruit BME280 breakout; confirm the BME280 variant and pinout. Connect through headers at 3.3 V.
- **20 × 683ZZ bearings, 3 × 7 × 3 mm** — [multi-size bearing listing](https://shopee.tw/product/149365831/5247363259). Select and confirm that exact variant; this is an unbranded alternative to MISUMI B683ZZ, so inspect rotation and play before machining all rollers.
- **1 cut set of 4040 extrusion** — [台中3D總舖 listing](https://shopee.tw/product/7974691/11368338350). This listing is for European-profile extrusion, not MISUMI HFS8. Obtain matching brackets, nuts, and bolts from the same profile system; confirm dimensions before cutting.

With the generic multiplexer/BME280 options, replace the five-cable Qwiic bundle below with **2 Qwiic-to-bare-wire cables for the NAU7802 boards, plus headers and short hookup wires**. Confirm connector pin order before powering up.

Shopee availability remains unconfirmed for **Feather RP2040 4884, the specified Phidgets load cells, SDP810-500Pa/SEK-SDP8xx, and Dwyer 160-8**. Their manufacturer links below remain the specification references. Do not substitute an unspecified weighing sensor or pressure module solely to keep every purchase on Shopee.

## 1. Logger and sensor electronics — order week 1, assemble week 3

- **1 × [Adafruit Feather RP2040, product 4884](https://www.adafruit.com/product/4884).** Main controller; connect by USB to an existing laptop for CSV logging.
- **2 × [SparkFun Qwiic Scale, NAU7802, SEN-15242](https://www.sparkfun.com/sparkfun-qwiic-scale-nau7802.html).** One bridge amplifier/ADC for drag and one for vertical force. ADC bit count does not establish force accuracy.
- **1 × [Adafruit PCA9548 I²C multiplexer, product 5626](https://www.adafruit.com/product/5626).** Put the two NAU7802 boards on separate branches because both use address `0x2A`. Timestamp both channels and check acquisition delay; these boards do not provide simultaneous sampling.
- **1 × [Adafruit BME280 breakout, product 2652](https://www.adafruit.com/product/2652).** Air temperature, absolute pressure, and RH for density estimation. Mount away from electronics heat and direct fog. No separate humidity-calibration equipment is required.
- **5 × 100–200 mm STEMMA QT/Qwiic cables**, **1 × USB-C data cable**, **1 × small electronics enclosure**, and **1 set of terminal blocks, shielded load-cell cable, headers, and strain reliefs**. Use 3.3 V logic; keep the sensor wiring away from the motor controller.

## 2. Force sensors — confirm capacity in week 1

- **1 × [Phidgets FRC4130_0, 300 g C3 single-point load cell](https://phidgets.com/?prodid=1299)** for drag. Nominal capacity is approximately 2.94 N; specified repeatability is ±45 mg. Orient its sensing axis horizontally, with guides carrying vehicle weight and unwanted moments.
- **1 × [Phidgets FRC4125_0, 3 kg C4 single-point load cell](https://phidgets.com/?prodid=1324)** for vertical force. Specified repeatability is ±300 mg, approximately 0.0029 N. Select it only if the car, cradles, moving frame, aerodynamic load, and overload allowance fit the capacity. Taring does not remove physical dead load.

These are candidates for the 0.005 N installed repeatability target. Temperature drift, creep, cross-axis loading, and cradle seating still require verification. Two load cells alone are not a complete two-axis balance: fabricate the guided frame and adjustable overload stops described below.

## 3. Airspeed measurement — order week 1, install week 4

- **1 × Dwyer 160-8 Pitot-static tube**, from the [Series 160 range](https://www.dwyeromega.com/en-us/stainless-steel-pitot-tube-for-airflow-corrosion-resistant-3-4-in-pipe/p/Series-160). This model has approximately 219 mm insertion length and a 7.94 mm stem. Fit an adjustable, retractable mount ahead of the car, with its tip facing upstream.
- **1 × [Sensirion SEK-SDP8xx evaluation kit](https://sensirion.com/products/catalog/SEK-SDP8xx)**, containing an SDP810-500Pa sensor and connection cable. Adapt the cable to the Feather's I²C interface using the manufacturer's pinout; it is not a direct Qwiic cable. The separate SensorBridge is needed for Sensirion's USB evaluation workflow, not for this custom microcontroller connection.
- **2 × approximately 1 m lengths of pressure tubing**, matching adapters for the probe/sensor ports, **1 × retractable probe clamp**, and **2 × access-port caps**. Check actual barb dimensions before ordering tubing. Connect total pressure to `+`, static pressure to `−`; keep the sensor and lines dry.

**Pressure accuracy is the purchasing limitation.** The [SDP810-500Pa specification](https://sensirion.com/products/catalog/SDP810-500Pa) gives ±500 Pa range, 0.1 Pa zero-point accuracy, and 3% of reading span accuracy. It covers the required 15–135 Pa but does **not** meet the plan's 1% pressure objective out of the box. Use it for commissioning, then individually calibrate and assess the achieved uncertainty. Do not substitute the ±125 Pa version: 135 Pa exceeds its range.

If 1% is mandatory, obtain a quotation for a calibrated higher-accuracy pressure system before buying this kit. The acceptance requirement is uncertainty no greater than 0.15 Pa at 15 Pa, including the readout and calibration. Borrow or rent a suitable reference for week 6; another uncalibrated low-cost sensor is insufficient.

## 4. Rollers and balance — prototype week 2, complete week 3

- **20 × MISUMI B683ZZ miniature bearings:** 16 installed, four spares. Specify **3 mm bore × 7 mm outside diameter × 3 mm width**, as in the [MISUMI bearing catalogue](https://uk.misumi-ec.com/pdf/fa/p1_0907.pdf).
- **8 × precision 3 mm steel shafts**, cut to the cradle width, with matching spacers and shaft retention hardware.
- **8 × machined POM rollers**, each with two bearing seats. Final outside diameter and width depend on tire diameter, tire width, and required ground clearance.
- **4 × adjustable aluminium cradle brackets**, **1 × common moving support frame**, and **1 × guided two-axis balance assembly** with flexures, leveling screws, overload stops, and a clear-running vehicle catch.

Give these quantities to a local machine shop. Measure wheelbase, track, tire dimensions, and model mass first. Approve one assembled cradle before machining the remaining three. Keep the ground plate on a separate fixed support.

## 5. Tunnel structure — quote week 1, fabricate weeks 2–3

- **1 cut set of [MISUMI HFS8-4040 aluminium extrusion](https://th.misumi-ec.com/en/vona2/detail/110302689860/?HissuCode=HFS8-4040)**, with compatible brackets, T-nuts, bolts, feet, and diagonal bracing. Cut lengths follow the complete duct and room layout.
- **1 cut set of clear polycarbonate panels** for the test section. Ask the fabricator to quote 6 mm sheet initially; verify stiffness and supports before releasing drawings.
- **1 fabricated flat aluminium ground plate**, with four replaceable cradle-clearance inserts and adjustable supports.
- **1 fabricated settling chamber, contraction, and diffuser set**, with sealed smooth interiors, removable flanges, gasket tape, and fasteners.
- **1 removable honeycomb panel and 2 removable screen panels**, sized to the settling chamber. Final cell geometry, mesh/open area, and spacing belong in the week-1 airflow and pressure-loss design; window insect mesh is not an automatic substitute.
- **1 independent fan base**, **1 independent balance base**, and appropriately rated vibration isolators/flexible duct connection.

These are custom fabrication orders, not stock assemblies. Do not order sheet sizes or extrusion lengths from the schematic figures.

## 6. Fan package — request quotation in week 1

Request **1 × [Kruger BSB-series centrifugal fan package](https://www.krugerfan.com/products/view/5/44/?lang=en)**, including motor, compatible variable-speed controller, guards, isolator, emergency shutdown, and an RPM feedback provision. Have the supplier select the exact size from its pressure–flow curve.

Send this duty specification: **2,160–6,480 m³/h through the assembled tunnel**, at its calculated pressure loss, for a 400 × 300 mm test section operating at 5–15 m/s. Require the selected operating points and electrical requirements in the quotation. The 135 Pa test-section dynamic pressure is not the fan's total pressure-loss requirement.

The exact fan and controller cannot be selected responsibly until the pressure-loss estimate and mains voltage/phase are known. Confirm delivery by week 3 and install in week 4. Include a properly interfaced tachometer if the supplied package cannot report actual RPM.

## 7. Water fog and lighting — order week 1, install week 5

- **1 × [Seeed Grove Water Atomization module, 101020090](https://www.seeedstudio.com/Grove-Water-Atomization-v1-0.html)** for an initial fog-delivery trial, with a separate regulated **5 V, 2 A supply**. Do not power the atomizer from a controller GPIO. This small module's visibility at full tunnel speed remains to be demonstrated.
- **1 × external reservoir/enclosure**, short delivery hose, **1 × removable metal delivery wand**, adjustable clamp, and a capped access port. Match fittings after selecting the wand bore; provide condensate collection outside the tunnel.
- **1 × white LED light bar with its matching power supply**, mounted outside the transparent panel.

Place the outlet after the contraction, ahead of the car, pointing downstream, as shown in the [placement drawing](figures/probe-and-fog-placement.svg). Retract the Pitot before fogging. Test the small atomizer before spending on a larger fog system.

## 8. Calibration access — arrange week 1, use week 6

Arrange a **certified mass set covering the intended calibration loads**, a horizontal-load fixture with characterized friction, and a **calibrated low-pressure reference** suitable at 15–135 Pa. Borrowing laboratory equipment is reasonable; include rental/calibration charges in the budget. Calibrate the complete mounted apparatus, including both force channels and their cross-axis response.
