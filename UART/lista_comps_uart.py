import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

janela = tk.Tk()
janela.title("Seleção de Componentes UART")
janela.geometry("420x520")

import json

with open("componentes_uart.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

componentes = []

for el in dados:
    componentes.append(el["nome"])



ttk.Label(text="Componentes UART",
          font=("Segoe UI", 16, "bold")).pack(pady=(0, 15))


botoes = ttk.Frame(janela)
botoes.pack(pady=5)

def selecionar(event):
    selecionados = lista.curselection()
    txt = "Selecionado(s): "
    for i in selecionados:
        nome = lista.get(i)
        txt += nome + ",\n"
    
    
    label.config(text=txt)
    

def cadastrar():
    subprocess.Popen([sys.executable, "cadastro&edicao_uart.py"])
    janela.destroy()

def apagar():
    selecionados = lista.curselection()
    if len(selecionados) == 0:
        messagebox.showwarning("Seleção inválida", "Selecione pelo menos um componente para apagar.")
        return
    resposta = messagebox.askyesno("Confirmar", "Você realmente quer apagar?")
    if resposta:
        with open("componentes_uart.json", "r", encoding="utf-8") as f:
            comps = json.load(f)
        nomes = []
        for i in selecionados: 
            nomes.append(lista.get(i))
        for i in sorted(selecionados, reverse=True):
            lista.delete(i)
            del comps[i]
        with open("componentes_uart.json", "w", encoding="utf-8") as f:
            json.dump(comps, f, ensure_ascii=False, indent=2)
        apagados.config(text="Apagado(s): " + ", ".join(nomes))
        selecionados = []


def editar():
    selecionados = lista.curselection()
    if len(selecionados) != 1:
        messagebox.showwarning("Seleção inválida", "Selecione exatamente um componente para editar.")
        return
    subprocess.Popen([sys.executable, "cadastro&edicao_uart.py", str(selecionados[0])])
    janela.destroy()
    

tk.Button(botoes, text="Cadastrar", command=cadastrar).grid(row=0, column=0, padx=5)
tk.Button(botoes, text="Apagar", command=apagar).grid(row=0, column=2, padx=5)
tk.Button(botoes, text="Editar", command=editar).grid(row=0, column=1, padx=5)


label = tk.Label(janela, text="")
label.pack()


apagados = tk.Label(janela, text="")
apagados.pack()

lista = tk.Listbox(janela, selectmode=tk.MULTIPLE)
for item in componentes:
    lista.insert(tk.END, item)
lista.pack(pady=10, fill=tk.BOTH, expand=True)



lista.bind('<<ListboxSelect>>', selecionar)


def sair():
    #(subprocess.Popen([sys.executable, ".py"]))
    #adicionar endereço par o menu principal
    janela.destroy()

tk.Button(janela, text="Sair", command=sair).pack(pady=5)


janela.mainloop()