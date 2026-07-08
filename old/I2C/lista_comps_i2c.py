import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from functools import partial
import json
import formulario_i2c

try:
    import serial
    from serial.tools import list_ports
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False

ARQUIVO = "componentes_i2c.json"
BAUD = 9600

janela = tk.Tk()
janela.title("Seleção de Componentes I2C")
janela.geometry("480x780")

selecionados = []

def carregar():
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def recarregar_lista():
    """Relê o JSON e repopula a Listbox, sem reabrir a janela."""
    lista.delete(0, tk.END)
    for el in carregar():
        lista.insert(tk.END, el["nome"] + "  -  " + el.get("endereco", ""))


ttk.Label(janela, text="Componentes I2C",
          font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))

botoes = ttk.Frame(janela)
botoes.pack(pady=5)


def selecionar(event=None):
    global selecionados
    selecionados = lista.curselection()
    if not selecionados:
        label.config(text="")
        return
    text = "Selecionado(s): \n"
    for i in selecionados:
        text = text + lista.get(i) + "\n"
    label.config(text=text)


def cadastrar():
    formulario_i2c.abrir_formulario(janela, indice=None, ao_salvar=recarregar_lista)


def editar():
    global selecionados
    if len(selecionados) != 1:
        messagebox.showwarning("Seleção inválida", "Selecione exatamente um componente para editar.")
        return
    formulario_i2c.abrir_formulario(janela, indice=selecionados[0], ao_salvar=recarregar_lista)


def apagar():
    global selecionados
    if len(selecionados) == 0:
        messagebox.showwarning("Seleção inválida", "Selecione pelo menos um componente para apagar.")
        return
    resposta = messagebox.askyesno("Confirmar", "Você realmente quer apagar?")
    if resposta:
        comps = carregar()
        nomes = [lista.get(i) for i in selecionados]
        for i in sorted(selecionados, reverse=True):
            del comps[i]
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(comps, f, ensure_ascii=False, indent=2)
        recarregar_lista()
        apagados.config(text="Apagados: " + ", ".join(nomes))
        selecionados = []
        
def executar_comando(cmd):
    """Executa a sequência de um comando (chamado direto pelo botão do comando)."""
    addr = addr_detectado["valor"]
    if not addr:
        return

    pares = []
    for item in cmd.get("sequencia", "").split(","):
        item = item.strip()
        if ":" in item:
            reg, val = item.split(":", 1)
            pares.append(reg.strip() + ";" + val.strip())

    if not pares:
        resp_lbl.config(text="Comando '%s' sem sequência válida (use reg:val)."
                        % cmd.get("nome", ""), foreground="red")
        return

    resp_lbl.config(text="Executando: " + cmd.get("nome", ""), foreground="black")
    enviar("WRITE;%s;" % addr + ";".join(pares))


tk.Button(botoes, text="Cadastrar", command=cadastrar).grid(row=0, column=0, padx=5)
tk.Button(botoes, text="Editar", command=editar).grid(row=0, column=1, padx=5)
tk.Button(botoes, text="Apagar", command=apagar).grid(row=0, column=2, padx=5)

label = tk.Label(janela, text="")
label.pack()

apagados = tk.Label(janela, text="")
apagados.pack()

lista = tk.Listbox(janela, selectmode=tk.MULTIPLE)
lista.pack(pady=10, fill=tk.BOTH, expand=True)
lista.bind("<<ListboxSelect>>", selecionar)

recarregar_lista()

# --------------------------------------------------------------------------
# Detecção I2C via serial (conexão única, viva enquanto o app estiver aberto).
#
# O Arduino (controleArduinoI2C.ino) manda "CONN;0xNN" / "DISC;0xNN". 
# --------------------------------------------------------------------------

painel = ttk.LabelFrame(janela, text="Dispositivo conectado (I2C)")
painel.pack(fill="x", padx=10, pady=(0, 8))

linha_porta = ttk.Frame(painel)
linha_porta.pack(fill="x", padx=8, pady=(6, 2))
ttk.Label(linha_porta, text="Porta:").pack(side="left")
porta_sel = ttk.Combobox(linha_porta, width=20, state="readonly")
porta_sel.pack(side="left", padx=4)

status_lbl = ttk.Label(painel, text="", foreground="gray")
status_lbl.pack(anchor="w", padx=8)

info_lbl = ttk.Label(painel, text="", justify="left")
info_lbl.pack(anchor="w", padx=8, pady=4)

acoes_frame = ttk.Frame(painel)
acoes_frame.pack(pady=(0, 4))
cad_btn = tk.Button(acoes_frame, text="Cadastrar detectado", state="disabled")
cad_btn.pack(side="left", padx=2)
edit_btn = tk.Button(acoes_frame, text="Editar detectado", state="disabled")
edit_btn.pack(side="left", padx=2)

