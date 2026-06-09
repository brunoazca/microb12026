/*
 * Ligacao:
 *   Arduino Uno  -> SDA = A4, SCL = A5
 *   Arduino Mega -> SDA = 20, SCL = 21
 *   GND comum entre Arduino e o componente.
*/

#include <Wire.h>

void setup() {
  Wire.begin();
  Serial.begin(9600);
  varredura();
}

void varredura() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Escaneando");

  for (address = 0x08; address <= 0x77; address++) {
    
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    // endTransmission() retorna:
    //   0 = sucesso (slave respondeu ACK -> existe device aqui)
    //   1 = dados longos demais para o buffer
    //   2 = NACK no envio do endereco (ninguem respondeu)
    //   3 = NACK no envio dos dados
    //   4 = outro erro

    if (error == 0) {
      Serial.print("ACHOU 0x");
      if (address < 16) Serial.print('0');
      Serial.println(address, HEX);
      nDevices++;
    } else if (error == 4) {
      Serial.print("ERRO 0x");
      if (address < 16) Serial.print('0');
      Serial.println(address, HEX);
    }
  }

  Serial.print("Acabou; n_dispositivos=");
  Serial.println(nDevices);
}

