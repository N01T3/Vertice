"""Busca textual na base — interface pública `buscar` de arquitetura §3.

Porquê: FTS5, não `LIKE` — VERTICE-modulo-sinapi.md §12 exige resposta
abaixo de 100 ms sobre ~15 mil itens de catálogo por base.
"""

from __future__ import annotations

import sqlite3

from core.reference_base.constants import NOME_TABELA_FTS
from core.reference_base.query_results import ResultadoBusca

LIMITE_PADRAO: int = 20


def buscar(
    conexao: sqlite3.Connection,
    termo: str,
    id_base: int | None = None,
    limite: int = LIMITE_PADRAO,
) -> list[ResultadoBusca]:
    """Busca por relevância textual, com acento e caixa ignorados.

    Porquê: `remove_diacritics 2` do esquema já resolve acento; aqui
    só falta compor o filtro opcional de base e devolver tipado.
    """
    termo_fts = _termo_como_prefixo(termo)
    sql = (
        f"SELECT codigo, tipo, descricao, grupo, unidade, id_base "
        f"FROM {NOME_TABELA_FTS} WHERE {NOME_TABELA_FTS} MATCH ?"
    )
    parametros: list[object] = [termo_fts]
    if id_base is not None:
        sql += " AND id_base = ?"
        parametros.append(id_base)
    sql += " ORDER BY rank LIMIT ?"
    parametros.append(limite)
    linhas = conexao.execute(sql, parametros).fetchall()
    return [
        ResultadoBusca(
            codigo=codigo,
            tipo=tipo,
            descricao=descricao,
            grupo=grupo,
            unidade=unidade,
            id_base=id_base_linha,
        )
        for codigo, tipo, descricao, grupo, unidade, id_base_linha in linhas
    ]


def _termo_como_prefixo(termo: str) -> str:
    """Cada palavra do termo vira busca por prefixo — resultado parcial digitado."""
    palavras = [p for p in termo.strip().split() if p]
    return " ".join(f"{_escapar(p)}*" for p in palavras) or '""'


def _escapar(palavra: str) -> str:
    """Aspas duplas dentro do termo quebrariam a sintaxe de FTS5."""
    return '"' + palavra.replace('"', '""') + '"'
