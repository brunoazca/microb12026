"""Formulario generico + a tabela de campos de cada barramento.

Descrevemos os campos numa tabela (CAMPOS) e a classe Formulario monta
os widgets percorrendo essa tabela. Para mudar um formulario, edite a
tabela.

Cada campo e um dict:
    chave   -> nome do campo no JSON
    rotulo  -> texto na tela
    tipo    -> "texto", "int" ou "combo"
    opcoes  -> lista de opcoes (so quando tipo == "combo")
"""

import tkinter as tk
from tkinter import ttk

NIVEIS = ["3,3 V", "5 V", "5 V toler.", "2,8 V"]

TIPOS_I2C = ["acelerometro/IMU", "magnetometro", "temperatura/umidade",
             "pressao", "luz", "distancia/ToF", "ADC/DAC", "PWM",
             "expansor IO", "display", "RTC", "memoria/EEPROM", "gas/CO2",
             "multiplexador", "outro"]

BAUDS = ["300", "600", "1200", "2400", "4800", "9600",
         "19200", "38400", "57600", "115200", "230400"]

# campos do componente, por barramento
CAMPOS = {
    "i2c": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "tipo", "rotulo": "Tipo", "tipo": "combo",
         "opcoes": TIPOS_I2C},
        {"chave": "endereco", "rotulo": "Endereco", "tipo": "texto"},
        {"chave": "enderecos_alt", "rotulo": "Enderecos alt.", "tipo": "texto"},
        {"chave": "velocidade", "rotulo": "Velocidade", "tipo": "combo",
         "opcoes": ["100000", "400000", "1000000"]},
        {"chave": "registrador_id", "rotulo": "Registrador ID",
         "tipo": "texto"},
        {"chave": "valor_id", "rotulo": "Valor ID", "tipo": "texto"},
        {"chave": "nivel_logico", "rotulo": "Nivel logico", "tipo": "combo",
         "opcoes": NIVEIS},
        {"chave": "obs", "rotulo": "Obs", "tipo": "texto"},
    ],
    "uart": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "baud", "rotulo": "Baud", "tipo": "combo", "opcoes": BAUDS},
        {"chave": "frame", "rotulo": "Frame", "tipo": "combo",
         "opcoes": ["8N1", "8E1", "8O1", "8N2", "7E1", "7O1"]},
        {"chave": "timeout", "rotulo": "Timeout (ms)", "tipo": "int"},
        {"chave": "transmite_sozinho", "rotulo": "Transmite sozinho",
         "tipo": "combo", "opcoes": ["nao", "sim", "boot"]},
        {"chave": "tipo_protocolo", "rotulo": "Protocolo", "tipo": "combo",
         "opcoes": ["AT", "binario", "nmea", "passivo"]},
        {"chave": "nivel_logico", "rotulo": "Nivel logico", "tipo": "combo",
         "opcoes": NIVEIS},
    ],
    "spi": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "ss_pin", "rotulo": "Pino SS", "tipo": "int"},
        {"chave": "spi_mode", "rotulo": "Modo SPI", "tipo": "combo",
         "opcoes": ["0", "1", "2", "3"]},
        {"chave": "clock", "rotulo": "Clock (Hz)", "tipo": "int"},
        {"chave": "nivel_logico", "rotulo": "Nivel logico", "tipo": "combo",
         "opcoes": NIVEIS},
        {"chave": "obs", "rotulo": "Obs", "tipo": "texto"},
    ],
}

# campos do editor de comando (o formato muda por barramento)
CAMPOS_COMANDO = {
    "i2c": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "sequencia", "rotulo": "Sequencia (reg:val, ...)",
         "tipo": "texto"},
    ],
    "uart": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "tx", "rotulo": "Comando", "tipo": "texto"},
        {"chave": "modo", "rotulo": "Modo", "tipo": "combo",
         "opcoes": ["T", "H"]},
    ],
    "spi": [
        {"chave": "nome", "rotulo": "Nome", "tipo": "texto"},
        {"chave": "tx", "rotulo": "Registrador (R 0xNN)", "tipo": "texto"},
        {"chave": "esperado", "rotulo": "Esperado", "tipo": "texto"},
    ],
}


class Formulario(ttk.Frame):
    """Monta um rotulo + um widget para cada campo de uma tabela."""

    def __init__(self, pai, campos):
        super().__init__(pai)
        self.campos = campos
        self.widgets = {}

        for linha, campo in enumerate(campos):
            ttk.Label(self, text=campo["rotulo"] + ":").grid(
                row=linha, column=0, sticky="e", padx=5, pady=3)
            if campo["tipo"] == "combo":
                w = ttk.Combobox(self, width=28, values=campo["opcoes"])
            else:
                w = ttk.Entry(self, width=30)
            w.grid(row=linha, column=1, sticky="w", pady=3)
            self.widgets[campo["chave"]] = w

    def limpar(self):
        for w in self.widgets.values():
            w.delete(0, tk.END)

    def preencher(self, dados):
        """Joga os valores de um dict para dentro dos widgets."""
        self.limpar()
        for campo in self.campos:
            valor = dados.get(campo["chave"], "")
            self.widgets[campo["chave"]].insert(0, str(valor))

    def coletar(self):
        """Le os widgets e devolve um dict com os valores."""
        valores = {}
        for campo in self.campos:
            texto = self.widgets[campo["chave"]].get().strip()

            valor = texto
            if campo["tipo"] == "int" and texto:
                valor = int(texto)

            valores[campo["chave"]] = valor
        return valores
