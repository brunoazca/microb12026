/*
 * Arduino unificado — I2C / UART / SPI para o terminal.py
 *
 * Uma unica placa (Arduino Mega) atende as tres interfaces. Nao existe
 * comando de "modo": o tipo e deduzido do proprio comando recebido, no
 * mesmo formato que cada aba do terminal ja usa hoje.
 *
 *   I2C  (Wire, SDA 20 / SCL 21)
 *     PC -> Arduino : READ;0xNN;0xRR;n
 *                     WRITE;0xNN;0xRR;0xVV(;0xRR;0xVV...)
 *     Arduino -> PC : CONN;0xNN | DISC;0xNN | RESP;... | OK;... | ERR;...
 *     Varre o barramento sozinho — apenas enquanto em modo I2C.
 *
 *   UART (ponte via Serial1, TX1 18 / RX1 19)
 *     PC -> Arduino : CFG|baud|timeout|modo|cmd | DETECT
 *                     SEND|modo|payload | LISTEN|ms | STOP
 *     Arduino -> PC : LOG:... | ERR:... | RX:hex | BAUD:OK/NADA/INCONCLUSIVO
 *
 *   SPI  (RC522, SS 53 / RST 5, HW SPI 50/51/52)
 *     PC -> Arduino : R 0xNN  (le registrador) | W 0xNN 0xVV (escreve)
 *     Arduino -> PC : SPI;0xNN;0xVV
 *
 * USB serial a 115200 para as tres interfaces (terminal.py usa o mesmo
 * baud para todas).
 */

#include <Wire.h>
#include <SPI.h>
#include <LiquidCrystal_I2C.h>  
#include <RotaryEncoder.h>

// ---------------- link USB ----------------
const long USB_BAUD = 115200;
String linha = "";
bool modoI2C = true;          // a varredura I2C so roda neste modo

// ---------------- LCD de display (I2C) ----------------
// Fica no mesmo barramento (SDA 20 / SCL 21). Este endereco e ISOLADO da
// varredura: nunca vira "componente detectado". Um segundo LCD para testar
// o I2C deve usar OUTRO endereco (ex.: 0x3F) para nao colidir no barramento.
const uint8_t LCD_ADDR = 0x27;
const uint8_t LCD_COLS = 16;
const uint8_t LCD_ROWS = 2;
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

// ---------------- Encoder ----------------
const byte ENC_A  = 2;   // CLK
const byte ENC_B  = 3;   // DT
const byte ENC_SW = 4;   // Botão

// Botão (debounce)
bool swUltimaLeitura = HIGH;
bool swEstado = HIGH;
unsigned long swUltimaMudanca = 0;
const unsigned long SW_DEBOUNCE = 40;

// Encoder
RotaryEncoder encoder(ENC_A, ENC_B);
long ultimaPosicao = 0;

// ---------------- helpers de hex (compartilhados) ----------------
void printHex2(byte v) {
  if (v < 16) Serial.print('0');
  Serial.print(v, HEX);
}

int hexVal(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

// ================================================================
//  I2C
// ================================================================
const unsigned long I2C_INTERVALO = 4000;
unsigned long i2cUltimaVarredura = 0;
bool i2cPresente[0x78];

void i2cAvisa(const char* evento, byte addr) {
  Serial.print(evento);
  Serial.print(";0x");
  printHex2(addr);
  Serial.println();
}

void i2cErro(byte addr, const char* motivo) {
  Serial.print("ERR;0x");
  printHex2(addr);
  Serial.print(";");
  Serial.println(motivo);
}

void i2cVarredura() {
  for (byte addr = 0x08; addr <= 0x77; addr++) {
    if (addr == LCD_ADDR) continue;   // isola o LCD de display da deteccao
    Wire.beginTransmission(addr);
    bool achou = (Wire.endTransmission() == 0);
    if (achou) i2cAvisa("CONN", addr);
    else if (i2cPresente[addr]) i2cAvisa("DISC", addr);
    i2cPresente[addr] = achou;
  }
}

void i2cLer(byte addr, byte reg, int n) {
  Wire.beginTransmission(addr);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) { i2cErro(addr, "sem ACK"); return; }
  int lidos = Wire.requestFrom((int)addr, n);
  if (lidos < 1) { i2cErro(addr, "sem resposta"); return; }
  Serial.print("RESP;0x");
  printHex2(addr);
  Serial.print(";0x");
  printHex2(reg);
  Serial.print(";");
  for (int i = 0; i < lidos; i++) {
    if (i) Serial.print(",");
    Serial.print("0x");
    printHex2(Wire.read());
  }
  Serial.println();
}

