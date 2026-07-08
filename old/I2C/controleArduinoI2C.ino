/*
 * controleArduinoI2C - varre o barramento e atende comandos do Python.
 *
 * Arduino -> Python:  CONN;0xNN | DISC;0xNN | RESP;0xNN;0xRR;0xVV | OK;0xNN;... | ERR;0xNN;motivo
 * Python -> Arduino:  READ;0xNN;0xRR;n | WRITE;0xNN;0xRR;0xVV(;0xRR;0xVV...)
 * Uno: SDA=A4 SCL=A5 | Mega: SDA=20 SCL=21 | Baud 9600
 */

 #include <Wire.h>

 const unsigned long INTERVALO_MS = 1000;
 unsigned long ultimaVarredura = 0;
 bool presente[0x78];
 
 void setup() {
   Wire.begin();
   Serial.begin(9600);
   Serial.setTimeout(50);
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
   int achados = 0;
   for (byte addr = 0x08; addr <= 0x77; addr++) {
     Wire.beginTransmission(addr);
     bool achou = (Wire.endTransmission() == 0);
     if (achou) {
       achados++;
       avisa("CONN", addr);
     } else if (presente[addr]) {
       avisa("DISC", addr);
     }
     presente[addr] = achou;
   }
   if (achados == 0) {
     Serial.println("Nada encontrado i2c");
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
 void comandoEscrever(byte addr) {
   bool ok = true;
   char* sr = strtok(NULL, ";");
   
   while (sr != NULL) {
     char* sv = strtok(NULL, ";");
     if (!sv) break;
     
     byte reg = (byte)strtol(sr, NULL, 16);
     byte val;
     int tempoEspera = 2; // <<< Tempo padrão (default) de 2 milissegundos se não especificado
 
     // Se o valor começar com 'W' (ou 'T'), extrai o tempo customizado
     if (sv[0] == 'W' || sv[0] == 'w' || sv[0] == 'T' || sv[0] == 't') {
       char* posDoisPontos = strchr(sv, ':');
       if (posDoisPontos != NULL) {
         tempoEspera = atoi(sv + 1);          // Extrai o número após o caractere indicador
         val = (byte)strtol(posDoisPontos + 1, NULL, 16); // Converte o hex após os dois-pontos
       } else {
         val = (byte)strtol(sv, NULL, 16);
       }
     } else {
       // Se for um comando hexadecimal comum (ex: 0x34), processa normalmente
       val = (byte)strtol(sv, NULL, 16);
     }
 
     // Aplica o intervalo de tempo específico/default ANTES do envio físico
     if (tempoEspera > 0) {
       delay(tempoEspera);
     }
 
     Wire.beginTransmission(addr);
     if (reg == 0x00) {
       Wire.write(val);          // Escrita direta de 1 byte (Módulo LCD I2C)
     } else {
       Wire.write(reg);          // Registrador + valor (Sensores comuns)
       Wire.write(val);
     }
     if (Wire.endTransmission() != 0) ok = false;
     
     sr = strtok(NULL, ";");
   }
   
   if (ok) {
     Serial.print("OK;0x");
     imprimeHex(addr);
     Serial.println(";LISTA");
   } else {
     erro(addr, "falha na escrita");
   }
 }
 
 void processaComando(String linha) {
   linha.trim();
   if (linha.length() == 0) return;
 
   int tam = linha.length() + 1;
   char buf[tam];
   linha.toCharArray(buf, tam);
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
     if (!sa) return;
     comandoEscrever((byte)strtol(sa, NULL, 16));
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
 