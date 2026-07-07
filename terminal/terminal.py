"""Terminal compartilhado I2C / UART / SPI.

Uma janela so. No topo escolhe-se o tipo (barramento) e a porta serial.
Abaixo: o banco de componentes (lista + editor) e, por ultimo, o
componente detectado, com envio manual a esquerda e os comandos
cadastrados como botoes a direita.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

import db
import form

try:
    import serial
    from serial.tools import list_ports
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False


BAUD = 115200 # UART precisa de 115200

# estado global (dicts para poder alterar de dentro das funcoes)
tipo = {"v": "i2c"}
tipo_a_confirmar = {"v": "i2c"}
tipo_confirmado = {"v": True}
ser = {"obj": None}
comps = {"lista": []}        # componentes carregados do banco
sel = {"i": None}            # indice selecionado na lista
comandos = {"lista": []}     # comandos do componente em edicao
ativo = {"comp": None}       # componente mostrado na secao "detectado"
loop_id = {"v": None}
lcd_timer = {"v": None}      # after() pendente que restaura o LCD apos um flash


janela = tk.Tk()
janela.title("Testador de Componentes Complexos")
janela.geometry("900x900")


# HEADER
cabecalho = ttk.Frame(janela)
cabecalho.pack(fill="x", padx=10, pady=8)

ttk.Label(cabecalho, text="Tipo:").pack(side="left")
tipo_sel = ttk.Combobox(cabecalho, width=6, state="readonly",
                        values=["i2c", "uart", "spi"])
tipo_sel.set("i2c")
tipo_sel.pack(side="left", padx=(2, 12))

ttk.Label(cabecalho, text="Porta:").pack(side="left")
porta_sel = ttk.Combobox(cabecalho, width=18, state="readonly")
porta_sel.pack(side="left", padx=2)
ttk.Button(cabecalho, text="↻", width=3,
           command=lambda: atualizar_portas()).pack(side="left", padx=2)

status = ttk.Label(cabecalho, text="X desconectado", foreground="gray")
status.pack(side="left", padx=12)

ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=10, pady=4)


# BANCO DE COMPONENTES
banco = ttk.LabelFrame(janela, text="Banco de componentes")
banco.pack(fill="both", expand=True, padx=10, pady=4)

# esquerda: lista + botoes
esq = ttk.Frame(banco)
esq.pack(side="left", fill="both", expand=True, padx=6, pady=6)

lista = tk.Listbox(esq, height=12)
lista.pack(fill="both", expand=True)

botoes_lista = ttk.Frame(esq)
botoes_lista.pack(fill="x", pady=4)
ttk.Button(botoes_lista, text="Novo",
           command=lambda: novo()).pack(side="left", padx=2)
ttk.Button(botoes_lista, text="Apagar",
           command=lambda: apagar()).pack(side="left", padx=2)

# direita: editor do componente + editor de comandos
right = ttk.Frame(banco)
right.pack(side="left", fill="both", expand=True, padx=6, pady=6)

form_comp = {"w": None}          
form_cmd = {"w": None}          

caixa_form = ttk.Frame(right)     # onde o form do componente e montado
caixa_form.pack(fill="x")

ttk.Label(right, text="Comandos:").pack(anchor="w", pady=(8, 2))
lista_cmd = tk.Listbox(right, height=5)
lista_cmd.pack(fill="x")

caixa_cmd = ttk.Frame(right)      # onde o form do comando e montado
caixa_cmd.pack(fill="x", pady=4)

botoes_cmd = ttk.Frame(right)
botoes_cmd.pack(fill="x")
ttk.Button(botoes_cmd, text="Add comando",
           command=lambda: add_comando()).pack(side="left", padx=2)
ttk.Button(botoes_cmd, text="Remover comando",
           command=lambda: del_comando()).pack(side="left", padx=2)

ttk.Button(right, text="Salvar componente",
           command=lambda: salvar()).pack(anchor="e", pady=8)

ttk.Separator(janela, orient="horizontal").pack(fill="x", padx=10, pady=4)


# COMPONENTE DETECTADO
det = ttk.LabelFrame(janela, text="Componente detectado")
det.pack(fill="both", expand=True, padx=10, pady=(4, 10))

# esquerda: nome + envio/recebimento manual
det_esq = ttk.Frame(det)
det_esq.pack(side="left", fill="both", expand=True, padx=6, pady=6)

nome_ativo = ttk.Label(det_esq, text="(nenhum)", font=("Segoe UI", 12, "bold"))
nome_ativo.pack(anchor="w")

linha_envio = ttk.Frame(det_esq)
linha_envio.pack(fill="x", pady=6)
entrada = ttk.Entry(linha_envio)
entrada.pack(side="left", fill="x", expand=True)
ttk.Button(linha_envio, text="Enviar",
           command=lambda: enviar_manual()).pack(side="left", padx=4)

log_txt = scrolledtext.ScrolledText(det_esq, height=10, state="disabled",
                                    font=("Menlo", 9), wrap="none")
log_txt.pack(fill="both", expand=True)

# direita: comandos cadastrados executaveis
det_dir = ttk.Frame(det)
det_dir.pack(side="left", fill="both", expand=True, padx=6, pady=6)
ttk.Label(det_dir, text="Comandos cadastrados:").pack(anchor="w")
botoes_exec = ttk.Frame(det_dir)
botoes_exec.pack(fill="both", expand=True, pady=4)


# funcoes
def log(texto, enviado=False):
    """Escreve uma linha no log da tela (prefixo '> ' quando enviado)."""
    prefixo = ""
    if enviado:
        prefixo = "> "
    log_txt.config(state="normal")
    log_txt.insert("end", prefixo + texto.rstrip() + "\n")
    log_txt.see("end")
    log_txt.config(state="disabled")


def montar_forms():
    """Recria os formularios (componente e comando) para o tipo atual."""
    for w in caixa_form.winfo_children():
        w.destroy()
    for w in caixa_cmd.winfo_children():
        w.destroy()
    form_comp["w"] = form.Formulario(caixa_form, form.CAMPOS[tipo["v"]])
    form_comp["w"].pack(fill="x")
    form_cmd["w"] = form.Formulario(caixa_cmd, form.CAMPOS_COMANDO[tipo["v"]])
    form_cmd["w"].pack(fill="x")


def carregar_comps():
    """Le o banco do tipo atual e enche a lista."""
    comps["lista"] = db.carregar(tipo["v"])
    lista.delete(0, tk.END)
    for c in comps["lista"]:
        lista.insert(tk.END, c["nome"])


def mostrar_comandos_edit():
    """Enche a lista de comandos do componente em edicao."""
    lista_cmd.delete(0, tk.END)
    for c in comandos["lista"]:
        lista_cmd.insert(tk.END, c.get("nome", "(sem nome)"))


def selecionar(event=None):
    """Ao clicar num componente da lista: preenche o editor e o ativa."""
    if not lista.curselection():
        return
    sel["i"] = lista.curselection()[0]
    comp = comps["lista"][sel["i"]]
    form_comp["w"].preencher(comp)
    # copia os comandos do componente para edicao (uma copia de cada um)
    comandos["lista"] = []
    for c in comp.get("comandos", []):
        comandos["lista"].append(dict(c))
    mostrar_comandos_edit()
    definir_ativo(comp)


def selecionar_comando(event=None):
    """Ao clicar num comando da lista: joga ele para o editor."""
    if not lista_cmd.curselection():
        return
    cmd = comandos["lista"][lista_cmd.curselection()[0]]
    form_cmd["w"].preencher(cmd)


def novo():
    """Limpa o editor para cadastrar um componente novo."""
    sel["i"] = None
    form_comp["w"].limpar()
    comandos["lista"] = []
    mostrar_comandos_edit()


def add_comando():
    """Adiciona o comando do editor a lista do componente."""
    cmd = form_cmd["w"].coletar()
    if not cmd.get("nome"):
        messagebox.showwarning("Comando", "O comando precisa de um nome.")
        return
    comandos["lista"].append(cmd)
    mostrar_comandos_edit()


def del_comando():
    """Remove o comando selecionado da lista."""
    if not lista_cmd.curselection():
        return
    del comandos["lista"][lista_cmd.curselection()[0]]
    mostrar_comandos_edit()


def salvar():
    """Salva o componente do editor no banco (novo ou editado)."""
    valores = form_comp["w"].coletar()
    if not valores.get("nome"):
        messagebox.showwarning("Componente", "O componente precisa de um nome.")
        return
    comp = dict(valores)                  # nome, endereco, velocidade...
    comp["comandos"] = comandos["lista"]
    if sel["i"] is None:
        comps["lista"].append(comp)
    else:
        comps["lista"][sel["i"]] = comp
    db.salvar(tipo["v"], comps["lista"])
    carregar_comps()


def apagar():
    """Apaga o componente selecionado do banco."""
    if sel["i"] is None:
        messagebox.showwarning("Apagar", "Selecione um componente.")
        return
    if not messagebox.askyesno("Confirmar", "Apagar o componente?"):
        return
    del comps["lista"][sel["i"]]
    db.salvar(tipo["v"], comps["lista"])
    sel["i"] = None
    carregar_comps()


def definir_ativo(comp):
    """Mostra o componente na secao de baixo e cria os botoes de comando."""
    ativo["comp"] = comp

    # limpa os botoes antigos
    for w in botoes_exec.winfo_children():
        w.destroy()

    if not comp:
        nome_ativo.config(text="(nenhum)")
        atualizar_lcd()
        return

    nome_ativo.config(text=comp["nome"])
    atualizar_lcd()

    # UART precisa configurar a ponte antes de enviar comandos
    if tipo["v"] == "uart" and ser["obj"]:
        enviar("CFG|%s|%s|T|" % (comp.get("baud", 9600),
                                 comp.get("timeout", 500)))
    for cmd in comp.get("comandos", []):
        b = tk.Button(botoes_exec, text=cmd.get("nome", "?"), bg="#e1f5fe")
        b.config(command=lambda c=cmd: executar(c))
        b.pack(fill="x", pady=1)


def linha_comando(comp, cmd):
    """Monta a linha serial de um comando, conforme o tipo."""
    t = tipo["v"]
    if t == "i2c":
        addr = comp.get("endereco", "")
        pares = []
        for item in cmd.get("sequencia", "").split(","):
            item = item.strip()
            if ":" in item:
                reg, val = item.split(":", 1)
                pares.append(reg.strip() + ";" + val.strip())
        if not pares:
            return None
        return "WRITE;" + addr + ";" + ";".join(pares)
    if t == "uart":
        return "SEND|" + cmd.get("modo", "T") + "|" + cmd.get("tx", "")
    # spi: envia o registrador (ex.: "R 0x37")
    return cmd.get("tx", "")


def executar(cmd):
    """Monta e envia a linha serial de um comando cadastrado."""
    if not ativo["comp"]:
        return
    linha = linha_comando(ativo["comp"], cmd)
    if linha:
        enviar(linha)
        flash_lcd("comando enviado")


def enviar(linha):
    """Envia uma linha pela serial e registra no log."""
    if ser["obj"] is None:
        log("(sem conexao serial)")
        return
    try:
        ser["obj"].write((linha + "\n").encode())
        log(linha, enviado=True)
    except Exception as e:
        log("erro ao enviar: " + str(e))


def enviar_manual():
    """Envia o texto digitado usando o protocolo da interface atual e le a resposta."""
    texto = entrada.get().strip()
    if not texto:
        return
    t = tipo["v"]
    if t == "uart":
        linha = "SEND|T|" + texto                 # manda como texto e le a resposta
    elif t == "i2c":
        if not ativo["comp"]:
            log("(sem componente I2C detectado)")
            return
        linha = "READ;" + ativo["comp"].get("endereco", "") + ";" + texto + ";1"
    else:
        linha = texto                             # spi: registrador cru (ex.: R 0x37)
    enviar(linha)
    flash_lcd("comando enviado")


# LCD de display e botao (dependem da placa unificada)
def enviar_modo():
    """Avisa o Arduino qual interface esta ativa (liga/desliga varredura I2C)."""
    enviar("MODE|" + tipo["v"])


def atualizar_lcd(cima=None):
    """Linha de cima = componente; linha de baixo = tipo de comunicacao."""
    if cima is None:
        cima = ativo["comp"]["nome"] if ativo["comp"] else ""
    enviar("LCD:" + (tipo["v"] if tipo_confirmado["v"] else tipo_a_confirmar["v"]+"?"+" (cur:%s)"%(tipo["v"])) + "\\n" + cima )


def flash_lcd(msg):
    """Mostra uma mensagem rapida na linha de cima e depois restaura."""
    enviar("LCD:" + msg + "\\n" + tipo["v"])
    if lcd_timer["v"] is not None:
        janela.after_cancel(lcd_timer["v"])
    lcd_timer["v"] = janela.after(3000, atualizar_lcd)


def proximo_tipo(eh_cw):
    """Cicla i2c -> uart -> spi (acionado pelo botao no Arduino)."""
    ordem = ["i2c", "uart", "spi"]
    prox = ordem[(ordem.index(tipo_a_confirmar["v"]) + (1 if eh_cw else -1)) % len(ordem)]
    tipo_a_confirmar["v"] = prox
    tipo_confirmado["v"] = False
    atualizar_lcd()

def confirma_tipo():
    """Confirma ciclo i2c -> uart -> spi (acionado pelo botao no Arduino)."""
    tipo_sel.set(tipo_a_confirmar["v"])
    trocar_tipo()
    atualizar_lcd()

# serial
def atualizar_portas():
    """Lista as portas seriais disponiveis no combobox."""
    portas = []
    if SERIAL_OK:
        for p in list_ports.comports():
            portas.append(p.device)
    porta_sel["values"] = portas
    if portas and not porta_sel.get():
        porta_sel.set(portas[0])


def fechar_porta():
    """Fecha a porta serial e marca como desconectado."""
    if ser["obj"] is not None:
        try:
            ser["obj"].close()
        except Exception:
            pass
        ser["obj"] = None
    status.config(text="X desconectado", foreground="gray")


def abrir_porta(event=None):
    """Abre a porta serial escolhida e sincroniza modo/LCD."""
    fechar_porta()
    if not SERIAL_OK:
        status.config(text="X pyserial ausente", foreground="red")
        return
    porta = porta_sel.get()
    if not porta:
        return
    try:
        ser["obj"] = serial.Serial(porta, BAUD, timeout=0.1)
        status.config(text="conectado (" + porta + ")",
                      foreground="green")
        enviar_modo()        # sincroniza a interface e o LCD (o RDY do
        atualizar_lcd()      # Arduino tambem redispara isso apos o reset)
    except Exception as e:
        status.config(text="X erro: " + str(e), foreground="red")


def norm_addr(texto):
    """Normaliza um endereco hex para o formato 0xNN (None se invalido)."""
    try:
        return "0x%02X" % int(texto.strip(), 16)
    except ValueError:
        return None


def detectar_i2c(linha):
    """Auto-deteccao I2C: se a linha for um 'CONN;0xNN' (dispositivo achado
    no barramento), procura no banco um componente com aquele endereco e o
    ativa sozinho. So vale no modo I2C; em UART/SPI a funcao ignora a linha."""
    if tipo["v"] != "i2c":
        return
    partes = linha.split(";")
    if len(partes) < 2:
        return
    if partes[0].strip().upper() != "CONN":
        return

    addr = norm_addr(partes[1])
    if addr is None:
        return

    # procura na lista um componente com esse endereco
    for c in comps["lista"]:
        endereco = c.get("endereco", "")
        if endereco.lower() == addr.lower():
            definir_ativo(c)
            return


def ler_serial():
    """Loop periodico: le a serial e trata BTN/RDY/eventos das interfaces."""
    s = ser["obj"]
    if s is not None:
        try:
            while s.in_waiting:
                linha = s.readline().decode("utf-8", errors="replace")
                texto = linha.strip()
                if not texto:
                    continue
                log(linha)
                if texto == "ENC;CW":
                    proximo_tipo(True)
                elif texto == "ENC;CCW":
                    proximo_tipo(False)
                elif texto == "BTN":            # botao: proxima interface
                    confirma_tipo()
                elif texto == "RDY":          # Arduino (re)iniciou: ressincroniza
                    enviar_modo()
                    atualizar_lcd()
                else:
                    detectar_i2c(linha)
        except Exception as e:
            status.config(text="X desconectado: " + str(e),
                          foreground="red")
            fechar_porta()
    loop_id["v"] = janela.after(200, ler_serial)


def trocar_tipo(event=None):
    """Troca a interface ativa (i2c/uart/spi) e avisa o Arduino."""
    tipo["v"] = tipo_sel.get()
    tipo_a_confirmar["v"] = tipo_sel.get()
    tipo_confirmado["v"] = True
    sel["i"] = None
    comandos["lista"] = []
    definir_ativo(None)          # limpa componente e atualiza o LCD
    montar_forms()
    carregar_comps()
    mostrar_comandos_edit()
    enviar_modo()                


def sair():
    """Fecha tudo e encerra o programa."""
    fechar_porta()
    if loop_id["v"] is not None:
        janela.after_cancel(loop_id["v"])
    janela.destroy()


# ligacoes
tipo_sel.bind("<<ComboboxSelected>>", trocar_tipo)
porta_sel.bind("<<ComboboxSelected>>", abrir_porta)
lista.bind("<<ListboxSelect>>", selecionar)
lista_cmd.bind("<<ListboxSelect>>", selecionar_comando)
janela.protocol("WM_DELETE_WINDOW", sair)

# inicio
montar_forms()
carregar_comps()
atualizar_portas()
abrir_porta()
loop_id["v"] = janela.after(200, ler_serial)
janela.mainloop()
