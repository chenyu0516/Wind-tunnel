// fan_control.ino -- run the 4 x Delta QFR1212GHE 4-wire fans (option B), one layer
//
// The YYNMOS board only switches the fans on and off (low side, black lead).
// The speed is set by 25 kHz PWM on the fans' yellow wires, and fan 1
// reports its speed on the blue tach wire.
//
// Wiring (see the "QFR Fan Wiring" diagram):
//   every fan  RED    -> 5 A fuse -> +12 V rail
//              BLACK  -> the YYNMOS board OUTn-
//              YELLOW -> 1 kOhm -> D9, one resistor per fan
//   fan 1      BLUE   -> 1 kOhm -> D2      (other blue wires: tape off)
//   board IN1-4 joined -> A2, board signal GND -> Uno GND
//   board DC+ / DC- -> +12 V rail / GND rail;  Uno GND -> 12 V supply - (common ground)
//   hatch switch between D8 and GND (closed = hatch shut)
//   D10 shares Timer1 with D9: leave it unconnected.
//
// Rules this sketch keeps:
//   - Start: set the duty first, then power the board.
//   - Stop: release the yellow pin (high impedance) FIRST, then switch the board
//     off. A yellow pin driven LOW while a fan's ground floats would give the fan
//     a ground path through the Uno.
//   - Hatch open, a stalled fan or a hung sketch (watchdog) all stop the fans.
//   - During any reset all pins float: the board goes off and the fans stop.
//
// Serial Monitor at 115200 baud, line ending "Newline". Commands:
//   on        start the fans at the target duty
//   off       stop the fans (also: s)
//   d 45      set the target duty to 45 %  (works while running or stopped)
//   ?         print one status line now
// Status line every second:  t_s,state,duty_pct,target_pct,rpm_fan1,hatch
//
// Check before first use: TACH_PULSES_PER_REV (2 for most Delta fans; compare
// with a phone tachometer app once) and whether 0 % duty stops the fan or only
// slows it (many PWM fans keep a minimum speed; "off" always stops them).

#include <avr/wdt.h>

// ---- pins ----
const uint8_t PIN_PWM   = 9;      // OC1A = PB1, yellow wires of fans 1-4
const uint8_t PIN_EN    = A2;     // YYNMOS board inputs
const uint8_t PIN_TACH  = 2;      // INT0, fan 1 blue wire
const uint8_t PIN_HATCH = 8;      // LOW = hatch closed
const uint8_t PIN_LED   = 13;     // on while the fans are powered
const uint8_t PWM_PIN_MASK = _BV(PB1);

// ---- settings ----
const uint16_t PWM_TOP = 639;              // 16 MHz / (1 x 640) = 25 kHz
const uint8_t  TACH_PULSES_PER_REV = 2;
const uint16_t TACH_MIN_GAP_US = 1000;     // ignore noise; real gap >= 5 ms at 6000 rpm
const float    DEFAULT_TARGET_PCT = 30.0;
const float    START_DUTY_MAX_PCT = 30.0;  // start no higher than this, then ramp
const float    RAMP_PCT_PER_S = 10.0;      // gentle duty changes, no current surges
const bool     CHECK_STALL = true;         // set false if no tach wire is connected
const uint32_t STALL_GRACE_MS = 15000;     // fan soft start is 10 s
const float    STALL_MIN_DUTY_PCT = 20.0;  // only check above this duty
const uint16_t STALL_RPM = 300;
const uint16_t STATUS_PERIOD_MS = 1000;

// ---- state ----
enum State : uint8_t { STOPPED, RUNNING };
State state = STOPPED;
float targetPct = DEFAULT_TARGET_PCT;
float dutyPct = 0;
uint32_t startMs = 0;
uint32_t lastRampMs = 0;
uint32_t lastStatusMs = 0;
uint16_t rpm = 0;

volatile uint16_t tachCount = 0;
volatile uint32_t tachLastUs = 0;

char lineBuf[24];
uint8_t lineLen = 0;

// ---- tach ----
void onTach() {
  uint32_t now = micros();
  if (now - tachLastUs >= TACH_MIN_GAP_US) {
    tachLastUs = now;
    tachCount++;
  }
}

void updateRpm(uint16_t windowMs) {
  noInterrupts();
  uint16_t n = tachCount;
  tachCount = 0;
  interrupts();
  rpm = (uint32_t)n * 60000UL / windowMs / TACH_PULSES_PER_REV;
}

// ---- PWM on the yellow wires ----
void setupTimer1() {
  TCCR1A = _BV(WGM11);                              // fast PWM, TOP = ICR1 (mode 14)
  TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);     // no prescaler -> 25 kHz
  ICR1 = PWM_TOP;
  OCR1A = 0;
}

