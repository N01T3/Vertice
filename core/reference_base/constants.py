"""Constantes do adaptador SINAPI, ancoradas no pacote real 08/2026.

Porquê: número e string soltos no parser viram decisão invisível.
Tudo que é limiar, sigla ou vocabulário mora aqui, com nome que
explica o papel — a mesma regra de core/documents/constants.py.
"""

from __future__ import annotations

from decimal import Decimal

# `Regime`/`TipoItem` (em types.py) não são importados aqui de propósito:
# fariam de `constants` mais um importador de `types`, e o módulo já
# tem oito — o limite duro de VD-14. Quem precisa do tipo exato usa
# `typing.cast` no ponto de uso; o valor é o mesmo, só o rótulo muda.

# As 26 siglas de UF mais o Distrito Federal, exatamente como o
# cabeçalho do arquivo as grafa. Não incluir "BR" nem agregado nacional:
# a base não publica preço nacional, só por UF.
UFS_VALIDAS: frozenset[str] = frozenset(
    {
        "AC",
        "AL",
        "AM",
        "AP",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MG",
        "MS",
        "MT",
        "PA",
        "PB",
        "PE",
        "PI",
        "PR",
        "RJ",
        "RN",
        "RO",
        "RR",
        "RS",
        "SC",
        "SE",
        "SP",
        "TO",
    }
)

REGIME_ONERADO: str = "ONERADO"
REGIME_DESONERADO: str = "DESONERADO"
REGIME_SEM_ENCARGOS: str = "SEM_ENCARGOS"
REGIMES_VALIDOS: frozenset[str] = frozenset(
    {REGIME_ONERADO, REGIME_DESONERADO, REGIME_SEM_ENCARGOS}
)

TIPO_INSUMO: str = "INSUMO"
TIPO_COMPOSICAO: str = "COMPOSICAO"

# Aba de insumo e de composição, por regime — abas do arquivo
# SINAPI_Referência, conforme VERTICE-modulo-sinapi.md §2.1.
ABA_INSUMO_POR_REGIME: dict[str, str] = {
    REGIME_ONERADO: "ISD",
    REGIME_DESONERADO: "ICD",
    REGIME_SEM_ENCARGOS: "ISE",
}
ABA_COMPOSICAO_POR_REGIME: dict[str, str] = {
    REGIME_ONERADO: "CSD",
    REGIME_DESONERADO: "CCD",
    REGIME_SEM_ENCARGOS: "CSE",
}
ABA_ANALITICO: str = "Analítico"

# Rótulo de cabeçalho que identifica a linha de coluna em cada aba.
# Buscado por igualdade após normalização (maiúsculo, sem acento).
ROTULO_CABECALHO_INSUMO: str = "CLASSIFICACAO"
ROTULO_CABECALHO_COMPOSICAO: str = "GRUPO"
ROTULO_MES_REFERENCIA: str = "MES DE REFERENCIA:"
ROTULO_DATA_EMISSAO: str = "DATA DE EMISSAO:"

# V3: abaixo disto, a coluna de código está corrompida — o incidente
# real do pacote 07/2026 motivou a regra (VERTICE-modulo-sinapi.md §3).
# Decimal, não float: é comparado por igualdade/ordem em validation.py,
# e VD-01 não abre exceção para "não é dinheiro, mas também não seria
# menos exato como Decimal".
LIMIAR_V3_CODIGOS_DISTINTOS: Decimal = Decimal("0.9")

# Explosão analítica: limite duro contra ciclo, e tolerância de
# arredondamento ao comparar com o custo sintético publicado (§6).
PROFUNDIDADE_MAXIMA_EXPLOSAO: int = 30
TOLERANCIA_ARREDONDAMENTO_CENTAVOS: int = 2

# Manutenções cujo tipo bloqueia o código em orçamento novo (§7).
MANUTENCOES_BLOQUEIAM: frozenset[str] = frozenset(
    {"DESATIVAÇÃO", "COMPOSIÇÃO SUSPENSA"}
)
MANUTENCAO_ALTERACAO_UNIDADE: str = "ALTERAÇÃO DE UNIDADE"

# Situações do vocabulário oficial, importadas como estão (§2.3):
# não normalizar para não perder distinção que a base publicou.
SITUACOES_CONHECIDAS: frozenset[str] = frozenset(
    {"COM CUSTO", "SEM CUSTO", "COM PREÇO", "SEM PREÇO", "EM ESTUDO"}
)

NOME_TABELA_FTS: str = "busca_sinapi"
