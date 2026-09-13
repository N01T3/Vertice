"""Leitura de `SINAPI_mao_de_obra`: segunda fonte para a recuperação V3.

Porquê: preserva o código da composição de forma independente do
Analítico. VERTICE-modulo-sinapi.md §3.2 exige que os dois caminhos
concordem antes de aceitar um código recuperado.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

import openpyxl

from core.reference_base.adapters.sinapi.spreadsheet import normalizar

_NOME_ABA: str = "SEM Desoneração"
_PRIMEIRA_LINHA_DADO: int = 7


class _LinhaMaoDeObra(NamedTuple):
    grupo: object
    codigo: object
    descricao: object
    unidade: object


def ler_chave_por_codigo(caminho: Path) -> dict[str, tuple[str, str]]:
    """Mapa código → (descrição normalizada, unidade normalizada).

    Porquê: essa aba nunca teve o incidente de código zerado — dá
    para conferir a recuperação feita a partir do Analítico contra
    uma fonte que não passou pelo mesmo problema.
    """
    livro = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    planilha = livro[_NOME_ABA]
    mapa: dict[str, tuple[str, str]] = {}
    for bruta in planilha.iter_rows(min_row=_PRIMEIRA_LINHA_DADO, values_only=True):
        linha = _LinhaMaoDeObra(*bruta[: len(_LinhaMaoDeObra._fields)])
        if linha.codigo is None:
            continue
        descricao = str(linha.descricao) if linha.descricao is not None else None
        unidade = str(linha.unidade) if linha.unidade is not None else None
        codigo = int(Decimal(str(linha.codigo)))
        mapa[str(codigo)] = (normalizar(descricao), normalizar(unidade))
    livro.close()
    return mapa