// continua o strtok iniciado em i2cComando (o buffer ainda esta vivo)
void i2cEscrever(byte addr) {
  bool ok = true;
  char* sr = strtok(NULL, ";");
  while (sr != NULL) {
    char* sv = strtok(NULL, ";");
    if (!sv) break;

    byte reg = (byte)strtol(sr, NULL, 16);
    byte val;
    int espera = 2;   // tempo padrao entre escritas (ms)

    // valor pode vir com prefixo de espera: "W15:0x38" / "T5:0x28"
    if (sv[0] == 'W' || sv[0] == 'w' || sv[0] == 'T' || sv[0] == 't') {
      char* dp = strchr(sv, ':');
      if (dp) { espera = atoi(sv + 1); val = (byte)strtol(dp + 1, NULL, 16); }
      else      val = (byte)strtol(sv, NULL, 16);
    } else      val = (byte)strtol(sv, NULL, 16);

    if (espera > 0) delay(espera);

    Wire.beginTransmission(addr);
    if (reg == 0x00) Wire.write(val);           // escrita direta (LCD I2C)
    else { Wire.write(reg); Wire.write(val); }   // registrador + valor
    if (Wire.endTransmission() != 0) ok = false;

    sr = strtok(NULL, ";");
  }
  if (ok) { Serial.print("OK;0x"); printHex2(addr); Serial.println(";LISTA"); }
  else i2cErro(addr, "falha na escrita");
}

void i2cComando(String l) {
  int tam = l.length() + 1;
  char buf[tam];
  l.toCharArray(buf, tam);
  char* cmd = strtok(buf, ";");
  if (!cmd) return;

  if (strcmp(cmd, "READ") == 0) {
    char* sa = strtok(NULL, ";");
    char* sr = strtok(NULL, ";");
    char* sn = strtok(NULL, ";");
    if (!sa || !sr) return;
    int n = sn ? atoi(sn) : 1;
    if (n < 1) n = 1;
    i2cLer((byte)strtol(sa, NULL, 16), (byte)strtol(sr, NULL, 16), n);
  } else if (strcmp(cmd, "WRITE") == 0) {
    char* sa = strtok(NULL, ";");
    if (!sa) return;
    i2cEscrever((byte)strtol(sa, NULL, 16));
  }
}

// ================================================================
//  UART (ponte Serial1)
// ================================================================
long uartBaud = 9600;
int  uartTimeout = 500;
char uartModo = 'T';
String uartCmdBoot = "";
bool uartAberta = false;

void uartLog(const String &m) { Serial.print("LOG:"); Serial.println(m); }
void uartErr(const String &m) { Serial.print("ERR:"); Serial.println(m); }

void uartRX(uint8_t *buf, int n) {
  Serial.print("RX:");
  for (int i = 0; i < n; i++) {
    printHex2(buf[i]);
    if (i < n - 1) Serial.print(' ');
  }
  Serial.println();
}

void uartAbrir() {
  if (uartAberta) Serial1.end();
  Serial1.begin(uartBaud);
  uartAberta = true;
  uartLog("Serial1 aberta @ " + String(uartBaud));
}

void uartLimpar() { while (Serial1.available() > 0) Serial1.read(); }

void uartTexto(String t) {
  t.replace("<CR>", "\r");
  t.replace("<LF>", "\n");
  Serial1.print(t);
}

bool uartHex(String h) {
  h.replace(" ", "");
  if (h.length() % 2 != 0) { uartErr("hex com numero impar de digitos"); return false; }
  for (unsigned int i = 0; i + 1 < h.length(); i += 2) {
    int hi = hexVal(h.charAt(i));
    int lo = hexVal(h.charAt(i + 1));
    if (hi < 0 || lo < 0) { uartErr("hex invalido"); return false; }
    Serial1.write((uint8_t)(hi * 16 + lo));
  }
  return true;
}

void uartLerResposta(int &total, int &legiveis) {
  uint8_t buf[256];
  total = 0;
  legiveis = 0;
  unsigned long ini = millis();
  while (millis() - ini < (unsigned long)uartTimeout) {
    while (Serial1.available() > 0 && total < 256) {
      uint8_t b = Serial1.read();
      buf[total++] = b;
      if ((b >= 0x20 && b <= 0x7E) || b == '\r' || b == '\n' || b == '\t') legiveis++;
    }
  }
  if (total > 0) uartRX(buf, total);
}

