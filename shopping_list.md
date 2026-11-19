# Mini Wind Tunnel Shopping List (1:43, Arduino Uno, cap NT$5,000)

Goes with [build_plan_mini.md](build_plan_mini.md). The earlier Traditional Chinese version is kept at [shopping_list.zh-TW.md](shopping_list.zh-TW.md). Prices marked "checked" are based on real listings (sources at the end); prices marked "estimate" have no Taiwanese listing checked yet, so confirm on Shopee before ordering. The Shopee search terms are left in Chinese because that is what you type on Shopee. The Arduino Uno is already owned and not counted.

## Why the upper estimate reaches NT$8,000–9,000

Adding the most expensive case of every item gives **NT$9,750**; the cheapest case of every item gives **NT$4,660**. Most of the gap comes from three things:

| Item | Price | Share of the lowest total | Why it cannot be dropped |
| --- | --- | --- | --- |
| 8 × QFR1212GHE high-static-pressure fans (price to recheck) | 2,000–3,000 | 43% | Must push the whole tunnel's resistance at 14 m/s (about 85 Pa, 1,070 m³/h). Ordinary PC case fans reach only about 75 Pa; four of them give only about 7 m/s |
| Home-made speed sensor A + backup B + calibration | 430–800 | 9% | The dynamic pressure is only 15–118 Pa; ready-made digital differential-pressure sensors cost NT$1,100–1,600 with shipping, so a home-made bell manometer (primary) + two BMP280s (backup) is used instead |
| 12 V 25 A power supply | 0–900 | 0–19% | Eight QFR fans draw 14.4 A rated, 21.6 A max (datasheet); an old PC supply is free, a new one costs about 500–900 |

**The other 11 small items cost only NT$80–900 each, but together add up to about NT$2,230–5,050.** So "8,000–9,000" is not one expensive item: the fans are half, plus many small things. A real order usually lands in between (about 5,000–6,000), so **staying at 5,000 means deliberately following the low-cost route below.**

## Low-cost route (target ≤ NT$5,000)

1. **Power supply: an old PC ATX supply (free).** Ask the school IT office, recycling, or a retired home PC; the 12 V output must be rated ≥ 25 A (supplies of 400 W and up usually are).
2. **Fans at NT$500 or less each:** look for server pulls; 8 QFR1212GHE must still fit about 2,000–3,000 (re-price).
3. **Tunnel body from scrap wherever possible:** ribs, spines, sleeves and the settling chamber from the school workshop's offcuts or cardboard; only the test section must be bought clear PC.
4. **A cheap closed-body car** (about NT$80–200), not a collector's model.
5. **Per-fan fuses in inline holders** (about NT$150 for 8) instead of two fuse boxes.
6. **Borrow** the 0.01 g pocket scale, soldering iron, multimeter and 3D printer.

This comes to about **NT$4,450–4,650**. If fans cannot be found at 500 or less, or a new power supply is needed and the total goes over 5,000, **cut speed sensor B first** (saves NT$120–300 but loses the backup and cross-check); speed sensor A and the calibration manometer cannot be cut.

## Option C: buy a ready-made ABP2 (only if home-made A and B both fail)

The decision rule is in the plan, "D2. Home-made speed sensors". Normally **do not buy this**; this section just keeps the information ready.

| Source | In stock? | Shipping | Notes |
| --- | --- | --- | --- |
| **DigiKey Taiwan** (digikey.tw) | Yes, NT$755, 64 in stock in 2026-11 | Free over NT$1,400, otherwise NT$600 | The only source confirmed in stock; about 4 days |
| Mouser Taiwan (mouser.tw) | Not confirmed (search timed out) | Free over NT$1,400 | Search the full part number and compare |
| RS Taiwan | Not this part (only other ranges such as 005ND) | Individuals free over NT$1,300 (before tax), otherwise NT$500 | — |
| Shopee, Ruten, Taobao | Not found | — | Not recommended: easy to get a different suffix or an unknown source |

**Ways to save the shipping (pick one):**

1. **Bring the DigiKey order up to NT$1,400:** add a level-shifter module (Adafruit 757), a test MOSFET module, a 1000 µF capacitor, better HX711s (SparkFun). The extra parts cost about the same as the shipping, and they are better parts.
2. **Share one DigiKey order** with classmates or a club.
3. Buy one alone: NT$755 + 600 = NT$1,355.

### How to connect it when it arrives

