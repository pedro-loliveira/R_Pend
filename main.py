import os
import time
import warnings
from datetime import datetime

from Dados.API_ig import processa_api
from Dados.SQLQUERY_ig import processa_sql

from config import EMAIL_DIR, ASSINATURA_PATH, HORARIOS_EXECUCAO, ENVIAR_EMAIL
from utilitario import log
from processar import tratar_processos_api, tratar_colunas
from historico import carregar_historico, salvar_historico, normalizar_id
from gerar_htmls import criar_email
from enviar_email import enviar_email

warnings.filterwarnings("ignore", category=UserWarning)
os.makedirs(EMAIL_DIR, exist_ok=True)


def gerar_relatorio_email():
    ts = datetime.now().strftime("%d%m%y_%H%M%S")
    arquivo_email = os.path.join(EMAIL_DIR, f"Relatorio_{ts}.msg")

    log("Iniciando processo...")
    df_api = processa_api()
    df_api = tratar_processos_api(df_api)
    df_sql = processa_sql()

    log("Tratando dados e aplicando filtros...")
    df_final = tratar_colunas(df_api, df_sql)

    if df_final.empty:
        log("Nenhum item pendente encontrado. Email não será gerado.")
        return

    # marcar quais itens apareceram em anteriores
    historico = carregar_historico()
    ids_normalizados = df_final["op"].apply(normalizar_id)
    df_final["ITEM_REPETIDO"] = ids_normalizados.isin(historico.keys())

    mail, total_itens = criar_email(df_final, ASSINATURA_PATH, arquivo_email)
    log(f"Email criado com {total_itens} itens como pendência!")

    if not ENVIAR_EMAIL:
        log(f"MODO TESTE (ENVIAR_EMAIL=False): email NÃO enviado. "
            f"Arquivo salvo em: {arquivo_email}")
        log("Histórico não atualizado (modo teste).")
        return

    enviado = enviar_email(mail)

    if enviado:
        salvar_historico(ids_normalizados.tolist(), historico)
    else:
        log("Histórico não atualizado (email não enviado).")


if __name__ == "__main__":
    print(f"\n{'>' * 15} {datetime.now().strftime('%d/%m/%Y')} {'<' * 15}")
    log("Aguardando horários programados... HORARIOS_EXECUCAO: " +
        ", ".join(HORARIOS_EXECUCAO))

    while True:
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")
        dia_semana = agora.weekday()  # 0 = segunda, 6 = domingo

        if dia_semana < 5 and hora_atual in HORARIOS_EXECUCAO:
            print(f"\n{'>' * 15} {agora.strftime('%d/%m/%Y')} {'<' * 15}")
            log(f"Execução agendada iniciada ({hora_atual})")
            try:
                gerar_relatorio_email()
            except Exception as e:
                log(f"Erro inesperado: {e}")

            time.sleep(60)

        time.sleep(60)
