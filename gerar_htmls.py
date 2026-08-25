

import html
from datetime import datetime

import pandas as pd
import win32com.client as win32

from styles import CORES, FONTE
from config import DESTINATARIOS_TO, DESTINATARIOS_CC


def _valor_e_zero(valor):

    if valor in (None, ""):
        return True
    try:
        return float(valor) == 0
    except (TypeError, ValueError):
        return False


def saudacao():
    hora = datetime.now().hour
    return "Bom dia" if hora < 12 else "Boa tarde"


def gerar_faixa_estatisticas_html(total_itens, nao_pagas, pagas, zeradas, repetidos):

    def card(valor, label, alerta=False):
        fundo = CORES["card_fundo_alerta"] if alerta else CORES["card_fundo"]
        cor_valor = CORES["card_valor_alerta"] if alerta else CORES["card_valor"]
        return (
            f"<td style=\"padding:4px;\">"
            f"<div style=\"background:{fundo}; border:1px solid {CORES['card_borda']}; "
            f"border-radius:10px; padding:12px 10px; text-align:center;\">"
            f"<div style=\"font-family:{FONTE}; font-size:20px; font-weight:700; "
            f"color:{cor_valor};\">{valor}</div>"
            f"<div style=\"font-family:{FONTE}; font-size:10px; letter-spacing:0.5px; "
            f"text-transform:uppercase; color:{CORES['card_label']}; margin-top:2px;\">"
            f"{label}</div></div></td>"
        )

    celulas = (
        card(total_itens, "Total")
        + card(nao_pagas, "Separacao Pend.")
        + card(pagas, "Em Processo")
        + card(zeradas, "Falha de Prod.", alerta=True)
        + card(repetidos, "Persistentes")
    )

    return (
        "<table border='0' cellpadding='0' cellspacing='0' "
        "style=\"width:100%; border-collapse:separate; margin-bottom:18px;\">"
        f"<tr>{celulas}</tr></table>"
    )


def gerar_tabela_html(df, colunas):

    ths = "".join(
        f"<th style=\"text-align:left; padding:10px; font-family:{FONTE}; "
        f"font-size:11px; text-transform:uppercase; letter-spacing:0.5px; "
        f"font-weight:600; color:{CORES['tabela_texto_cabecalho']}; "
        f"background:{CORES['tabela_fundo_cabecalho']};\">"
        f"{html.escape(str(titulo))}</th>"
        for _, titulo in colunas
    )

    linhas_html = ""
    for i, (_, row) in enumerate(df.reset_index(drop=True).iterrows()):
        repetido = bool(row.get("ITEM_REPETIDO", False))
        fundo_linha = CORES["linha_repetida"] if repetido else (
            CORES["linha_zebra"] if i % 2 == 1 else CORES["linha_fundo"]
        )
        barra = CORES["barra_repetida"] if repetido else CORES["barra_padrao"]

        tds = ""
        for j, (chave, _) in enumerate(colunas):
            bruto = row.get(chave)
            valor = "" if pd.isna(bruto) else str(bruto)
            cor_texto = CORES["texto_padrao"]
            conteudo = html.escape(valor)

            if chave == "STATUS_SISTEMA" and valor == "ERRO!":
                cor_texto = CORES["texto_zerado"]
            elif chave in ("tempo", "realizado") and _valor_e_zero(bruto):
                cor_texto = CORES["texto_zerado"]
            elif chave == "STATUS_SAIDA" and valor.startswith("SEPARADO:"):
                conteudo = (
                    f"<span style=\"background:{CORES['badge_pago_fundo']}; "
                    f"color:{CORES['badge_pago_texto']}; padding:2px 8px; "
                    f"border-radius:999px; font-size:11px; font-weight:600;\">"
                    f"{conteudo}</span>"
                )

            borda_esquerda = (
                f"border-left:3px solid {barra};" if j == 0 else ""
            )
            estilo = (
                f"padding:9px 10px; font-family:{FONTE}; font-size:12px; "
                f"color:{cor_texto}; {borda_esquerda}"
            )
            tds += f"<td style=\"{estilo}\">{conteudo}</td>"

        linhas_html += f"<tr style=\"background:{fundo_linha};\">{tds}</tr>"

    return (
        "<table border='0' cellpadding='0' cellspacing='0' "
        "style=\"width:100%; border-collapse:collapse; border-radius:8px; "
        "overflow:hidden;\">"
        f"<tr>{ths}</tr>{linhas_html}</table>"
    )


