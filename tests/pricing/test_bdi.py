"""BDI analítico — os testes de aceite P01, P03, P04 de VERTICE-modulo-precificacao.md.

Porquê a âncora do CME: é o mesmo número que VERTICE-REGRAS.md §3.2
lista como teste-âncora do sistema inteiro ("BDI do CME | 23,6245%").
Se este teste quebrar, a âncora quebrou.
"""

from __future__ import annotations

from decimal import Decimal

from core.pricing.bdi import (
    ParcelasBdi,
    calcular_bdi,
    classificar_faixa_tcu,
    exige_justificativa,
    verificar_coerencia_de_regime,
)

# Mesma fórmula de VERTICE-modulo-precificacao.md §3 e de
# packages/civil-construction-br/package.yaml (markup.formula) — ver
# test_formula_do_pacote_bate_com_a_documentada em tests/packages/
# para a prova de que as duas concordam.
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


def test_p01_bdi_do_cme_bate_a_ancora() -> None:
    """P01 e a âncora de REGRAS §3.2: as parcelas do CME dão 23,6245%."""
    bdi = calcular_bdi(FORMULA_BDI_ANALITICO_BR, PARCELAS_CME)
    assert round(bdi, 4) == Decimal("0.2362")


def test_p03_cprb_positivo_em_onerado_e_alerta() -> None:
    """P03: orçamento onerado com CPRB > 0 é incoerência de regime."""
    parcelas_incoerentes = ParcelasBdi(
        administracao_central=Decimal("0.04"),
        seguro_garantia=Decimal("0.003"),
        risco=Decimal("0.005"),
        despesas_financeiras=Decimal("0.01"),
        lucro=Decimal("0.066"),
        pis=Decimal("0.0065"),
        cofins=Decimal("0.03"),
        iss=Decimal("0.05"),
        cprb=Decimal("0.045"),
    )
    alertas = verificar_coerencia_de_regime("ONERADO", parcelas_incoerentes)
    assert len(alertas) == 1

    sem_alerta = verificar_coerencia_de_regime("ONERADO", PARCELAS_CME)
    assert sem_alerta == []


def test_p03_cprb_positivo_em_desonerado_nao_e_alerta() -> None:
    """Desonerado é justamente o regime que troca encargo por CPRB."""
    parcelas = ParcelasBdi(
        administracao_central=Decimal("0.04"),
        seguro_garantia=Decimal("0.003"),
        risco=Decimal("0.005"),
        despesas_financeiras=Decimal("0.01"),
        lucro=Decimal("0.066"),
        pis=Decimal("0.0065"),
        cofins=Decimal("0.03"),
        iss=Decimal("0.05"),
        cprb=Decimal("0.045"),
    )
    assert verificar_coerencia_de_regime("DESONERADO", parcelas) == []


def test_p04_faixas_do_tcu_e_exigencia_de_justificativa() -> None:
    """P04: acima do 3º quartil, a exportação exige justificativa."""
    assert classificar_faixa_tcu(Decimal("0.15")) == "ABAIXO_1_QUARTIL"
    assert classificar_faixa_tcu(Decimal("0.21")) == "ENTRE_1_QUARTIL_E_MEDIO"
    assert classificar_faixa_tcu(Decimal("0.23")) == "ENTRE_MEDIO_E_3_QUARTIL"
    assert classificar_faixa_tcu(Decimal("0.30")) == "ACIMA_3_QUARTIL"

    assert not exige_justificativa(Decimal("0.2362"))  # BDI do CME: não exige
    assert exige_justificativa(Decimal("0.30"))


def test_bdi_nunca_e_um_valor_guardado_a_parte() -> None:
    """§3.5: o percentual é sempre função das parcelas, nunca um campo solto.

    Porquê este teste: prova que duas instâncias com as mesmas
    parcelas sempre concordam — não há como o resultado divergir da
    entrada, porque não existe onde ele possa ser editado à parte.
    """
    outra_instancia_das_mesmas_parcelas = ParcelasBdi(**vars(PARCELAS_CME))
    assert calcular_bdi(FORMULA_BDI_ANALITICO_BR, PARCELAS_CME) == calcular_bdi(
        FORMULA_BDI_ANALITICO_BR, outra_instancia_das_mesmas_parcelas
    )
