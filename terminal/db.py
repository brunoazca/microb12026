"""Leitura e escrita do banco de componentes (JSON).

Cada barramento tem um arquivo em
terminal/data/componentes_<barramento>.json, e o arquivo e apenas
a lista de componentes:

"""

import json
import os

PASTA = os.path.join(os.path.dirname(__file__), "data")


def caminho(barramento):
    """Caminho do arquivo JSON daquele barramento."""
    return os.path.join(PASTA, "componentes_" + barramento + ".json")


def carregar(barramento):
    """Le o arquivo e devolve a lista de componentes (vazia se nao existir)."""
    arq = caminho(barramento)
    if not os.path.exists(arq):
        return []
    with open(arq, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar(barramento, componentes):
    """Grava a lista de componentes no arquivo."""
    with open(caminho(barramento), "w", encoding="utf-8") as f:
        json.dump(componentes, f, indent=2, ensure_ascii=False)