def criar_email(df, assinatura_path, caminho_email):
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItemFromTemplate(assinatura_path)
    mail.Subject = "Itens Finalizados Pendentes"

    df_pendencias = df[df["STATUS_SISTEMA"] != "ERRO!"]
    df_problemas = df[df["STATUS_SISTEMA"] == "ERRO!"]
    total_itens = len(df)
    nao_pagas = df["STATUS_SAIDA"].eq("SEPARACAO PEND.").sum()
    pagas = df["STATUS_SAIDA"].str.startswith(
        "SEPARADO:", na=False).sum()
    zeradas = len(df_problemas)
    repetidos = int(df.get("ITEM_REPETIDO", pd.Series(dtype=bool)).sum())

    paragrafo = (
        f"<div style=\"font-family:{FONTE}; font-size:14px; line-height:1.7; "
        f"color:{CORES['texto_padrao']}; margin-bottom:14px;\">"
        f"{saudacao()},<br>"
        f"Relatorio de material produzido com pendência de atualização sistêmica.<br>"
        f"Materiais com status <b>\"ERRO!\"</b> foram apontados com falha e necessita de atenção.</div><br>"
    )

    legenda = (
        f"<div style=\"font-family:{FONTE}; font-size:13px; line-height:1.7; "
        f"color:{CORES['texto_padrao']}; margin-bottom:18px;\">"
        f"As informações <b>P1, P2, P3</b> fazem parte do mapa de processos de cada Material, "
        "em ordem.<br>"
        f"Materiais destacados são considarados <b>\"Persistentes\"</b>, que já apareceram em "
        "relatórios anteriores e prosseguem pendentes de atualizações.</div>"
    )

    colunas_tabela = [
        ("op", "ID"), ("codigo", "Material"), ("cliente", "CL"),
        ("tempo", "Tempo Prod."), ("realizado", "Quantidade Prod."),
        ("prc1", "P1"), ("prc2", "P2"), ("prc3", "P3"),
        ("STATUS_SISTEMA", "Producao"), ("STATUS_SAIDA", "Sitema"),
    ]
    colunas_tabela = [(c, t) for c, t in colunas_tabela if c in df.columns]

    bloco_pendencias = ""
    if not df_pendencias.empty:
        bloco_pendencias = (
            f"<div style=\"font-family:{FONTE}; font-size:13px; font-weight:bold; "
            f"color:{CORES['texto_padrao']}; margin:18px 0 8px;\">"
            "Materiais pendentes de atualizações</div>"
            + gerar_tabela_html(df_pendencias, colunas_tabela)
        )

    bloco_problemas = ""
    if not df_problemas.empty:
        bloco_problemas = (
            f"<div style=\"font-family:{FONTE}; font-size:13px; font-weight:bold; "
            f"color:{CORES['texto_padrao']}; margin:20px 0 8px;\">"
            "Materiais pendentes porem com <b>Erro</b>. Aguardando resposta dos responsaveis pela producao."
            + gerar_tabela_html(df_problemas, colunas_tabela)
        )

    corpo_email = (
        paragrafo
        + gerar_faixa_estatisticas_html(total_itens,
                                        nao_pagas, pagas, zeradas, repetidos)
        + legenda
        + bloco_pendencias
        + bloco_problemas
    )

    mail.HTMLBody = f"{corpo_email}{mail.HTMLBody}"
    mail.To = "; ".join(DESTINATARIOS_TO)
    mail.CC = "; ".join(DESTINATARIOS_CC)
    mail.SaveAs(caminho_email)

    return mail, total_itens
