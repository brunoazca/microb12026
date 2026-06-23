/*
 *
 * Responsabilidade do Arduino: varrer o barramento, avisar conexao/desconexao
 * e atender comandos de leitura/escrita de registrador vindos do Python.
 * A identificacao e a exibicao ficam por conta do Python (lista_comps_i2c.py).
 *
 * Ligacao:
 *   Arduino Uno  -> SDA = A4, SCL = A5
 *   Arduino Mega -> SDA = 20, SCL = 21
 *   GND comum entre Arduino e o componente.
 *
 * Arduino -> Python:
 *   CONN;0xNN              -> apareceu um dispositivo no endereco 0xNN
 *   DISC;0xNN             -> o dispositivo do endereco 0xNN sumiu
 *   RESP;0xNN;0xRR;0xVV   -> leitura do registrador 0xRR devolveu 0xVV
 *   OK;0xNN;0xRR          -> escrita no registrador 0xRR concluida
 *   ERR;0xNN;motivo       -> erro
 *
 * Python -> Arduino:
 *   READ;0xNN;0xRR;n      -> ler n bytes a partir do registrador 0xRR
 *   WRITE;0xNN;0xRR;0xVV  -> escrever 0xVV no registrador 0xRR
 *
 * Baud: 9600
 */

#include <Wire.h>

const unsigned long INTERVALO_MS = 1000;  // periodo entre varreduras
unsigned long ultimaVarredura = 0;

bool presente[0x78];  // estado da varredura anterior (0x08..0x77)

void setup() {
  Wire.begin();
  Serial.begin(9600);
  Serial.setTimeout(50);  // readStringUntil nao trava o loop
  for (byte a = 0; a < 0x78; a++) presente[a] = false;
}

void imprimeHex(byte v) {
  if (v < 16) Serial.print('0');
  Serial.print(v, HEX);
}

void avisa(const char* evento, byte addr) {
  Serial.print(evento);
  Serial.print(";0x");
  imprimeHex(addr);
  Serial.println();
}

void erro(byte addr, const char* motivo) {
  Serial.print("ERR;0x");
  imprimeHex(addr);
  Serial.print(";");
  Serial.println(motivo);
}

void varredura() {
  for (byte addr = 0x08; addr <= 0x77; addr++) {
    Wire.beginTransmission(addr);
    bool achou = (Wire.endTransmission() == 0);  // 0 = ACK (existe device)

    if (achou && !presente[addr]) {
      avisa("CONN", addr);
    } else if (!achou && presente[addr]) {
      avisa("DISC", addr);
    }
    presente[addr] = achou;
  }
}

void comandoLer(byte addr, byte reg, int n) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) {  
    erro(addr, "sem ACK");
    return;
  }
  int lidos = Wire.requestFrom((int)addr, n);
  if (lidos < 1) {
    erro(addr, "sem resposta");
    return;
  }
  Serial.print("RESP;0x");
  imprimeHex(addr);
  Serial.print(";0x");
  imprimeHex(reg);
  Serial.print(";");
  for (int i = 0; i < lidos; i++) {
    if (i) Serial.print(",");
    Serial.print("0x");
    imprimeHex(Wire.read());
  }
  Serial.println();
}

void comandoEscrever(byte addr, byte reg, byte val) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  Wire.write(val);
  if (Wire.endTransmission() == 0) {
    Serial.print("OK;0x");
    imprimeHex(addr);
    Serial.print(";0x");
    imprimeHex(reg);
    Serial.println();
  } else {
    erro(addr, "falha na escrita");
  }
}

void processaComando(String linha) {
  linha.trim();
  if (linha.length() == 0) return;

  char buf[48];
  linha.toCharArray(buf, sizeof(buf));
  char* cmd = strtok(buf, ";");
  if (!cmd) return;

  if (strcmp(cmd, "READ") == 0) {
    char* sa = strtok(NULL, ";");
    char* sr = strtok(NULL, ";");
    char* sn = strtok(NULL, ";");
    if (!sa || !sr) return;
    int n = sn ? atoi(sn) : 1;
    if (n < 1) n = 1;
    comandoLer((byte)strtol(sa, NULL, 16), (byte)strtol(sr, NULL, 16), n);
  } else if (strcmp(cmd, "WRITE") == 0) {
    char* sa = strtok(NULL, ";");
    char* sr = strtok(NULL, ";");
    char* sv = strtok(NULL, ";");
    if (!sa || !sr || !sv) return;
    comandoEscrever((byte)strtol(sa, NULL, 16), (byte)strtol(sr, NULL, 16),
                    (byte)strtol(sv, NULL, 16));
  }
}

void loop() {
  if (Serial.available()) {
    processaComando(Serial.readStringUntil('\n'));
  }
  if (millis() - ultimaVarredura >= INTERVALO_MS) {
    ultimaVarredura = millis();
    varredura();
  }
}
