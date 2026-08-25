

import pandas as pd

from config import MAP_PROCESSOS


def tratar_processos_api(df_api):
    cols = [
        "processo-1-nome",
        "processo-2-nome",
        "processo-3-nome",
    ]
    cols_existentes = [c for c in cols if c in df_api.columns]

    if cols_existentes:
        df_api[cols_existentes] = df_api[cols_existentes].replace(
            MAP_PROCESSOS)

    df_api = df_api.rename(columns={
        "processo-1-nome": "prc1",
        "processo-2-nome": "prc2",
        "processo-3-nome": "prc3",
    })

    return df_api


def tratar_colunas(df_api, df_sql):
    df = pd.merge(df_api, df_sql, on="op", how="inner")

    def calcula_status_sistema(row):
        encerrado = row.get("encerramento") or row.get("encerrado")
        realizado = str(row.get("realizado")).strip()
        if pd.notna(encerrado) and encerrado != "":
            if realizado in ("", "0", "None", None):
                return "ERRO!"
            return f"Prod.: {encerrado}"
        return None

    df = df.sort_values("encerramento", ascending=True)
    df["STATUS_SISTEMA"] = df.apply(calcula_status_sistema, axis=1)

    def trata_data(valor, prefixo):
        if valor in ("00000000", 0, "", None):
            return "SEP. PENDENTE"
        try:
            dt = pd.to_datetime(str(valor), format="%Y%m%d")
            return f"{prefixo}:{dt.strftime('%d/%m/%y')}"
        except Exception:
            return None

    def calcula_status_saida(row):
        dt_ter = str(row.get("dt_ter", "00000000")).strip()
        dt_efet = str(row.get("dt_efet", "00000000")).strip()
        if dt_ter not in ("00000000", "0", "", None):
            return trata_data(dt_ter, "ENC")
        elif dt_efet not in ("00000000", "0", "", None):
            return trata_data(dt_efet, "SEPARADO")
        return "SEPARACAO PEND."

    df["STATUS_SAIDA"] = df.apply(calcula_status_saida, axis=1)

    mask = df["STATUS_SISTEMA"].str.contains("Prod.:", regex=False, na=False)
    mask = mask & ~df["STATUS_SAIDA"].str.contains(
        "ENC:", regex=False, na=False)
    df = df.loc[mask]

    colunas = [
        "op", "codigo", "cliente",
        "tempo", "realizado",
        "prc1", "prc2", "prc3",
        "STATUS_SISTEMA", "STATUS_SAIDA",
    ]
    return df[[c for c in colunas if c in df.columns]]
