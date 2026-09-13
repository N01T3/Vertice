"""Explosão analítica: soma, ciclo e preço ausente — as três armadilhas do §6.

Porquê: a fórmula é simples; o que quebra em produção é o caso
degenerado. Cada teste aqui é uma das três armadilhas documentadas.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Literal

import pytest

from core.reference_base.explosion import (
    CicloDetectado,
    ContextoPreco,
    explodir,
)
from core.reference_base.schema import criar_esquema

ID_BASE = 1
UF = "SP"
REGIME: Literal["ONERADO"] = "ONERADO"


@pytest.fixture
def conexao() -> Iterator[sqlite3.Connection]:
    """Banco em memória com o esquema real — sem tocar em disco."""
    conn = sqlite3.connect(":memory:")
    criar_esquema(conn)
    yield conn
    conn.close()


def _item(
    conexao: sqlite3.Connection, codigo: str, tipo: str, descricao: str, unidade: str
) -> None:
    conexao.execute(
        "INSERT INTO item_sinapi "
        "(id_base, codigo, tipo, grupo, descricao, unidade, situacao) "
        "VALUES (?, ?, ?, NULL, ?, ?, NULL)",
        (ID_BASE, codigo, tipo, descricao, unidade),
    )


def _preco(
    conexao: sqlite3.Connection, codigo: str, tipo: str, centavos: int | None
) -> None:
    conexao.execute(
        "INSERT INTO preco_sinapi "
        "(id_base, codigo, tipo, uf, regime, valor_centavos, percentual_as) "
        "VALUES (?, ?, ?, ?, ?, ?, NULL)",
        (ID_BASE, codigo, tipo, UF, REGIME, centavos),
    )


def _filho(
    conexao: sqlite3.Connection, pai: str, codigo: str, tipo: str, coeficiente: str
) -> None:
    conexao.execute(
        "INSERT INTO composicao_item "
        "(id_base, codigo_composicao, tipo_item, codigo_item, coeficiente, situacao) "
        "VALUES (?, ?, ?, ?, ?, NULL)",
        (ID_BASE, pai, tipo, codigo, coeficiente),
    )


def test_explode_dois_niveis_e_soma_correto(conexao: sqlite3.Connection) -> None:
    """`custo = soma(coeficiente x preço)`, recursivo, exatamente como o §6 define."""
    _item(conexao, "CIMENTO", "INSUMO", "Cimento", "KG")
    _preco(conexao, "CIMENTO", "INSUMO", 150)  # R$ 1,50/kg
    _item(conexao, "ARGAMASSA", "COMPOSICAO", "Argamassa", "M2")
    _preco(
        conexao, "ARGAMASSA", "COMPOSICAO", 999
    )  # sintético publicado, só referência
    _filho(conexao, "ARGAMASSA", "CIMENTO", "INSUMO", "2")  # 2 kg por m2

    resultado = explodir(
        conexao, ContextoPreco(ID_BASE, UF, REGIME), "ARGAMASSA", "COMPOSICAO"
    )

    assert resultado.completo
    assert resultado.custo_total_centavos == 300  # 2 x 150
    assert (
        resultado.arvore.custo_unitario_centavos == 999
    )  # sintético preservado à parte


def test_preco_ausente_marca_incompleto_sem_virar_zero(
    conexao: sqlite3.Connection,
) -> None:
    """Armadilha 2: item sem preço na UF não pode devolver zero silencioso."""
    _item(conexao, "TELHA_ESPECIAL", "INSUMO", "Telha especial", "UN")
    _preco(conexao, "TELHA_ESPECIAL", "INSUMO", None)  # sem coleta em SP
    _item(conexao, "TELHADO", "COMPOSICAO", "Telhado", "M2")
    _preco(conexao, "TELHADO", "COMPOSICAO", None)
    _filho(conexao, "TELHADO", "TELHA_ESPECIAL", "INSUMO", "1")

    resultado = explodir(
        conexao, ContextoPreco(ID_BASE, UF, REGIME), "TELHADO", "COMPOSICAO"
    )

    assert resultado.custo_total_centavos is None
    assert not resultado.completo


def test_ciclo_na_cadeia_e_erro_de_importacao_nao_de_calculo(
    conexao: sqlite3.Connection,
) -> None:
    """Armadilha 1: composição que volta a si mesma pela cadeia."""
    _item(conexao, "A", "COMPOSICAO", "A", "UN")
    _item(conexao, "B", "COMPOSICAO", "B", "UN")
    _preco(conexao, "A", "COMPOSICAO", None)
    _preco(conexao, "B", "COMPOSICAO", None)
    _filho(conexao, "A", "B", "COMPOSICAO", "1")
    _filho(conexao, "B", "A", "COMPOSICAO", "1")  # fecha o ciclo

    with pytest.raises(CicloDetectado):
        explodir(conexao, ContextoPreco(ID_BASE, UF, REGIME), "A", "COMPOSICAO")


def test_losango_nao_e_confundido_com_ciclo(conexao: sqlite3.Connection) -> None:
    """Duas composições-irmãs usando o mesmo insumo não é um ciclo."""
    _item(conexao, "AREIA", "INSUMO", "Areia", "KG")
    _preco(conexao, "AREIA", "INSUMO", 10)
    _item(conexao, "REBOCO", "COMPOSICAO", "Reboco", "M2")
    _item(conexao, "CHAPISCO", "COMPOSICAO", "Chapisco", "M2")
    _item(conexao, "PAREDE", "COMPOSICAO", "Parede", "M2")
    _preco(conexao, "REBOCO", "COMPOSICAO", None)
    _preco(conexao, "CHAPISCO", "COMPOSICAO", None)
    _preco(conexao, "PAREDE", "COMPOSICAO", None)
    _filho(conexao, "REBOCO", "AREIA", "INSUMO", "3")
    _filho(conexao, "CHAPISCO", "AREIA", "INSUMO", "1")
    _filho(conexao, "PAREDE", "REBOCO", "COMPOSICAO", "1")
    _filho(conexao, "PAREDE", "CHAPISCO", "COMPOSICAO", "1")

    resultado = explodir(
        conexao, ContextoPreco(ID_BASE, UF, REGIME), "PAREDE", "COMPOSICAO"
    )

    assert resultado.custo_total_centavos == 40  # (3+1) x 10
