// Arduino Nano sketch
// Mikrobrytare kopplad mellan GND och D2 (normal open)
// Skickar "start" via USB när knappen trycks in

const int buttonPin = 2;   // D2
int buttonState = HIGH;    // startar som HIGH (normal open)

void setup() {
  pinMode(buttonPin, INPUT_PULLUP); // intern pull-up, så knappen drar till GND
  Serial.begin(9600);               // öppna USB-serial
}

void loop() {
  // Läs knappens status
  buttonState = digitalRead(buttonPin);

  // Om knappen trycks (går till LOW)
  if (buttonState == LOW) {
    Serial.println("start");   // skicka texten "start" till datorn
    delay(300);                // liten fördröjning för att undvika studs
  }
}
