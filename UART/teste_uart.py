import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import subprocess
import sys

try:
    import serial
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False

JSON_PATH = "componentes_uart.json"

USB_BAUD = 115200

BAUDS_PADRAO = ["300", "600", "1200", "2400", "4800", "9600",
                "19200", "38400", "57600", "115200", "230400"]

PROTO_ENVIA = ("AT", "binario")

BOOT_ARDUINO = 1.5

if len(sys.argv) > 1:
    indice = int(sys.argv[1])
else:
    indice = None

with open(JSON_PATH, "r", encoding="utf-8") as f:
    comp = json.load(f)[indice]

janela = tk.Tk()
janela.title("Teste de Componente UART")
janela.geometry("500x640")

ttk.Label(janela, text="Teste de Componente UART",
          font=("Segoe UI", 16, "bold")).pack(pady=(15, 5))

proto = comp.get("tipo_protocolo", "?")
info = ttk.Label(janela, font=("Segoe UI", 10),
                 text=f"{comp.get('nome', '?')}  |  protocolo: {proto}  |  "
                      f"frame: {comp.get('frame', '?')}  |  "
                      f"nível: {comp.get('nivel_logico', '?')}")
info.pack(pady=(0, 8))

conexao = ttk.LabelFrame(janela, text="Conexão (Arduino)")
conexao.pack(fill="x", padx=15, pady=5)

