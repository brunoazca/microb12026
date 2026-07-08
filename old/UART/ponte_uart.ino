
#define RX_PIN 19  // RX da Serial1 no Mega (referencia)


long compBaud = 9600;
int  compTimeout = 500;
char compModo = 'T';
String compComando = "";
bool serial1Aberta = false;

String linha = "";

void enviarLog(const String &msg) {
  Serial.print("LOG:");
  Serial.println(msg);
}

void enviarErro(const String &msg) {
  Serial.print("ERR:");
  Serial.println(msg);
}

void enviarRX(uint8_t *buf, int n) {
  Serial.print("RX:");
  for (int i = 0; i < n; i++) {
    if (buf[i] < 0x10) Serial.print('0');
    Serial.print(buf[i], HEX);
    if (i < n - 1) Serial.print(' ');
  }
  Serial.println();
}

// ---------- utilitarios ----------
int hexVal(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

void abrirSerial1() {
  if (serial1Aberta) Serial1.end();
  Serial1.begin(compBaud);
  serial1Aberta = true;
  enviarLog("Serial1 aberta @ " + String(compBaud));
}

void limparEntradaSerial1() {
  while (Serial1.available() > 0) Serial1.read();
}

void enviarTexto(String txt) {
  txt.replace("<CR>", "\r");
  txt.replace("<LF>", "\n");
  Serial1.print(txt);
}

bool enviarHex(String hexStr) {
  hexStr.replace(" ", "");
  if (hexStr.length() % 2 != 0) {
    enviarErro("hex com numero impar de digitos");
    return false;
  }
  for (unsigned int i = 0; i + 1 < hexStr.length(); i += 2) {
    int hi = hexVal(hexStr.charAt(i));
    int lo = hexVal(hexStr.charAt(i + 1));
    if (hi < 0 || lo < 0) {
      enviarErro("hex invalido");
      return false;
    }
    Serial1.write((uint8_t)(hi * 16 + lo));
  }
  return true;
}

void lerResposta(int &total, int &imprimiveis) {
  uint8_t buf[256];
  total = 0;
  imprimiveis = 0;
  unsigned long inicio = millis();
  while (millis() - inicio < (unsigned long)compTimeout) {
    while (Serial1.available() > 0 && total < 256) {
      uint8_t b = Serial1.read();
      buf[total++] = b;
      if ((b >= 0x20 && b <= 0x7E) || b == '\r' || b == '\n' || b == '\t')
        imprimiveis++;
    }
  }
  if (total > 0) enviarRX(buf, total);
}

void processarCFG(String args) {
  int p1 = args.indexOf('|');
  int p2 = args.indexOf('|', p1 + 1);
  int p3 = args.indexOf('|', p2 + 1);
  if (p1 < 0 || p2 < 0 || p3 < 0) {
    enviarErro("CFG malformado");
    return;
  }
  compBaud = args.substring(0, p1).toInt();
  compTimeout = args.substring(p1 + 1, p2).toInt();
  String m = args.substring(p2 + 1, p3);
  compModo = (m.length() > 0) ? m.charAt(0) : 'T';
  compComando = args.substring(p3 + 1);
  abrirSerial1();
}

void processarDETECT() {
  if (!serial1Aberta) { enviarErro("Serial1 fechada (envie CFG antes)"); return; }
  enviarLog("Detectando no baud " + String(compBaud) + "...");
  limparEntradaSerial1();
  if (compComando.length() > 0) {
    if (compModo == 'H') enviarHex(compComando);
    else enviarTexto(compComando);
  }
  int total, imprimiveis;
  lerResposta(total, imprimiveis);
  if (total == 0) {
    Serial.println("BAUD:NADA");
    enviarLog("Nenhuma resposta no baud " + String(compBaud));
  } else if (imprimiveis * 10 >= total * 7) {
    Serial.println("BAUD:OK");
    enviarLog("Resposta legivel — baud " + String(compBaud) + " parece correto");
  } else {
    Serial.println("BAUD:INCONCLUSIVO");
    enviarLog("Bytes recebidos mas nao-texto (baud pode estar errado)");
  }
}

void processarSEND(String args) {
  if (!serial1Aberta) { enviarErro("Serial1 fechada (envie CFG antes)"); return; }
  int p1 = args.indexOf('|');
  if (p1 < 0) { enviarErro("SEND malformado"); return; }
  char modo = args.substring(0, p1).charAt(0);
  String payload = args.substring(p1 + 1);
  limparEntradaSerial1();
  if (modo == 'H') {
    if (!enviarHex(payload)) return;
  } else {
    enviarTexto(payload);
  }
  int total, imprimiveis;
  lerResposta(total, imprimiveis);
  if (total == 0) enviarLog("Sem resposta do componente");
}

void processarLISTEN(String args) {
  if (!serial1Aberta) { enviarErro("Serial1 fechada (envie CFG antes)"); return; }
  long ms = args.toInt();
  enviarLog("Escutando por " + String(ms) + " ms...");
  uint8_t buf[256];
  int n = 0;
  unsigned long inicio = millis();
  while (millis() - inicio < (unsigned long)ms) {
    while (Serial1.available() > 0) {
      buf[n++] = Serial1.read();
      if (n >= 256) { enviarRX(buf, n); n = 0; }
    }
  }
  if (n > 0) enviarRX(buf, n);
  enviarLog("Fim da escuta");
}

void processarLinha(String l) {
  l.trim();
  if (l.length() == 0) return;
  if (l.startsWith("CFG|")) processarCFG(l.substring(4));
  else if (l == "DETECT") processarDETECT();
  else if (l.startsWith("SEND|")) processarSEND(l.substring(5));
  else if (l.startsWith("LISTEN|")) processarLISTEN(l.substring(7));
  else if (l == "STOP") {
    if (serial1Aberta) { Serial1.end(); serial1Aberta = false; }
    enviarLog("Serial1 fechada");
  } else {
    enviarErro("Comando desconhecido: " + l);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }
  enviarLog("Arduino pronto");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      processarLinha(linha);
      linha = "";
    } else if (c != '\r') {
      linha += c;
    }
  }
}
