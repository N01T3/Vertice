"""Extração de mês de referência e data de emissão do próprio arquivo.

Porquê: VERTICE-modulo-sinapi.md §2.2 — "as células de cabeçalho
carregam tudo que o app precisa... sem perguntar nada ao usuário".
O nome do arquivo nunca é a fonte: S11 exige identificar pelo
cabeçalho, não pelo nome.
"""

from __future__ import annotations

import openpyxl

from core.reference_base.adapters.sinapi.spreadsheet import normalizar

_LIMITE_LINHAS_METADADO: int = 6
_ROTULO_MES: str = "MES DE REFERENCIA:"
_ROTULO_EMISSAO: str = "DATA DE EMISSAO:"


def ler_metadados(livro: openpyxl.Workbook, aba: str) -> tuple[str, str]:
    """Devolve (mês de referência, data de emissão) lidos do cabeçalho.

    Porquê `livro` já aberto, não `Path`: usar qualquer aba do arquivo
    funciona — o cabeçalho se repete em todas — e o chamador já tem o
    arquivo aberto para outra leitura; abrir de novo custaria segundos
    medidos no pacote real (§12 do documento).
    """
    planilha = livro[aba]
    mes_referencia: str | None = None
    data_emissao: str | None = None
    for linha in planilha.iter_rows(
        min_row=1, max_row=_LIMITE_LINHAS_METADADO, values_only=True
    ):
        if not linha:
            continue
        rotulo = normalizar(linha[0] if linha[0] else None)
        if rotulo == _ROTULO_MES and len(linha) > 1:
            mes_referencia = str(linha[1]).strip()
        elif rotulo == _ROTULO_EMISSAO and len(linha) > 1:
            data_emissao = str(linha[1]).strip()
    if mes_referencia is None or data_emissao is None:
        raise ValueError(f"metadados não encontrados na aba {aba}")
    return mes_referencia, data_emissao
