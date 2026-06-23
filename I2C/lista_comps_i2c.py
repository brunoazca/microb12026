import tkinter as tk
from tkinter import ttk, messagebox
import json

import formulario_i2c

ARQUIVO = "componentes_i2c.json"

janela = tk.Tk()
janela.title("Seleção de Componentes I2C")
janela.geometry("440x520")

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

tk.Button(janela, text="Sair", command=janela.destroy).pack(pady=5)

janela.mainloop()
