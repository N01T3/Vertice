"""BDI analítico — VERTICE-modulo-precificacao.md §3.

Porquê `calcular_bdi` exige a fórmula como argumento, em vez de trazer
uma constante embutida: ADR-019 — "BDI é uma instância declarada no
pacote", não um número do núcleo. A instância real mora em
`packages/civil-construction-br/package.yaml` (`markup.formula`),
carregada por `core.packages.loader.carregar`. Este módulo sabe
*calcular* um BDI; ele nunca decide qual fórmula é a certa.

`ParcelasBdi` continua tipado com os nove campos do modelo
`bdi-analitico-br`, não um `dict[str, Decimal]` genérico: são as
parcelas *desta* instância de markup, documentadas por nome em
`VERTICE-modulo-precificacao.md` §3.1 — tipar dá segurança sem
reintroduzir a fórmula como constante.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from core.domain.markup import calcular_markup
from core.reference_base.literals import (
    Regime as Regime,
)  # reexportado: core.pricing.types o usa

# Faixas do Acórdão 2622/2013 do TCU — VERTICE-modulo-precificacao.md §3.3.
LIMIAR_1_QUARTIL_TCU: Decimal = Decimal("0.2034")
LIMIAR_MEDIO_TCU: Decimal = Decimal("0.2212")
LIMIAR_3_QUARTIL_TCU: Decimal = Decimal("0.25")

FaixaTcu = Literal[
    "ABAIXO_1_QUARTIL",
    "ENTRE_1_QUARTIL_E_MEDIO",
    "ENTRE_MEDIO_E_3_QUARTIL",
    "ACIMA_3_QUARTIL",
]


@dataclass(frozen=True)
class ParcelasBdi:
    """As nove parcelas da fórmula — cada uma, um percentual decimal.

    Porquê nomeadas por extenso, não pelas siglas da fórmula: quem lê
    o cadastro do orçamento não devia precisar saber que "AC" é
    administração central — a sigla é vocabulário da fórmula, não do
    usuário. `como_simbolos` faz a tradução na fronteira.
    """

    administracao_central: Decimal
    seguro_garantia: Decimal
    risco: Decimal
    despesas_financeiras: Decimal
    lucro: Decimal
    pis: Decimal
    cofins: Decimal
    iss: Decimal
    cprb: Decimal

    def como_simbolos(self) -> dict[str, Decimal]:
        """Traduz nome por extenso para a sigla que a fórmula usa."""
        return {
            "AC": self.administracao_central,
            "SG": self.seguro_garantia,
            "R": self.risco,
            "DF": self.despesas_financeiras,
            "L": self.lucro,
            "PIS": self.pis,
            "COFINS": self.cofins,
            "ISS": self.iss,
            "CPRB": self.cprb,
        }


def calcular_bdi(formula: str, parcelas: ParcelasBdi) -> Decimal:
    """O percentual de BDI — nunca guardado, sempre recalculado (§3.5).

    Porquê `formula` vem de fora: é o texto declarado em
    `packages/civil-construction-br/package.yaml` (`markup.formula`),
    não uma escolha deste módulo — ver o porquê do arquivo.

    Porquê nunca guardar o resultado: `VERTICE-modulo-precificacao.md`
    §3.5 — "guardar o resultado permitiria que ele divergisse das
    entradas... é exatamente como planilha antiga passa a mentir".
    """
    return calcular_markup(formula, parcelas.como_simbolos())


def classificar_faixa_tcu(bdi: Decimal) -> FaixaTcu:
    """Posiciona o BDI composto contra as faixas do TCU — nunca bloqueia (§3.3)."""
    if bdi < LIMIAR_1_QUARTIL_TCU:
        return "ABAIXO_1_QUARTIL"
    if bdi < LIMIAR_MEDIO_TCU:
        return "ENTRE_1_QUARTIL_E_MEDIO"
    if bdi < LIMIAR_3_QUARTIL_TCU:
        return "ENTRE_MEDIO_E_3_QUARTIL"
    return "ACIMA_3_QUARTIL"


def exige_justificativa(bdi: Decimal) -> bool:
    """P04: acima do 3º quartil, a exportação exige justificativa escrita."""
    return classificar_faixa_tcu(bdi) == "ACIMA_3_QUARTIL"


def verificar_coerencia_de_regime(regime: Regime, parcelas: ParcelasBdi) -> list[str]:
    """P03: CPRB positivo em regime onerado é dupla contagem — alerta, não trava.

    Porquê alerta, não exceção: ADR-012 — "nada trava". Cabe ao
    antagonista transformar isto em objeção; esta função só detecta
    o fato, na regra 5 de `VERTICE-modulo-precificacao.md` §2.2.
    """
    if regime == "ONERADO" and parcelas.cprb != Decimal(0):
        return [
            "CPRB maior que zero em regime onerado é dupla contagem "
            "(VERTICE-modulo-precificacao.md §2.2, regra 5)"
        ]
    return []
