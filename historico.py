
import os
import json
from datetime import datetime

from config import EMAIL_DIR
from utilitario import log
from config import ARQ_HIST

os.makedirs(EMAIL_DIR, exist_ok=True)


def normalizar_id(valor):
    try:
        return str(int(float(valor)))
    except (TypeError, ValueError):
        return str(valor).strip()


def carregar_historico():

    if os.path.exists(ARQ_HIST):
        try:
            with open(ARQ_HIST, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            log("Aviso: histórico corrompido/ilegível, iniciando um novo.")
            return {}
    return {}


def salvar_historico(itens_enviados, historico_atual):
    hoje = datetime.now().strftime("%d/%m/%Y")
    for item in itens_enviados:
        historico_atual[str(item)] = hoje

    with open(ARQ_HIST, "w", encoding="utf-8") as f:
        json.dump(historico_atual, f, ensure_ascii=False, indent=2)