1. Solder the ABP2 onto perfboard: line the two rows of pins up with two rows of pads 4 holes apart and solder pin by pin with a fine tip; add a 6-pin header.
2. Pins (datasheet Table 21): 1 = GND, 2 = VDD, 3 = EOC (not connected), 4 = NC, 5 = SDA, 6 = SCL.
3. **VDD to the Uno's 3V3**, never 5V (datasheet absolute maximum 3.6 V).
4. SDA and SCL to the low-voltage side of the level shifter (LV to 3V3); the high-voltage side (HV to 5V) to Uno A4 and A5.
5. Port 1 (high) to the Pitot total pressure or the settling-chamber static ring; port 2 to the test-section entrance static ring.
6. Code: the datasheet has an Arduino Uno example. Before every fan start, average 5 s with fans off as the zero and subtract it. Without zeroing the error can reach ±12.5 Pa, while the dynamic pressure at 5 m/s is only 15 Pa.

## List

### A. Fans and power

| Item | Spec and quantity | Shopee search | NT$ | Basis | Check before ordering |
| --- | --- | --- | --- | --- | --- |
| High-static-pressure fan | Delta QFR1212GHE, 120×120×38 mm, 12 V, 2-wire, ×8 (2 × 2 array, two layers) | `Delta QFR1212GHE`, `12038 風扇 2線`, `伺服器 風扇 12038` | 2,000–3,000 | Placeholder (the checked US$16–24 each was for 4 × PFC1212DE); re-price for 8 | Buy 1 first and pass fan_pwm_test, then buy 7 more of the same model; note the rated current for sizing the supply and fuse. Fallback if the test fails: 4 × PFC1212DE (4-wire PWM) |
| Fan driver board | 4-channel opto-isolated MOSFET PWM board (YYNMOS-4 type): 3–20 V PWM input, 3.7–27 V output, ≤ 10 A per channel, screw terminals; ×2 + 1 spare (one per layer, one channel per fan) | `4路 MOS 模組 PWM`, `YYNMOS-4` | 150–450 | Estimate (no Shopee listing checked) | Buy 1 with the test fan first. Check: PWM limit (1 kHz or 200 Hz; 25 kHz is not possible), a common DC−/GND terminal sized for about 11 A, whether flyback diodes are on the board |
| Per-fan fuses and diodes | 8 × 5 A blade fuse (+ spares) in 2 × 6-way blade fuse box with negative bus (one per layer), or 8 inline holders on the low-cost route; 8 × SS34 Schottky diode | `6路 保險絲盒 負極`, `5A 刀片 保險絲`, `保險絲座 線上型`, `SS34` | 150–550 | Estimate | Fuse box rated ≥ 20 A per way; diode stripe to the fan's red lead |
| 12 V power supply | 12 V ≥ 25 A, ×1 | `ATX 電源 二手`, `12V 25A 電源供應器` | 0–900 | Checked (wholesale about US$17; retail is an estimate) | An old ATX needs the green wire shorted to start; an LED-type supply needs an enclosure and a fuse |
| Fuse + holder | 30 A automotive blade fuse + in-line holder, ×1 | `汽車 保險絲座 30A` | In wiring below | Estimate | At the supply's + output |
| Emergency stop | Latching mushroom button, rated ≥ 25 A DC, or use it to switch a relay, ×1 | `緊急停止開關 蘑菇頭` | In wiring below | Estimate | If the switch rating is too low, have it switch a 30 A automotive relay |
| Wire | 12 AWG red and black 1 m each (main run), 16 AWG 2 m each (to each fan layer); 1000 µF / 25 V capacitor across 12 V+ and GND on the supply side, before the boards (never across a fan) | `12AWG 矽膠線`, `16AWG 矽膠線` | In wiring below | Estimate | Silicone wire is softer and easier to route |
| Fan guard | 12 cm metal guard ×4 | `12公分 風扇 網罩` | In wiring below | Estimate | On the outlet side |
| **Wiring subtotal** | Fuse, emergency stop, wire, guards, jumper wires, terminals, heat-shrink | | **200–400** | Estimate | |

### B. Sensors (Arduino side)

