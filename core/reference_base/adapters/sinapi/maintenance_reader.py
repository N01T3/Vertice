"""Leitura de `SINAPI_Manutenções`: o arquivo que ninguém lê.

Porquê: sem ele, o app deixa usar composição desativada sem aviso —
VERTICE-modulo-sinapi.md §2.4.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import openpyxl

from core.reference_base.types import RegistroManutencao

_NOME_ABA: str = "Manutenções"
_PRIMEIRA_LINHA_DADO: int = 7
_NUMERO_COLUNAS: int = 5


class _LinhaManutencao(NamedTuple):
    referencia: object
    tipo: object
    codigo: object
    descricao: object
    manutencao: object


def ler_manutencoes(caminho: Path) -> Iterator[RegistroManutencao]:
    """Lê cada evento de manutenção, na ordem em que o arquivo traz."""
    livro = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    planilha = livro[_NOME_ABA]
    for bruta in planilha.iter_rows(min_row=_PRIMEIRA_LINHA_DADO, values_only=True):
        if bruta[0] is None:
            continue
        linha = _LinhaManutencao(*bruta[:_NUMERO_COLUNAS])
        yield RegistroManutencao(
            referencia=str(linha.referencia),
            tipo=str(linha.tipo).strip(),
            codigo=str(linha.codigo).strip(),
            descricao=str(linha.descricao).strip() if linha.descricao else None,
            manutencao=str(linha.manutencao).strip(),
        )
    livro.close()
