"""Gramática do id_origem, conforme VERTICE-arquitetura.md §4.1.

Porquê: o formato é dono único. Definido aqui, é lido pelo código que
emite, pelo teste-âncora e pelo portão VD-16 — três leitores, uma verdade.
Repetir a expressão em cada um deles é como a regra diverge sem ninguém ver.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

RAIZES_ID_ORIGEM: Final[tuple[str, ...]] = (
    "GEO",
    "BASE",
    "USUARIO",
    "DOC",
    "ACHADO",
    "CALCULO",
)

EXPRESSAO_ID_ORIGEM: Final[re.Pattern[str]] = re.compile(
    r"^(?:" + "|".join(RAIZES_ID_ORIGEM) + r"):[\w._/-]+(?:#[\w._:/-]+)?$"
)

# Texto livre que vira endereço: tudo fora do alfabeto colapsa em hífen.
ALFABETO_ID_ORIGEM: Final[re.Pattern[str]] = re.compile(r"[^\w._-]+")


def resolve(id_origem: str) -> bool:
    """Diz se o id_origem está na gramática de §4.1.

    Porquê: a auditoria de proveniência A11 varre campo numérico órfão.
    Sem um predicado único, cada varredura inventa o seu e discordam.
    """
    return bool(EXPRESSAO_ID_ORIGEM.match(id_origem))


def sanear_endereco(bruto: str, limite: int, vazio: str) -> str:
    """Reduz texto livre ao alfabeto do id_origem sem perder a pista.

    Porquê: nome de arquivo real tem espaço e parêntese; descartar o
    endereço por causa disso seria perder a origem para agradar a regex.
    """
    limpo = ALFABETO_ID_ORIGEM.sub("-", bruto.strip()).strip("-")
    return limpo[:limite] or vazio


class OrigemInvalida(ValueError):
    """Um `id_origem` fora da gramática de §4.1 tentou virar `Origem`.

    Porquê: regra 1 de `VERTICE-REGRAS.md` — "a IA nunca produz número
    mágico" — só é impossibilidade de verdade se o tipo que carrega a
    origem recusar existir sem uma origem válida, não apenas se alguém
    lembrar de chamar `resolve()` antes de usar o `str`.
    """


@dataclass(frozen=True)
class Origem:
    """Um `id_origem` validado — nunca um `str` cru que pode estar fora da gramática.

    Porquê tipo, não `str`: `item_orcamento.origem_quantidade` e afins
    hoje guardam texto livre; nada impede um `"chute"` de entrar no
    lugar de `"USUARIO:rt-01#..."`. `Origem` fecha essa porta no
    próprio construtor, não numa checagem que alguém pode esquecer.
    """

    id_origem: str

    def __post_init__(self) -> None:
        if not resolve(self.id_origem):
            raise OrigemInvalida(
                f"fora da gramática de arquitetura §4.1: {self.id_origem!r}"
            )

    @property
    def raiz(self) -> str:
        """A raiz — GEO, BASE, USUARIO, DOC, ACHADO ou CALCULO."""
        return self.id_origem.split(":", 1)[0]

    def __str__(self) -> str:
        return self.id_origem
