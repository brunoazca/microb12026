import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import json

janela = tk.Tk()
janela.title("Seleção de Componentes I2C")
janela.geometry("440x520")

with open("componentes_i2c.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

componentes = []
for el in dados:
    # mostra nome + endereco na lista (ex.: "MPU6050 (IMU 6 eixos)  -  0x68")
    componentes.append(el["nome"] + "  -  " + el.get("endereco", ""))


ttk.Label(text="Componentes I2C",
          font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))


botoes = ttk.Frame(janela)
botoes.pack(pady=5)

global selecionados
selecionados = []


def selecionar(event=None):
    global selecionados
    selecionados = lista.curselection()
    if not selecionados:
        label.config(text="")
        return
    nomes = []
    for i in selecionados:
        nomes.append(lista.get(i))
    label.config(text="Selecionado(s): " + ", ".join(nomes))


def cadastrar():
    subprocess.Popen([sys.executable, "cadastro_i2c.py"])
    janela.destroy()


def apagar():
    global selecionados
    if len(selecionados) == 0:
        messagebox.showwarning("Seleção inválida", "Selecione pelo menos um componente para apagar.")
        return
    resposta = messagebox.askyesno("Confirmar", "Você realmente quer apagar?")
    if resposta:
        with open("componentes_i2c.json", "r", encoding="utf-8") as f:
            comps = json.load(f)
        nomes = []
        for i in selecionados:
            nomes.append(lista.get(i))
        for i in sorted(selecionados, reverse=True):
            lista.delete(i)
            del comps[i]
        with open("componentes_i2c.json", "w", encoding="utf-8") as f:
            json.dump(comps, f, ensure_ascii=False, indent=2)
        apagados.config(text="Apagados: " + ", ".join(nomes))
        selecionados = []


def editar():
    global selecionados
    if len(selecionados) != 1:
        messagebox.showwarning("Seleção inválida", "Selecione exatamente um componente para editar.")
        return
    subprocess.Popen([sys.executable, "edicao_i2c.py", str(selecionados[0])])
    janela.destroy()


tk.Button(botoes, text="Cadastrar", command=cadastrar).grid(row=0, column=0, padx=5)
tk.Button(botoes, text="Editar", command=editar).grid(row=0, column=1, padx=5)
tk.Button(botoes, text="Apagar", command=apagar).grid(row=0, column=2, padx=5)

label = tk.Label(janela, text="")
label.pack()

apagados = tk.Label(janela, text="")
apagados.pack()

lista = tk.Listbox(janela, selectmode=tk.MULTIPLE)
for item in componentes:
    lista.insert(tk.END, item)
lista.pack(pady=10, fill=tk.BOTH, expand=True)

# clicar em um item ja seleciona automaticamente (sem botao "Selecionar")
lista.bind("<<ListboxSelect>>", selecionar)


def sair():
    # adicionar endereco para o menu principal
    janela.destroy()


tk.Button(janela, text="Sair", command=sair).pack(pady=5)


janela.mainloop()
