"""Leitura de cabeçalho sem índice fixo, e conversão numérica segura.

Porquê: VERTICE-modulo-sinapi.md §2.1 é categórico — "nunca fixar o
índice da coluna no código". O layout já mudou entre insumo e
composição no mesmo arquivo; fixar índice é apostar contra o próprio
publicador da base.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

LIMITE_LINHAS_BUSCA_CABECALHO: int = 20
TAMANHO_SIGLA_UF: int = 2
CENTAVOS_POR_REAL: int = 100


def normalizar(texto: str | None) -> str:
    """Maiúsculo, sem acento — para comparar rótulo sem depender dele.

    Porquê: "Código" e "codigo" e "CÓDIGO" são o mesmo rótulo; exigir
    grafia exata quebraria no primeiro ano em que a Caixa mudar a caixa.
    """
    if texto is None:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return sem_acento.strip().upper()


def localizar_linha_cabecalho(
    linhas: Sequence[tuple[Any, ...]], rotulo_primeira_coluna: str
) -> int:
    """Devolve o índice (na sequência dada) da linha cujo rótulo bate.

    Porquê: a linha do cabeçalho varia entre abas do mesmo arquivo —
    detectar pelo conteúdo é a única forma de não hardcodar a posição.
    """
    alvo = normalizar(rotulo_primeira_coluna)
    limite = min(len(linhas), LIMITE_LINHAS_BUSCA_CABECALHO)
    for indice in range(limite):
        primeira_celula = linhas[indice][0] if linhas[indice] else None
        if normalizar(primeira_celula) == alvo:
            return indice
    raise ValueError(f"cabeçalho '{rotulo_primeira_coluna}' não encontrado")


def mapa_ufs_por_coluna_unica(
    cabecalho: Sequence[Any], colunas_validas: Iterable[str]
) -> dict[int, str]:
    """Uma UF por coluna — layout das abas de insumo (ISD/ICD/ISE).

    Porquê: cada estado é uma coluna só; basta reconhecer a sigla.
    """
    validas = frozenset(colunas_validas)
    mapa: dict[int, str] = {}
    for indice, valor in enumerate(cabecalho):
        sigla = normalizar(valor) if isinstance(valor, str) else ""
        if len(sigla) == TAMANHO_SIGLA_UF and sigla in validas:
            mapa[indice] = sigla
    return mapa


def mapa_ufs_por_par_de_colunas(
    linha_siglas: Sequence[Any], colunas_validas: Iterable[str]
) -> dict[str, tuple[int, int]]:
    """UF cobre duas colunas — layout das abas de composição (CSD/CCD/CSE).

    Porquê: `Custo (R$)` e `%AS` vêm em par sob uma sigla mesclada;
    a sigla só aparece na primeira das duas colunas.
    """
    validas = frozenset(colunas_validas)
    mapa: dict[str, tuple[int, int]] = {}
    for indice, valor in enumerate(linha_siglas):
        sigla = normalizar(valor) if isinstance(valor, str) else ""
        if len(sigla) == TAMANHO_SIGLA_UF and sigla in validas:
            mapa[sigla] = (indice, indice + 1)
    return mapa


def valor_para_centavos(bruto: Any) -> int | None:
    """Converte preço em reais (float da planilha) para centavo exato.

    Porquê: `arquitetura.md` §5.1 bane `REAL`/`float` do dado persistido.
    A fonte é float por natureza do `.xlsx` — o corte para exato
    acontece uma vez, aqui, nunca mais tarde na cadeia de cálculo.
    """
    if bruto is None or bruto == "":
        return None
    texto = str(bruto).strip().replace(",", ".")
    if texto in ("-", "0", "0.0"):
        # A própria aba anota: "Custo zerado (hífen) indica que pelo
        # menos um dos itens da composição não tem custo/preço" — 0
        # aqui não é um preço real, é ausência com outra máscara.
        # A razão de verdade mora em item_sinapi.situacao (SEM CUSTO).
        return None
    decimal = Decimal(texto).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return int(decimal * CENTAVOS_POR_REAL)


def valor_para_texto_decimal(bruto: Any) -> str | None:
    """Preserva coeficiente/percentual como texto, sem normalizar casas.

    Porquê: o `repr` do `float` do Python já é o menor texto que
    reproduz o mesmo valor — é o que a planilha realmente guarda,
    conforme conferido em amostra do pacote real (nenhum ruído de
    ponto flutuante nas primeiras ~1900 linhas de coeficiente lidas).
    """
    if bruto is None or bruto == "":
        return None
    if isinstance(bruto, float):
        return repr(bruto)
    return str(bruto).strip()
