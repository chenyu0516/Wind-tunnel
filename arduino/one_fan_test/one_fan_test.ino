// one_fan_test.ino -- minimum test of ONE QFR1212GHE 4-wire fan
//
// Wiring:
//   12V +  -> 5 A fuse -> fan RED
//   fan BLACK -> YYNMOS OUT1-   (or straight to 12V - without the board)
//   fan YELLOW -> 1 kOhm -> Uno D9     (25 kHz PWM, sets the speed)
//   fan BLUE   -> 1 kOhm -> Uno D2     (tach, reads the speed)
//   YYNMOS IN1 -> Uno A2,  YYNMOS signal GND -> Uno GND
//   YYNMOS DC+ / DC- -> 12V + / 12V -
//   Uno GND -> 12V -   (must have)
//
// Serial Monitor 115200 baud, line ending "Newline":
//   on      power the fan
//   off     stop the fan
//   d 50    set the speed to 50 %
// It prints "duty %, rpm" every second.

const uint8_t PIN_PWM  = 9;    // yellow wire (Timer1 OC1A)
const uint8_t PIN_EN   = A2;   // YYNMOS board input
const uint8_t PIN_TACH = 2;    // blue wire
const uint8_t PULSES_PER_REV = 2;

volatile uint16_t pulses = 0;
volatile uint32_t lastPulseUs = 0;
float duty = 30;
bool fanOn = false;

void onPulse() {
  uint32_t now = micros();
  if (now - lastPulseUs > 1000) { lastPulseUs = now; pulses++; }   // ignore noise
}

void setDuty(float pct) {
  duty = constrain(pct, 0, 100);
  OCR1A = (uint16_t)(duty / 100.0 * 639);
}

void fanStart() {
  pinMode(PIN_PWM, OUTPUT);        // speed signal first
  digitalWrite(PIN_EN, HIGH);      // then power
  fanOn = true;
  Serial.println(F("# fan on"));
}

void fanStop() {
  pinMode(PIN_PWM, INPUT);         // release the yellow wire first
  digitalWrite(PIN_EN, LOW);       // then power off
  fanOn = false;
  Serial.println(F("# fan off"));
}

void setup() {
  digitalWrite(PIN_EN, LOW);
  pinMode(PIN_EN, OUTPUT);
  pinMode(PIN_PWM, INPUT);         // released until "on"

  // Timer1: fast PWM, TOP = 639, no prescaler -> 25 kHz on D9
  TCCR1A = _BV(COM1A1) | _BV(WGM11);
  TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS10);
  ICR1 = 639;
  setDuty(duty);

  pinMode(PIN_TACH, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH), onPulse, FALLING);

  Serial.begin(115200);
  Serial.println(F("# one_fan_test: on, off, d NN"));
  Serial.println(F("duty_pct,rpm"));
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "on") fanStart();
    else if (cmd == "off") fanStop();
    else if (cmd.startsWith("d")) { setDuty(cmd.substring(1).toFloat()); Serial.print(F("# duty ")); Serial.println(duty); }
  }

  static uint32_t lastMs = 0;
  if (millis() - lastMs >= 1000) {
    lastMs += 1000;
    noInterrupts(); uint16_t n = pulses; pulses = 0; interrupts();
    Serial.print(fanOn ? duty : 0); Serial.print(',');
    Serial.println((uint32_t)n * 60 / PULSES_PER_REV);
  }
}
