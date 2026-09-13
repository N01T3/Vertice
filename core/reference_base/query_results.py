"""Resultado de leitura: o que `search.py` e `explosion.py` devolvem.

Porquê separado de `types.py`: aquele arquivo tipa o que a *ingestão*
grava; este tipa o que a *consulta* lê de volta. `search.py` nunca
precisou de `RegistroPreco`, e `persistence.py` nunca precisou de
`NoExplosao` — dois arquivos, cada um só com o que o seu lado usa.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.reference_base.literals import Regime, TipoItem


@dataclass(frozen=True)
class ResultadoBusca:
    """Uma linha de resultado da busca textual em `busca_sinapi`."""

    codigo: str
    tipo: TipoItem
    descricao: str
    grupo: str | None
    unidade: str
    id_base: int


@dataclass(frozen=True)
class NoExplosao:
    """Um nó resolvido na explosão analítica — item ou subcomposição.

    Porquê: a árvore inteira, não só o total, é o que permite ao
    orçamentista conferir a conta em vez de confiar cegamente nela.
    """

    codigo: str
    tipo: TipoItem
    descricao: str
    unidade: str
    coeficiente_acumulado: str
    custo_unitario_centavos: int | None
    custo_total_centavos: int | None
    filhos: list[NoExplosao] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoExplosao:
    """O resultado de explodir uma composição numa UF e regime."""

    codigo_raiz: str
    uf: str
    regime: Regime
    custo_total_centavos: int | None
    completo: bool
    arvore: NoExplosao
