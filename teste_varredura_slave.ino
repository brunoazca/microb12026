#include <Wire.h>

int enderecoI2C;

void setup() {
  Serial.begin(9600);
  
  randomSeed(analogRead(A0));
  
  enderecoI2C = random(8, 120);
  Wire.begin(enderecoI2C);
  
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  
  Serial.print("Endereço I2C definido para este run: 0x");
  Serial.println(enderecoI2C, HEX);
}

void loop() {
  delay(100);
}

void receiveEvent(int howMany) {
  while (Wire.available() > 0) {
    char c = Wire.read();
  }
}

void requestEvent() {
  Wire.write("ACK");
}