| Item | Spec and quantity | Shopee search | NT$ | Basis | Check before ordering |
| --- | --- | --- | --- | --- | --- |
| Speed sensor A: load cell + HX711 | 100 g aluminium single-point load cell + HX711, ×1 set (the third set, on A0/A1) | `荷重元 100g HX711` | 230–350 (incl. next two rows) | Estimate | Same model as the drag cell, so they are interchangeable spares |
| Speed sensor A: box and liquid | Airtight food container about 1.5–2 L and at least about 12–13 cm tall inside ×1; dish ≥ 100 mm inside diameter, ≥ 57 mm deep ×1; about 150 mL baby oil; 2 straight bulkhead tube fittings | `樂扣 保鮮盒 1.5L`, `嬰兒油`, `隔板接頭 4mm` | (as above) | Estimate | The box must seal completely; the dish can be a small bowl from home or 3D-printed |
| Speed sensor A: bell | 3D-printed PETG straight cylinder: 60 mm inside diameter, 80 mm tall, 1.2 mm wall, hanging loop on top | — | 0 | School printer | **Do not use a tapered paper or plastic cup** |
| Speed sensor B | **2 × BMP280 module, 5 V-capable** (on-board 3.3 V regulator and level shifting, usually marked 3–5 V or 5V); 2 × 35 mm film canister or small airtight box | `BMP280 5V 模組`, `GY-BMP280 5V` | 120–300 | Estimate | The small purple boards marked only "3.3V" cannot connect directly to the Uno; SDO must be selectable to GND/VCC for the address |
| Calibration tools | Clear PVC tube 4 mm inside diameter about 1 m, board ≥ 30 cm, 60 mL syringe, 2 tees, food colouring | `PVC 透明管 4mm`, `針筒 60ml` | 80–150 | Estimate | The syringe must pull smoothly and slowly |
| HX711 module | 24-bit load-cell amplifier board, ×2 | `HX711 模組` | 250–400 (incl. next two rows) | Estimate | Some sellers sell "load cell + HX711" together more cheaply |
| Load cell (drag) | 100 g aluminium single-point, ×1 | `荷重元 100g` | (as above) | Estimate | Rated 100 g, with 4 wires |
| Load cell (vertical) | 1 kg aluminium single-point, ×1 | `荷重元 1kg` | (as above) | Estimate | As above |
| Pitot tube and tubing | Brass tube Ø4 mm about 50 cm (Pitot + bell U-tube) and one Ø3 mm; silicone tube 2–3 mm inside diameter about 3 m (red and blue if possible); 4 tees | `黃銅管 4mm`, `矽膠管 內徑2mm`, `氣管 三通` | 150–300 | Estimate | The silicone tube must grip the brass tube and fittings tightly |
| LCD 1602 (optional) | I²C interface | `LCD1602 I2C` | Not budgeted | — | Optional; the laptop shows everything |

### C. Tunnel body

