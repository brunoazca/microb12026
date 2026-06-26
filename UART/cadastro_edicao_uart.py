import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import sys

JSON_PATH = "componentes_uart.json"

if len(sys.argv) > 1:
    indice = int(sys.argv[1])
else:
    indice = None

comandos = {}

janela = tk.Tk()
janela.title("Cadastro de Componente UART")
janela.geometry("500x640")

formulario = ttk.Frame(janela)
formulario.pack(padx=20, pady=15)

titulo = ttk.Label(formulario, text="Cadastro de Componente UART",
                   font=("Segoe UI", 16, "bold"))
titulo.grid(row=0, column=0, columnspan=2, pady=(0, 15))

ttk.Label(formulario, text="Nome*:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
nome = ttk.Entry(formulario, width=28)
nome.grid(row=1, column=1, pady=4)

ttk.Label(formulario, text="Baud padrão:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
baud = ttk.Combobox(formulario, width=25, state="readonly",
                    values=["0", "300", "600", "1200", "2400", "4800", "9600",
                            "19200", "38400", "57600", "115200", "230400"])
baud.set("9600")
baud.grid(row=2, column=1, pady=4)

ttk.Label(formulario, text="Frame:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
frame = ttk.Combobox(formulario, width=25,
                     values=["8N1", "8E1", "8O1", "8N2", "7E1", "7O1"])
frame.set("8N1")
frame.grid(row=3, column=1, pady=4)

ttk.Label(formulario, text="Transmite sozinho:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
transmite = ttk.Combobox(formulario, width=25, state="readonly",
                         values=["nao", "sim", "boot"])
transmite.set("nao")
transmite.grid(row=4, column=1, pady=4)

ttk.Label(formulario, text="Tipo protocolo:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
tipo_protocolo = ttk.Combobox(formulario, width=25, state="readonly",
                              values=["AT", "binario", "nmea", "passivo"])
tipo_protocolo.set("AT")
tipo_protocolo.grid(row=5, column=1, pady=4)

ttk.Label(formulario, text="Timeout (ms):").grid(row=6, column=0, sticky="e", padx=5, pady=4)
timeout = ttk.Spinbox(formulario, from_=0, to=10000, increment=100, width=26)
timeout.set(500)
timeout.grid(row=6, column=1, pady=4)

ttk.Label(formulario, text="Nível lógico:").grid(row=7, column=0, sticky="e", padx=5, pady=4)
nivel = ttk.Combobox(formulario, width=25,
                     values=["3,3 V", "5 V", "5 V toler.", "2,8 V"])
nivel.set("5 V")
nivel.grid(row=7, column=1, pady=4)

comandos_frame = ttk.LabelFrame(janela, text="Comandos")
comandos_frame.pack(fill="both", expand=True, padx=20, pady=5)

entrada = ttk.Frame(comandos_frame)
entrada.pack(fill="x", padx=5, pady=5)
cmd_entry = ttk.Entry(entrada)
cmd_entry.pack(side="left", fill="x", expand=True)


def adicionar_comando():
    cmd = cmd_entry.get().strip()
    if not cmd:
        return
    if cmd in comandos: 
        messagebox.showwarning("Comando repetido", "Esse comando já foi adicionado.")
        return
    comandos[cmd] = cmd
    cmd_entry.delete(0,tk.END)
    redesenhar_comandos()


def remover_comando(cmd):
    if cmd in comandos:
        del comandos[cmd]
        redesenhar_comandos()


def redesenhar_comandos():
    for w in lista_comandos.winfo_children():
        w.destroy()
    for cmd in comandos:
        linha = ttk.Frame(lista_comandos)
        linha.pack(fill="x", pady=1)
        ttk.Label(linha, text=cmd).pack(side="left", padx=5)
        tk.Button(linha, text="Remover",
                  command=lambda c=cmd: remover_comando(c)).pack(side="right")


cmd_entry.bind("<Return>", lambda e: adicionar_comando())
tk.Button(entrada, text="Adicionar", command=adicionar_comando).pack(side="left", padx=5)

lista_comandos = ttk.Frame(comandos_frame)
lista_comandos.pack(fill="both", expand=True, padx=5, pady=5)


def salvar():
    if not nome.get().strip():
        messagebox.showwarning("Dados inválidos", "O campo Nome não pode estar vazio.")
        return
    if not baud.get().isdigit() or int(baud.get()) < 0:
        messagebox.showwarning("Dados inválidos", "Baud padrão deve ser um número inteiro não negativo.")
        return

    dados = {
        "nome": nome.get(),
        "baud": int(baud.get()),
        "frame": frame.get(),
        "transmite_sozinho": transmite.get(),
        "tipo_protocolo": tipo_protocolo.get(),
        "timeout": int(timeout.get()),
        "nivel_logico": nivel.get(),
        "comandos": comandos
    }

    aviso = messagebox.askyesno("Confirmar", "Salvar componente?")
    if aviso:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            componentes = json.load(f)
        if indice is not None:
            componentes[indice] = dados
        else:
            componentes.append(dados)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(componentes, f, ensure_ascii=False, indent=2)
        voltar()


def voltar():
    subprocess.Popen([sys.executable, "lista_comps_uart.py"])
    janela.destroy()


rodape = ttk.Frame(janela)
rodape.pack(pady=12)
ttk.Button(rodape, text="Voltar", command=voltar).grid(row=0, column=0, padx=5)
ttk.Button(rodape, text="Salvar", command=salvar).grid(row=0, column=1, padx=5)


if indice is not None:
    titulo.config(text="Edição de Componente UART")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        comp = json.load(f)[indice]
    nome.insert(0, comp.get("nome", ""))
    baud.set(str(comp.get("baud", "")))
    frame.set(comp.get("frame", "8N1"))
    transmite.set(comp.get("transmite_sozinho", "nao"))
    tipo_protocolo.set(comp.get("tipo_protocolo", "AT"))
    timeout.set(comp.get("timeout", 500))
    nivel.set(comp.get("nivel_logico", "5 V"))
    comandos = comp.get("comandos", {})
    redesenhar_comandos()

janela.mainloop()
