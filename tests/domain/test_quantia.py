"""Quantia: centavo inteiro, nunca float — VD-01 e arquitetura §5.1."""

from __future__ import annotations

from decimal import Decimal

from core.domain.quantia import ZERO, Quantia


def test_de_reais_arredonda_meio_par() -> None:
    """Fronteira Decimal->centavo é aqui, uma vez só."""
    assert Quantia.de_reais(Decimal("40.635")).centavos == 4064  # metade-par sobe
    assert Quantia.de_reais(Decimal("40.625")).centavos == 4062  # metade-par desce


def test_ida_e_volta_preserva_o_valor() -> None:
    original = Decimal("1234.56")
    assert Quantia.de_reais(original).para_reais() == original


def test_soma_e_subtracao_sao_exatas() -> None:
    a = Quantia.de_centavos(1050)
    b = Quantia.de_centavos(325)
    assert (a + b).centavos == 1375
    assert (a - b).centavos == 725
    assert (-a).centavos == -1050


def test_multiplicacao_por_fator_arredonda_uma_vez_no_fim() -> None:
    """VERTICE-modulo-sinapi.md §6: arredondar por etapa acumula erro."""
    base = Quantia.de_centavos(333)
    resultado = base * Decimal("3")
    assert resultado.centavos == 999


def test_ordenacao_e_por_centavo_exato() -> None:
    barato = Quantia.de_centavos(100)
    caro = Quantia.de_centavos(200)
    assert barato < caro
    assert sorted([caro, barato]) == [barato, caro]


def test_zero_e_elemento_neutro_da_soma() -> None:
    valor = Quantia.de_centavos(777)
    assert (valor + ZERO) == valor
