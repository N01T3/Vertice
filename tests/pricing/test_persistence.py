"""orcamento, bdi e fonte: ida e volta no banco, sem perder precisão.

Porquê a âncora do CME aparece de novo aqui: salvar e reler as
parcelas precisa devolver exatamente o que calcula 23,6245% — se a
volta do banco perder uma casa decimal, o teste pega antes do usuário.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from decimal import Decimal

import pytest

from core.pricing.bdi import ParcelasBdi, calcular_bdi
from core.pricing.persistence import (
    buscar_orcamento,
    carregar_bdi,
    criar_orcamento,
    inserir_fonte,
    salvar_bdi,
)
from core.pricing.schema import criar_esquema as criar_esquema_pricing
from core.pricing.types import Fonte, Orcamento, RegistroBdi
from core.reference_base.schema import criar_esquema as criar_esquema_reference_base

FORMULA_BDI_ANALITICO_BR = "((1+AC+SG+R)*(1+DF)*(1+L))/(1-(PIS+COFINS+ISS+CPRB))-1"

PARCELAS_CME = ParcelasBdi(
    administracao_central=Decimal("0.0401"),
    seguro_garantia=Decimal("0.0032"),
    risco=Decimal("0.0050"),
    despesas_financeiras=Decimal("0.0102"),
    lucro=Decimal("0.0664"),
    pis=Decimal("0.0065"),
    cofins=Decimal("0.0300"),
    iss=Decimal("0.0500"),
    cprb=Decimal("0"),
)


@pytest.fixture
def conexao() -> Iterator[sqlite3.Connection]:
    """Esquema de `reference_base` primeiro — `orcamento.id_base` referencia lá."""
    conn = sqlite3.connect(":memory:")
    criar_esquema_reference_base(conn)
    criar_esquema_pricing(conn)
    conn.execute(
        "INSERT INTO base_referencia "
        "(id, mes_referencia, data_emissao, arquivo_nome, arquivo_hash, "
        "importado_em, codigo_recuperado, total_composicoes, total_insumos) "
        "VALUES (1, '2026-08', '2026-08-11', 'x.xlsx', 'hash', "
        "datetime('now'), 0, 0, 0)"
    )
    conn.commit()
    yield conn
    conn.close()


def test_orcamento_sem_regime_nao_compila() -> None:
    """§2.2 regra 1: regime é obrigatório — o tipo não tem valor padrão."""
    with pytest.raises(TypeError):
        Orcamento(
            identificacao="X", uf="SP", id_base=1, data_base="2026-08", id_origem="x"
        )  # type: ignore[call-arg]


def test_orcamento_grava_e_le_de_volta(conexao: sqlite3.Connection) -> None:
    orcamento = Orcamento(
        identificacao="Reforma CME",
        regime="ONERADO",
        uf="SP",
        id_base=1,
        data_base="2026-08",
        id_origem="USUARIO:rt-01#2026-09-13T14:00",
    )
    id_orcamento = criar_orcamento(conexao, orcamento)
    lido = buscar_orcamento(conexao, id_orcamento)
    assert lido == orcamento


def test_orcamento_inexistente_devolve_none(conexao: sqlite3.Connection) -> None:
    assert buscar_orcamento(conexao, 999) is None


def test_bdi_ida_e_volta_reproduz_a_ancora_do_cme(conexao: sqlite3.Connection) -> None:
    """Salvar e reler não pode perder precisão — o BDI recalculado tem que bater."""
    orcamento = Orcamento(
        identificacao="Reforma CME",
        regime="ONERADO",
        uf="SP",
        id_base=1,
        data_base="2026-08",
        id_origem="USUARIO:rt-01#2026-09-13T14:00",
    )
    id_orcamento = criar_orcamento(conexao, orcamento)
    registro = RegistroBdi(
        id_orcamento=id_orcamento,
        parcelas=PARCELAS_CME,
        municipio_iss="Cerqueira César",
        base_iss=Decimal("1.00"),
        id_origem="USUARIO:rt-01#2026-09-13T14:05",
    )

    salvar_bdi(conexao, registro)
    lido = carregar_bdi(conexao, id_orcamento)

    assert lido is not None
    assert lido.parcelas == PARCELAS_CME
    assert lido.municipio_iss == "Cerqueira César"
    bdi = calcular_bdi(FORMULA_BDI_ANALITICO_BR, lido.parcelas)
    assert round(bdi, 4) == Decimal("0.2362")


def test_bdi_sem_registro_devolve_none(conexao: sqlite3.Connection) -> None:
    orcamento = Orcamento("X", "ONERADO", "SP", 1, "2026-08", "USUARIO:x#1")
    id_orcamento = criar_orcamento(conexao, orcamento)
    assert carregar_bdi(conexao, id_orcamento) is None


def test_salvar_bdi_de_novo_substitui_nao_acumula(conexao: sqlite3.Connection) -> None:
    """Revisar uma parcela antes do orçamento fechar é normal, não duplicação."""
    orcamento = Orcamento("X", "ONERADO", "SP", 1, "2026-08", "USUARIO:x#1")
    id_orcamento = criar_orcamento(conexao, orcamento)
    primeiro = RegistroBdi(
        id_orcamento, PARCELAS_CME, "Cerqueira César", Decimal("1"), "USUARIO:x#2"
    )
    salvar_bdi(conexao, primeiro)

    parcelas_revisadas = ParcelasBdi(**{**vars(PARCELAS_CME), "lucro": Decimal("0.08")})
    segundo = RegistroBdi(
        id_orcamento, parcelas_revisadas, "Cerqueira César", Decimal("1"), "USUARIO:x#3"
    )
    salvar_bdi(conexao, segundo)

    total = conexao.execute(
        "SELECT COUNT(*) FROM bdi WHERE id_orcamento = ?", (id_orcamento,)
    ).fetchone()[0]
    assert total == 1
    lido = carregar_bdi(conexao, id_orcamento)
    assert lido is not None
    assert lido.parcelas.lucro == Decimal("0.08")


def test_fonte_grava_e_devolve_id(conexao: sqlite3.Connection) -> None:
    fonte = Fonte(
        tipo="PÚBLICA",
        nome="Cerqueira César",
        item="Quadro de composição BDI",
        data_base="2026-08",
        confiabilidade="PUBLICA_REGIONAL",
        url="https://www.cerqueiracesar.sp.gov.br/",
    )
    id_fonte = inserir_fonte(conexao, fonte)
    assert id_fonte > 0
