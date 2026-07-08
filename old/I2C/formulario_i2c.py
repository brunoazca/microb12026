import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import json

TIPOS = ["acelerometro/IMU", "magnetometro", "temperatura/umidade", "pressao",
         "luz", "distancia/ToF", "ADC/DAC", "PWM", "expansor IO", "display",
         "RTC", "memoria/EEPROM", "gas/CO2", "multiplexador", "outro"]

VELOCIDADES = ["100000", "400000", "1000000"]

NIVEIS = ["3,3 V", "5 V", "5 V toler.", "2,8 V"]

ARQUIVO = "componentes_i2c.json"


def endereco_valido(texto):
    """Aceita formatos como 0x68, 68 ou 104 e confere a faixa 0x08-0x77."""
    t = texto.strip().lower()
    if not t:
        return None
    try:
        valor = int(t, 16)
    except ValueError:
        return None
    if 0x08 <= valor <= 0x77:
        return "0x%02X" % valor
    return None


def abrir_formulario(parent, indice=None, ao_salvar=None, endereco_inicial=None):
    """Abre o formulário de componente I2C como subjanela (Toplevel) de `parent`.

    - `indice is None`  -> modo cadastro: o componente é adicionado ao final.
    - `indice` inteiro  -> modo edição: carrega esse componente e o substitui.
    - `endereco_inicial` -> no cadastro, já preenche o endereço (ex.: o que foi
      detectado pelo Arduino na tela principal).

    `ao_salvar` (opcional) é chamado depois de gravar com sucesso, para a janela
    principal atualizar sua lista sem reabrir nada.
    """
    edicao = indice is not None

    top = tk.Toplevel(parent)
    top.title("Edição de Componente I2C" if edicao else "Cadastro de Componente I2C")
    top.geometry("460x700")
    top.transient(parent)

    formulario = ttk.Frame(top)
    formulario.pack(padx=20, pady=20)

    ttk.Label(formulario,
              text="Edição de Componentes I2C" if edicao else "Cadastro de Componentes I2C",
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

    ttk.Label(formulario, text="Tipo:").grid(row=4, column=0, sticky="e", padx=5, pady=4)
    tipo = ttk.Combobox(formulario, width=25, values=TIPOS)
    tipo.set("outro")
    tipo.grid(row=4, column=1, pady=4)

    ttk.Label(formulario, text="Registrador ID:").grid(row=5, column=0, sticky="e", padx=5, pady=4)
    registrador_id = ttk.Entry(formulario, width=28)
    registrador_id.grid(row=5, column=1, pady=4)

    ttk.Label(formulario, text="Valor ID:").grid(row=6, column=0, sticky="e", padx=5, pady=4)
    valor_id = ttk.Entry(formulario, width=28)
    valor_id.grid(row=6, column=1, pady=4)

    ttk.Label(formulario, text="Velocidade (Hz):").grid(row=7, column=0, sticky="e", padx=5, pady=4)
    velocidade = ttk.Combobox(formulario, width=25, values=VELOCIDADES, state="readonly")
    velocidade.set("100000")
    velocidade.grid(row=7, column=1, pady=4)

    ttk.Label(formulario, text="Nível lógico:").grid(row=8, column=0, sticky="e", padx=5, pady=4)
    nivel = ttk.Combobox(formulario, width=25, values=NIVEIS, state="readonly")
    nivel.set("3,3 V")
    nivel.grid(row=8, column=1, pady=4)

    ttk.Label(formulario, text="Obs.:").grid(row=9, column=0, sticky="e", padx=5, pady=4)
    obs = ttk.Entry(formulario, width=28)
    obs.grid(row=9, column=1, pady=4)
    

    ttk.Label(formulario, text="Comandos:").grid(
        row=10, column=0, sticky="ne", padx=5, pady=4
    )

    comandos_txt = scrolledtext.ScrolledText(
        formulario,
        width=28,
        height=5,
        font=("Menlo", 10)
    )
    comandos_txt.grid(row=10, column=1, pady=4)

    ttk.Label(
        formulario,
        text="Um por linha:  nome=reg:val, reg:val\nex.: Acende=0x00:0x08",
        font=("Segoe UI", 8, "italic"),
        foreground="gray"
    ).grid(row=11, column=1, sticky="w")

    # ----- LOAD: edição carrega o componente; cadastro usa o endereço dado --
    if edicao:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            comp = json.load(f)[indice]
        nome.insert(0, comp.get("nome", ""))
        endereco.set(comp.get("endereco", ""))
        enderecos_alt.insert(0, comp.get("enderecos_alt", ""))
        tipo.set(comp.get("tipo", "outro"))
        registrador_id.insert(0, comp.get("registrador_id", ""))
        valor_id.insert(0, comp.get("valor_id", ""))
        velocidade.set(str(comp.get("velocidade", "100000")))
        nivel.set(comp.get("nivel_logico", "3,3 V"))
        obs.insert(0, comp.get("obs", ""))
        linhas = []
        for cmd in comp.get("comandos", []):
            linhas.append(
                f'{cmd.get("nome","")}={cmd.get("sequencia","")}'
            )

        comandos_txt.insert("1.0", "\n".join(linhas))
    elif endereco_inicial:
        endereco.set(endereco_inicial)

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
        
        lista_comandos = []

        for linha in comandos_txt.get("1.0", "end").splitlines():

            linha = linha.strip()

            if not linha:
                continue

            if "=" not in linha:
                continue

            nome_cmd, sequencia = linha.split("=", 1)

            lista_comandos.append({
                "nome": nome_cmd.strip(),
                "sequencia": sequencia.strip()
            })

        dados = {
            "nome": nome.get().strip(),
            "endereco": addr,
            "enderecos_alt": enderecos_alt.get(),
            "tipo": tipo.get(),
            "registrador_id": registrador_id.get(),
            "valor_id": valor_id.get(),
            "velocidade": vel,
            "nivel_logico": nivel.get(),
            "obs": obs.get(),
            "comandos": lista_comandos
        }


        if not messagebox.askyesno("Confirmar", "Salvar componente?"):
            return

        # ----- SAVE: edição substitui, cadastro adiciona -------------------
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            componentes = json.load(f)
        if edicao:
            componentes[indice] = dados
        else:
            componentes.append(dados)
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(componentes, f, ensure_ascii=False, indent=2)

        top.destroy()
        if ao_salvar:
            ao_salvar()

    ttk.Button(formulario, text="Salvar", command=salvar).grid(row=12, column=1, pady=15)
    ttk.Button(formulario, text="Voltar", command=top.destroy).grid(row=12, column=0, pady=15)
    return top


if __name__ == "__main__":
    import sys
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else None
    raiz = tk.Tk()
    raiz.withdraw()
    janela = abrir_formulario(raiz, idx)
    janela.protocol("WM_DELETE_WINDOW", raiz.destroy)
    raiz.mainloop()


