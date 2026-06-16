import tkinter as tk
from tkinter import ttk, messagebox
import json
import subprocess
import sys

# Categorias usadas no campo "Tipo"
TIPOS = ["acelerometro/IMU", "magnetometro", "temperatura/umidade", "pressao",
         "luz", "distancia/ToF", "ADC/DAC", "PWM", "expansor IO", "display",
         "RTC", "memoria/EEPROM", "gas/CO2", "multiplexador", "outro"]

# Velocidades padrao do barramento I2C (Hz)
VELOCIDADES = ["100000", "400000", "1000000"]

NIVEIS = ["3,3 V", "5 V", "5 V toler.", "2,8 V"]


def endereco_valido(texto):
    """Aceita formatos como 0x68, 68 ou 104 e confere a faixa 0x08-0x77."""
    t = texto.strip().lower()
    if not t:
        return None
    try:
        valor = int(t, 16) if t.startswith("0x") else int(t, 16)
    except ValueError:
        return None
    if 0x08 <= valor <= 0x77:
        return "0x%02X" % valor
    return None


janela = tk.Tk()
janela.title("Cadastro de Componente I2C")
janela.geometry("440x520")

formulario = ttk.Frame(janela)
formulario.pack(padx=20, pady=20)


ttk.Label(formulario, text="Cadastro de Componentes I2C",
          font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))


ttk.Label(formulario, text="Nome*:").grid(row=1, column=0, sticky="e", padx=5, pady=4)
nome = ttk.Entry(formulario, width=28)
nome.grid(row=1, column=1, pady=4)


ttk.Label(formulario, text="Endereço*:").grid(row=2, column=0, sticky="e", padx=5, pady=4)
endereco = ttk.Combobox(formulario, width=25,
                        values=["0x" + format(a, "02X") for a in range(0x08, 0x78)])
endereco.grid(row=2, column=1, pady=4)


ttk.Label(formulario, text="Endereços alt.:").grid(row=3, column=0, sticky="e", padx=5, pady=4)
enderecos_alt = ttk.Entry(formulario, width=28)
enderecos_alt.grid(row=3, column=1, pady=4)


ttk.Label(formulario, text="Obs. endereço:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
endereco_obs = ttk.Entry(formulario, width=28)
endereco_obs.grid(row=4, column=1, pady=4)


ttk.Label(formulario, text="Tipo:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
tipo = ttk.Combobox(formulario, width=25, values=TIPOS)
tipo.set("outro")
tipo.grid(row=5, column=1, pady=4)


ttk.Label(formulario, text="Registrador ID:").grid(row=6, column=0, sticky="e", padx=5, pady=4)
registrador_id = ttk.Entry(formulario, width=28)
registrador_id.grid(row=6, column=1, pady=4)


ttk.Label(formulario, text="Valor ID:").grid(row=7, column=0, sticky="e", padx=5, pady=4)
valor_id = ttk.Entry(formulario, width=28)
valor_id.grid(row=7, column=1, pady=4)


ttk.Label(formulario, text="Velocidade (Hz):").grid(row=8, column=0, sticky="e", padx=5, pady=4)
velocidade = ttk.Combobox(formulario, width=25, values=VELOCIDADES)
velocidade.set("100000")
velocidade.grid(row=8, column=1, pady=4)


ttk.Label(formulario, text="Nível lógico:").grid(row=9, column=0, sticky="e", padx=5, pady=4)
nivel = ttk.Combobox(formulario, width=25, values=NIVEIS)
nivel.set("3,3 V")
nivel.grid(row=9, column=1, pady=4)


ttk.Label(formulario, text="Obs.:").grid(row=10, column=0, sticky="e", padx=5, pady=4)
obs = ttk.Entry(formulario, width=28)
obs.grid(row=10, column=1, pady=4)


def salvar():
    if not nome.get().strip():
        messagebox.showwarning("Dados inválidos", "O campo Nome não pode estar vazio.")
        return

    addr = endereco_valido(endereco.get())
    if addr is None:
        messagebox.showwarning("Dados inválidos",
                               "Endereço deve ser hexadecimal na faixa 0x08 a 0x77 (ex.: 0x68).")
        return

    try:
        vel = int(velocidade.get())
    except ValueError:
        messagebox.showwarning("Dados inválidos", "Velocidade deve ser um número inteiro (Hz).")
        return

    dados = {
        "nome": nome.get().strip(),
        "endereco": addr,
        "enderecos_alt": enderecos_alt.get(),
        "endereco_obs": endereco_obs.get(),
        "tipo": tipo.get(),
        "registrador_id": registrador_id.get(),
        "valor_id": valor_id.get(),
        "velocidade": vel,
        "nivel_logico": nivel.get(),
        "obs": obs.get()
    }

    aviso = messagebox.askyesno("Confirmar", "Salvar componente?")
    if aviso:
        with open("componentes_i2c.json", "r", encoding="utf-8") as f:
            componentes = json.load(f)
        componentes.append(dados)
        with open("componentes_i2c.json", "w", encoding="utf-8") as f:
            json.dump(componentes, f, ensure_ascii=False, indent=2)
        subprocess.Popen([sys.executable, "lista_comps_i2c.py"])
        janela.destroy()


def voltar():
    subprocess.Popen([sys.executable, "lista_comps_i2c.py"])
    janela.destroy()


ttk.Button(formulario, text="Salvar", command=salvar).grid(row=11, column=1, pady=15)
ttk.Button(formulario, text="Voltar", command=voltar).grid(row=11, column=0, pady=15)


janela.mainloop()
