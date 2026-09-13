"""Tipos do adaptador SINAPI.

Porquê: a fronteira entre "linha de planilha" e "linha de banco" é
onde o número mágico e o float entram sem avisar. Tipar essa fronteira
é o que torna o parser revisável sem reabrir o Excel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal

from core.reference_base.literals import Regime, TipoItem

__all__ = [
    "MetadadosArquivo",
    "Regime",
    "RegistroComposicaoItem",
    "RegistroItem",
    "RegistroManutencao",
    "RegistroPreco",
    "ResultadoImportacao",
    "ResultadoRecuperacao",
    "TipoItem",
]


@dataclass(frozen=True)
class MetadadosArquivo:
    """Identidade do arquivo lido, para a linha de `base_referencia`.

    Porquê: sem hash e nome, a mesma base pode ser importada duas
    vezes sem que ninguém perceba — o oposto de ADR-008.
    """

    caminho: Path
    hash_sha256: str
    mes_referencia: str
    data_emissao: str


@dataclass(frozen=True)
class RegistroItem:
    """Uma linha de catálogo: um insumo ou uma composição.

    Porquê: `item_sinapi` não guarda preço, só identidade — preço
    muda por UF e regime, identidade não.
    """

    codigo: str
    tipo: TipoItem
    grupo: str | None
    descricao: str
    unidade: str
    situacao: str | None


@dataclass(frozen=True)
class RegistroPreco:
    """Um preço publicado: código, UF e regime definem a linha.

    Porquê: `valor_centavos` é None quando a UF não teve coleta —
    None e zero são fatos diferentes, e a tabela precisa distingui-los.
    """

    codigo: str
    tipo: TipoItem
    uf: str
    regime: Regime
    valor_centavos: int | None
    percentual_as: str | None


@dataclass(frozen=True)
class RegistroComposicaoItem:
    """Um item dentro de uma composição, com o coeficiente exato.

    Porquê: é a aresta do grafo que a explosão percorre; sem ela
    a composição é só um preço publicado, não uma conta auditável.
    """

    codigo_composicao: str
    tipo_item: TipoItem
    codigo_item: str
    coeficiente: str
    situacao: str | None


@dataclass(frozen=True)
class RegistroManutencao:
    """Um evento do ciclo de vida de um código, do arquivo mensal."""

    referencia: str
    tipo: str
    codigo: str
    descricao: str | None
    manutencao: str


@dataclass(frozen=True)
class ResultadoRecuperacao:
    """O que a recuperação de código (V3) fez, para o relatório.

    Porquê: `VERTICE-modulo-sinapi.md` §3.2 exige que a auditoria saiba
    que a base foi reconstruída, não só que ela foi importada.
    """

    aconteceu: bool
    metodo: Literal["ANALITICO", "MAO_DE_OBRA"] | None
    itens_recuperados: int


@dataclass(frozen=True)
class ResultadoImportacao:
    """Sumário devolvido ao fim da importação — nunca em silêncio."""

    id_base: int
    total_composicoes: int
    total_insumos: int
    total_precos: int
    recuperacao: ResultadoRecuperacao
    tempo_segundos: Decimal
    alertas: list[str] = field(default_factory=list)