void uartCFG(String a) {
  int p1 = a.indexOf('|');
  int p2 = a.indexOf('|', p1 + 1);
  int p3 = a.indexOf('|', p2 + 1);
  if (p1 < 0 || p2 < 0 || p3 < 0) { uartErr("CFG malformado"); return; }
  uartBaud = a.substring(0, p1).toInt();
  uartTimeout = a.substring(p1 + 1, p2).toInt();
  String m = a.substring(p2 + 1, p3);
  uartModo = (m.length() > 0) ? m.charAt(0) : 'T';
  uartCmdBoot = a.substring(p3 + 1);
  uartAbrir();
}

void uartDETECT() {
  if (!uartAberta) { uartErr("Serial1 fechada (envie CFG antes)"); return; }
  uartLog("Detectando no baud " + String(uartBaud) + "...");
  uartLimpar();
  if (uartCmdBoot.length() > 0) {
    if (uartModo == 'H') uartHex(uartCmdBoot);
    else uartTexto(uartCmdBoot);
  }
  int total, leg;
  uartLerResposta(total, leg);
  if (total == 0) {
    Serial.println("BAUD:NADA");
    uartLog("Nenhuma resposta no baud " + String(uartBaud));
  } else if (leg * 10 >= total * 7) {
    Serial.println("BAUD:OK");
    uartLog("Resposta legivel — baud " + String(uartBaud) + " parece correto");
  } else {
    Serial.println("BAUD:INCONCLUSIVO");
    uartLog("Bytes recebidos mas nao-texto (baud pode estar errado)");
  }
}

void uartSEND(String a) {
  if (!uartAberta) { uartErr("Serial1 fechada (envie CFG antes)"); return; }
  int p1 = a.indexOf('|');
  if (p1 < 0) { uartErr("SEND malformado"); return; }
  char modo = a.substring(0, p1).charAt(0);
  String payload = a.substring(p1 + 1);
  uartLimpar();
  if (modo == 'H') { if (!uartHex(payload)) return; }
  else uartTexto(payload);
  int total, leg;
  uartLerResposta(total, leg);
  if (total == 0) uartLog("Sem resposta do componente");
}

void uartLISTEN(String a) {
  if (!uartAberta) { uartErr("Serial1 fechada (envie CFG antes)"); return; }
  long ms = a.toInt();
  uartLog("Escutando por " + String(ms) + " ms...");
  uint8_t buf[256];
  int n = 0;
  unsigned long ini = millis();
  while (millis() - ini < (unsigned long)ms) {
    while (Serial1.available() > 0) {
      buf[n++] = Serial1.read();
      if (n >= 256) { uartRX(buf, n); n = 0; }
    }
  }
  if (n > 0) uartRX(buf, n);
  uartLog("Fim da escuta");
}

void uartSTOP() {
  if (uartAberta) { Serial1.end(); uartAberta = false; }
  uartLog("Serial1 fechada");
}

// ================================================================
//  SPI (RC522)
// ================================================================
const int SPI_SS = 53;
const int SPI_RST = 5;
SPISettings spiCfg(4000000, MSBFIRST, SPI_MODE0);

byte spiTransfere(byte comando, byte dado) {
  SPI.beginTransaction(spiCfg);
  digitalWrite(SPI_SS, LOW);
  SPI.transfer(comando);
  byte r = SPI.transfer(dado);
  digitalWrite(SPI_SS, HIGH);
  SPI.endTransaction();
  return r;
}

// formatos aceitos: "R 0xNN", "W 0xNN 0xVV" ou so "0xNN" (leitura)
void spiComando(String l) {
  l.trim();
  char op = 'R';
  int i = 0;
  if (l.length() && (l[0] == 'R' || l[0] == 'r' || l[0] == 'W' || l[0] == 'w')) {
    op = toupper(l[0]);
    i = 1;
  }

  byte reg = 0, val = 0;
  int achados = 0;
  while (i < (int)l.length() && achados < 2) {
    while (i < (int)l.length() && l[i] == ' ') i++;
    if (i >= (int)l.length()) break;
    int j = i;
    while (j < (int)l.length() && l[j] != ' ') j++;
    byte v = (byte)strtol(l.substring(i, j).c_str(), NULL, 16);
    if (achados == 0) reg = v; else val = v;
    achados++;
    i = j;
  }
  if (achados == 0) { Serial.println("ERR;SPI;sem registrador"); return; }

  if (op == 'W') {
    spiTransfere((reg << 1) & 0x7E, val);       // RC522: bit0=0 escreve
    Serial.print("SPI;0x"); printHex2(reg); Serial.println(";OK");
  } else {
    byte r = spiTransfere((reg << 1) | 0x80, 0x00);  // RC522: MSB=1 le
    Serial.print("SPI;0x"); printHex2(reg);
    Serial.print(";0x"); printHex2(r);
    Serial.println();
  }
}

