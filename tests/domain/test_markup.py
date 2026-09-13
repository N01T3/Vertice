"""calcular_markup — ADR-019: fórmula é dado do pacote, núcleo só avalia.

Porquê testar rejeição tão quanto aceitação: a fórmula vem de um
arquivo YAML de pacote (VERTICE-plataforma.md §3.1) — um pacote mal
escrito não pode virar execução de código arbitrário.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from core.domain.markup import FormulaDeMarkupInvalida, calcular_markup

FORMULA_BDI_ANALITICO_BR = "((1+AC+SG+R)*(1+DF)*(1+L))/(1-(PIS+COFINS+ISS+CPRB))-1"


def test_formula_bdi_analitico_br_bate_com_a_conta_manual() -> None:
    """A fórmula declarada em VERTICE-plataforma.md §3, avaliada por nome."""
    parcelas = {
        "AC": Decimal("0.04"),
        "SG": Decimal("0.008"),
        "R": Decimal("0.0104"),
        "DF": Decimal("0.0059"),
        "L": Decimal("0.099"),
        "PIS": Decimal("0.0065"),
        "COFINS": Decimal("0.03"),
        "ISS": Decimal("0.05"),
        "CPRB": Decimal("0"),
    }
    esperado = (
        (1 + parcelas["AC"] + parcelas["SG"] + parcelas["R"])
        * (1 + parcelas["DF"])
        * (1 + parcelas["L"])
    ) / (
        1 - (parcelas["PIS"] + parcelas["COFINS"] + parcelas["ISS"] + parcelas["CPRB"])
    ) - 1
    assert calcular_markup(FORMULA_BDI_ANALITICO_BR, parcelas) == esperado


def test_formula_simples_soma_e_subtracao() -> None:
    assert (
        calcular_markup("A+B-C", {"A": Decimal(10), "B": Decimal(5), "C": Decimal(3)})
        == 12
    )


def test_unario_negativo() -> None:
    assert calcular_markup("-A", {"A": Decimal(5)}) == -5


def test_parcela_nao_declarada_aborta_sem_adivinhar() -> None:
    with pytest.raises(FormulaDeMarkupInvalida):
        calcular_markup("A+B", {"A": Decimal(1)})


def test_sintaxe_invalida_aborta() -> None:
    with pytest.raises(FormulaDeMarkupInvalida):
        calcular_markup("A + * B", {"A": Decimal(1), "B": Decimal(1)})


def test_literal_fracionario_e_recusado() -> None:
    """Fração solta na fórmula devia ser parcela, não número mágico."""
    with pytest.raises(FormulaDeMarkupInvalida):
        calcular_markup("A*1.5", {"A": Decimal(1)})


@pytest.mark.parametrize(
    "formula",
    [
        "__import__('os').system('echo x')",
        "A.upper()",
        "[A for A in range(3)]",
        "A if A else B",
    ],
)
def test_formula_fora_da_aritmetica_e_recusada(formula: str) -> None:
    """VERTICE-plataforma.md §3.1: pacote declara expressão, nunca código."""
    with pytest.raises(FormulaDeMarkupInvalida):
        calcular_markup(formula, {"A": Decimal(1), "B": Decimal(2)})
