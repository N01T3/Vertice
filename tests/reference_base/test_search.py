"""Busca textual: S12 (acento) e o filtro por base.

Porquê: `remove_diacritics 2` é a linha mais fácil de quebrar num
rename de dependência — sem teste, ninguém percebe até o suporte ligar.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

import pytest

from core.reference_base.schema import criar_esquema
from core.reference_base.search import buscar

NOME_TABELA_FTS = "busca_sinapi"


@pytest.fixture
def conexao() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    criar_esquema(conn)
    linhas = [
        (
            "87622",
            "COMPOSICAO",
            "IMPERMEABILIZAÇÃO DE LAJE COM MANTA ASFÁLTICA",
            "Grupo",
            "M2",
            1,
        ),
        ("12345", "INSUMO", "AREIA MÉDIA LAVADA", "Grupo", "M3", 1),
        ("99999", "COMPOSICAO", "PISO CERÂMICO", "Grupo", "M2", 2),
    ]
    conn.executemany(
        f"INSERT INTO {NOME_TABELA_FTS} "
        "(codigo, descricao, grupo, unidade, tipo, id_base) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(c, d, g, u, t, b) for c, t, d, g, u, b in linhas],
    )
    yield conn
    conn.close()


def test_busca_ignora_acento_e_caixa(conexao: sqlite3.Connection) -> None:
    """S12: 'impermeabilizacao' encontra 'IMPERMEABILIZAÇÃO'."""
    resultados = buscar(conexao, "impermeabilizacao")
    assert any(r.codigo == "87622" for r in resultados)


def test_busca_filtra_por_base(conexao: sqlite3.Connection) -> None:
    """Duas bases coexistem (§4 do módulo); a busca respeita o filtro."""
    resultados = buscar(conexao, "piso", id_base=1)
    assert resultados == []
    resultados = buscar(conexao, "piso", id_base=2)
    assert any(r.codigo == "99999" for r in resultados)


def test_busca_por_prefixo_encontra_termo_parcial(conexao: sqlite3.Connection) -> None:
    """Digitação incompleta ainda deve achar — planilha viva, não formulário."""
    resultados = buscar(conexao, "arei")
    assert any(r.codigo == "12345" for r in resultados)