// ================================================================
//  LCD de display + botao
// ================================================================

void lcdMostrar(const String &cima, const String &baixo) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(cima.substring(0, LCD_COLS));
  lcd.setCursor(0, 1);
  lcd.print(baixo.substring(0, LCD_COLS));
}

// payload (depois de "LCD:") usa "\n" literal como separador das duas linhas
void lcdComando(String p) {
  int q = p.indexOf("\\n");
  if (q >= 0) lcdMostrar(p.substring(0, q), p.substring(q + 2));
  else        lcdMostrar(p, "");
}

void tickDoEncoder() {
  encoder.tick();
}

void lerEncoder() {
  long posicao = encoder.getPosition();

  if (posicao != ultimaPosicao) {
    if (posicao > ultimaPosicao)
      Serial.println("ENC;CW");
    else
      Serial.println("ENC;CCW");

    ultimaPosicao = posicao;
  }

  // Trata botão (debounce)
  bool leitura = digitalRead(ENC_SW);

  if (leitura != swUltimaLeitura) {
    swUltimaMudanca = millis();
    swUltimaLeitura = leitura;
  }

  if (millis() - swUltimaMudanca >= SW_DEBOUNCE) {
    if (leitura != swEstado) {
      swEstado = leitura;

      if (swEstado == LOW) {
        Serial.println("BTN");
      }
    }
  }
}

// ================================================================
//  Dispatcher + setup/loop
// ================================================================
void processaLinha(String l) {
  l.trim();
  if (!l.length()) return;

  // controle vindo do Python (nao pertence a nenhuma das tres interfaces)
  if (l.startsWith("MODE|")) {                          // define a interface ativa
    bool i2c = (l.substring(5) == "i2c");
    if (i2c && !modoI2C)                                // ao (re)entrar em I2C,
      for (int a = 0; a < 0x78; a++) i2cPresente[a] = false;  // forca re-anuncio
    modoI2C = i2c;
    return;
  }
  if (l.startsWith("LCD:")) { lcdComando(l.substring(4)); return; }
  if (l == "LCDCLEAR")      { lcd.clear();                return; }

  // UART: prefixos proprios da ponte
  if (l.startsWith("CFG|"))    { uartCFG(l.substring(4));    return; }
  if (l == "DETECT")           { uartDETECT();               return; }
  if (l.startsWith("SEND|"))   { uartSEND(l.substring(5));   return; }
  if (l.startsWith("LISTEN|")) { uartLISTEN(l.substring(7)); return; }
  if (l == "STOP")             { uartSTOP();                 return; }

  // I2C: READ / WRITE
  if (l.startsWith("READ;") || l.startsWith("WRITE;")) { i2cComando(l); return; }

  // padrao: registrador SPI
  spiComando(l);
}

void setup() {
  Serial.begin(USB_BAUD);

  // I2C
  Wire.begin();
  for (int a = 0; a < 0x78; a++) i2cPresente[a] = false;

  // LCD de display
  lcd.init();
  lcd.backlight();
  lcdMostrar("Arduino", "iniciando...");

  // encoder
  pinMode(ENC_SW, INPUT_PULLUP);
  int origem1 = digitalPinToInterrupt(ENC_A); 
  int origem2 = digitalPinToInterrupt(ENC_B); 
  attachInterrupt(origem1, tickDoEncoder, CHANGE); 
  attachInterrupt(origem2, tickDoEncoder, CHANGE); 

  // SPI / RC522
  pinMode(SPI_SS, OUTPUT);
  pinMode(SPI_RST, OUTPUT);
  digitalWrite(SPI_SS, HIGH);
  digitalWrite(SPI_RST, LOW);  delay(10);
  digitalWrite(SPI_RST, HIGH); delay(50);
  SPI.begin();

  lcdMostrar("Pronto.", "Ligue o py");

  // UART: Serial1 so e aberta quando chega um CFG
  Serial.println("RDY");   // avisa o Python; ele responde com MODE|... e LCD:...
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') { processaLinha(linha); linha = ""; }
    else if (c != '\r') linha += c;
  }

  lerEncoder();

  if (modoI2C && millis() - i2cUltimaVarredura >= I2C_INTERVALO) {
    i2cUltimaVarredura = millis();
    i2cVarredura();
  }
}