# leitura/escrita de registrador do dispositivo detectado
cmd_frame = ttk.Frame(painel)
cmd_frame.pack(fill="x", padx=8, pady=5)
ttk.Label(cmd_frame, text="Envio de comandos:").pack(anchor="w", pady=(0, 5))

campos_frame = ttk.Frame(cmd_frame)
campos_frame.pack(fill="x")
ttk.Label(campos_frame, text="Reg:").pack(side="left")
reg_entry = ttk.Entry(campos_frame, width=6)
reg_entry.pack(side="left", padx=2)
ler_btn = tk.Button(campos_frame, text="Ler", state="disabled")
ler_btn.pack(side="left", padx=2)
ttk.Label(campos_frame, text="Val:").pack(side="left", padx=(8, 0))
val_entry = ttk.Entry(campos_frame, width=6)
val_entry.pack(side="left", padx=2)
esc_btn = tk.Button(campos_frame, text="Escrever", state="disabled")
esc_btn.pack(side="left", padx=2)
ttk.Label(
    cmd_frame,
    text="Comandos cadastrados:"
).pack(anchor="w", pady=(8, 2))

# um botão por comando do componente; clicar já executa
comandos_frame = ttk.Frame(cmd_frame)
comandos_frame.pack(fill="x", pady=(0, 5))


resp_lbl = ttk.Label(painel, text="", justify="left")
resp_lbl.pack(anchor="w", padx=8, pady=(0, 8))

ser = {"obj": None}
addr_detectado = {"valor": None}
loop_id = {"valor": None}


def info_registrada(addr):
    return [c for c in carregar() if c.get("endereco", "").lower() == addr.lower()]

def atualizar_lista_comandos(addr):
    # recria os botões dos comandos do componente detectado
    for w in comandos_frame.winfo_children():
        w.destroy()
    if not addr:
        return
    comp = next((c for c in carregar()
                 if c.get("endereco", "").lower() == addr.lower()), None)
    if not comp:
        return
    for cmd in comp.get("comandos", []):
        tk.Button(comandos_frame, text=cmd.get("nome", "Sem nome"),
                  command=partial(executar_comando, cmd),
                  bg="#e1f5fe").pack(fill="x", pady=1)

def mostrar_detectado(addr):
    addr_detectado["valor"] = addr
    estado = "disabled" if addr is None else "normal"
    cad_btn.config(state=estado)
    ler_btn.config(state=estado)
    esc_btn.config(state=estado)
    if addr is None:
        atualizar_lista_comandos(None)
        edit_btn.config(state="disabled")
        info_lbl.config(text="Nenhum dispositivo detectado.")
        resp_lbl.config(text="")
        return
    registrados = info_registrada(addr)
    edit_btn.config(state="normal" if registrados else "disabled")
    if registrados:
        nomes = ", ".join(c.get("nome", "?") for c in registrados)
        texto = "Endereço " + addr + " - identificado:\n" + nomes
    else:
        texto = "Endereço " + addr + " - não cadastrado ainda."
    info_lbl.config(text=texto)
    atualizar_lista_comandos(addr)


def cadastrar_detectado():
    addr = addr_detectado["valor"]
    if addr:
        formulario_i2c.abrir_formulario(janela, indice=None,
                                        ao_salvar=recarregar_lista, endereco_inicial=addr)


def editar_detectado():
    addr = addr_detectado["valor"]
    if not addr:
        return
    comps = carregar()
    indices = [i for i, c in enumerate(comps)
               if c.get("endereco", "").lower() == addr.lower()]
    if not indices:
        messagebox.showinfo("Não cadastrado",
                            "Esse endereço ainda não está cadastrado. Use Cadastrar detectado.")
        return
    if len(indices) > 1:
        messagebox.showinfo("Vários componentes",
                            "Há mais de um componente nesse endereço; editando o primeiro.")
    formulario_i2c.abrir_formulario(janela, indice=indices[0], ao_salvar=recarregar_lista)


def enviar(cmd):
    """Manda um comando (uma linha) para o Arduino pela serial."""
    s = ser["obj"]
    if s is None:
        resp_lbl.config(text="sem conexão serial", foreground="red")
        return
    try:
        s.write((cmd + "\n").encode())
        log(cmd, enviado=True)
    except Exception as e:
        resp_lbl.config(text="erro ao enviar: " + str(e), foreground="red")


