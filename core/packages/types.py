"""Formas do manifesto de pacote — VERTICE-plataforma.md §3.

Porquê tipado, não um `dict` cru circulando pelo núcleo: um pacote mal
escrito vira erro de atributo em qualquer lugar que o lê. Validar a
forma uma vez, na fronteira, é o que faz o resto do núcleo confiar
no formato sem checar de novo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Classificacao:
    """A taxonomia declarada pelo pacote — nunca a do núcleo."""

    padrao: str
    eixos: tuple[str, ...]
    arquivo: str


@dataclass(frozen=True)
class BasePreco:
    """Uma base de referência que o pacote registra pelo nome do adaptador.

    Porquê só o nome, não a implementação: ADR-018 — "registrar
    adaptadores de base por nome" é o que o pacote pode; "implementar
    o adaptador" é o que ele não pode (`VERTICE-plataforma.md` §3.1).
    """

    adaptador: str
    rotulo: str
    oficial: bool
    regimes: tuple[str, ...]
    granularidade_geografica: str | None


@dataclass(frozen=True)
class ModeloMarkup:
    """A fórmula de markup declarada — ADR-019, nunca hardcoded no núcleo.

    Porquê `formula` é `str`, não um objeto de fórmula: o núcleo
    (`core.domain.markup.calcular_markup`) é quem entende a sintaxe;
    aqui ela é só o texto que o pacote escreveu.
    """

    modelo: str
    parcelas: tuple[str, ...]
    tributos_sobre_faturamento: tuple[str, ...]
    formula: str
    referencias_externas: tuple[str, ...]


@dataclass(frozen=True)
class PacoteDominio:
    """Um pacote de domínio, já com a forma validada.

    Porquê `bruto` ao lado dos campos tipados: `tipologias`,
    `antagonista` e `pesquisa` do manifesto ainda não têm consumidor
    no núcleo — tipá-los agora seria adivinhar a forma antes do
    segundo caso concreto (o mesmo critério de ADR-018).
    """

    dominio: str
    caminho_raiz: Path
    unidades: tuple[str, ...]
    classificacao: Classificacao
    bases_preco: tuple[BasePreco, ...]
    regras_medicao_glob: str
    markup: ModeloMarkup
    custos_fora_do_markup: tuple[dict[str, str], ...] = field(default_factory=tuple)
    bruto: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ResultadoInstalacao:
    """O que `instalar` devolve — pacote carregado e o que a validação achou."""

    pacote: PacoteDominio
    alertas: list[str]
