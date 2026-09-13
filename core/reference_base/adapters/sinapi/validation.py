"""Portões V3, V5 e V6 de VERTICE-modulo-sinapi.md §3.1.

Porquê: V1 (estrutura) e V2 (metadados) já falham naturalmente — o
`ValueError` de `localizar_linha_cabecalho` e de `ler_metadados` é a
própria verificação. O que precisa de lógica própria é o que uma
planilha "estruturalmente perfeita" ainda pode errar em silêncio.
"""

from __future__ import annotations

from decimal import Decimal

from core.reference_base.constants import LIMIAR_V3_CODIGOS_DISTINTOS
from core.reference_base.types import RegistroComposicaoItem, RegistroItem


class RecuperacaoDivergente(ValueError):
    """V3 passo 3: Analítico e mão de obra discordam sobre um código.

    Porquê: S03 exige abortar diante de ambiguidade, nunca escolher
    um dos dois caminhos por conta própria.
    """


def coluna_de_codigo_esta_corrompida(codigos_brutos: list[object]) -> bool:
    """V3: cardinalidade de código abaixo de 90% é código corrompido."""
    if not codigos_brutos:
        return False
    distintos = len({_chave_bruta(c) for c in codigos_brutos})
    proporcao = Decimal(distintos) / Decimal(len(codigos_brutos))
    return proporcao < LIMIAR_V3_CODIGOS_DISTINTOS


def _chave_bruta(valor: object) -> object:
    """Formulas de HYPERLINK viram o texto inteiro — todas 'iguais'."""
    if isinstance(valor, str) and valor.startswith("="):
        return "=FORMULA="
    return valor


def conferir_recuperacao_cruzada(
    recuperacao_por_chave: dict[tuple[str, str], str],
    chave_por_codigo_mao_de_obra: dict[str, tuple[str, str]],
) -> None:
    """V3 passo 3: todo código da mão de obra deve bater com o Analítico.

    Porquê: a mão de obra nunca teve o incidente de zeragem — é a
    segunda fonte independente que a recuperação promete conferir.
    """
    mapa_codigo_por_chave = {v: k for k, v in recuperacao_por_chave.items()}
    for codigo, chave in chave_por_codigo_mao_de_obra.items():
        codigo_via_analitico = recuperacao_por_chave.get(chave)
        if codigo_via_analitico is not None and codigo_via_analitico != codigo:
            raise RecuperacaoDivergente(
                f"código {codigo} (mão de obra) diverge de "
                f"{codigo_via_analitico} (Analítico) para a chave {chave!r}"
            )
    if len(mapa_codigo_por_chave) != len(recuperacao_por_chave):
        raise RecuperacaoDivergente("Analítico tem chave com mais de um código")


def verificar_referencias_cruzadas(
    itens: list[RegistroComposicaoItem],
    catalogo_insumos: dict[str, RegistroItem],
    catalogo_composicoes: dict[str, RegistroItem],
) -> list[str]:
    """V6: todo `codigo_item` do Analítico existe em algum catálogo."""
    alertas = []
    for item in itens:
        catalogo = (
            catalogo_composicoes if item.tipo_item == "COMPOSICAO" else catalogo_insumos
        )
        if item.codigo_item not in catalogo:
            alertas.append(
                f"V6: item {item.codigo_item} ({item.tipo_item}) da composição "
                f"{item.codigo_composicao} não existe no catálogo importado"
            )
    return alertas
