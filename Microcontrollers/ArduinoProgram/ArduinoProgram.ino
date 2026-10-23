void setup() {
  Serial.begin(9600); // Communication port linked to ESP32-Cam TX (GPIO 14)
  
  
  pinMode(12, OUTPUT);
  // Initialize your motor driver pins here (e.g., L298N pins)
  // pinMode(IN1, OUTPUT);
  // pinMode(IN2, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Strip carriage returns and spaces

    if (command == "forward") {
      Serial.print("Forward");
      blinkLED();
      // Execute motor forward behavior
      // digitalWrite(IN1, HIGH);
      // digitalWrite(IN2, LOW);
    } 
    else if (command == "backward") {
      Serial.print("Backward");
      blinkLED();
      // Execute motor backward behavior
    } 
    else if (command == "left") {
      Serial.print("Left");
      blinkLED();
      // Execute turn left behavior
    } 
    else if (command == "right") {
      Serial.print("Right");
      blinkLED();
      // Execute turn right behavior
    } 
    else if (command == "stop") {
      Serial.print("Stop");
      blinkLED();
      // Execute stop behavior
      // digitalWrite(IN1, LOW);
      // digitalWrite(IN2, LOW);
    }
  }
}

void blinkLED() {
      digitalWrite(12, HIGH);  // change state of the LED by setting the pin to the HIGH voltage level
      delay(1000);                      // wait for a second
      digitalWrite(12, LOW);   // change state of the LED by setting the pin to the LOW voltage level
      delay(1000);  
}