void writeDuty(float pct) {
  if (pct <= 0) {                                   // steady LOW, no 1-tick spikes
    TCCR1A &= ~_BV(COM1A1);
    PORTB &= ~PWM_PIN_MASK;
  } else {
    OCR1A = (uint16_t)(pct / 100.0 * PWM_TOP + 0.5);
    TCCR1A |= _BV(COM1A1);
  }
}

// Registers are used directly: digitalWrite() on D9 would switch the PWM off.
void drivePwmPin()   { DDRB |= PWM_PIN_MASK; }
void releasePwmPin() {                              // high impedance, no pull-up
  DDRB &= ~PWM_PIN_MASK;
  PORTB &= ~PWM_PIN_MASK;
}

// ---- start / stop ----
bool hatchOpen() { return digitalRead(PIN_HATCH) == HIGH; }

void startFans() {
  if (state == RUNNING) return;
  if (hatchOpen()) { Serial.println(F("# not started: hatch open")); return; }
  dutyPct = min(targetPct, START_DUTY_MAX_PCT);
  writeDuty(dutyPct);
  drivePwmPin();                                    // speed signal first
  digitalWrite(PIN_EN, HIGH);                       // then power
  startMs = lastRampMs = millis();
  rpm = 0;
  state = RUNNING;
  digitalWrite(PIN_LED, HIGH);
  Serial.println(F("# fans starting"));
}

void stopFans(const __FlashStringHelper *reason) {
  releasePwmPin();                                  // yellow wires first
  writeDuty(0);
  digitalWrite(PIN_EN, LOW);                        // then power off
  dutyPct = 0;
  bool wasRunning = (state == RUNNING);
  state = STOPPED;
  digitalWrite(PIN_LED, LOW);
  if (wasRunning) { Serial.print(F("# fans stopped: ")); Serial.println(reason); }
}

// ---- serial commands ----
void printStatus() {
  Serial.print(millis() / 1000); Serial.print(',');
  Serial.print(state == RUNNING ? F("on") : F("off")); Serial.print(',');
  Serial.print(dutyPct, 1); Serial.print(',');
  Serial.print(targetPct, 1); Serial.print(',');
  Serial.print(rpm); Serial.print(',');
  Serial.println(hatchOpen() ? F("open") : F("closed"));
}

void handleLine(char *s) {
  while (*s == ' ') s++;
  if (strcmp(s, "on") == 0) startFans();
  else if (strcmp(s, "off") == 0 || strcmp(s, "s") == 0) stopFans(F("command"));
  else if (strcmp(s, "?") == 0) printStatus();
  else if (s[0] == 'd') {
    float pct = atof(s + 1);
    targetPct = constrain(pct, 0, 100);
    Serial.print(F("# target duty ")); Serial.println(targetPct, 1);
  } else if (*s) {
    Serial.println(F("# commands: on, off, d NN, ?"));
  }
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      handleLine(lineBuf);
      lineLen = 0;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    }
  }
}

// ---- main ----
void setup() {
  uint8_t resetFlags = MCUSR;
  MCUSR = 0;
  wdt_disable();

  // Safe state before anything else: board off, yellow pin released.
  digitalWrite(PIN_EN, LOW);
  pinMode(PIN_EN, OUTPUT);
  releasePwmPin();
  setupTimer1();
  writeDuty(0);

  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_HATCH, INPUT_PULLUP);
  pinMode(PIN_TACH, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH), onTach, FALLING);

  Serial.begin(115200);
  if (resetFlags & _BV(WDRF)) Serial.println(F("# restarted by the watchdog; fans were stopped"));
  Serial.println(F("# fan_control ready. on, off, d NN, ?"));
  Serial.println(F("t_s,state,duty_pct,target_pct,rpm_fan1,hatch"));

  wdt_enable(WDTO_1S);                              // a hung sketch resets -> fans off
}

void loop() {
  wdt_reset();
  uint32_t now = millis();

  if (state == RUNNING && hatchOpen()) stopFans(F("hatch open"));

  readSerial();

  if (state == RUNNING) {
    // Ramp the duty toward the target.
    float step = RAMP_PCT_PER_S * (now - lastRampMs) / 1000.0;
    lastRampMs = now;
    if (dutyPct < targetPct) dutyPct = min(dutyPct + step, targetPct);
    else if (dutyPct > targetPct) dutyPct = max(dutyPct - step, targetPct);
    writeDuty(dutyPct);
  }

  if (now - lastStatusMs >= STATUS_PERIOD_MS) {
    updateRpm(now - lastStatusMs);
    lastStatusMs = now;

    if (CHECK_STALL && state == RUNNING && now - startMs > STALL_GRACE_MS &&
        dutyPct >= STALL_MIN_DUTY_PCT && rpm < STALL_RPM) {
      stopFans(F("fan 1 stalled or its tach wire is off"));
    }
    printStatus();
  }
}
