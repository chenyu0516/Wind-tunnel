// fan_pwm_test.ino -- one-fan go/no-go test before buying 8 x Delta QFR1212GHE (2-wire)
//
// Question: can the Uno set the speed of a 2-wire fan by switching its 12 V
// with a logic-level MOSFET, smoothly from about 30 % to 100 % of full speed,
// without the fan's built-in "start slow, full speed after 10 s" routine
// restarting on every pulse?
//
// Wiring (fans never take power from the Uno; all GNDs common):
//   12 V PSU +  -> fan RED
//   fan BLACK   -> MOSFET module OUT- / drain
//   MOSFET module GND / source -> 12 V PSU -
//   MOSFET module SIG -> Uno D9          (logic-level module, e.g. AOD4184/D4184;
//                                          NOT an IRF520 module: it barely turns on at 5 V)
//   Schottky diode (1N5819/SS34) across the fan: stripe to RED, other end to BLACK
//   1000 uF / 25 V capacitor across the 12 V PSU output (Delta asks for > 4.7 uF)
//   Uno GND -> 12 V PSU -
// Speed reading (pick one):
//   a) TCRT5000 reflective module: VCC 5V, GND, D0 -> Uno D2. One strip of white
//      tape on one blade, sensor 3-5 mm from the blade tips. PULSES_PER_REV = 1.
//   b) No sensor: phone spectrum-analyser app next to the fan. Blade-pass peak
//      f [Hz] -> rpm = 60 * f / number_of_blades (count the blades).
//
// Safety: clamp the fan to the table (it pushes itself), fit the guard, keep
// fingers and cables out. The fan is 6000 rpm and 64 dBA; wear ear plugs.
//
// Serial Monitor at 115200 baud. Commands:
//   1..4  choose PWM frequency: 1 = 25 kHz, 2 = 1 kHz, 3 = 122 Hz, 4 = 30 Hz
//   a     automatic sweep at the chosen frequency: 100,80,60,50,40,30,20 % then 100 %
//   0..9  after 'd': set a fixed duty, e.g. "d35" = 35 %   (Enter after typing)
//   s     stop (MOSFET off)
//
// Pass if, at one of the frequencies:
//   - rpm rises steadily with duty from 30 % to 100 %,
//   - rpm at 30-35 % duty is about 30-40 % of the rpm at 100 %
//     (5 m/s needs about 31 % of full fan speed),
//   - each step settles within 15 s and then stays within +-3 %,
//   - the fan never drops back to its slow start speed while running.

const uint8_t PIN_PWM = 9;          // Timer1 OC1A
const uint8_t PIN_SPEED = 2;        // INT0, optional optical sensor
const uint8_t PULSES_PER_REV = 1;   // one tape strip
const uint16_t STEP_HOLD_S = 20;    // > 10 s soft start + settle

volatile uint32_t pulses = 0;
uint8_t freqIndex = 0;              // 0 = 25 kHz
uint16_t topValue = 639;
float dutyPct = 0;

struct PwmSetting { const char *name; uint8_t csBits; uint16_t top; };
// f = 16 MHz / (prescaler * (1 + TOP)), fast PWM mode 14 (TOP = ICR1)
const PwmSetting SETTINGS[] = {
  {"25 kHz", _BV(CS10),            639},   // /1
  {"1 kHz",  _BV(CS11),            1999},  // /8
  {"122 Hz", _BV(CS11) | _BV(CS10), 2047}, // /64
  {"30 Hz",  _BV(CS12),            2082},  // /256
};

void onPulse() { pulses++; }

void applyFrequency(uint8_t i) {
  freqIndex = i;
  topValue = SETTINGS[i].top;
  TCCR1A = _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(WGM12) | SETTINGS[i].csBits;
  ICR1 = topValue;
  setDuty(dutyPct);
  Serial.print(F("# PWM frequency ")); Serial.println(SETTINGS[i].name);
}

void setDuty(float pct) {
  dutyPct = constrain(pct, 0, 100);
  if (dutyPct <= 0) {                 // true off: disconnect timer, drive low
    TCCR1A &= ~_BV(COM1A1);
    digitalWrite(PIN_PWM, LOW);
  } else if (dutyPct >= 100) {        // true on
    TCCR1A &= ~_BV(COM1A1);
    digitalWrite(PIN_PWM, HIGH);
  } else {
    OCR1A = (uint16_t)(dutyPct / 100.0 * topValue);
    TCCR1A |= _BV(COM1A1);
  }
}

uint32_t rpmOver(uint16_t ms) {
  noInterrupts(); pulses = 0; interrupts();
  delay(ms);
  noInterrupts(); uint32_t n = pulses; interrupts();
  return n * 60000UL / ms / PULSES_PER_REV;
}

void holdAndLog(uint16_t seconds) {
  for (uint16_t t = 1; t <= seconds; t++) {
    uint32_t rpm = rpmOver(1000);
    Serial.print(SETTINGS[freqIndex].name); Serial.print(',');
    Serial.print(dutyPct, 0); Serial.print(',');
    Serial.print(t); Serial.print(',');
    Serial.println(rpm);
    if (Serial.available() && Serial.peek() == 's') return;
  }
}

void autoSweep() {
  const uint8_t steps[] = {100, 80, 60, 50, 40, 30, 20, 100};
  Serial.println(F("freq,duty_pct,t_s,rpm"));
  for (uint8_t i = 0; i < sizeof(steps); i++) {
    setDuty(steps[i]);
    holdAndLog(STEP_HOLD_S);
    if (Serial.available() && Serial.peek() == 's') break;
  }
  setDuty(0);
  Serial.println(F("# sweep done, fan off"));
}

void setup() {
  pinMode(PIN_PWM, OUTPUT);
  digitalWrite(PIN_PWM, LOW);         // MOSFET off at power-up
  pinMode(PIN_SPEED, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_SPEED), onPulse, FALLING);
  Serial.begin(115200);
  applyFrequency(0);
  setDuty(0);
  Serial.println(F("# fan_pwm_test ready. 1-4 = frequency, a = auto sweep, dNN = duty NN %, s = stop"));
}

void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c >= '1' && c <= '4') applyFrequency(c - '1');
  else if (c == 'a') autoSweep();
  else if (c == 's') { setDuty(0); Serial.println(F("# stopped")); }
  else if (c == 'd') {
    float pct = Serial.parseFloat();
    setDuty(pct);
    Serial.println(F("freq,duty_pct,t_s,rpm"));
    holdAndLog(STEP_HOLD_S);
  }
}