ttk.Label(conexao, text="Porta:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
porta = ttk.Entry(conexao, width=12)
porta.insert(0, "COM3")
porta.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(conexao, text="Baud comp.:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
bauds = []
b0 = str(comp.get("baud", ""))
if b0 and b0 != "0":
    bauds.append(b0)
for p in BAUDS_PADRAO:
    if p not in bauds:
        bauds.append(p)
baud = ttk.Combobox(conexao, width=10, values=bauds)
baud.set(bauds[0] if bauds else "9600")
baud.grid(row=0, column=3, padx=5, pady=5, sticky="w")

# --- Ações ---
acoes = ttk.LabelFrame(janela, text="Ações")
acoes.pack(fill="x", padx=15, pady=5)

# --- Envio de comandos ---
terminal = ttk.LabelFrame(janela, text="Envio de comandos")
terminal.pack(fill="x", padx=15, pady=5)

modo = tk.StringVar(value="hex" if proto == "binario" else "texto")
ttk.Radiobutton(terminal, text="Texto", variable=modo, value="texto").grid(row=0, column=0, padx=5, pady=5)
ttk.Radiobutton(terminal, text="Hex", variable=modo, value="hex").grid(row=0, column=1, padx=5, pady=5)
crlf = tk.BooleanVar(value=True)
ttk.Checkbutton(terminal, text="CR+LF (texto)", variable=crlf).grid(row=0, column=2, padx=5, pady=5)

entrada = ttk.Combobox(terminal, width=38, values=list(comp.get("comandos", {}).values()))
entrada.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="we")

aviso_envio = ttk.Label(terminal, text="", foreground="#888888")
aviso_envio.grid(row=2, column=0, columnspan=4, pady=(0, 4))

log_frame = ttk.LabelFrame(janela, text="Log")
log_frame.pack(fill="both", expand=True, padx=15, pady=5)
log = tk.Text(log_frame, height=10, state="disabled", wrap="word")
scroll = ttk.Scrollbar(log_frame, command=log.yview)
log.configure(yscrollcommand=scroll.set)
log.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")
log.tag_config("tx", foreground="#0066cc")
log.tag_config("rx", foreground="#008800")
log.tag_config("status", foreground="#888888")
log.tag_config("erro", foreground="#cc0000")
log.tag_config("ok", foreground="#008800")


def escrever(msg, tag=""):
    ts = time.strftime("%H:%M:%S")
    log.config(state="normal")
    log.insert(tk.END, f"[{ts}] {msg}\n", tag)
    log.see(tk.END)
    log.config(state="disabled")


def limpar_log():
    log.config(state="normal")
    log.delete("1.0", tk.END)
    log.config(state="disabled")


def esperar(seg):
    fim = time.time() + seg
    while time.time() < fim:
        janela.update()
        time.sleep(0.02)


def envia_comandos():
    return proto in PROTO_ENVIA


def monta_cfg():
    cmd = ""
    cmds = list(comp.get("comandos", {}).values())
    if proto in PROTO_ENVIA and cmds:
        cmd = cmds[0]
    m = "H" if proto == "binario" else "T"
    return f"CFG|{baud.get().strip()}|{comp.get('timeout', 500)}|{m}|{cmd}\n"


def mostrar_rx_hex(hex_str):
    try:
        dados = bytes.fromhex(hex_str.replace(" ", ""))
    except ValueError:
        escrever(f"RX (hex inválido): {hex_str}", "rx")
        return
    imprimiveis = sum(1 for x in dados if 0x20 <= x <= 0x7E or x in (9, 10, 13))
    if dados and imprimiveis >= len(dados) * 0.7:
        texto = dados.decode("ascii", errors="replace").strip()
        escrever(f"RX: {texto}   [{hex_str}]", "rx")
    else:
        escrever(f"RX: [{hex_str}]", "rx")


def processar_linha(linha):
    if linha.startswith("RX:"):
        mostrar_rx_hex(linha[3:].strip())
    elif linha.startswith("LOG:"):
        escrever(linha[4:].strip(), "status")
    elif linha.startswith("ERR:"):
        escrever("ERRO: " + linha[4:].strip(), "erro")
    elif linha.startswith("BAUD:"):
        v = linha[5:].strip()
        if v == "OK":
            escrever("BAUD OK - resposta legível recebida.", "ok")
        elif v == "NADA":
            escrever("BAUD: nenhuma resposta.", "erro")
        else:
            escrever("BAUD inconclusivo - bytes não-texto.", "erro")
    else:
        escrever(linha, "status")


def executar(linhas_envio, janela_leitura):
    if not SERIAL_OK:
        messagebox.showerror("Erro", "pyserial não está instalado.\nRode: pip install pyserial")
        return
    p = porta.get().strip()
    if not p:
        messagebox.showwarning("Dados inválidos", "Informe a porta do Arduino (ex: COM3).")
        return
    if not baud.get().strip().isdigit():
        messagebox.showwarning("Dados inválidos", "Baud do componente deve ser um número.")
        return
    try:
        ser = serial.Serial(p, USB_BAUD, timeout=0.1)
    except Exception as e:
        escrever(f"Falha ao abrir {p}: {e}", "erro")
        messagebox.showerror("Erro de conexão", str(e))
        return

    escrever(f"Abrindo {p}, aguardando o Arduino...", "status")
    esperar(BOOT_ARDUINO)
    try:
        ser.reset_input_buffer()
        ser.write(monta_cfg().encode("ascii", errors="replace"))
        esperar(0.4)
        for l in linhas_envio:
            ser.write(l.encode("ascii", errors="replace"))
        buf = b""
        fim = time.time() + janela_leitura
        while time.time() < fim:
            n = ser.in_waiting
            if n:
                buf += ser.read(n)
            else:
                esperar(0.02)
    except Exception as e:
        escrever(f"Erro na comunicação: {e}", "erro")
        buf = b""
    finally:
        try:
            ser.close()
        except Exception:
            pass

    for bruta in buf.split(b"\n"):
        texto = bruta.decode("ascii", errors="replace").strip()
        if texto:
            processar_linha(texto)


def verificar_linha():
    executar(["IDLE\n"], 0.6)


def detectar():
    janela_leitura = comp.get("timeout", 500) / 1000.0 + 0.6
    executar(["DETECT\n"], janela_leitura)


def escutar():
    ms = comp.get("timeout", 2000)
    executar([f"LISTEN|{ms}\n"], ms / 1000.0 + 0.6)


def enviar_manual():
    if not envia_comandos():
        return
    valor = entrada.get()
    if not valor:
        return
    if modo.get() == "hex":
        m = "H"
        try:
            bytes.fromhex(valor.replace(" ", ""))
        except ValueError:
            messagebox.showwarning("Hex inválido", "Use bytes hex, ex: FF 01 86")
            return
        payload = valor
        escrever("TX: [" + valor + "]", "tx")
    else:
        m = "T"
        payload = valor
        if "<CR>" not in valor and "<LF>" not in valor and crlf.get():
            payload = valor + "<CR><LF>"
        escrever(f"TX: {valor}", "tx")
    janela_leitura = comp.get("timeout", 500) / 1000.0 + 0.6
    executar([f"SEND|{m}|{payload}\n"], janela_leitura)
    entrada.set("")


def voltar():
    subprocess.Popen([sys.executable, "lista_comps_uart.py"])
    janela.destroy()


tk.Button(acoes, text="Detectar baud", command=detectar).grid(row=0, column=0, padx=5, pady=6)
tk.Button(acoes, text="Verificar linha", command=verificar_linha).grid(row=0, column=1, padx=5, pady=6)
tk.Button(acoes, text="Escutar", command=escutar).grid(row=0, column=2, padx=5, pady=6)

btn_enviar = tk.Button(terminal, text="Enviar", command=enviar_manual)
btn_enviar.grid(row=1, column=3, padx=5, pady=5)
entrada.bind("<Return>", lambda e: enviar_manual())

if not envia_comandos():
    btn_enviar.config(state="disabled")
    aviso_envio.config(text=f"Protocolo '{proto}' não envia comandos (use Escutar).")

# rodapé
rodape = ttk.Frame(janela)
rodape.pack(pady=8)
tk.Button(rodape, text="Limpar log", command=limpar_log).grid(row=0, column=0, padx=5)
tk.Button(rodape, text="Voltar", command=voltar).grid(row=0, column=1, padx=5)

if not SERIAL_OK:
    escrever("pyserial não instalado. Rode: pip install pyserial", "erro")

janela.mainloop()
