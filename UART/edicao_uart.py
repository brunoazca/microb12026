import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import sys

indice = int(sys.argv[1]) if len(sys.argv) > 1 else None

janela = tk.Tk()
janela.title("Edição de Componente UART")
janela.geometry("420x480")

formulario = ttk.Frame(janela)
formulario.pack(padx=20, pady=20)


ttk.Label(formulario, text="Edição de Componentes UART",
          font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))


ttk.Label(formulario, text="Nome*:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
nome = ttk.Entry(formulario, width=28)
nome.grid(row=1, column=1, pady=4)


ttk.Label(formulario, text="Baud padrão*:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
baud = ttk.Combobox(formulario, width=25,
                    values=["0","300","600","1200", "2400", "4800", "9600", "19200",
                            "38400", "57600", "115200", "230400"])
baud.grid(row=2, column=1, pady=4)


ttk.Label(formulario, text="Obs. baud:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
baud_obs = ttk.Entry(formulario, width=28)
baud_obs.grid(row=3, column=1, pady=4)


ttk.Label(formulario, text="Bauds alt.:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
bauds_alt = ttk.Entry(formulario, width=28)
bauds_alt.grid(row=4, column=1, pady=4)


ttk.Label(formulario, text="Frame:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
frame = ttk.Combobox(formulario, width=25,
                     values=["8N1", "8E1", "8O1", "8N2", "7E1", "7O1"])
frame.set("8N1")
frame.grid(row=5, column=1, pady=4)


ttk.Label(formulario, text="Transmite sozinho:").grid(row=6, column=0, sticky="e", padx=5, pady=4)
transmite = ttk.Combobox(formulario, width=25, state="readonly",
                         values=["nao", "sim", "boot"])
transmite.set("nao")
transmite.grid(row=6, column=1, pady=4)


ttk.Label(formulario, text="Tipo protocolo:").grid(row=7, column=0, sticky="e", padx=5, pady=4)
tipo_protocolo = ttk.Combobox(formulario, width=25, state="readonly",
                              values=["AT", "binario", "nmea", "passivo"])
tipo_protocolo.set("AT")
tipo_protocolo.grid(row=7, column=1, pady=4)


ttk.Label(formulario, text="Comando:").grid(row=8, column=0, sticky="e", padx=5, pady=4)
comando = ttk.Entry(formulario, width=28)
comando.grid(row=8, column=1, pady=4)


ttk.Label(formulario, text="Resposta:").grid(row=9, column=0, sticky="e", padx=5, pady=4)
resposta = ttk.Entry(formulario, width=28)
resposta.grid(row=9, column=1, pady=4)


ttk.Label(formulario, text="Timeout (ms):").grid(row=10, column=0, sticky="e", padx=5, pady=4)
timeout = ttk.Spinbox(formulario, from_=0, to=10000, increment=100, width=26)
timeout.set(500)
timeout.grid(row=10, column=1, pady=4)


ttk.Label(formulario, text="Nível lógico:").grid(row=11, column=0, sticky="e", padx=5, pady=4)
nivel = ttk.Combobox(formulario, width=25,
                     values=["3,3 V", "5 V", "5 V toler.", "2,8 V"])
nivel.set("5 V")
nivel.grid(row=11, column=1, pady=4)


if indice is not None:
    with open("UART\\componentes_uart.json", "r", encoding="utf-8") as f:
        comps = json.load(f)
    comp = comps[indice]
    nome.insert(0, comp["nome"])
    baud.set(str(comp["baud"]))
    baud_obs.insert(0, comp["baud_obs"])
    bauds_alt.insert(0, comp["bauds_alt"])
    frame.set(comp["frame"])
    transmite.set(comp["transmite_sozinho"])
    tipo_protocolo.set(comp["tipo_protocolo"])
    comando.insert(0, comp["comando"])
    resposta.insert(0, comp["resposta"])
    timeout.set(comp["timeout"])
    nivel.set(comp["nivel_logico"])


def salvar():
    dados = {
        "nome": nome.get(),
        "baud": int(baud.get()),
        "baud_obs": baud_obs.get(),
        "bauds_alt": bauds_alt.get(),
        "frame": frame.get(),
        "transmite_sozinho": transmite.get(),
        "tipo_protocolo": tipo_protocolo.get(),
        "comando": comando.get(),
        "resposta": resposta.get(),
        "timeout": int(timeout.get()),
        "nivel_logico": nivel.get()
    }

    if not nome.get().strip():
        messagebox.showwarning("Dados inválidos", "O campo Nome não pode estar vazio.")
        return
    if not baud.get().isdigit() or int(baud.get()) < 0:
        messagebox.showwarning("Dados inválidos", "Baud padrão deve ser um número inteiro não negativo.")
        return

    aviso = messagebox.askyesno("Confirmar", "Salvar componente?")
    if aviso:
        with open("UART\\componentes_uart.json", "r", encoding="utf-8") as f:
            componentes = json.load(f)
        if indice is not None:
            componentes[indice] = dados
        else:
            componentes.append(dados)
        with open("UART\\componentes_uart.json", "w", encoding="utf-8") as f:
            json.dump(componentes, f, ensure_ascii=False, indent=2)
        subprocess.Popen([sys.executable, "UART\\lista_comps_uart.py"])
        janela.destroy()


def voltar():
    subprocess.Popen([sys.executable, "UART\\lista_comps_uart.py"])
    janela.destroy()


ttk.Button(formulario, text="Salvar", command=salvar).grid(row=12, column=1, pady=15)
ttk.Button(formulario, text="Voltar", command=voltar).grid(row=12, column=0, pady=15)


janela.mainloop()