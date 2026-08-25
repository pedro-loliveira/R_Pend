import time
from datetime import datetime, timedelta

from config import RETRY_LIMIT_MIN, RETRY_INTERVAL
from utilitario import log


def enviar_email(mail):
    """Tenta enviar o e-mail por até RETRY_LIMIT_MIN minutos."""
    log("Tentando enviar o email!")
    inicio = datetime.now()

    while True:
        try:
            mail.Send()
            log("Email enviado corretamente!")
            return True
        except Exception as e:
            if (datetime.now() - inicio) > timedelta(minutes=RETRY_LIMIT_MIN):
                log("Email não enviado, cancelando o envio de qualquer email pendente!")
                return False
            log(f"Falha ao enviar, tentando novamente... ({str(e)[:80]})")
            time.sleep(RETRY_INTERVAL)