def ler_registrador():
    addr, reg = addr_detectado["valor"], reg_entry.get().strip()
    if not addr or not reg:
        return
    resp_lbl.config(text="lendo " + reg + "...", foreground="gray")
    enviar("READ;%s;%s;1" % (addr, reg))

def escrever_registrador():
    addr, reg, val = addr_detectado["valor"], reg_entry.get().strip(), val_entry.get().strip()
    if not addr or not reg or not val:
        return
    resp_lbl.config(text="escrevendo...", foreground="gray")
    enviar("WRITE;%s;%s;%s" % (addr, reg, val))


cad_btn.config(command=cadastrar_detectado)
edit_btn.config(command=editar_detectado)
ler_btn.config(command=ler_registrador)
esc_btn.config(command=escrever_registrador)


def atualizar_portas():
    portas = [p.device for p in list_ports.comports()] if SERIAL_OK else []
    porta_sel["values"] = portas
    if portas and not porta_sel.get():
        porta_sel.set(portas[0])


def fechar_porta():
    if ser["obj"] is not None:
        try:
            ser["obj"].close()
        except Exception:
            pass
        ser["obj"] = None


def abrir_porta(event=None):
    fechar_porta()
    mostrar_detectado(None)
    if not SERIAL_OK:
        status_lbl.config(text="pyserial não instalado (pip install pyserial)", foreground="red")
        return
    porta = porta_sel.get()
    if not porta:
        status_lbl.config(text="selecione uma porta", foreground="gray")
        return
    try:
        ser["obj"] = serial.Serial(porta, BAUD, timeout=0.1)
        status_lbl.config(text="conectado em " + porta, foreground="green")
    except Exception as e:
        status_lbl.config(text="erro: " + str(e), foreground="red")


def norm_addr(texto):
    try:
        return "0x%02X" % int(texto.strip(), 16)
    except ValueError:
        return None


def processar(linha):
    partes = [p.strip() for p in linha.strip().split(";")]
    tag = partes[0].upper() if partes else ""

    if tag == "CONN" and len(partes) >= 2:
        addr = norm_addr(partes[1])
        if addr:
            mostrar_detectado(addr)
    elif tag == "DISC" and len(partes) >= 2:
        if norm_addr(partes[1]) == addr_detectado["valor"]:
            mostrar_detectado(None)
    elif tag == "RESP" and len(partes) >= 4:
        resp_lbl.config(text="Reg " + partes[2] + " = " + partes[3], foreground="black")
    elif tag == "OK" and len(partes) >= 3:
        resp_lbl.config(text="Escrita OK em " + partes[2], foreground="green")
    elif tag == "ERR" and len(partes) >= 2:
        resp_lbl.config(text="Erro: " + "; ".join(partes[1:]), foreground="red")


def ler_serial():
    s = ser["obj"]
    if s is not None:
        try:
            while s.in_waiting:
                linha = s.readline().decode("utf-8", errors="replace")
                if linha.strip():
                    log(linha)
                    processar(linha)
        except Exception as e:
            status_lbl.config(text="desconectado: " + str(e), foreground="red")
            fechar_porta()
    loop_id["valor"] = janela.after(200, ler_serial)


def sair():
    fechar_porta()
    if loop_id["valor"] is not None:
        janela.after_cancel(loop_id["valor"])
    janela.destroy()


porta_sel.bind("<<ComboboxSelected>>", abrir_porta)
ttk.Button(linha_porta, text="↻", width=3, command=atualizar_portas).pack(side="left", padx=2)


# Log da serial: tudo que o Arduino manda (e o que enviamos, com "> ")
log_frame = ttk.LabelFrame(janela, text="Log serial (Arduino)")
log_frame.pack(fill="both", expand=False, padx=10, pady=(0, 6))
log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled",
                                     font=("Menlo", 9), wrap="none")
log_text.pack(fill="both", expand=True, padx=4, pady=4)


def log(texto, enviado=False):
    log_text.config(state="normal")
    log_text.insert("end", ("> " if enviado else "") + texto.rstrip() + "\n")
    linhas = int(log_text.index("end-1c").split(".")[0])
    if linhas > 300:                       
        log_text.delete("1.0", "%d.0" % (linhas - 300))
    log_text.see("end")
    log_text.config(state="disabled")


tk.Button(janela, text="Limpar log",
          command=lambda: (log_text.config(state="normal"),
                           log_text.delete("1.0", "end"),
                           log_text.config(state="disabled"))).pack(pady=(0, 4))

tk.Button(janela, text="Sair", command=sair).pack(pady=5)

atualizar_portas()
abrir_porta()
mostrar_detectado(None)
janela.protocol("WM_DELETE_WINDOW", sair)
loop_id["valor"] = janela.after(200, ler_serial)

janela.mainloop()


