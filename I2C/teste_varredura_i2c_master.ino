/*
 * Varredura I2C continua + protocolo serial para o Python.
 *
 * Ligacao:
 *   Arduino Uno  -> SDA = A4, SCL = A5
 *   Arduino Mega -> SDA = 20, SCL = 21
 *   GND comum entre Arduino e o componente.
 *
 * Protocolo serial (uma mensagem por linha, campos separados por ';'):
 *   READY                 -> enviado uma vez ao ligar
 *   CONN;0xNN;nome        -> um dispositivo novo apareceu no endereco 0xNN
 *   DISC;0xNN             -> o dispositivo do endereco 0xNN sumiu
 *   SCAN;n                -> heartbeat: terminou uma varredura, n dispositivos presentes
 *
 * Baud: 9600
 */

#include <Wire.h>

const unsigned long INTERVALO_MS = 1000;  // periodo entre varreduras
unsigned long ultimaVarredura = 0;

// presente[addr] guarda o estado da varredura anterior (0x08..0x77).
bool presente[0x78];

void setup() {
  Wire.begin();
  Serial.begin(9600);
  for (byte a = 0; a < 0x78; a++) presente[a] = false;
  Serial.println("READY");
}

const char* nomeProvavel(byte addr) {
  switch (addr) {
    case 0x0C: case 0x0D: case 0x0F:
      return "MLX90393 (magnetometro)";
    case 0x0E:
      return "MAG3110 / MLX90393 (magnetometro)";
    case 0x10:
      return "VEML7700 (luz) / VEML6075 (UV)";
    case 0x11:
      return "Si4713 (transmissor FM)";
    case 0x13:
      return "VCNL4000 (proximidade)";
    case 0x18: case 0x19:
      return "LIS3DH (acelerometro) / MCP9808 (temp)";
    case 0x1A: case 0x1B: case 0x1C: case 0x1F:
      return "MCP9808 (temperatura)";
    case 0x1D:
      return "ADXL345 (acelerometro) / LSM303";
    case 0x1E:
      return "HMC5883L (bussola) / LSM303 (magnet.)";
    case 0x20: case 0x21: case 0x22: case 0x24:
    case 0x25: case 0x26:
      return "MCP23017/23008 (expansor IO) ou LCD PCF8574";
    case 0x23:
      return "BH1750 (luz) ou expansor MCP23017";
    case 0x27:
      return "LCD I2C backpack PCF8574 (0x27) ou MCP23017";
    case 0x28: case 0x29:
      return "BNO055 (IMU) / TSL2561 / VL53L0X (ToF)";
    case 0x38:
      return "AHT10/AHT20 (umid/temp) / FT6206 (touch)";
    case 0x39:
      return "APDS9960 (gesto/cor) / TSL2561 (luz)";
    case 0x3C: case 0x3D:
      return "Display OLED SSD1306 / SH1106";
    case 0x3F:
      return "LCD I2C backpack PCF8574A (0x3F)";
    case 0x40:
      return "PCA9685 (PWM) / INA219 / Si7021 / HTU21D";
    case 0x41: case 0x42: case 0x43: case 0x44:
    case 0x45: case 0x46: case 0x47:
      return "INA219 (corrente) / PCA9685 (PWM)";
    case 0x48: case 0x49: case 0x4A: case 0x4B:
      return "ADS1115 (ADC) / TMP102/TMP117 (temp)";
    case 0x4C: case 0x4D: case 0x4E: case 0x4F:
      return "PCF8591 (ADC/DAC) / INA219";
    case 0x50: case 0x51: case 0x52: case 0x53:
    case 0x54: case 0x55: case 0x56:
      return "EEPROM 24LCxx / AT24Cxx";
    case 0x57:
      return "EEPROM AT24C32 (em modulos RTC) / MAX3010x";
    case 0x58:
      return "SGP30 (gas)";
    case 0x5A:
      return "MLX90614 (temp IR) / CCS811 / MPR121";
    case 0x5C:
      return "BH1750 (luz) / AM2320 (umid/temp)";
    case 0x60:
      return "MCP4725 (DAC) / MCP9600 / Si5351";
    case 0x61:
      return "SCD30 (CO2) / MCP4725 (DAC)";
    case 0x62: case 0x63: case 0x64:
    case 0x65: case 0x66: case 0x67:
      return "MCP4725 (DAC) / MCP9600 (termopar)";
    case 0x68:
      return "MPU6050 (IMU) ou RTC DS1307/DS3231";
    case 0x69:
      return "MPU6050/MPU9250 (IMU)";
    case 0x6A: case 0x6B:
      return "LSM6DS / L3GD20 (giroscopio)";
    case 0x70: case 0x71: case 0x72: case 0x73:
    case 0x74: case 0x75:
      return "PCA9685 (PWM) / TCA9548A (mux) / HT16K33";
    case 0x76: case 0x77:
      return "BMP280/BME280/BMP180 (pressao/temp)";
    default:
      return "desconhecido (cadastrar manualmente)";
  }
}

void imprimeEndereco(byte addr) {
  Serial.print("0x");
  if (addr < 16) Serial.print('0');
  Serial.print(addr, HEX);
}

void varredura() {
  byte error, address;
  int nDevices = 0;

  for (address = 0x08; address <= 0x77; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    // 0 = ACK (existe device) | 2 = NACK (vazio) | 4 = outro erro
    bool achou = (error == 0);

    if (achou) nDevices++;

    if (achou && !presente[address]) {
      // dispositivo novo -> avisa o Python
      Serial.print("CONN;");
      imprimeEndereco(address);
      Serial.print(";");
      Serial.println(nomeProvavel(address));
    } else if (!achou && presente[address]) {
      // dispositivo sumiu
      Serial.print("DISC;");
      imprimeEndereco(address);
      Serial.println();
    }

    presente[address] = achou;
  }

  Serial.print("SCAN;");
  Serial.println(nDevices);
}

void loop() {
  unsigned long agora = millis();
  if (agora - ultimaVarredura >= INTERVALO_MS) {
    ultimaVarredura = agora;
    varredura();
  }
}
