"""Tipos persistidos de precificação — orçamento, BDI e fonte.

Porquê `Orcamento` mora aqui, não num módulo próprio: nenhum dos
módulos de `VERTICE-arquitetura.md` §3 declara "orçamento" como
segredo — `obra` (dono geométrico) e `orcamento` (dono financeiro,
referenciado por `bdi` em `VERTICE-modulo-precificacao.md` §3.5) nunca
ganharam tabela própria em documento nenhum. Até `measurement`
precisar de `obra` para valer, a versão financeira mínima mora onde
o primeiro consumidor real (`bdi`) está.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from core.pricing.bdi import ParcelasBdi, Regime


@dataclass(frozen=True)
class Fonte:
    """Uma citação — de onde um valor persistido veio, para humano ler.

    Porquê ao lado de `id_origem`, não no lugar dele: `arquitetura.md`
    §4.1 — `id_fonte` é a citação legível, `id_origem` é o ponteiro
    resolvível por máquina. Um orçamento cita `id_fonte`; uma
    auditoria de proveniência percorre `id_origem`. `VERTICE-modulo-cpu.md`
    §schema define a forma; este tipo só a reflete.
    """

    tipo: str
    nome: str
    item: str
    data_base: str
    confiabilidade: str
    url: str | None = None
    uso: str | None = None
    observacao: str | None = None


@dataclass(frozen=True)
class Orcamento:
    """O orçamento — regime, base e UF fixados na criação (§2.2 regra 1).

    Porquê sem método para trocar `regime`: `VERTICE-modulo-precificacao.md`
    §2.2 regra 3 — "não pode ser trocado sem recálculo explícito, com
    comparativo antes e depois item a item". Esse recálculo ainda não
    existe; até existir, o tipo recusa oferecer um jeito silencioso
    de trocar, mesmo que fosse só reatribuir um campo.
    """

    identificacao: str
    regime: Regime
    uf: str
    id_base: int
    data_base: str
    id_origem: str


@dataclass(frozen=True)
class RegistroBdi:
    """As parcelas do BDI de um orçamento, prontas para persistir (§3.5).

    Porquê `parcelas` é `ParcelasBdi`, não campos soltos repetidos:
    é o mesmo tipo que `calcular_bdi` já usa — persistir e calcular
    concordam sobre a forma por construção, não por convenção.
    """

    id_orcamento: int
    parcelas: ParcelasBdi
    municipio_iss: str
    base_iss: Decimal
    id_origem: str
    justificativa: str | None = None
    id_fonte: int | None = None
