"""Leitura da aba Analítico: catálogo de composição, arestas e recuperação.

Porquê: é a única aba do pacote com o código de composição íntegro
(VERTICE-modulo-sinapi.md §2.3). Uma passada só resolve três coisas —
reler o arquivo três vezes para separá-las custaria tempo de importação
sem trazer nada em troca.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple, cast

import openpyxl

from core.reference_base.adapters.sinapi.spreadsheet import (
    normalizar,
    valor_para_texto_decimal,
)
from core.reference_base.constants import TIPO_COMPOSICAO, TIPO_INSUMO
from core.reference_base.literals import TipoItem
from core.reference_base.types import RegistroComposicaoItem, RegistroItem

_PRIMEIRA_LINHA_DADO: int = 11
NUMERO_COLUNAS_ANALITICO: int = 8

ChaveRecuperacao = tuple[str, str]


class _LinhaAnalitico(NamedTuple):
    """As oito colunas da aba, já fatiadas — evita função de 8 parâmetros."""

    grupo: object
    codigo_composicao: object
    tipo_item: object
    codigo_item: object
    descricao: object
    unidade: object
    coeficiente: object
    situacao: object


@dataclass
class ResultadoAnalitico:
    """Tudo que a aba Analítico entrega numa passada só.

    Porquê: agrupar o retorno evita cinco funções que reabrem o mesmo
    arquivo de 66 mil linhas para calcular cada pedaço em separado.
    """

    catalogo_composicoes: dict[str, RegistroItem] = field(default_factory=dict)
    recuperacao_por_chave: dict[ChaveRecuperacao, str] = field(default_factory=dict)
    itens: list[RegistroComposicaoItem] = field(default_factory=list)
    situacao_por_insumo: dict[str, str] = field(default_factory=dict)
    # Insumo "SEM PREÇO" nunca aparece em ISD/ICD/ISE — a única
    # descrição e unidade disponíveis são as que o Analítico repete a
    # cada composição que o referencia. Sem isto, V6 acusa órfão que
    # não é órfão: é item real, só sem preço coletado (§2.3).
    catalogo_insumos_de_reserva: dict[str, RegistroItem] = field(default_factory=dict)


def ler_analitico(livro: openpyxl.Workbook) -> ResultadoAnalitico:
    """Lê a aba Analítico inteira e devolve catálogo, arestas e recuperação.

    Porquê `livro` já aberto: esta é a maior aba do pacote (66 mil
    linhas); abrir o arquivo de novo só para isto soma segundos que
    o §12 do documento pede para não desperdiçar.
    """
    aba = livro["Analítico"]
    resultado = ResultadoAnalitico()
    for bruta in aba.iter_rows(min_row=_PRIMEIRA_LINHA_DADO, values_only=True):
        linha = _LinhaAnalitico(*bruta[:NUMERO_COLUNAS_ANALITICO])
        if linha.grupo is None or linha.codigo_composicao is None:
            continue
        if linha.tipo_item is None:
            _registrar_cabecalho(resultado, linha)
        else:
            _registrar_item(resultado, linha)
    return resultado


def _registrar_cabecalho(resultado: ResultadoAnalitico, linha: _LinhaAnalitico) -> None:
    """Linha sem `Tipo Item`: é a própria composição, não um item dela."""
    codigo = str(linha.codigo_composicao)
    descricao = str(linha.descricao).strip() if linha.descricao else ""
    unidade = str(linha.unidade).strip() if linha.unidade else ""
    resultado.catalogo_composicoes[codigo] = RegistroItem(
        codigo=codigo,
        tipo=cast(TipoItem, TIPO_COMPOSICAO),
        grupo=str(linha.grupo).strip(),
        descricao=descricao,
        unidade=unidade,
        situacao=str(linha.situacao).strip() if linha.situacao else None,
    )
    chave = (normalizar(descricao), normalizar(unidade))
    resultado.recuperacao_por_chave[chave] = codigo


def _registrar_item(resultado: ResultadoAnalitico, linha: _LinhaAnalitico) -> None:
    """Linha com `Tipo Item`: é uma aresta composição → item."""
    eh_composicao = str(linha.tipo_item).strip() == "COMPOSICAO"
    tipo = cast(TipoItem, TIPO_COMPOSICAO if eh_composicao else TIPO_INSUMO)
    codigo_item = str(linha.codigo_item).strip()
    situacao = str(linha.situacao).strip() if linha.situacao else None
    resultado.itens.append(
        RegistroComposicaoItem(
            codigo_composicao=str(linha.codigo_composicao),
            tipo_item=tipo,
            codigo_item=codigo_item,
            coeficiente=valor_para_texto_decimal(linha.coeficiente) or "0",
            situacao=situacao,
        )
    )
    if tipo != TIPO_INSUMO:
        return
    if situacao:
        resultado.situacao_por_insumo[codigo_item] = situacao
    if codigo_item not in resultado.catalogo_insumos_de_reserva:
        resultado.catalogo_insumos_de_reserva[codigo_item] = RegistroItem(
            codigo=codigo_item,
            tipo=tipo,
            grupo=None,  # classificação (MATERIAL/SERVIÇOS) não vem no Analítico
            descricao=str(linha.descricao).strip() if linha.descricao else "",
            unidade=str(linha.unidade).strip() if linha.unidade else "",
            situacao=situacao,
        )
