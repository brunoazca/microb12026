"""
Leitura serial do Arduino que faz a varredura I2C.

Roda numa thread separada, lê as linhas do Arduino (protocolo CONN/DISC/SCAN/READY)
e coloca eventos numa fila (queue.Queue) que a GUI consome com janela.after().

Eventos colocados na fila (dicionários):
    {"tipo": "conn",   "endereco": "0x68", "nome": "MPU6050 ..."}
    {"tipo": "disc",   "endereco": "0x68"}
    {"tipo": "scan",   "n": 2}
    {"tipo": "status", "conectado": True/False, "msg": "..."}

Degrada com elegancia: se o pyserial nao estiver instalado ou a porta nao abrir,
emite um evento de status com a mensagem de erro em vez de quebrar a GUI.
"""

import threading
import queue
import time

try:
    import serial
    import serial.tools.list_ports as list_ports
    PYSERIAL_OK = True
except ImportError:
    serial = None
    list_ports = None
    PYSERIAL_OK = False


def listar_portas():
    """Retorna lista de (device, descricao) das portas seriais disponiveis."""
    if not PYSERIAL_OK:
        return []
    return [(p.device, p.description) for p in list_ports.comports()]


def autodetectar_porta():
    """Tenta adivinhar a porta do Arduino. Retorna o device ou None."""
    if not PYSERIAL_OK:
        return None
    candidatos = list_ports.comports()
    # prioriza portas com cara de Arduino / conversor USB-serial
    chaves = ("usbmodem", "usbserial", "arduino", "wch", "ch340", "ttyacm", "ttyusb")
    for p in candidatos:
        alvo = (p.device + " " + (p.description or "")).lower()
        if any(k in alvo for k in chaves):
            return p.device
    return candidatos[0].device if candidatos else None


class LeitorI2C(threading.Thread):
    """Thread que mantem a conexao serial e publica eventos numa fila."""

    def __init__(self, porta, fila, baud=9600):
        super().__init__(daemon=True)
        self.porta = porta
        self.baud = baud
        self.fila = fila
        self._parar = threading.Event()
        self._ser = None

    def parar(self):
        self._parar.set()

    def _status(self, conectado, msg):
        self.fila.put({"tipo": "status", "conectado": conectado, "msg": msg})

    def run(self):
        if not PYSERIAL_OK:
            self._status(False, "pyserial nao instalado (pip install pyserial)")
            return
        if not self.porta:
            self._status(False, "nenhuma porta selecionada")
            return

        while not self._parar.is_set():
            try:
                self._ser = serial.Serial(self.porta, self.baud, timeout=1)
                # Arduino reinicia ao abrir a serial; espera o boot
                time.sleep(2)
                self._status(True, "conectado em " + self.porta)
                self._loop_leitura()
            except Exception as e:  # porta sumiu, sem permissao, etc.
                self._status(False, "erro: " + str(e))
                # espera antes de tentar reconectar (a menos que seja para parar)
                if self._parar.wait(2):
                    break
            finally:
                self._fechar()

        self._status(False, "desconectado")

    def _loop_leitura(self):
        while not self._parar.is_set():
            linha = self._ser.readline()
            if not linha:
                continue  # timeout, so volta a checar o evento de parada
            try:
                texto = linha.decode("utf-8", errors="replace").strip()
            except Exception:
                continue
            if texto:
                self._processar(texto)

    def _processar(self, texto):
        partes = texto.split(";")
        tag = partes[0].strip().upper()

        if tag == "CONN" and len(partes) >= 2:
            nome = partes[2].strip() if len(partes) >= 3 else ""
            self.fila.put({"tipo": "conn", "endereco": _norm(partes[1]), "nome": nome})
        elif tag == "DISC" and len(partes) >= 2:
            self.fila.put({"tipo": "disc", "endereco": _norm(partes[1])})
        elif tag == "SCAN" and len(partes) >= 2:
            try:
                self.fila.put({"tipo": "scan", "n": int(partes[1])})
            except ValueError:
                pass
        # READY e linhas desconhecidas sao ignoradas

    def _fechar(self):
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None


def _norm(endereco):
    """Normaliza '0x68', '68', '0X68' -> '0x68' (2 digitos hex maiusculos)."""
    t = endereco.strip().lower()
    try:
        valor = int(t, 16)
        return "0x%02X" % valor
    except ValueError:
        return endereco.strip()
