"""Quantia: dinheiro exato, sempre centavo inteiro — VD-01 e arquitetura §5.1.

Porquê: `float` nunca representa R$ 0,10 exatamente, e a coluna
persistida é `INTEGER` de centavos, nunca `REAL` (§5.1). Centavo
inteiro soma, subtrai e ordena sem aproximação nenhuma. Exibir em
reais formatado é problema da exportação (`VERTICE-modulo-exportacao.md`
§4), não deste tipo — `Quantia` guarda dinheiro, não o mostra.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

CENTAVOS_POR_REAL: int = 100


@dataclass(frozen=True, order=True)
class Quantia:
    """Uma quantia em dinheiro, guardada como centavo inteiro.

    Porquê `order=True`: comparar quantias (curva ABC, maior custo
    primeiro) é comparação de `int`, exata — não há "quase igual" em
    dinheiro.
    """

    centavos: int

    @staticmethod
    def de_centavos(valor: int) -> Quantia:
        """Constrói direto do que o banco guarda — nunca arredonda de novo."""
        return Quantia(valor)

    @staticmethod
    def de_reais(valor: Decimal) -> Quantia:
        """Converte um valor em reais (`Decimal`) para centavo exato.

        Porquê exige `Decimal` na entrada, nunca `float`: a fronteira
        float→Decimal já devia ter sido cruzada antes de chegar aqui —
        ver `arquitetura.md` §5.1. Este construtor só arredonda o
        centavo, uma vez, com metade-par.
        """
        arredondado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        return Quantia(int(arredondado * CENTAVOS_POR_REAL))

    def para_reais(self) -> Decimal:
        """Devolve o valor em reais, exato — para cálculo, não para exibir."""
        return Decimal(self.centavos) / CENTAVOS_POR_REAL

    def __add__(self, outra: Quantia) -> Quantia:
        return Quantia(self.centavos + outra.centavos)

    def __sub__(self, outra: Quantia) -> Quantia:
        return Quantia(self.centavos - outra.centavos)

    def __neg__(self) -> Quantia:
        return Quantia(-self.centavos)

    def __mul__(self, fator: Decimal) -> Quantia:
        """Aplica um fator (markup, rateio) — arredonda uma vez, no fim.

        Porquê arredondar só no fim: arredondar a cada etapa de uma
        conta em cadeia acumula erro que some com o centavo real do
        orçamento — a mesma armadilha que a explosão analítica evita
        em `VERTICE-modulo-sinapi.md` §6.
        """
        produto = Decimal(self.centavos) * fator
        return Quantia(int(produto.to_integral_value(rounding=ROUND_HALF_EVEN)))


ZERO: Quantia = Quantia(0)
