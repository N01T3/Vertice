"""A prova de ADR-019: a fórmula do pacote produz o mesmo BDI do CME.

Porquê este teste existe separado dos outros dois: `tests/pricing/`
prova que o motor calcula certo dada uma fórmula; `tests/packages/`
prova que o manifesto carrega certo. Nenhum dos dois, sozinho, prova
que o motor e o manifesto real *concordam* — só rodar os dois juntos
prova isso, e é exatamente o que ADR-019 promete.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from core.packages.loader import carregar
from core.pricing.bdi import ParcelasBdi, calcular_bdi

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


def test_formula_do_pacote_real_reproduz_a_ancora_do_cme() -> None:
    """A fórmula que o pacote declara — não uma cópia dela — dá 23,6245%."""
    pacote = carregar(Path("packages/civil-construction-br/package.yaml"))
    bdi = calcular_bdi(pacote.markup.formula, PARCELAS_CME)
    assert round(bdi, 4) == Decimal("0.2362")