| Item | Spec and quantity | Shopee search | NT$ | Basis | Check before ordering |
| --- | --- | --- | --- | --- | --- |
| Clear acrylic sheet | **3 mm cast acrylic**, about 0.4 m² (test section, balance box walls, car hatch, ground plate), laser-cut from the CAD laser view | `壓克力板 3mm 透明 雷射切割` | 300–600 | Estimate | Cast, not extruded, if the shop offers both (cleaner laser edges, less cracking with solvent glue); peel the film only after cutting |
| PET sheet | 1 mm clear rigid PET (bell and contraction walls, 8 pieces cut from the flat patterns), about 4 sheets of A3 | `PET 硬片 1mm` | 600–1,200 (incl. next two rows) | Estimate | Must bend without creasing; the two contraction top/bottom sheets (393 × 412 mm) are bigger than A3, so buy A2 or a roll |
| Plywood | **3 mm only** (the laser's limit), about 4 m², e.g. fourteen 60 × 40 cm sheets plus the four diffuser panels (about 650 × 245 mm each): ribs and spines as glued pairs, settling chamber and fan box (finger joints), diffuser, sleeves, cradles, balance plates | `椴木合板 3mm 雷射` | (as above) | Estimate | Laser plywood (basswood/poplar) cuts cleanly; MDF also works but is heavier. Ask the school for offcuts first |
| Sealing and glue | Hot-glue sticks, foam tape, screws and nuts, acrylic solvent cement (test section), wood glue (laminated plywood pairs) | `泡棉膠條 單面`, `壓克力 接著劑` | (as above) | Estimate | |
| Honeycomb | About 4,000 × 6 mm straws (cut to 40 mm), or 3D-printed hexagonal cells | `吸管 6mm 1000入` | 100–200 (incl. screens) | Estimate | About 6 mm diameter, must be straight |
| Screens | Polyester voile (window screen) or fine stainless mesh, about 50 × 40 cm ×2 | `窗紗 布`, `不鏽鋼網 細` | (as above) | Estimate | Hold it up to a light: more opening than wire (60–70% open area) |

### D. Balance, car and portability

| Item | Spec and quantity | Shopee search | NT$ | Basis | Check before ordering |
| --- | --- | --- | --- | --- | --- |
| Hatch hardware | 4 × 6 × 3 mm neodymium magnets + 4 steel washers, 2 mm single-sided foam tape, 1 × lever microswitch (hatch interlock) | `釹鐵硼 磁鐵 6x3`, `泡棉膠條 單面 2mm`, `微動開關 滾輪` | 100–200 (incl. next row) | Estimate | Magnets press-fit in the roof's 6 mm holes |
| Stop and balance screws | M4 × 25 pan-head screw + M4 lock nut + M4 heat-set insert (down-stop); 2 × M3 × 16 screw + 2 M3 lock nuts (fore-aft stops); M3/M4 screws for the load cells, bracket and frame | `M4 熱熔螺母`, `M3 螺絲 不鏽鋼` | (as above) | Estimate | Check the load cells' thread size when they arrive |
| 1:43 car | **Closed body**, ordinary saloon or hatchback, ×1 | `1:43 合金 模型車` | 80–450 | Checked (SHEIN Taiwan NT$77–445) | Wheels must turn freely, length about 100–110 mm; measure it after buying and update the spec |
| V-saddles | 4, 3D-printed (PETG) | — | 0 | School printer | |
| Portability parts | 12 × M6 levelling feet (with rubber pads) and T-nuts, 2 × M4 thumb screws with nuts or inserts (transport lock), 2 × Ø4 mm tube quick-connects | `M6 調整腳 橡膠`, `手轉螺絲 M4`, `4mm 快速接頭` | 150–300 | Estimate | The feet's thread must fit the T-nuts in the cradles and the balance tray |

### E. Borrow (not budgeted)

| Item | Use |
| --- | --- |
| 0.01 g pocket scale | Weigh coins as calibration weights |
| Laser cutter (3 mm max) | Every LC3 part; switch the CAD feature to the "Laser sheets" view and export each bed as DXF |
| 3D printer | Saddles, wheel wells, balance spacer, corner bracket, drag-cell foot, stop pillar and fork, hatch knob, honeycomb (optional), bell |
| Soldering iron, multimeter | Wiring and checks |
| Fine wool or sewing thread | Tufts for visualization |

## Totals

| Group | Low | High |
| --- | --- | --- |
| A. Fans and power (incl. wiring) | 2,500 | 5,300 |
| B. Sensors | 830 | 1,500 |
| C. Tunnel body | 1,000 | 2,000 |
| D. Balance, car and portability | 330 | 950 |
| **Total** | **4,660** | **9,750** |

These numbers match `budget_ntd` in [spec/mini.json](spec/mini.json); `python3 tools/mini_calc.py` adds them up automatically.

## Price sources

- Fans: [Newegg Delta 12038](https://www.newegg.com/p/1YF-003V-00JY6), [eBay Wathai 12038 PWM](https://www.ebay.com/itm/196887445182), [Walmart 12038 PWM](https://www.walmart.com/ip/5357691938), [FridayParts PFC1212DE](https://www.fridayparts.com/12v-4-8a-12cm-aftermarket-delta-pfc1212de-12038-volume-violent-general-cooling-fan-for-industrial-automation-system)
- BMP280: [Bosch BMP280 datasheet](https://bluerobotics.com/wp-content/uploads/2022/05/BMP280-DATASHEET.pdf) (noise 1.3 Pa, temperature coefficient 1.5 Pa/K, relative accuracy ±12 Pa)
- Option C ABP2: [DigiKey Taiwan ABP2MRRN001ND2A3XX](https://www.digikey.tw/en/products/detail/honeywell-sensing-and-productivity-solutions/ABP2MRRN001ND2A3XX/26264563), [Honeywell ABP2 datasheet 32350268 (RS copy)](https://docs.rs-online.com/578f/A700000015334102.pdf), [Adafruit BSS138 level shifter](https://www.adafruit.com/product/757)
- Shipping: [DigiKey Taiwan (NT$600 under NT$1,400)](https://www.digikey.tw/en/maker/profiles/791dd58bcd43431aa002264bd14ce00c), [RS Taiwan delivery (individuals NT$500 under NT$1,300)](https://twcn.rs-online.com/web/content/support/all-articles/delivery)
- 12 V supply (these listings are 20 A / 240 W; buy ≥ 25 A / 300 W): [Alibaba open-frame supply](https://www.alibaba.com/product-detail/240W-12V-open-frame-switching-power_60821400748.html), [RS Taiwan industrial](https://twcn.rs-online.com/web/p/switching-power-supplies/1618225) (industrial grade costs NT$2,500 and up; not needed here)
- Car: [SHEIN Taiwan Burago 1:43](https://m.shein.tw/Burago%201%2043%20F1%20AMR25%20Alloy%20Car%20Model%202025%20No%2014%20Alonso%20Regular%20Version-p-322987138.html), [SHEIN Taiwan 1:43 diecast](https://m.shein.tw/1%2043%20Scale%20Supercar%20Model%20Alloy%20Diecast%20Model%20Car%20Detailed%20Craftsmanship%20Openable%20Doors%20Toy%20Car%20Gift%20Suitable%20For%20Boys-p-93016086.html)
