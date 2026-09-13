"""V3 e V6 — os portões nascidos do incidente real de código zerado.

Porquê: VERTICE-modulo-sinapi.md §3 documenta um incidente real (10.544
linhas de código zero no pacote 07/2026); estes testes são a âncora
que impede a regressão silenciosa dessa detecção.
"""

from __future__ import annotations

import pytest

from core.reference_base.adapters.sinapi.validation import (
    RecuperacaoDivergente,
    coluna_de_codigo_esta_corrompida,
    conferir_recuperacao_cruzada,
    verificar_referencias_cruzadas,
)
from core.reference_base.types import RegistroComposicaoItem, RegistroItem


def test_coluna_integra_nao_e_marcada_corrompida() -> None:
    """Códigos distintos em toda linha: nada a recuperar."""
    assert not coluna_de_codigo_esta_corrompida([101, 102, 103, 104])


def test_coluna_toda_zero_e_o_incidente_real() -> None:
    """O caso real: 10.544 linhas, todas com código 0."""
    assert coluna_de_codigo_esta_corrompida([0] * 100)


def test_formula_de_hyperlink_conta_como_corrompida() -> None:
    """O incidente de 08/2026: HYPERLINK cacheia 0, não o código real."""
    formulas: list[object] = [f'=HYPERLINK("#...",{n})' for n in range(50)]
    assert coluna_de_codigo_esta_corrompida(formulas)


def test_recuperacao_cruzada_aceita_quando_os_dois_caminhos_concordam() -> None:
    """S02: recuperação válida quando Analítico e mão de obra concordam."""
    recuperacao = {("piso", "m2"): "104658"}
    mao_de_obra = {"104658": ("piso", "m2")}
    conferir_recuperacao_cruzada(recuperacao, mao_de_obra)  # não deve lançar


def test_recuperacao_cruzada_aborta_em_divergencia() -> None:
    """S03: chave ambígua entre as duas fontes aborta, nunca escolhe."""
    recuperacao = {("piso", "m2"): "104658"}
    mao_de_obra = {"999999": ("piso", "m2")}
    with pytest.raises(RecuperacaoDivergente):
        conferir_recuperacao_cruzada(recuperacao, mao_de_obra)


def test_v6_acusa_item_sem_catalogo() -> None:
    """V6: item do Analítico sem catálogo correspondente vira alerta, não exceção."""
    itens = [
        RegistroComposicaoItem(
            codigo_composicao="1",
            tipo_item="INSUMO",
            codigo_item="999",
            coeficiente="1",
            situacao=None,
        )
    ]
    alertas = verificar_referencias_cruzadas(
        itens, catalogo_insumos={}, catalogo_composicoes={}
    )
    assert len(alertas) == 1
    assert "999" in alertas[0]


def test_v6_silencioso_quando_catalogo_cobre_tudo() -> None:
    """Sem órfão, sem alerta — V6 não deve gerar ruído em base íntegra."""
    item = RegistroItem(
        codigo="999",
        tipo="INSUMO",
        grupo=None,
        descricao="x",
        unidade="un",
        situacao=None,
    )
    itens = [
        RegistroComposicaoItem(
            codigo_composicao="1",
            tipo_item="INSUMO",
            codigo_item="999",
            coeficiente="1",
            situacao=None,
        )
    ]
    alertas = verificar_referencias_cruzadas(
        itens, catalogo_insumos={"999": item}, catalogo_composicoes={}
    )
    assert alertas == []
